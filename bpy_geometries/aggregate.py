import bpy
import bmesh
import random
import math
from mathutils import Vector, Euler
from .geometry import Geometry


class Aggregate(Geometry):
    def __init__(
        self,
        geometry: Geometry,
        output_dir: str,
        num_monomers: int = None,
        target_diameter: float = None,
    ):
        super().__init__(output_dir)
        self.geometry: Geometry = geometry

        if num_monomers is None and target_diameter is None:
            raise ValueError("Either num_monomers or target_diameter must be specified")
        if num_monomers is not None and target_diameter is not None:
            raise ValueError("Cannot specify both num_monomers and target_diameter")

        self.num_monomers: int = num_monomers
        self.target_diameter: float = target_diameter

    def _get_bounding_box_z_height(self, obj: bpy.types.Object) -> float:
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        z_coords = [corner.z for corner in bbox_corners]
        return max(z_coords) - min(z_coords)

    def _get_planar_diameters(self, obj: bpy.types.Object) -> dict:
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        x_coords = [corner.x for corner in bbox_corners]
        y_coords = [corner.y for corner in bbox_corners]
        z_coords = [corner.z for corner in bbox_corners]

        x_min = min(x_coords)
        x_max = max(x_coords)
        y_min = min(y_coords)
        y_max = max(y_coords)
        z_min = min(z_coords)
        z_max = max(z_coords)

        x_extent = x_max - x_min
        y_extent = y_max - y_min
        z_extent = z_max - z_min

        xy_diameter = max(x_extent, y_extent)
        xz_diameter = max(x_extent, z_extent)
        yz_diameter = max(y_extent, z_extent)

        print(
            f"Bounding box: x=[{x_min:.2f}, {x_max:.2f}], y=[{y_min:.2f}, {y_max:.2f}], z=[{z_min:.2f}, {z_max:.2f}]"
        )
        print(f"Extents: x={x_extent:.2f}, y={y_extent:.2f}, z={z_extent:.2f}")
        print(
            f"Planar diameters: XY={xy_diameter:.2f}, XZ={xz_diameter:.2f}, YZ={yz_diameter:.2f}"
        )

        return {
            "xy": xy_diameter,
            "xz": xz_diameter,
            "yz": yz_diameter,
        }

    def _check_intersection(
        self, obj1: bpy.types.Object, obj2: bpy.types.Object
    ) -> bool:
        bpy.ops.object.select_all(action="DESELECT")
        obj1.select_set(True)
        bpy.context.view_layer.objects.active = obj1

        bpy.ops.object.modifier_add(type="BOOLEAN")
        boolean_mod = obj1.modifiers[-1]
        boolean_mod.operation = "INTERSECT"
        boolean_mod.object = obj2
        boolean_mod.solver = "FAST"

        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj1.evaluated_get(depsgraph)

        has_intersection = len(obj_eval.data.vertices) > 0

        bpy.ops.object.modifier_remove(modifier=boolean_mod.name)

        return has_intersection

    def _apply_random_rotation(self, obj: bpy.types.Object):
        rotation_angles = (
            random.uniform(0, 2 * math.pi),
            random.uniform(0, 2 * math.pi),
            random.uniform(0, 2 * math.pi),
        )
        obj.rotation_euler = rotation_angles
        bpy.context.view_layer.update()

    def _translate_until_touching(
        self, monomer: bpy.types.Object, aggregate: bpy.types.Object
    ):
        monomer_bb = self._get_bounding_box_z_height(monomer)
        aggregate_bb = self._get_bounding_box_z_height(aggregate)

        initial_translation = (aggregate_bb + monomer_bb) / 2
        monomer.location.z += initial_translation
        bpy.context.view_layer.update()

        num_steps = 10

        for step in range(num_steps):
            step_size = monomer_bb / (2**step)

            has_intersection = self._check_intersection(monomer, aggregate)

            if has_intersection:
                monomer.location.z += step_size
            else:
                monomer.location.z -= step_size

            bpy.context.view_layer.update()

    def _merge_objects(
        self, target: bpy.types.Object, source: bpy.types.Object
    ) -> bpy.types.Object:
        bpy.ops.object.select_all(action="DESELECT")
        target.select_set(True)
        bpy.context.view_layer.objects.active = target

        bpy.ops.object.modifier_add(type="BOOLEAN")
        boolean_mod = target.modifiers[-1]
        boolean_mod.operation = "UNION"
        boolean_mod.object = source
        boolean_mod.solver = "EXACT"

        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        bpy.ops.object.select_all(action="DESELECT")
        source.select_set(True)
        bpy.ops.object.delete()

        return target

    def to_filename(self) -> str:
        geom_filename = self.geometry.to_filename()
        if self.num_monomers is not None:
            return f"aggregate_n{self.num_monomers}_{geom_filename}"
        else:
            diameter_str = f"{self.target_diameter:.1f}".replace(".", "p")
            return f"aggregate_d{diameter_str}_{geom_filename}"

    def _create_geometry(self) -> bpy.types.Object:
        aggregate = None

        if self.num_monomers is not None:
            for i in range(self.num_monomers):
                monomer = self.geometry._create_geometry()
                monomer.name = f"Monomer_{i}"

                if aggregate is None:
                    aggregate = monomer
                    aggregate.name = "Aggregate"
                else:
                    self._apply_random_rotation(aggregate)
                    bpy.ops.object.transform_apply(
                        location=False, rotation=True, scale=False
                    )

                    self._translate_until_touching(monomer, aggregate)
                    bpy.ops.object.transform_apply(
                        location=True, rotation=False, scale=False
                    )

                    aggregate = self._merge_objects(aggregate, monomer)
        else:
            i = 0
            while True:
                monomer = self.geometry._create_geometry()
                monomer.name = f"Monomer_{i}"

                if aggregate is None:
                    aggregate = monomer
                    aggregate.name = "Aggregate"
                    print(f"Monomer {i}: Created first monomer")
                    i += 1
                    continue

                print(f"\nMonomer {i}: Adding monomer...")

                self._apply_random_rotation(aggregate)
                bpy.ops.object.transform_apply(
                    location=False, rotation=True, scale=False
                )

                self._translate_until_touching(monomer, aggregate)
                bpy.ops.object.transform_apply(
                    location=True, rotation=False, scale=False
                )

                aggregate = self._merge_objects(aggregate, monomer)
                i += 1

                print(f"Monomer {i - 1}: Merged. Checking aggregate diameters...")
                diameters = self._get_planar_diameters(aggregate)

                if (
                    diameters["xy"] >= self.target_diameter
                    or diameters["xz"] >= self.target_diameter
                    or diameters["yz"] >= self.target_diameter
                ):
                    print(
                        f"Target diameter {self.target_diameter:.2f} reached! Stopping."
                    )
                    break

                print(f"Target: {self.target_diameter:.2f}, continuing...")

        return aggregate

    def generate(self) -> str:
        self._clear_scene()

        obj = self._create_geometry()

        filename = f"{self.get_full_filename()}.obj"
        filepath = self._export_obj(filename)

        return filepath
