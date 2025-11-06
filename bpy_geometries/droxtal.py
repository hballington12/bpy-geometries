import bpy
import bmesh
import math
from .geometry import Geometry


class Droxtal(Geometry):
    """
    A droxtal is a complex ice crystal geometry formed by cutting and scaling
    a hexagonal column at specific angles.

    The geometry is defined by:
    - A hexagonal column with calculated height and base radius
    - Two cuts parallel to the basal facets at calculated z-positions
    - Scaled basal facets based on angle relationships

    The angles theta1 (32.35°) and theta2 (71.81°) are fixed geometric properties
    of droxtals.
    """

    # Hardcoded angle relationships for droxtal geometry
    THETA1_DEG = 32.35
    THETA2_DEG = 71.81

    def __init__(self, radius: float, output_dir: str):
        """
        Initialize a droxtal geometry.

        Args:
            radius: The characteristic radius (R) that defines the droxtal size
            output_dir: Directory where OBJ file will be exported
        """
        super().__init__(output_dir)
        self.radius: float = radius

        # Calculate derived parameters
        self._theta1_rad = math.radians(self.THETA1_DEG)
        self._theta2_rad = math.radians(self.THETA2_DEG)

        # Validate calculations
        if abs(math.sin(self._theta2_rad)) < 1e-9:
            raise ValueError(
                "sin(theta2) is too close to zero, scaling factor is undefined"
            )
        if abs(math.cos(self._theta1_rad)) < 1e-9:
            raise ValueError(
                "cos(theta1) is too close to zero, cannot determine cut positions"
            )

        # Calculate geometry parameters
        self.height = 2 * self.radius * math.cos(self._theta1_rad)
        self.base_radius = self.radius * math.sin(self._theta2_rad)
        self.scale_factor = math.sin(self._theta1_rad) / math.sin(self._theta2_rad)

        # Calculate cut position
        if abs(math.cos(self._theta2_rad)) < 1e-9:
            self.z_cut = 0.0
        else:
            self.z_cut = self.radius * math.cos(self._theta2_rad)

    def _scale_face_vertices(self, bm_face, center, scale_factor):
        """
        Scale the vertices of a face radially around its center in the XY plane.
        Assumes face normal is primarily along Z.

        Args:
            bm_face: BMesh face to scale
            center: Center point of the face
            scale_factor: Factor to scale by
        """
        z_coord = center.z  # Keep original Z height
        for v in bm_face.verts:
            # Vector in XY plane from center to vertex
            vec_xy = v.co.xy - center.xy
            # Scale the XY vector
            scaled_vec_xy = vec_xy * scale_factor
            # Update vertex XY position
            v.co.xy = center.xy + scaled_vec_xy
            # Ensure Z coordinate remains unchanged
            v.co.z = z_coord

    def _create_geometry(self) -> bpy.types.Object:
        """Create the droxtal geometry and return the object without exporting."""
        # Create the hexagonal column
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=6, radius=self.base_radius, depth=self.height, location=(0, 0, 0)
        )

        obj = bpy.context.active_object
        if obj is None or obj.type != "MESH":
            raise Exception("Failed to create or retrieve the cylinder mesh")

        # Create cuts using BMesh
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        # Ensure lookup tables are updated
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # Perform Cut 1 (Upper)
        bmesh.ops.bisect_plane(
            bm,
            geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            plane_co=(0, 0, self.z_cut),
            plane_no=(0, 0, 1),  # Normal points up
            clear_inner=False,
            clear_outer=False,
        )

        # Update geometry references after first cut
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        all_geom = bm.verts[:] + bm.edges[:] + bm.faces[:]

        # Perform Cut 2 (Lower)
        bmesh.ops.bisect_plane(
            bm,
            geom=all_geom,
            plane_co=(0, 0, -self.z_cut),
            plane_no=(0, 0, -1),  # Normal points down
            clear_inner=False,
            clear_outer=False,
        )

        # Update geometry references after second cut
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # Find the top and bottom hexagonal faces to scale
        top_face = None
        bottom_face = None
        max_z = -float("inf")
        min_z = float("inf")

        for f in bm.faces:
            if len(f.verts) == 6:  # Hexagonal face
                center = f.calc_center_median()
                if center.z > max_z:
                    max_z = center.z
                    top_face = f
                if center.z < min_z:
                    min_z = center.z
                    bottom_face = f

        # Scale the basal facets
        if top_face and bottom_face:
            top_center = top_face.calc_center_median()
            bottom_center = bottom_face.calc_center_median()

            self._scale_face_vertices(top_face, top_center, self.scale_factor)
            self._scale_face_vertices(bottom_face, bottom_center, self.scale_factor)
        else:
            raise Exception("Could not identify top and/or bottom faces for scaling")

        # Update mesh and clean up BMesh
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()

        return obj

    def to_filename(self) -> str:
        """Return complete filename without extension."""
        radius_str = str(self.radius).replace(".", "p")
        return f"droxtal_r{radius_str}"

    def generate(self) -> str:
        """Generate the droxtal geometry and export to OBJ file."""
        self._clear_scene()
        obj = self._create_geometry()

        filename = f"{self.to_filename()}.obj"
        filepath = self._export_obj(filename)

        return filepath
