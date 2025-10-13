import bpy
import math
import random
from mathutils import Vector, Euler
from .geometry import Geometry
from .hexagonal_bullet import HexagonalBullet


class HexagonalBulletRosette(Geometry):
    def __init__(
        self,
        length: float,
        radius: float,
        indentation_factor: float,
        inset: float,
        num_bullets: int,
        output_dir: str,
    ):
        super().__init__(output_dir)
        self.length: float = length
        self.radius: float = radius
        self.indentation_factor: float = indentation_factor
        self.inset: float = inset
        self.num_bullets: int = num_bullets
        self.rotation_factor: float = 1.0
        self.tolerance: float = 0.001

    def _compute_column_axis_vector(self, rotation_angles: tuple) -> Vector:
        euler = Euler(rotation_angles, "XYZ")
        rotation_matrix = euler.to_matrix()
        local_z = Vector((0, 0, 1))
        k_vector = rotation_matrix @ local_z
        return k_vector

    def _check_column_overlap(
        self,
        k_new: Vector,
        radius_new: float,
        length_new: float,
        k_existing: Vector,
        radius_existing: float,
        length_existing: float,
    ) -> bool:
        dot_product = k_new.dot(k_existing)
        dot_product = max(-1.0, min(1.0, dot_product))
        angle = math.acos(abs(dot_product))

        if angle > math.pi / 2:
            return False

        angle_half = angle / 2
        sin_half_angle = math.sin(angle_half)
        sum_radii = radius_new + radius_existing
        min_length = min(length_new, length_existing)
        overlap_threshold = sum_radii / (2 * min_length)

        return sin_half_angle < overlap_threshold

    def _find_non_overlapping_rotation(
        self, existing_columns: list, max_attempts: int = 100
    ) -> tuple:
        for attempt in range(max_attempts):
            rotation_angles = (
                random.uniform(0, 2 * math.pi * self.rotation_factor),
                random.uniform(0, 2 * math.pi * self.rotation_factor),
                random.uniform(0, 2 * math.pi * self.rotation_factor),
            )

            k_new = self._compute_column_axis_vector(rotation_angles)

            overlaps = False
            for k_existing, radius_existing, length_existing in existing_columns:
                if self._check_column_overlap(
                    k_new,
                    self.radius,
                    self.length,
                    k_existing,
                    radius_existing,
                    length_existing,
                ):
                    overlaps = True
                    break

            if not overlaps:
                return rotation_angles, True

        return rotation_angles, False

    def _create_and_orient_bullet(self, rotation_angles: tuple) -> bpy.types.Object:
        # Create cylinder directly without clearing scene
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=6,
            radius=self.radius,
            depth=self.length,
            end_fill_type="NGON",
            location=(0, 0, 0),
        )
        obj = bpy.context.active_object
        obj.name = "HexagonalBullet"

        # Create a bullet generator to use its methods
        bullet_gen = HexagonalBullet(
            length=self.length,
            radius=self.radius,
            indentation_factor=self.indentation_factor,
            inset=self.inset,
            output_dir=self.output_dir,
        )

        # Apply bullet shaping
        bullet_gen._add_loop_cut(obj)
        bullet_gen._indent_top(obj)
        bullet_gen._create_bullet_tip(obj)
        bpy.ops.object.mode_set(mode="OBJECT")

        # Now we need to position the bullet so the non-indented base is at origin
        # The non-indented base is at z = -length/2 in the bullet's local coordinates
        # We need to translate it up by length/2
        obj.location.z += self.length / 2.0

        # Set origin to world origin for proper rotation
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

        # Apply rotation
        obj.rotation_euler = rotation_angles

        # Apply transforms
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        return obj

    def _create_geometry(self) -> bpy.types.Object:
        """Create the hexagonal bullet rosette geometry and return the object without exporting."""
        self._clear_scene()

        existing_columns = []
        bullets_created = 0

        # Create first bullet with random rotation
        first_rotation = (
            random.uniform(0, 2 * math.pi * self.rotation_factor),
            random.uniform(0, 2 * math.pi * self.rotation_factor),
            random.uniform(0, 2 * math.pi * self.rotation_factor),
        )

        print(f"Creating bullet 1/{self.num_bullets}")
        aggregate = self._create_and_orient_bullet(first_rotation)
        aggregate.name = "BulletRosetteAggregate"
        bullets_created += 1

        # Track first bullet
        first_k_vector = self._compute_column_axis_vector(first_rotation)
        existing_columns.append((first_k_vector, self.radius, self.length))

        # Add additional bullets
        for i in range(1, self.num_bullets):
            print(f"\nAttempting to create bullet {i + 1}/{self.num_bullets}")
            rotation_angles, success = self._find_non_overlapping_rotation(
                existing_columns
            )

            if not success:
                print(
                    f"Warning: Could not find non-overlapping rotation for bullet {i + 1}, skipping"
                )
                continue  # Skip this bullet if we can't find a good rotation

            print(f"Creating bullet {i + 1} with rotation {rotation_angles}")
            new_bullet = self._create_and_orient_bullet(rotation_angles)
            new_bullet.name = f"Bullet_{i + 1}"
            bullets_created += 1

            # Track new bullet
            k_vector = self._compute_column_axis_vector(rotation_angles)
            existing_columns.append((k_vector, self.radius, self.length))

            # Join with aggregate using Boolean union
            print(f"Applying Boolean union for bullet {i + 1}")
            bpy.ops.object.select_all(action="DESELECT")
            aggregate.select_set(True)
            bpy.context.view_layer.objects.active = aggregate

            # Check vertex count before union
            vert_count_before = len(aggregate.data.vertices)
            print(f"  Aggregate vertices before union: {vert_count_before}")

            bpy.ops.object.modifier_add(type="BOOLEAN")
            boolean_mod = aggregate.modifiers[-1]
            boolean_mod.name = f"UnionBullet{i + 1}"
            boolean_mod.operation = "UNION"
            boolean_mod.object = new_bullet
            boolean_mod.solver = "FAST"  # Try FAST solver

            try:
                bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
                vert_count_after = len(aggregate.data.vertices)
                print(f"  Aggregate vertices after union: {vert_count_after}")
                if vert_count_after <= vert_count_before:
                    print(
                        f"  WARNING: Boolean union may have failed (no vertex increase)"
                    )
            except Exception as e:
                print(f"  ERROR applying Boolean modifier: {e}")

            # Delete the bullet object after union
            bpy.ops.object.select_all(action="DESELECT")
            new_bullet.select_set(True)
            bpy.ops.object.delete()

            # Re-get the aggregate object since references can be lost
            aggregate = bpy.context.scene.objects.get("BulletRosetteAggregate")
            if not aggregate:
                print(f"  ERROR: Lost reference to aggregate object!")
                break

        # Final cleanup
        print(f"\nTotal bullets created: {bullets_created}/{self.num_bullets}")
        bpy.ops.object.select_all(action="DESELECT")
        if aggregate:
            aggregate.select_set(True)
            bpy.context.view_layer.objects.active = aggregate
        bpy.ops.object.shade_flat()

        return aggregate

    def to_filename(self) -> str:
        """Return complete filename without extension."""
        indentation_str = f"{self.indentation_factor:.2f}".replace(".", "p")
        inset_str = f"{self.inset:.2f}".replace(".", "p")
        return f"hexagonal_bullet_rosette_n{self.num_bullets}_l{self.length}_r{self.radius}_indentfactor{indentation_str}_inset{inset_str}"

    def generate(self) -> str:
        obj = self._create_geometry()

        # Export
        filename = f"{self.to_filename()}.obj"
        filepath = self._export_obj(filename)

        return filepath
