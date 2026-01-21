import bpy
import bmesh
import random
from .geometry import Geometry


class Roughened(Geometry):
    def __init__(
        self,
        geometry: Geometry,
        max_edge_length: float,
        displacement_sigma: float,
        merge_distance: float,
    ):
        super().__init__(geometry.output_dir)
        self.geometry: Geometry = geometry
        self.max_edge_length: float = max_edge_length
        self.displacement_sigma: float = displacement_sigma
        self.merge_distance: float = merge_distance

    def subdivide_until_max_edge_length(self, obj: bpy.types.Object):
        """
        Subdivide mesh edges until all edges are <= max_edge_length.

        Algorithm:
        1. Initial triangulation with FIXED method
        2. Check all edges
        3. If any edge > max_edge_length, subdivide once
        4. Triangulate all faces with BEAUTY method
        5. Repeat until no edges exceed max_edge_length
        """
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")

        # Perform initial triangulation with FIXED algorithm
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY", ngon_method="CLIP")

        max_iterations = 100
        iteration = 0

        while iteration < max_iterations:
            bpy.ops.mesh.select_all(action="DESELECT")

            # Get mesh data
            bm = bmesh.from_edit_mesh(obj.data)
            bm.edges.ensure_lookup_table()

            # Check if any edges exceed max length
            edges_to_subdivide = []
            max_edge_found = 0.0

            for edge in bm.edges:
                edge_length = edge.calc_length()
                if edge_length > self.max_edge_length:
                    edges_to_subdivide.append(edge)
                    edge.select = True
                    max_edge_found = max(max_edge_found, edge_length)

            bmesh.update_edit_mesh(obj.data)

            # If no edges exceed max length, we're done
            if not edges_to_subdivide:
                print(f"Subdivision complete after {iteration} iterations")
                break

            print(
                f"Iteration {iteration + 1}: Found {len(edges_to_subdivide)} edges to subdivide (max: {max_edge_found:.4f})"
            )

            # Subdivide selected edges once
            bpy.ops.mesh.subdivide(number_cuts=1)

            # Triangulate all faces using BEAUTY algorithm for subsequent iterations
            # quad_method options: 'BEAUTY', 'FIXED', 'FIXED_ALTERNATE', 'SHORTEST_DIAGONAL', 'LONG_EDGE'
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.quads_convert_to_tris(quad_method="SHORTEST_DIAGONAL")

            iteration += 1

        if iteration >= max_iterations:
            print(f"Warning: Reached maximum iterations ({max_iterations})")

        bpy.ops.object.mode_set(mode="OBJECT")

    def apply_random_displacement(self, obj: bpy.types.Object):
        """
        Apply random displacement to each vertex along its normal vector.

        Displacement = random(-sigma, sigma) * vertex_normal
        """
        if self.displacement_sigma == 0.0:
            print("Displacement sigma is 0.0, skipping displacement")
            return

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")

        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.normal_update()

        displaced_count = 0

        for vert in bm.verts:
            # Generate random displacement value between -sigma and +sigma
            displacement_amount = random.uniform(
                -self.displacement_sigma, self.displacement_sigma
            )

            # Displace vertex along its normal
            vert.co += vert.normal * displacement_amount
            displaced_count += 1

        bmesh.update_edit_mesh(obj.data)
        print(
            f"Applied random displacement to {displaced_count} vertices (sigma={self.displacement_sigma})"
        )

        bpy.ops.object.mode_set(mode="OBJECT")

    def merge_vertices_by_distance(self, obj: bpy.types.Object):
        """
        Merge vertices that are within merge_distance of each other.
        """
        if self.merge_distance <= 0.0:
            print("Merge distance is <= 0.0, skipping vertex merge")
            return

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")

        # Merge vertices by distance
        bpy.ops.mesh.remove_doubles(threshold=self.merge_distance)

        bpy.ops.object.mode_set(mode="OBJECT")
        print(f"Merged vertices within distance {self.merge_distance}")

    def to_filename(self) -> str:
        """Return complete filename without extension."""
        sigma_str = f"{self.displacement_sigma:.1f}".replace(".", "p")
        merge_str = f"{self.merge_distance:.1f}".replace(".", "p")
        geom_filename = self.geometry.to_filename()
        return f"roughened_edge{self.max_edge_length}_sigma{sigma_str}_merge{merge_str}_{geom_filename}"

    def generate(self) -> str:
        """
        Generate the wrapped geometry, apply roughness, and export.
        """
        # First, generate the base geometry (creates object in scene)
        self._clear_scene()

        base_geometry = self.geometry

        # Create the geometry object - geometry must implement _create_geometry() method
        obj = self._create_base_geometry_object(base_geometry)

        print(f"Created base geometry: {type(base_geometry).__name__}")
        print(f"Target max edge length: {self.max_edge_length}")
        print(f"Displacement sigma: {self.displacement_sigma}")
        print(f"Merge distance: {self.merge_distance}")
        print()

        # Apply roughening
        self.subdivide_until_max_edge_length(obj)
        self.apply_random_displacement(obj)
        self.merge_vertices_by_distance(obj)

        # Export with modified filename
        filename = f"{self.get_full_filename()}.obj"
        filepath = self._export_obj(filename)

        print(f"\nExported to: {filepath}")
        return filepath

    def _create_geometry(self) -> bpy.types.Object:
        """Create the roughened geometry object without exporting."""
        # Create the base geometry
        base_geometry = self.geometry
        obj = self._create_base_geometry_object(base_geometry)

        print(f"Created base geometry: {type(base_geometry).__name__}")
        print(f"Target max edge length: {self.max_edge_length}")
        print(f"Displacement sigma: {self.displacement_sigma}")
        print(f"Merge distance: {self.merge_distance}")
        print()

        # Apply roughening
        self.subdivide_until_max_edge_length(obj)
        self.apply_random_displacement(obj)
        self.merge_vertices_by_distance(obj)

        return obj

    def _create_base_geometry_object(self, geometry: Geometry) -> bpy.types.Object:
        """Create the base geometry object in the scene without exporting."""
        # All Geometry subclasses should implement _create_geometry()
        if hasattr(geometry, "_create_geometry"):
            return geometry._create_geometry()
        else:
            raise NotImplementedError(
                f"Roughened wrapper doesn't support {type(geometry).__name__} yet. "
                f"The geometry class must be updated to work with Roughened. "
                f"Add a _create_geometry() method that returns the mesh object without exporting."
            )
