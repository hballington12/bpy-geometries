import bpy
from .geometry import Geometry


class HexagonalColumn(Geometry):
    def __init__(self, length: float, radius: float, output_dir: str):
        super().__init__(output_dir)
        self.length: float = length
        self.radius: float = radius

    def _create_geometry(self) -> bpy.types.Object:
        """Create the hexagonal column geometry and return the object without exporting."""
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=6, radius=self.radius, depth=self.length, location=(0, 0, 0)
        )
        return bpy.context.active_object

    def to_filename(self) -> str:
        """Return complete filename without extension."""
        return f"hexagonal_column_l{self.length}_r{self.radius}"

    def generate(self) -> str:
        self._clear_scene()
        obj = self._create_geometry()

        filename = f"{self.get_full_filename()}.obj"
        filepath = self._export_obj(filename)

        return filepath
