"""
Aggregate geometry where monomers intersect (overlap).

Algorithm:
1. Create first monomer at origin
2. For each subsequent monomer:
   a. Create new monomer at origin with random orientation (uniform on SO(3))
   b. Rotate existing aggregate randomly
   c. Position monomer above aggregate, move down until intersection detected
   d. If no intersection found, re-rotate aggregate and retry
   e. Merge monomer into aggregate (boolean union)
"""

import bpy
import math
import numpy as np
from mathutils import Quaternion, Vector
from .geometry import Geometry


class AggregateIntersecting(Geometry):
    """
    Create an aggregate of intersecting (overlapping) monomers.

    Monomers are positioned using a "drop from above" approach,
    stopping as soon as intersection is detected. Each monomer gets
    a random orientation uniformly sampled from SO(3).
    """

    def __init__(
        self,
        geometry: Geometry,
        output_dir: str,
        num_monomers: int = None,
        target_diameter: float = None,
        seed: int = None,
        binary_search_steps: int = 10,
        max_retries: int = 10,
    ):
        """
        Args:
            geometry: Base geometry to use as monomer
            output_dir: Directory to save output files
            num_monomers: Fixed number of monomers (mutually exclusive with target_diameter)
            target_diameter: Target aggregate diameter - stop when reached (mutually exclusive with num_monomers)
            seed: Random seed for reproducibility
            binary_search_steps: Number of steps when searching for intersection
            max_retries: Maximum retries if no intersection found (re-rotates aggregate)
        """
        super().__init__(output_dir)
        self.geometry = geometry

        if num_monomers is None and target_diameter is None:
            raise ValueError("Either num_monomers or target_diameter must be specified")
        if num_monomers is not None and target_diameter is not None:
            raise ValueError("Cannot specify both num_monomers and target_diameter")

        self.num_monomers = num_monomers
        self.target_diameter = target_diameter
        self.seed = seed
        self.binary_search_steps = binary_search_steps
        self.max_retries = max_retries

        self._rng = np.random.default_rng(seed)

    def _random_quaternion(self) -> Quaternion:
        """
        Generate a uniformly distributed random quaternion on SO(3).

        Uses the subgroup algorithm (Shoemake, 1992).
        """
        u1, u2, u3 = self._rng.random(3)

        w = math.sqrt(1 - u1) * math.sin(2 * math.pi * u2)
        x = math.sqrt(1 - u1) * math.cos(2 * math.pi * u2)
        y = math.sqrt(u1) * math.sin(2 * math.pi * u3)
        z = math.sqrt(u1) * math.cos(2 * math.pi * u3)

        return Quaternion((w, x, y, z))

    def _get_bounding_box_z_extent(
        self, obj: bpy.types.Object
    ) -> tuple[float, float, float]:
        """Get Z extent of object's bounding box in world coordinates."""
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        z_coords = [corner.z for corner in bbox_corners]
        return min(z_coords), max(z_coords), max(z_coords) - min(z_coords)

    def _get_max_planar_diameter(self, obj: bpy.types.Object) -> float:
        """Get the maximum planar diameter (XY, XZ, or YZ) of the object."""
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        x_coords = [corner.x for corner in bbox_corners]
        y_coords = [corner.y for corner in bbox_corners]
        z_coords = [corner.z for corner in bbox_corners]

        x_extent = max(x_coords) - min(x_coords)
        y_extent = max(y_coords) - min(y_coords)
        z_extent = max(z_coords) - min(z_coords)

        xy_diameter = max(x_extent, y_extent)
        xz_diameter = max(x_extent, z_extent)
        yz_diameter = max(y_extent, z_extent)

        return max(xy_diameter, xz_diameter, yz_diameter)

    def _check_intersection(
        self, obj1: bpy.types.Object, obj2: bpy.types.Object
    ) -> bool:
        """Check if two objects intersect using boolean modifier."""
        bpy.ops.object.select_all(action="DESELECT")
        obj1.select_set(True)
        bpy.context.view_layer.objects.active = obj1

        bpy.ops.object.modifier_add(type="BOOLEAN")
        boolean_mod = obj1.modifiers[-1]
        boolean_mod.operation = "INTERSECT"
        boolean_mod.object = obj2
        boolean_mod.solver = "EXACT"

        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj1.evaluated_get(depsgraph)

        has_intersection = len(obj_eval.data.vertices) > 0

        bpy.ops.object.modifier_remove(modifier=boolean_mod.name)

        return has_intersection

    def _apply_rotation(self, obj: bpy.types.Object):
        """Apply rotation transform to object."""
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        obj.select_set(False)

    def _apply_location(self, obj: bpy.types.Object):
        """Apply location transform to object."""
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        obj.select_set(False)

    def _translate_until_intersecting(
        self, monomer: bpy.types.Object, aggregate: bpy.types.Object
    ) -> bool:
        """
        Move monomer down until intersection is detected.

        If no intersection is found after binary_search_steps, re-rotates
        aggregate and tries again up to max_retries times.

        Returns True if intersection found, False if all retries exhausted.
        """
        for retry in range(self.max_retries):
            _, _, monomer_height = self._get_bounding_box_z_extent(monomer)
            _, agg_z_max, agg_height = self._get_bounding_box_z_extent(aggregate)

            # Start with monomer well above aggregate
            initial_z = agg_z_max + monomer_height
            monomer.location.z = initial_z
            bpy.context.view_layer.update()

            # Move down until we hit intersection
            step_size = agg_height + monomer_height

            for _ in range(self.binary_search_steps):
                # First move down
                monomer.location.z -= step_size
                bpy.context.view_layer.update()

                has_intersection = self._check_intersection(monomer, aggregate)

                if has_intersection:
                    # Found intersection - done
                    return True

                # Halve step size for next iteration
                step_size = step_size / 2

            # No intersection found - re-rotate aggregate and try again
            agg_quat = self._random_quaternion()
            aggregate.rotation_mode = "QUATERNION"
            aggregate.rotation_quaternion = agg_quat
            bpy.context.view_layer.update()
            self._apply_rotation(aggregate)

        return False

    def _merge_objects(
        self, target: bpy.types.Object, source: bpy.types.Object
    ) -> bpy.types.Object:
        """Merge source into target using boolean union."""
        bpy.ops.object.select_all(action="DESELECT")
        target.select_set(True)
        bpy.context.view_layer.objects.active = target

        bpy.ops.object.modifier_add(type="BOOLEAN")
        boolean_mod = target.modifiers[-1]
        boolean_mod.operation = "UNION"
        boolean_mod.object = source
        boolean_mod.solver = "EXACT"

        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        # Delete source object
        bpy.ops.object.select_all(action="DESELECT")
        source.select_set(True)
        bpy.ops.object.delete()

        return target

    def to_filename(self) -> str:
        geom_filename = self.geometry.to_filename()
        seed_str = f"_s{self.seed}" if self.seed is not None else ""

        if self.num_monomers is not None:
            return f"aggregate_intersecting_n{self.num_monomers}{seed_str}_{geom_filename}"
        else:
            diameter_str = f"{self.target_diameter:.1f}".replace(".", "p")
            return f"aggregate_intersecting_d{diameter_str}{seed_str}_{geom_filename}"

    def _create_geometry(self) -> bpy.types.Object:
        aggregate = None
        monomer_count = 0

        def should_continue() -> bool:
            if self.num_monomers is not None:
                return monomer_count < self.num_monomers
            else:
                if aggregate is None:
                    return True
                diameter = self._get_max_planar_diameter(aggregate)
                return diameter < self.target_diameter

        while should_continue():
            monomer = self.geometry._create_geometry()
            monomer.name = f"Monomer_{monomer_count}"

            if aggregate is None:
                # First monomer becomes the aggregate
                aggregate = monomer
                aggregate.name = "Aggregate"
                self._apply_rotation(aggregate)
                self._apply_location(aggregate)
            else:
                # Apply random orientation to new monomer
                quat = self._random_quaternion()
                monomer.rotation_mode = "QUATERNION"
                monomer.rotation_quaternion = quat
                bpy.context.view_layer.update()
                self._apply_rotation(monomer)

                # Rotate aggregate randomly before dropping new monomer
                agg_quat = self._random_quaternion()
                aggregate.rotation_mode = "QUATERNION"
                aggregate.rotation_quaternion = agg_quat
                bpy.context.view_layer.update()
                self._apply_rotation(aggregate)

                # Move down until intersection
                success = self._translate_until_intersecting(monomer, aggregate)
                if not success:
                    raise RuntimeError(
                        f"Failed to find intersection after {self.max_retries} retries"
                    )
                self._apply_location(monomer)

                # Merge into aggregate
                aggregate = self._merge_objects(aggregate, monomer)

            monomer_count += 1

        return aggregate

    def generate(self) -> str:
        self._clear_scene()
        self._create_geometry()

        filename = f"{self.get_full_filename()}.obj"
        filepath = self._export_obj(filename)

        return filepath
