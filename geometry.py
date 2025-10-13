import bpy
import os
from abc import ABC, abstractmethod


class Geometry(ABC):
    def __init__(self, output_dir: str):
        self.output_dir: str = output_dir

    @abstractmethod
    def generate(self) -> str:
        pass

    @abstractmethod
    def to_filename(self) -> str:
        """
        Return a complete filename (without extension) for this geometry.

        This string should contain the geometry type and all parameters needed
        to reconstruct the geometry.

        Returns:
            Filename string with geometry name and parameter key-value pairs
        """
        pass

    def _clear_scene(self):
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()

    def _export_obj(self, filename):
        filepath = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)
        bpy.ops.wm.obj_export(
            filepath=filepath,
            export_selected_objects=False,
            export_triangulated_mesh=True,
            export_materials=False,
        )
        return filepath
