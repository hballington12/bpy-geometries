import bpy
import bmesh
import os
import uuid
import warnings
from abc import ABC, abstractmethod
from mathutils.bvhtree import BVHTree


class Geometry(ABC):
    def __init__(self, output_dir: str, triangulate: bool = False):
        self.output_dir: str = output_dir
        self.triangulate: bool = triangulate
        self._uuid: str = uuid.uuid4().hex[:8]

    @property
    def geometry_id(self) -> str:
        """Returns this geometry's unique identifier."""
        return self._uuid

    @abstractmethod
    def generate(self) -> str:
        pass

    @abstractmethod
    def to_filename(self) -> str:
        """
        Return filename parameters (without extension or UUID) for this geometry.

        This string should contain the geometry type and all parameters needed
        to reconstruct the geometry. The UUID is appended separately by
        get_full_filename().

        Returns:
            Filename string with geometry name and parameter key-value pairs
        """
        pass

    def get_full_filename(self) -> str:
        """
        Return complete filename with UUID appended.

        This should be called by generate() to get the final filename.
        The UUID ensures unique filenames even for geometries with
        identical parameters.

        Returns:
            Complete filename (without extension) including UUID
        """
        return f"{self.to_filename()}_{self._uuid}"

    def _clear_scene(self):
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()

    def _check_self_intersection(self, obj: bpy.types.Object) -> bool:
        """
        Check if mesh has self-intersecting faces.

        Uses BVHTree overlap detection to find faces that intersect
        but don't share vertices.

        Args:
            obj: Blender mesh object to check

        Returns:
            True if self-intersecting, False otherwise
        """
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")

        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()

        tree = BVHTree.FromBMesh(bm, epsilon=0.00001)
        overlap = tree.overlap(tree)

        for i, j in overlap:
            if i != j:
                face_i = bm.faces[i]
                face_j = bm.faces[j]
                shared_verts = set(face_i.verts) & set(face_j.verts)
                if len(shared_verts) == 0:
                    bpy.ops.object.mode_set(mode="OBJECT")
                    obj.select_set(False)
                    return True

        bpy.ops.object.mode_set(mode="OBJECT")
        obj.select_set(False)
        return False

    def _validate_geometry(self):
        """
        Run validation checks on all mesh objects in the scene.

        Emits warnings for any issues found but does not halt execution.
        """
        mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]

        for obj in mesh_objects:
            if self._check_self_intersection(obj):
                warnings.warn(
                    f"Self-intersection detected in mesh '{obj.name}'. "
                    "This may cause issues with boolean operations or rendering.",
                    UserWarning
                )

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

        # Validate geometry before export
        self._validate_geometry()

        # Clean up degenerate faces before export
        self._cleanup_degenerate_faces()

        bpy.ops.wm.obj_export(
            filepath=filepath,
            export_selected_objects=False,
            export_triangulated_mesh=self.triangulate,
            export_materials=False,
        )
        return filepath
