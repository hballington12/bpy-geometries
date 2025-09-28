import bpy
import os
from abc import ABC, abstractmethod


class Geometry(ABC):
    def __init__(self, output_dir: str):
        self.output_dir: str = output_dir

    @abstractmethod
    def generate(self) -> str:
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
