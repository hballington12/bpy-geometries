import bpy
import random
import math
from mathutils import Euler, Vector
from .geometry import Geometry


class Inclusions(Geometry):
    def __init__(
        self,
        geometry: Geometry,
        num_inclusions: int,
        inclusion_radius: float,
    ):
        super().__init__(geometry.output_dir)
        self.geometry: Geometry = geometry
        self.num_inclusions: int = num_inclusions
        self.inclusion_radius: float = inclusion_radius
        self.inclusion_height: float = inclusion_radius * 3 * math.sqrt(3) / 4

    def _calculate_bounding_box(self, obj: bpy.types.Object) -> tuple:
        """
        Calculate the axis-aligned bounding box of the object.

        Returns:
            tuple: (min_x, max_x, min_y, max_y, min_z, max_z)
        """
        # Get bounding box corners in world coordinates
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

        min_x = min(corner.x for corner in bbox_corners)
        max_x = max(corner.x for corner in bbox_corners)
        min_y = min(corner.y for corner in bbox_corners)
        max_y = max(corner.y for corner in bbox_corners)
        min_z = min(corner.z for corner in bbox_corners)
        max_z = max(corner.z for corner in bbox_corners)

        return (min_x, max_x, min_y, max_y, min_z, max_z)

    def _create_triangular_pyramid(self, name: str) -> bpy.types.Object:
        """
        Create a triangular pyramid using a Cone primitive with 3 vertices.

        Returns:
            bpy.types.Object: The created pyramid object
        """
        bpy.ops.mesh.primitive_cone_add(
            vertices=3,
            radius1=self.inclusion_radius,
            depth=self.inclusion_height,
            location=(0, 0, 0),
        )
        pyramid = bpy.context.active_object
        pyramid.name = name
        return pyramid

    def _get_center_of_mass(self, obj: bpy.types.Object):
        """
        Calculate the center of mass of the object.

        Returns:
            Vector: The center of mass in world coordinates
        """
        # For a cone, Blender places the origin at the base center by default
        # For a pyramid with height h, the center of mass is at h/4 from base
        # Since the cone is created along Z-axis with base at origin
        # We need to adjust for the actual geometry

        # Use Blender's built-in bound_box to get the geometric center
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        center = sum(
            (corner for corner in bbox_corners), start=bbox_corners[0].copy()
        ) / len(bbox_corners)
        return center

    def _random_position_in_bbox(self, bbox: tuple):
        """
        Generate a random position within the bounding box.

        Args:
            bbox: (min_x, max_x, min_y, max_y, min_z, max_z)

        Returns:
            tuple: (x, y, z) random position
        """
        min_x, max_x, min_y, max_y, min_z, max_z = bbox
        x = random.uniform(min_x, max_x)
        y = random.uniform(min_y, max_y)
        z = random.uniform(min_z, max_z)
        return (x, y, z)

    def _random_orientation(self):
        """
        Generate random Euler angles for random 3D orientation.

        Returns:
            Euler: Random rotation angles
        """
        x = random.uniform(0, 2 * math.pi)
        y = random.uniform(0, 2 * math.pi)
        z = random.uniform(0, 2 * math.pi)
        return Euler((x, y, z), "XYZ")

    def _apply_boolean_difference(
        self, target_obj: bpy.types.Object, subtract_obj: bpy.types.Object
    ):
        """
        Apply a boolean DIFFERENCE modifier to target_obj, subtracting subtract_obj.

        Args:
            target_obj: The object to modify
            subtract_obj: The object to subtract from target_obj
        """
        # Add boolean modifier
        bool_mod = target_obj.modifiers.new(name="Boolean", type="BOOLEAN")
        bool_mod.operation = "DIFFERENCE"
        bool_mod.object = subtract_obj

        # Apply the modifier
        bpy.context.view_layer.objects.active = target_obj
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    def to_filename(self) -> str:
        """Return complete filename without extension."""
        geom_filename = self.geometry.to_filename()
        radius_str = f"{self.inclusion_radius:.1f}".replace(".", "p")
        return f"inclusions_n{self.num_inclusions}_r{radius_str}_{geom_filename}"

    def generate(self) -> str:
        """
        Generate the base geometry with inclusions and export.
        """
        # Clear scene and create base geometry
        self._clear_scene()
        base_obj = self._create_base_geometry_object(self.geometry)

        print(f"Created base geometry: {type(self.geometry).__name__}")
        print(f"Number of inclusions: {self.num_inclusions}")
        print(f"Inclusion radius: {self.inclusion_radius}")
        print(f"Inclusion height: {self.inclusion_height:.4f}")
        print()

        # Calculate bounding box of base geometry
        bbox = self._calculate_bounding_box(base_obj)
        print(
            f"Bounding box: x[{bbox[0]:.2f}, {bbox[1]:.2f}], "
            f"y[{bbox[2]:.2f}, {bbox[3]:.2f}], "
            f"z[{bbox[4]:.2f}, {bbox[5]:.2f}]"
        )
        print()

        # Create a single pyramid that we'll reuse
        pyramid = self._create_triangular_pyramid("InclusionPyramid")

        # Process each inclusion
        for i in range(self.num_inclusions):
            print(f"Processing inclusion {i + 1}/{self.num_inclusions}")

            # Get current center of mass
            current_center = self._get_center_of_mass(pyramid)

            # Generate random target position and orientation
            target_pos = self._random_position_in_bbox(bbox)
            random_rot = self._random_orientation()

            # Calculate translation needed to move center of mass to target
            translation = (
                target_pos[0] - current_center.x,
                target_pos[1] - current_center.y,
                target_pos[2] - current_center.z,
            )

            # Apply rotation first (around current center)
            pyramid.rotation_euler = random_rot

            # Then translate to target position
            pyramid.location = (
                pyramid.location.x + translation[0],
                pyramid.location.y + translation[1],
                pyramid.location.z + translation[2],
            )

            print(
                f"  Position: ({target_pos[0]:.2f}, {target_pos[1]:.2f}, {target_pos[2]:.2f})"
            )
            print(
                f"  Rotation: ({random_rot.x:.2f}, {random_rot.y:.2f}, {random_rot.z:.2f})"
            )

            # Apply boolean difference
            self._apply_boolean_difference(base_obj, pyramid)
            print(f"  Applied boolean difference")

        # Delete the pyramid helper geometry
        bpy.data.objects.remove(pyramid, do_unlink=True)
        print(f"\nDeleted inclusion helper geometry")

        # Export the final geometry
        filename = f"{self.to_filename()}.obj"
        filepath = self._export_obj(filename)

        print(f"\nExported to: {filepath}")
        return filepath

    def _create_base_geometry_object(self, geometry: Geometry) -> bpy.types.Object:
        """Create the base geometry object in the scene without exporting."""
        if hasattr(geometry, "_create_geometry"):
            return geometry._create_geometry()
        else:
            raise NotImplementedError(
                f"Inclusions wrapper doesn't support {type(geometry).__name__} yet. "
                f"The geometry class must be updated to work with Inclusions. "
                f"Add a _create_geometry() method that returns the mesh object without exporting."
            )
