import bpy
import bmesh
import math
from .geometry import Geometry


class IndentedColumn(Geometry):
    def __init__(
        self, length: float, radius: float, indentation_amount: float, output_dir: str
    ):
        super().__init__(output_dir)

        # Validate indentation_amount
        if indentation_amount < 0.0 or indentation_amount > 1.0:
            raise ValueError(
                f"indentation_amount must be between 0.0 and 1.0, got {indentation_amount}"
            )

        self.length: float = length
        self.radius: float = radius
        self.indentation_amount: float = indentation_amount
        self.tolerance: float = 0.001

    def _calculate_indentation_depth(self) -> float:
        clamped_amount = max(0.0, min(1.0, self.indentation_amount))

        if clamped_amount == 0.0:
            return 0.0

        if clamped_amount == 1.0:
            effective_amount = 0.9999
        else:
            effective_amount = clamped_amount

        angle_rad = (math.pi / 2) * effective_amount
        tan_value = math.tan(angle_rad)
        indentation_depth = (self.length / 2) * tan_value

        return indentation_depth

    def _create_cylinder(self, name: str) -> bpy.types.Object:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=6,
            radius=self.radius,
            depth=self.length,
            end_fill_type="NGON",
            location=(0, 0, 0),
        )
        obj = bpy.context.active_object
        obj.name = name
        return obj

    def _indent_top(self, obj: bpy.types.Object, indentation_depth: float):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.mesh.select_all(action="DESELECT")

        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()

        for face in bm.faces:
            if (
                abs(face.normal.x) < self.tolerance
                and abs(face.normal.y) < self.tolerance
                and abs(face.normal.z - 1.0) < self.tolerance
            ):
                face.select_set(True)
                break

        bmesh.update_edit_mesh(obj.data)

        bpy.ops.mesh.inset(thickness=(self.radius * 0.25), depth=0)
        bpy.ops.mesh.merge(type="CENTER")
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.context.view_layer.update()

        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        expected_z = self.length / 2.0
        for v in bm.verts:
            if (
                abs(v.co.x) < self.tolerance
                and abs(v.co.y) < self.tolerance
                and abs(v.co.z - expected_z) < self.tolerance
            ):
                v.co.z -= indentation_depth
                break

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode="OBJECT")

    def _indent_bottom(self, obj: bpy.types.Object, indentation_depth: float):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.mesh.select_all(action="DESELECT")

        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()

        for face in bm.faces:
            if (
                abs(face.normal.x) < self.tolerance
                and abs(face.normal.y) < self.tolerance
                and abs(face.normal.z - (-1.0)) < self.tolerance
            ):
                face.select_set(True)
                break

        bmesh.update_edit_mesh(obj.data)

        bpy.ops.mesh.inset(thickness=(self.radius * 0.25), depth=0)
        bpy.ops.mesh.merge(type="CENTER")
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.context.view_layer.update()

        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        expected_z = -self.length / 2.0
        for v in bm.verts:
            if (
                abs(v.co.x) < self.tolerance
                and abs(v.co.y) < self.tolerance
                and abs(v.co.z - expected_z) < self.tolerance
            ):
                v.co.z += indentation_depth
                break

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode="OBJECT")

    def _create_geometry(self) -> bpy.types.Object:
        """Create the indented column geometry and return the object without exporting."""
        indentation_depth = self._calculate_indentation_depth()

        obj_A = self._create_cylinder("Cylinder_TopIndented")
        obj_B = self._create_cylinder("Cylinder_BottomIndented")

        self._indent_top(obj_A, indentation_depth)
        self._indent_bottom(obj_B, indentation_depth)

        bpy.ops.object.select_all(action="DESELECT")
        obj_A.select_set(True)
        bpy.context.view_layer.objects.active = obj_A

        bpy.ops.object.modifier_add(type="BOOLEAN")
        boolean_mod = obj_A.modifiers[-1]
        boolean_mod.name = "IntersectionWithB"
        boolean_mod.operation = "INTERSECT"
        boolean_mod.object = obj_B

        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

        bpy.ops.object.select_all(action="DESELECT")
        obj_B.select_set(True)
        bpy.ops.object.delete()

        obj_A.name = "IndentedColumn"
        return obj_A

    def to_filename(self) -> str:
        """Return complete filename without extension."""
        indent_str = f"{self.indentation_amount:.2f}".replace(".", "p")
        return f"indented_column_l{self.length}_r{self.radius}_indent{indent_str}"

    def generate(self) -> str:
        self._clear_scene()
        obj = self._create_geometry()

        filename = f"{self.to_filename()}.obj"
        filepath = self._export_obj(filename)

        return filepath
