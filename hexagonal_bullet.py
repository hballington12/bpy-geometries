import bpy
import bmesh
from geometry import Geometry


class HexagonalBullet(Geometry):
    def __init__(
        self,
        length: float,
        radius: float,
        indentation: float,
        inset: float,
        output_dir: str,
    ):
        super().__init__(output_dir)
        self.length: float = length
        self.radius: float = radius
        self.indentation: float = indentation
        self.inset: float = inset
        self.tolerance: float = 0.001

    def _create_hexagonal_column(self) -> bpy.types.Object:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=6,
            radius=self.radius,
            depth=self.length,
            end_fill_type="NGON",
            location=(0, 0, 0),
        )
        obj = bpy.context.active_object
        obj.name = "HexagonalBullet"
        return obj

    def _add_loop_cut(self, obj: bpy.types.Object):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")

        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()

        vertical_edges = []
        for edge in bm.edges:
            v1, v2 = edge.verts
            if (
                abs(v1.co.x - v2.co.x) < self.tolerance
                and abs(v1.co.y - v2.co.y) < self.tolerance
            ):
                if abs(abs(v1.co.z - v2.co.z) - self.length) < self.tolerance:
                    vertical_edges.append(edge)

        if vertical_edges:
            bmesh.ops.subdivide_edges(
                bm, edges=vertical_edges, cuts=1, use_grid_fill=False
            )

            # The new vertices are created at z=0 (midpoint)
            # We need to move them to the correct position
            cut_z_position = -self.length / 2.0 + self.inset

            # After subdivision, new vertices are at z=0
            # Move all vertices that are near z=0 to the cut position
            for vert in bm.verts:
                if abs(vert.co.z) < self.tolerance:  # Vertices at the midpoint (z=0)
                    vert.co.z = cut_z_position

            bmesh.update_edit_mesh(obj.data)

    def _indent_top(self, obj: bpy.types.Object):
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
        expected_z_top = self.length / 2.0
        for v in bm.verts:
            if (
                abs(v.co.x) < self.tolerance
                and abs(v.co.y) < self.tolerance
                and abs(v.co.z - expected_z_top) < self.tolerance
            ):
                v.co.z -= self.indentation
                break
        bmesh.update_edit_mesh(obj.data)

    def _create_bullet_tip(self, obj: bpy.types.Object):
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_mode(type="VERT")

        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        merge_tolerance = 0.1
        merge_threshold = -self.length / 2.0 + merge_tolerance

        for v in bm.verts:
            if v.co.z <= merge_threshold:
                v.select_set(True)

        bmesh.update_edit_mesh(obj.data)

        if any(v.select for v in bm.verts):
            bpy.ops.mesh.merge(type="CENTER")

    def generate(self) -> str:
        self._clear_scene()

        obj = self._create_hexagonal_column()

        self._add_loop_cut(obj)
        self._indent_top(obj)
        self._create_bullet_tip(obj)

        bpy.ops.object.mode_set(mode="OBJECT")

        indentation_str = f"{self.indentation:.2f}".replace(".", "p")
        inset_str = f"{self.inset:.2f}".replace(".", "p")
        filename = f"hexagonal_bullet_l{self.length}_r{self.radius}_indent{indentation_str}_inset{inset_str}.obj"
        filepath = self._export_obj(filename)

        return filepath
