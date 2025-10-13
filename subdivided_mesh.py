import bpy
import bmesh
import random
from geometry import Geometry


class SubdividedMesh(Geometry):
    def __init__(
        self, max_edge_length: float, displacement_sigma: float, output_dir: str
    ):
        super().__init__(output_dir)
        self.max_edge_length: float = max_edge_length
        self.displacement_sigma: float = displacement_sigma

    def subdivide_until_max_edge_length(self, obj: bpy.types.Object):
        """
        Subdivide mesh edges until all edges are <= max_edge_length.

        Algorithm:
        1. Check all edges
        2. If any edge > max_edge_length, subdivide once
        3. Triangulate all faces
        4. Repeat until no edges exceed max_edge_length
        """
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")

        max_iterations = 100
        iteration = 0

        while iteration < max_iterations:
            bpy.ops.mesh.select_all(action="DESELECT")

            # Get mesh data
            bm = bmesh.from_edit_mesh(obj.data)
            bm.edges.ensure_lookup_table()

            # Check if any edges exceed max length
            edges_to_subdivide = []
            max_edge_found = 0.0

            for edge in bm.edges:
                edge_length = edge.calc_length()
                if edge_length > self.max_edge_length:
                    edges_to_subdivide.append(edge)
                    edge.select = True
                    max_edge_found = max(max_edge_found, edge_length)

            bmesh.update_edit_mesh(obj.data)

            # If no edges exceed max length, we're done
            if not edges_to_subdivide:
                print(f"Subdivision complete after {iteration} iterations")
                break

            print(
                f"Iteration {iteration + 1}: Found {len(edges_to_subdivide)} edges to subdivide (max: {max_edge_found:.4f})"
            )

            # Subdivide selected edges once
            bpy.ops.mesh.subdivide(number_cuts=1)

            # Triangulate all faces
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.quads_convert_to_tris()

            iteration += 1

        if iteration >= max_iterations:
            print(f"Warning: Reached maximum iterations ({max_iterations})")

        bpy.ops.object.mode_set(mode="OBJECT")

    def apply_random_displacement(self, obj: bpy.types.Object):
        """
        Apply random displacement to each vertex along its normal vector.

        Displacement = random(-sigma, sigma) * vertex_normal
        """
        if self.displacement_sigma == 0.0:
            print("Displacement sigma is 0.0, skipping displacement")
            return

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")

        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.normal_update()

        displaced_count = 0

        for vert in bm.verts:
            # Generate random displacement value between -sigma and +sigma
            displacement_amount = random.uniform(
                -self.displacement_sigma, self.displacement_sigma
            )

            # Displace vertex along its normal
            vert.co += vert.normal * displacement_amount
            displaced_count += 1

        bmesh.update_edit_mesh(obj.data)
        print(
            f"Applied random displacement to {displaced_count} vertices (sigma={self.displacement_sigma})"
        )

        bpy.ops.object.mode_set(mode="OBJECT")

    def generate(self) -> str:
        """
        Subclasses should override this method to create their mesh,
        then call subdivide_until_max_edge_length() before exporting.
        """
        raise NotImplementedError("Subclasses must implement generate()")
