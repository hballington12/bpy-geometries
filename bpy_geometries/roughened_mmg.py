"""
Roughened geometry using MMG mesh refinement.

Uses the mmgs tool for high-quality isotropic mesh refinement,
followed by vertex displacement along normals and vertex merging.

Requires mmgs binary - see vendor/README.md for installation instructions.
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import bpy
import meshio
import numpy as np

from .geometry import Geometry


def _find_mmgs_binary() -> Path | None:
    """
    Find mmgs binary in standard locations.

    Search order:
    1. BPY_GEOMETRIES_MMGS_PATH environment variable
    2. {repo}/vendor/mmg/build/bin/mmgs_O3
    3. System PATH (via shutil.which)

    Returns Path to binary or None if not found.
    """
    # 1. Environment variable
    env_path = os.environ.get("BPY_GEOMETRIES_MMGS_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path

    # 2. Vendor directory
    repo_root = Path(__file__).parent.parent
    vendor_path = repo_root / "vendor" / "mmg" / "build" / "bin" / "mmgs_O3"
    if vendor_path.exists():
        return vendor_path

    # 3. System PATH
    system_path = shutil.which("mmgs_O3") or shutil.which("mmgs")
    if system_path:
        return Path(system_path)

    return None


class RoughenedMMG(Geometry):
    """
    Apply surface roughness using MMG mesh refinement.

    This class wraps another geometry and applies high-quality mesh
    refinement using the mmgs tool, followed by random vertex displacement
    along surface normals.

    MMG produces better quality meshes than Blender's subdivision,
    with isotropic triangulation that respects the specified maximum
    edge length.

    Requires mmgs binary to be installed. See vendor/README.md for
    installation instructions.
    """

    def __init__(
        self,
        geometry: Geometry,
        # Displacement - exactly one required
        sigma: float = None,
        sigma_percent: float = None,
        # Edge length - exactly one required
        hmax: float = None,
        hmax_percent: float = None,
        # Merge distance - at most one, defaults to 1%
        merge_distance: float = None,
        merge_percent: float = None,
        # RNG seed
        seed: int = None,
    ):
        """
        Args:
            geometry: Base geometry to roughen
            sigma: Absolute displacement magnitude (mutually exclusive with sigma_percent)
            sigma_percent: Displacement as percentage of mesh size (mutually exclusive with sigma)
            hmax: Absolute maximum edge length (mutually exclusive with hmax_percent)
            hmax_percent: Max edge length as percentage of mesh size (mutually exclusive with hmax)
            merge_distance: Absolute merge distance (mutually exclusive with merge_percent)
            merge_percent: Merge distance as percentage of mesh size (default 1.0)
            seed: Random seed for reproducible displacement
        """
        super().__init__(geometry.output_dir)
        self.geometry = geometry

        # Validate sigma parameters
        if sigma is None and sigma_percent is None:
            raise ValueError("Specify exactly one of sigma or sigma_percent")
        if sigma is not None and sigma_percent is not None:
            raise ValueError("Specify exactly one of sigma or sigma_percent")

        # Validate hmax parameters
        if hmax is None and hmax_percent is None:
            raise ValueError("Specify exactly one of hmax or hmax_percent")
        if hmax is not None and hmax_percent is not None:
            raise ValueError("Specify exactly one of hmax or hmax_percent")

        # Validate merge parameters (defaults to 1% if neither specified)
        if merge_distance is not None and merge_percent is not None:
            raise ValueError("Specify at most one of merge_distance or merge_percent")
        if merge_distance is None and merge_percent is None:
            merge_percent = 1.0

        self.sigma = sigma
        self.sigma_percent = sigma_percent
        self.hmax = hmax
        self.hmax_percent = hmax_percent
        self.merge_distance = merge_distance
        self.merge_percent = merge_percent
        self.seed = seed

        self._rng = np.random.default_rng(seed)

        # Find mmgs binary
        self._mmgs_path = _find_mmgs_binary()
        if self._mmgs_path is None:
            raise RuntimeError(
                "mmgs binary not found. Install MMG and either:\n"
                "  1. Set BPY_GEOMETRIES_MMGS_PATH environment variable\n"
                "  2. Run scripts/install_mmg.sh to install to vendor/\n"
                "  3. Add mmgs to your system PATH\n"
                "See vendor/README.md for installation instructions."
            )

    def _get_mesh_bounds(self, mesh: meshio.Mesh) -> tuple[np.ndarray, np.ndarray, float]:
        """Get mesh bounding box and max dimension."""
        points = mesh.points
        min_bounds = points.min(axis=0)
        max_bounds = points.max(axis=0)
        dimensions = max_bounds - min_bounds
        max_dim = float(dimensions.max())
        return min_bounds, max_bounds, max_dim

    def _compute_vertex_normals(self, mesh: meshio.Mesh) -> np.ndarray:
        """
        Compute per-vertex normals by averaging adjacent face normals.

        Returns array of shape (n_vertices, 3) with unit normals.
        """
        points = mesh.points
        normals = np.zeros_like(points)

        # Find triangle cells
        triangles = None
        for cell_block in mesh.cells:
            if cell_block.type == "triangle":
                triangles = cell_block.data
                break

        if triangles is None:
            raise ValueError("No triangles found in mesh")

        # Accumulate face normals at each vertex
        for tri in triangles:
            v0, v1, v2 = points[tri[0]], points[tri[1]], points[tri[2]]
            face_normal = np.cross(v1 - v0, v2 - v0)
            norm = np.linalg.norm(face_normal)
            if norm > 1e-10:
                face_normal /= norm
            for idx in tri:
                normals[idx] += face_normal

        # Normalize
        norms = np.linalg.norm(normals, axis=1, keepdims=True)
        norms[norms < 1e-10] = 1.0
        normals /= norms

        return normals

    def _apply_displacement(self, mesh: meshio.Mesh, sigma: float) -> meshio.Mesh:
        """Apply random displacement along vertex normals."""
        if sigma == 0.0:
            return mesh

        normals = self._compute_vertex_normals(mesh)
        displacements = self._rng.uniform(-sigma, sigma, size=len(mesh.points))
        mesh.points = mesh.points + normals * displacements[:, np.newaxis]

        return mesh

    def _merge_close_vertices(self, mesh: meshio.Mesh, merge_distance: float) -> meshio.Mesh:
        """Merge vertices within merge_distance of each other."""
        if merge_distance <= 0:
            return mesh

        points = mesh.points
        merged_to = np.arange(len(points))

        # Find vertices to merge
        for i in range(len(points)):
            if merged_to[i] != i:
                continue
            for j in range(i + 1, len(points)):
                if merged_to[j] != j:
                    continue
                if np.linalg.norm(points[i] - points[j]) < merge_distance:
                    merged_to[j] = i

        # Build new vertex list
        unique_indices = np.where(merged_to == np.arange(len(points)))[0]
        new_points = points[unique_indices]

        # Build index mapping
        old_to_new = np.zeros(len(points), dtype=int)
        for new_idx, old_idx in enumerate(unique_indices):
            old_to_new[old_idx] = new_idx
        for i in range(len(points)):
            if merged_to[i] != i:
                old_to_new[i] = old_to_new[merged_to[i]]

        # Remap cells and remove degenerate triangles
        new_cells = []
        for cell_block in mesh.cells:
            new_data = old_to_new[cell_block.data]
            if cell_block.type == "triangle":
                # Remove triangles where any two vertices are the same
                valid = (
                    (new_data[:, 0] != new_data[:, 1])
                    & (new_data[:, 1] != new_data[:, 2])
                    & (new_data[:, 0] != new_data[:, 2])
                )
                new_data = new_data[valid]
            new_cells.append(meshio.CellBlock(cell_block.type, new_data))

        return meshio.Mesh(new_points, new_cells)

    def _run_mmgs(self, input_path: Path, output_dir: Path, hmax: float) -> Path | None:
        """
        Run mmgs on input mesh file.

        Args:
            input_path: Path to input .mesh file
            output_dir: Directory for output
            hmax: Maximum edge length

        Returns:
            Path to output .mesh file, or None on failure
        """
        result = subprocess.run(
            [
                str(self._mmgs_path),
                "-hmax", str(hmax),
                "-nomove",
                "-ar", "1",
                str(input_path),
            ],
            capture_output=True,
            text=True,
            cwd=output_dir,
        )

        if result.returncode != 0:
            print(f"mmgs failed: {result.stderr[:200]}")
            return None

        # Find output file (mmgs adds .o.mesh suffix)
        output_files = list(output_dir.glob("*.o.mesh"))
        if not output_files:
            print("Could not find mmgs output file")
            return None

        return output_files[0]

    def _roughen_mesh(self, input_obj_path: Path, output_obj_path: Path) -> bool:
        """
        Roughen a mesh using MMG refinement and displacement.

        Args:
            input_obj_path: Path to input OBJ file
            output_obj_path: Path for output OBJ file

        Returns:
            True on success, False on failure
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)

            # Read input mesh
            try:
                mesh = meshio.read(str(input_obj_path))
            except Exception as e:
                print(f"Error reading mesh: {e}")
                return False

            # Compute absolute values from percentages
            _, _, max_dim = self._get_mesh_bounds(mesh)

            if self.sigma_percent is not None:
                sigma = max_dim * self.sigma_percent / 100.0
            else:
                sigma = self.sigma

            if self.hmax_percent is not None:
                hmax = max_dim * self.hmax_percent / 100.0
            else:
                hmax = self.hmax

            if self.merge_percent is not None:
                merge_dist = max_dim * self.merge_percent / 100.0
            else:
                merge_dist = self.merge_distance or 0.0

            # Write to MESH format for MMG
            mesh_file = tmp_dir / "input.mesh"
            try:
                meshio.write(str(mesh_file), mesh)
            except Exception as e:
                print(f"Error writing MESH file: {e}")
                return False

            # Fix ref values (MMG quirk - needs 0 instead of 1/-1)
            with open(mesh_file, "r") as f:
                content = f.read()
            content = re.sub(r" 1$", " 0", content, flags=re.MULTILINE)
            content = re.sub(r" -1$", " 0", content, flags=re.MULTILINE)
            with open(mesh_file, "w") as f:
                f.write(content)

            # Run MMG refinement
            refined_path = self._run_mmgs(mesh_file, tmp_dir, hmax)
            if refined_path is None:
                return False

            # Read refined mesh
            try:
                refined_mesh = meshio.read(str(refined_path))
            except Exception as e:
                print(f"Error reading refined mesh: {e}")
                return False

            # Apply displacement and merge
            refined_mesh = self._apply_displacement(refined_mesh, sigma)
            refined_mesh = self._merge_close_vertices(refined_mesh, merge_dist)

            # Write output OBJ
            try:
                # Keep only triangles
                triangle_cells = [
                    cb for cb in refined_mesh.cells if cb.type == "triangle"
                ]
                if not triangle_cells:
                    print("No triangles in output mesh")
                    return False

                output_mesh = meshio.Mesh(refined_mesh.points, triangle_cells)
                meshio.write(str(output_obj_path), output_mesh)
            except Exception as e:
                print(f"Error writing output OBJ: {e}")
                return False

        return True

    def _export_base_geometry(self, obj: bpy.types.Object, output_path: Path) -> None:
        """Export Blender object to triangulated OBJ."""
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        # Triangulate
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY", ngon_method="BEAUTY")
        bpy.ops.object.mode_set(mode="OBJECT")

        # Export
        bpy.ops.wm.obj_export(
            filepath=str(output_path),
            export_selected_objects=True,
            export_triangulated_mesh=True,
            export_normals=False,
            export_uv=False,
            export_materials=False,
        )
        obj.select_set(False)

    def _import_obj(self, obj_path: Path, name: str) -> bpy.types.Object:
        """Import OBJ file into Blender and fix normals."""
        bpy.ops.wm.obj_import(filepath=str(obj_path))
        obj = bpy.context.selected_objects[0]
        obj.name = name

        # Fix face orientation (MMG/meshio can flip winding)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        obj.select_set(False)

        return obj

    def to_filename(self) -> str:
        """Return filename parameters without extension or UUID."""
        # Format sigma
        if self.sigma is not None:
            sigma_str = f"sigma{self.sigma:.2f}".replace(".", "p")
        else:
            sigma_str = f"sigma{self.sigma_percent:.1f}pct".replace(".", "p")

        # Format hmax
        if self.hmax is not None:
            hmax_str = f"hmax{self.hmax:.2f}".replace(".", "p")
        else:
            hmax_str = f"hmax{self.hmax_percent:.1f}pct".replace(".", "p")

        geom_filename = self.geometry.to_filename()
        return f"roughened_mmg_{sigma_str}_{hmax_str}_{geom_filename}"

    def _create_geometry(self) -> bpy.types.Object:
        """Create the roughened geometry object without exporting."""
        # Create base geometry
        if hasattr(self.geometry, "_create_geometry"):
            base_obj = self.geometry._create_geometry()
        else:
            raise NotImplementedError(
                f"RoughenedMMG wrapper doesn't support {type(self.geometry).__name__}. "
                f"The geometry class must implement _create_geometry()."
            )

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)

            # Export base geometry
            pristine_path = tmp_dir / "pristine.obj"
            self._export_base_geometry(base_obj, pristine_path)

            # Remove base object from scene
            bpy.data.objects.remove(base_obj, do_unlink=True)

            # Roughen
            roughened_path = tmp_dir / "roughened.obj"
            success = self._roughen_mesh(pristine_path, roughened_path)

            if not success:
                raise RuntimeError("MMG roughening failed")

            # Import roughened mesh
            obj = self._import_obj(roughened_path, "RoughenedMMG")

        return obj

    def generate(self) -> str:
        """Generate the roughened geometry and export to OBJ file."""
        self._clear_scene()
        self._create_geometry()

        filename = f"{self.get_full_filename()}.obj"
        filepath = self._export_obj(filename)

        return filepath
