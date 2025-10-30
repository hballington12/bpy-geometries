import bpy
import os
from abc import ABC, abstractmethod


class Geometry(ABC):
    def __init__(self, output_dir: str, triangulate: bool = True):
        self.output_dir: str = output_dir
        self.triangulate: bool = triangulate

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

    def _cleanup_degenerate_faces(self):
        """
        Remove degenerate mesh elements (very thin triangles, zero-area faces).

        This is equivalent to Blender's Edit Mode → Mesh → Cleanup → Degenerate Dissolve.
        Operates on all mesh objects in the scene.
        """
        # Store current mode
        current_mode = bpy.context.object.mode if bpy.context.object else "OBJECT"

        # Find all mesh objects
        mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]

        if not mesh_objects:
            return

        # Process each mesh object
        for obj in mesh_objects:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")

            # Dissolve degenerate geometry
            # threshold: minimum distance between elements to merge (default: 1e-4)
            bpy.ops.mesh.dissolve_degenerate(threshold=1e-1)

            bpy.ops.object.mode_set(mode="OBJECT")

        print(f"Cleaned up degenerate faces from {len(mesh_objects)} mesh object(s)")

    def _export_obj(self, filename):
        filepath = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)

        # Clean up degenerate faces before export
        self._cleanup_degenerate_faces()

        bpy.ops.wm.obj_export(
            filepath=filepath,
            export_selected_objects=False,
            export_triangulated_mesh=self.triangulate,
            export_materials=False,
        )
        return filepath
