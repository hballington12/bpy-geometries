import bpy
import bmesh
import math
import os

# 1. Define parameters
radius = 1.0  # Radius of the hexagonal column
length = 5.0  # Length of the column
# indentation_amount will be set by the loop
# Tolerance for floating point comparisons when finding vertices/faces
tolerance = 0.001 
export_enabled = True # Set to False to disable export
export_directory = "output" # Directory to save the OBJ file

# --- Helper function to clear existing mesh objects for a clean scene ---
def clear_scene():
    """Clears all mesh objects from the current scene."""
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    if bpy.context.selected_objects:
        bpy.ops.object.delete()
    print("Cleared existing mesh objects.")

# --- Main script for creating a single column ---
def create_indented_base(current_indentation_amount, current_radius, current_length):
    """Creates a single hollow column with the given indentation, radius, and length."""
    print(f"\n--- Creating column for indentation: {current_indentation_amount:.1f}, R: {current_radius}, L: {current_length} ---")
    clear_scene()

    # Calculate the actual indentation depth
    original_indentation_amount_for_file = current_indentation_amount # Keep original for filename
    clamped_indentation_amount = max(0.0, min(1.0, current_indentation_amount))

    if clamped_indentation_amount != current_indentation_amount:
        print(f"Info: Input indentation_amount ({current_indentation_amount}) was clamped to {clamped_indentation_amount}.")
    
    if clamped_indentation_amount == 1.0:
        effective_indent_amount_for_calc = 0.9999 
        print(f"Info: indentation_amount is 1.0. Using {effective_indent_amount_for_calc} for calculation to approximate tan(pi/2).")
    else:
        effective_indent_amount_for_calc = clamped_indentation_amount

    actual_indentation_depth = 0.0
    if effective_indent_amount_for_calc == 0.0:
        actual_indentation_depth = 0.0
        print(f"Indentation amount is 0.0. Displacement depth is 0.0.")
    else:
        angle_rad = (math.pi / 2) * effective_indent_amount_for_calc
        tan_value = math.tan(angle_rad)
        actual_indentation_depth = (current_length / 2) * tan_value
        print(f"Calculated indentation depth: {actual_indentation_depth:.4f} (from effective amount: {effective_indent_amount_for_calc:.4f})")

    # --- Create First Cylinder (obj_A, for top indentation) ---
    print(f"Creating cylinder A: radius={current_radius}, length={current_length}")
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=6, radius=current_radius, depth=current_length, end_fill_type='NGON',
        location=(0, 0, 0), scale=(1, 1, 1)
    )
    obj_A = bpy.context.active_object
    obj_A.name = "Cylinder_TopIndented"
    print(f"'{obj_A.name}' created.")

    # --- Create Second Cylinder (obj_B, for bottom indentation) ---
    print(f"Creating cylinder B: radius={current_radius}, length={current_length}")
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=6, radius=current_radius, depth=current_length, end_fill_type='NGON',
        location=(0, 0, 0), scale=(1, 1, 1)
    )
    obj_B = bpy.context.active_object
    obj_B.name = "Cylinder_BottomIndented"
    print(f"'{obj_B.name}' created.")

    # --- Indent Top of obj_A ---
    print(f"Indenting top of '{obj_A.name}'.")
    bpy.context.view_layer.objects.active = obj_A
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="FACE")
    bpy.ops.mesh.select_all(action='DESELECT')

    bm_A = bmesh.from_edit_mesh(obj_A.data)
    bm_A.faces.ensure_lookup_table()
    selected_top_face_A = None
    for face_A in bm_A.faces:
        if abs(face_A.normal.x) < tolerance and abs(face_A.normal.y) < tolerance and abs(face_A.normal.z - 1.0) < tolerance:
            face_A.select_set(True)
            selected_top_face_A = face_A
            print(f"Top face of '{obj_A.name}' selected.")
            break
    bmesh.update_edit_mesh(obj_A.data)

    if selected_top_face_A:
        bpy.ops.mesh.inset(thickness=(current_radius * 0.25), depth=0)
        bpy.ops.mesh.merge(type='CENTER')
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.context.view_layer.update()
        
        bm_A = bmesh.from_edit_mesh(obj_A.data)
        bm_A.verts.ensure_lookup_table()
        center_vert_A = None
        expected_z_top_A = current_length / 2.0
        for v_A in bm_A.verts:
            if abs(v_A.co.x) < tolerance and abs(v_A.co.y) < tolerance and abs(v_A.co.z - expected_z_top_A) < tolerance:
                center_vert_A = v_A
                break
        if center_vert_A:
            print(f"Top center vertex of '{obj_A.name}' found. Displacing by {-actual_indentation_depth:.4f}.")
            center_vert_A.co.z -= actual_indentation_depth
            bmesh.update_edit_mesh(obj_A.data)
        else:
            print(f"Error: Could not find top center vertex for '{obj_A.name}'.")
    else:
        print(f"Error: Could not find top face for '{obj_A.name}'.")
    bpy.ops.object.mode_set(mode='OBJECT')

    # --- Indent Bottom of obj_B ---
    print(f"Indenting bottom of '{obj_B.name}'.")
    bpy.context.view_layer.objects.active = obj_B
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="FACE")
    bpy.ops.mesh.select_all(action='DESELECT')

    bm_B = bmesh.from_edit_mesh(obj_B.data)
    bm_B.faces.ensure_lookup_table()
    selected_bottom_face_B = None
    for face_B in bm_B.faces:
        if abs(face_B.normal.x) < tolerance and abs(face_B.normal.y) < tolerance and abs(face_B.normal.z - (-1.0)) < tolerance:
            face_B.select_set(True)
            selected_bottom_face_B = face_B
            print(f"Bottom face of '{obj_B.name}' selected.")
            break
    bmesh.update_edit_mesh(obj_B.data)

    if selected_bottom_face_B:
        bpy.ops.mesh.inset(thickness=(current_radius * 0.25), depth=0)
        bpy.ops.mesh.merge(type='CENTER')
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.context.view_layer.update()

        bm_B = bmesh.from_edit_mesh(obj_B.data)
        bm_B.verts.ensure_lookup_table()
        center_vert_B = None
        expected_z_bottom_B = -current_length / 2.0
        for v_B in bm_B.verts:
            if abs(v_B.co.x) < tolerance and abs(v_B.co.y) < tolerance and abs(v_B.co.z - expected_z_bottom_B) < tolerance:
                center_vert_B = v_B
                break
        if center_vert_B:
            print(f"Bottom center vertex of '{obj_B.name}' found. Displacing by {actual_indentation_depth:.4f}.")
            center_vert_B.co.z += actual_indentation_depth
            bmesh.update_edit_mesh(obj_B.data)
        else:
            print(f"Error: Could not find bottom center vertex for '{obj_B.name}'.")
    else:
        print(f"Error: Could not find bottom face for '{obj_B.name}'.")
    bpy.ops.object.mode_set(mode='OBJECT')

    # --- Boolean Intersection ---
    print(f"Performing Boolean intersection: '{obj_A.name}' INTERSECT '{obj_B.name}'.")
    bpy.ops.object.select_all(action='DESELECT')
    obj_A.select_set(True)
    bpy.context.view_layer.objects.active = obj_A

    bpy.ops.object.modifier_add(type='BOOLEAN')
    boolean_mod = obj_A.modifiers[-1]
    boolean_mod.name = "IntersectionWithB"
    boolean_mod.operation = 'INTERSECT'
    boolean_mod.object = obj_B
    # boolean_mod.solver = 'EXACT' 

    print(f"Applying Boolean modifier to '{obj_A.name}'.")
    bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

    # --- Cleanup ---
    print(f"Deleting helper object '{obj_B.name}'.")
    bpy.ops.object.select_all(action='DESELECT')
    obj_B.select_set(True)
    bpy.ops.object.delete()

    # Ensure the final object is selected and named
    bpy.ops.object.select_all(action='DESELECT')
    obj_A.select_set(True)
    bpy.context.view_layer.objects.active = obj_A
    obj_A.name = "HollowColumn"
    print(f"Final result is in '{obj_A.name}'.")

    # --- Export the final object ---
    if export_enabled:
        if not os.path.exists(export_directory):
            os.makedirs(export_directory)
            print(f"Created export directory: '{export_directory}'")

        # Format values for filename
        radius_str = str(current_radius).replace('.', 'p')
        length_str = str(current_length).replace('.', 'p')
        indent_str = f"{original_indentation_amount_for_file:.1f}".replace('.', 'p') # Format to one decimal place

        export_filename = f"hollow_column_r{radius_str}_l{length_str}_indent_{indent_str}.obj"
        export_filepath = os.path.join(export_directory, export_filename)

        print(f"Exporting '{obj_A.name}' to '{export_filepath}'")
        bpy.ops.wm.obj_export(
            filepath=export_filepath,
            check_existing=True,
            filter_glob='*.obj;*.mtl',
            export_selected_objects=True,
            forward_axis='NEGATIVE_Z',
            up_axis='Y',
            apply_modifiers=True,
            export_materials=False
        )
        print(f"Export complete: {export_filepath}")
    else:
        print("Export is disabled.")

# --- Function to generate multiple columns ---
def generate_multiple_columns():
    """Generates hollow columns for a range of indentation values."""
    # Indentation values from 0.0 to 1.0 in steps of 0.1
    indent_steps = [i / 10.0 for i in range(11)] # Generates 0.0, 0.1, ..., 1.0

    for indent_val in indent_steps:
        create_indented_base(current_indentation_amount=indent_val, 
                             current_radius=radius, 
                             current_length=length)
    
    print("\nAll column generation finished.")

# --- Run the script ---
if __name__ == "__main__":
    generate_multiple_columns()
    # To run for a single, specific indentation, comment out generate_multiple_columns()
    # and uncomment the line below, setting your desired indentation_amount at the top.
    # create_indented_base(indentation_amount, radius, length) 
    print("Script finished.")