import bpy
from .geometry import Geometry


class Bevel(Geometry):
    def __init__(
        self,
        geometry: Geometry,
        percent: float,
    ):
        super().__init__(geometry.output_dir)
        self.geometry: Geometry = geometry
        self.percent: float = percent

    def _apply_bevel_modifier(self, obj: bpy.types.Object):
        """
        Apply a bevel modifier to the object with PERCENT width type.

        Args:
            obj: The object to apply the bevel modifier to
        """
        # Add bevel modifier
        bevel_mod = obj.modifiers.new(name="Bevel", type="BEVEL")
        bevel_mod.offset_type = "PERCENT"
        bevel_mod.width_pct = self.percent
        bevel_mod.segments = 1
        bevel_mod.limit_method = "NONE"  # Apply to all edges

        # Apply the modifier
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=bevel_mod.name)

        print(f"Applied bevel modifier: {self.percent}% width, 1 segment")

    def to_filename(self) -> str:
        """Return complete filename without extension."""
        percent_str = f"{self.percent:.1f}".replace(".", "p")
        geom_filename = self.geometry.to_filename()
        return f"bevel_{percent_str}pct_{geom_filename}"

    def generate(self) -> str:
        """
        Generate the base geometry with bevel applied and export.
        """
        # Clear scene and create base geometry
        self._clear_scene()
        base_obj = self._create_base_geometry_object(self.geometry)

        print(f"Created base geometry: {type(self.geometry).__name__}")
        print(f"Bevel percent: {self.percent}%")
        print()

        # Apply bevel modifier
        self._apply_bevel_modifier(base_obj)

        # Export the final geometry
        filename = f"{self.to_filename()}.obj"
        filepath = self._export_obj(filename)

        print(f"\nExported to: {filepath}")
        return filepath

    def _create_geometry(self) -> bpy.types.Object:
        """Create the beveled geometry object without exporting."""
        # Create the base geometry
        base_obj = self._create_base_geometry_object(self.geometry)

        print(f"Created base geometry: {type(self.geometry).__name__}")
        print(f"Bevel percent: {self.percent}%")
        print()

        # Apply bevel modifier
        self._apply_bevel_modifier(base_obj)

        return base_obj

    def _create_base_geometry_object(self, geometry: Geometry) -> bpy.types.Object:
        """Create the base geometry object in the scene without exporting."""
        if hasattr(geometry, "_create_geometry"):
            return geometry._create_geometry()
        else:
            raise NotImplementedError(
                f"Bevel wrapper doesn't support {type(geometry).__name__} yet. "
                f"The geometry class must be updated to work with Bevel. "
                f"Add a _create_geometry() method that returns the mesh object without exporting."
            )
