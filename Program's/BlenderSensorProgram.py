# import bpy
# import sys
# import argparse
# import os
# import math
# import random
# import csv
# import bmesh
# from mathutils import Vector, Euler, Matrix

# # --- 1. ARGUMENT PARSING ---
# def get_args():
#     """Retrieves arguments that follow '--' in the command line."""
#     if "--" not in sys.argv:
#         return []
#     return sys.argv[sys.argv.index("--") + 1:]

# # --- 2. HELPER FUNCTIONS ---

# def setup_sensor_object(location_str):
#     """Creates an empty object that serves as our 'Sensor' origin."""
#     try:
#         x, y, z = map(float, location_str.split(','))
#     except ValueError:
#         print(f"CRITICAL ERROR: Could not parse position '{location_str}'. Format must be 'X,Y,Z'")
#         sys.exit(1)
    
#     if "SensorOrigin" in bpy.data.objects:
#         sensor = bpy.data.objects["SensorOrigin"]
#     else:
#         bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD')
#         sensor = bpy.context.active_object
#         sensor.name = "SensorOrigin"
    
#     sensor.location = Vector((x, y, z))
    
#     # Point towards origin (0,0,0) where the target usually is
#     direction = Vector((0, 0, 0)) - sensor.location
#     if direction.length < 0.001:
#         # Prevent error if sensor is exactly at 0,0,0
#         direction = Vector((0,0,-1))
        
#     # Align -Z axis (camera convention) to the direction
#     sensor.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
#     return sensor

# def randomize_target(target_obj, trans_range, rot_range):
#     """Randomly rotates and translates the target object."""
#     rx_deg = random.uniform(-rot_range, rot_range)
#     ry_deg = random.uniform(-rot_range, rot_range)
#     rz_deg = random.uniform(-rot_range, rot_range)
#     rx, ry, rz = map(math.radians, [rx_deg, ry_deg, rz_deg])
    
#     tx = random.uniform(-trans_range, trans_range)
#     ty = random.uniform(-trans_range, trans_range)
#     tz = random.uniform(-trans_range, trans_range)
    
#     target_obj.rotation_euler = Euler((rx, ry, rz), 'XYZ')
#     target_obj.location = Vector((tx, ty, tz))
    
#     # Force update of the scene dependency graph
#     bpy.context.view_layer.update()

#     matrix = target_obj.matrix_world.copy()
#     params = {"rx_rad": rx, "ry_rad": ry, "rz_rad": rz, "tx_m": tx, "ty_m": ty, "tz_m": tz}
#     return matrix, params

# def create_hud_axes():
#     """Creates a small 3D axis object for visualization."""
#     bpy.ops.object.empty_add(type='PLAIN_AXES')
#     container = bpy.context.active_object
#     container.name = "HUD_Axes_Container"
#     container.empty_display_size = 0.0
    
#     def create_bar(axis_vec, color):
#         mesh = bpy.data.meshes.new("AxisPart")
#         obj = bpy.data.objects.new("AxisPart", mesh)
#         bpy.context.scene.collection.objects.link(obj)
        
#         bm = bmesh.new()
#         rotation = Vector((0,0,1)).rotation_difference(axis_vec).to_matrix().to_4x4()
        
#         bmesh.ops.create_cube(bm, size=1.0)
#         bmesh.ops.scale(bm, verts=bm.verts, vec=(0.05, 0.05, 0.5)) 
#         bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.25))
#         bmesh.ops.transform(bm, verts=bm.verts, matrix=rotation)
        
#         bm.to_mesh(mesh)
#         bm.free()
        
#         obj.parent = container
#         obj.matrix_local = Matrix.Identity(4)
#         obj.color = color
#         return obj

#     create_bar(Vector((1,0,0)), (1,0,0,1)) # Red X
#     create_bar(Vector((0,1,0)), (0,1,0,1)) # Green Y
#     create_bar(Vector((0,0,1)), (0,0,1,1)) # Blue Z
    
#     return container

# def generate_debug_views(output_dir, target_obj, sensor_obj, fov_h, fov_v, max_dist):
#     """Generates images with Sensor Viz + HUD Axes."""
#     print(f"--- Generating Debug Views (Range: {max_dist}m) ---")
    
#     original_engine = bpy.context.scene.render.engine
#     bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
#     bpy.context.scene.display.shading.light = 'FLAT'
#     bpy.context.scene.display.shading.color_type = 'OBJECT'
#     bpy.context.scene.display.shading.show_xray = True
#     bpy.context.scene.display.shading.xray_alpha = 0.5 
    
#     # Sensor Viz (Red Box)
#     mesh_body = bpy.data.meshes.new("TempCamBody")
#     obj_body = bpy.data.objects.new("TempCamViz", mesh_body)
#     bpy.context.scene.collection.objects.link(obj_body)
#     bm = bmesh.new()
#     bmesh.ops.create_cube(bm, size=0.4)
#     bm.to_mesh(mesh_body)
#     bm.free()
#     obj_body.parent = sensor_obj
#     obj_body.matrix_local = Matrix.Identity(4)
#     obj_body.color = (1.0, 0.0, 0.0, 1.0) 

#     # FOV Viz (Cyan Transparent)
#     mesh_fov = bpy.data.meshes.new("TempFOVMesh")
#     obj_fov = bpy.data.objects.new("TempFOVViz", mesh_fov)
#     bpy.context.scene.collection.objects.link(obj_fov)
#     L = max_dist 
#     dx = L * math.tan(math.radians(fov_h / 2.0))
#     dy = L * math.tan(math.radians(fov_v / 2.0))
#     bm = bmesh.new()
#     v_top = bm.verts.new((0,0,0))
#     v1 = bm.verts.new((-dx, -dy, -L))
#     v2 = bm.verts.new((-dx, dy, -L))
#     v3 = bm.verts.new((dx, dy, -L))
#     v4 = bm.verts.new((dx, -dy, -L))
#     bm.verts.ensure_lookup_table()
#     bm.faces.new((v_top, v2, v1))
#     bm.faces.new((v_top, v3, v2))
#     bm.faces.new((v_top, v4, v3))
#     bm.faces.new((v_top, v1, v4))
#     bm.to_mesh(mesh_fov)
#     bm.free()
#     obj_fov.parent = sensor_obj
#     obj_fov.matrix_local = Matrix.Identity(4)
#     obj_fov.color = (0.0, 1.0, 1.0, 0.15)
#     obj_fov.display_type = 'SOLID' 

#     # HUD & Camera
#     hud_axes = create_hud_axes()
    
#     cam_data = bpy.data.cameras.new("DebugCamData")
#     cam_obj = bpy.data.objects.new("DebugCam", cam_data)
#     bpy.context.scene.collection.objects.link(cam_obj)
#     bpy.context.scene.camera = cam_obj
    
#     track_con = cam_obj.constraints.new(type='TRACK_TO')
#     track_con.target = target_obj
#     track_con.track_axis = 'TRACK_NEGATIVE_Z'
#     track_con.up_axis = 'UP_Y'
#     cam_data.lens = 35

#     dist = 8.0 
#     height = 4.0
#     views = {
#         "view_iso":   Vector((dist, -dist, height)),
#         "view_front": Vector((0, -dist, 0)),
#         "view_right": Vector((dist, 0, 0)),
#         "view_top":   Vector((0, 0, dist))
#     }

#     for name, pos in views.items():
#         cam_obj.location = pos
#         bpy.context.view_layer.update()
        
#         # Position HUD relative to camera
#         mat = cam_obj.matrix_world
#         right_vec = Vector((mat[0][0], mat[0][1], mat[0][2]))
#         up_vec    = Vector((mat[1][0], mat[1][1], mat[1][2]))
#         back_vec  = Vector((mat[2][0], mat[2][1], mat[2][2]))
        
#         hud_pos = cam_obj.location + (back_vec * -5.0) + (right_vec * 2.2) + (up_vec * -1.2)
#         hud_axes.location = hud_pos
#         hud_axes.rotation_euler = (0,0,0) 

#         filepath = os.path.join(output_dir, f"setup_{name}.png")
#         bpy.context.scene.render.filepath = filepath
#         bpy.ops.render.render(write_still=True)

#     # Cleanup
#     bpy.context.scene.render.engine = original_engine
#     bpy.context.scene.display.shading.show_xray = False
    
#     objs_to_delete = [cam_obj, obj_body, obj_fov, hud_axes] + list(hud_axes.children)
#     bpy.ops.object.select_all(action='DESELECT')
#     for obj in objs_to_delete:
#         obj.select_set(True)
#     bpy.ops.object.delete()
    
#     for mesh in [mesh_body, mesh_fov]:
#         bpy.data.meshes.remove(mesh, do_unlink=True)
    
#     print("--- Debug Views Saved ---")

# def perform_raycast_scan(sensor_obj, target_obj, res_w, res_h, fov_h, fov_v, max_dist, noise=0.0):
#     """Simulates the sensor by shooting rays."""
#     hit_points = []
#     depsgraph = bpy.context.evaluated_depsgraph_get()
#     sensor_loc, sensor_mat = sensor_obj.location, sensor_obj.matrix_world
#     fov_h_rad, fov_v_rad = math.radians(fov_h), math.radians(fov_v)
    
#     step_x = 1 
#     step_y = 1
    
#     missed_target_names = set() # Track what we hit if NOT the target
    
#     for y in range(0, res_h, step_y):
#         for x in range(0, res_w, step_x):
#             u, v = (x / res_w) - 0.5, (y / res_h) - 0.5
#             angle_x, angle_y = u * fov_h_rad, v * fov_v_rad
#             local_dir = Vector((math.tan(angle_x), math.tan(angle_y), -1.0)).normalized()
#             world_dir = sensor_mat.to_3x3() @ local_dir
            
#             result, location, normal, index, obj, matrix = bpy.context.scene.ray_cast(depsgraph, sensor_loc, world_dir, distance=max_dist)
            
#             if result:
#                 if obj.name == target_obj.name:
#                     if noise > 0:
#                         location = Vector((location.x + random.gauss(0, noise), 
#                                            location.y + random.gauss(0, noise), 
#                                            location.z + random.gauss(0, noise)))
#                     hit_points.append(location)
#                 else:
#                     # We hit something else!
#                     missed_target_names.add(obj.name)

#     # Debug info if empty
#     if len(hit_points) == 0:
#         if len(missed_target_names) > 0:
#             print(f"DEBUG: 0 points on target '{target_obj.name}'. Hit these instead: {missed_target_names}")
#         else:
#             print(f"DEBUG: 0 points found. Raycast hit nothing within {max_dist}m.")
            
#     return hit_points

# # --- 3. MAIN EXECUTION ---

# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--sensor_res", required=True)
#     parser.add_argument("--sensor_fov", required=True)
#     parser.add_argument("--position", required=True)
#     parser.add_argument("--samples", type=int, required=True)
#     parser.add_argument("--output", required=True)
    
#     parser.add_argument("--rot_range", type=float, default=180.0)
#     parser.add_argument("--trans_range", type=float, default=0.0)
#     parser.add_argument("--noise", type=float, default=0.0)
#     parser.add_argument("--target_name", default="Cube")
#     parser.add_argument("--max_dist", type=float, default=100.0)
#     parser.add_argument("--viz", action="store_true", help="Generate debug visualization images")

#     args = parser.parse_args(get_args())
    
#     try:
#         res_w, res_h = map(int, args.sensor_res.split('x'))
#         fov_h, fov_v = map(float, args.sensor_fov.split('x'))
#     except ValueError: return print("Error: Resolution or FOV format incorrect.")
    
#     print(f"--- Blender Script Start (Max Dist: {args.max_dist}m) ---")
    
#     # Check if target exists
#     if args.target_name not in bpy.data.objects:
#         print(f"CRITICAL ERROR: Target object '{args.target_name}' NOT FOUND in .blend file!")
#         print(f"Available objects: {[o.name for o in bpy.data.objects]}")
#         sys.exit(1) # Stop script immediately with error code
        
#     target_obj = bpy.data.objects[args.target_name]
    
#     # Setup sensor
#     sensor_obj = setup_sensor_object(args.position)
    
#     if not os.path.exists(args.output): os.makedirs(args.output)

#     if args.viz:
#         try:
#             generate_debug_views(args.output, target_obj, sensor_obj, fov_h, fov_v, args.max_dist)
#         except Exception as e:
#             print(f"Warning: Could not generate debug views: {e}")
#             import traceback; traceback.print_exc()
#     else:
#         print("--- Visualization skipped (Enable with --viz) ---")

#     gt_filepath = os.path.join(args.output, "ground_truth.csv")
#     with open(gt_filepath, 'w', newline='') as gt_file:
#         gt_writer = csv.writer(gt_file)
#         gt_file.write(f"# Settings: Res={res_w}x{res_h}, FOV={fov_h}x{fov_v}, Pos={args.position}, Range={args.max_dist}\n")
#         header = ['sample_id', 'filename', 'rx_rad', 'ry_rad', 'rz_rad', 'tx_m', 'ty_m', 'tz_m']
#         matrix_headers = [f"m{r}{c}" for r in range(4) for c in range(4)]
#         gt_writer.writerow(header + matrix_headers)

#         for i in range(args.samples):
#             gt_matrix, params = randomize_target(target_obj, args.trans_range, args.rot_range)
#             points = perform_raycast_scan(sensor_obj, target_obj, res_w, res_h, fov_h, fov_v, 
#                                           max_dist=args.max_dist, noise=args.noise)
            
#             # --- WARNING CHECK ---
#             if len(points) == 0:
#                 print(f"WARNING: Sample {i} produced 0 points! Check sensor position or target name.")
#             # ---------------------
            
#             filename = f"scan_{i:04d}.csv"
#             filepath = os.path.join(args.output, filename)
#             with open(filepath, 'w', newline='') as csvfile:
#                 writer = csv.writer(csvfile)
#                 writer.writerow(['X', 'Y', 'Z'])
#                 for p in points: writer.writerow([f"{p.x:.6f}", f"{p.y:.6f}", f"{p.z:.6f}"])
            
#             flat_matrix = [f"{gt_matrix[r][c]:.6f}" for r in range(4) for c in range(4)]
#             row_data = [i, filename, f"{params['rx_rad']:.6f}", f"{params['ry_rad']:.6f}", f"{params['rz_rad']:.6f}", f"{params['tx_m']:.6f}", f"{params['ty_m']:.6f}", f"{params['tz_m']:.6f}"]
#             gt_writer.writerow(row_data + flat_matrix)
            
#             if i % 10 == 0: print(f"Generated sample {i}/{args.samples} - {len(points)} points")

#     print("--- Blender Script Finished ---")

# if __name__ == "__main__":
#     main()

# import bpy
# import sys
# import argparse
# import os
# import math
# import random
# import csv
# import bmesh
# from mathutils import Vector, Euler, Matrix

# # --- 1. ARGUMENT PARSING ---
# def get_args():
#     """Retrieves arguments that follow '--' in the command line."""
#     if "--" not in sys.argv:
#         return []
#     return sys.argv[sys.argv.index("--") + 1:]

# # --- 2. HELPER FUNCTIONS ---

# def setup_sensor_object(location_str):
#     """Creates an empty object that serves as our 'Sensor' origin."""
#     try:
#         x, y, z = map(float, location_str.split(','))
#     except ValueError:
#         print(f"CRITICAL ERROR: Could not parse position '{location_str}'. Format must be 'X,Y,Z'")
#         sys.exit(1)
    
#     if "SensorOrigin" in bpy.data.objects:
#         sensor = bpy.data.objects["SensorOrigin"]
#     else:
#         bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD')
#         sensor = bpy.context.active_object
#         sensor.name = "SensorOrigin"
    
#     sensor.location = Vector((x, y, z))
    
#     # Point towards origin (0,0,0)
#     direction = Vector((0, 0, 0)) - sensor.location
#     if direction.length < 0.001:
#         direction = Vector((0,0,-1)) # Default down if at 0,0,0
        
#     sensor.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
#     return sensor

# def apply_target_transform(target_obj, trans_range, rot_range, force_zero=False):
#     """
#     Applies transformation to the target object.
#     If force_zero is True, resets target to (0,0,0) with 0 rotation.
#     Otherwise, applies random values within range.
#     """
#     if force_zero:
#         # --- REFERENCE SCAN (0,0,0) ---
#         rx, ry, rz = 0.0, 0.0, 0.0
#         tx, ty, tz = 0.0, 0.0, 0.0
#     else:
#         # --- RANDOM SCAN ---
#         # Rotation
#         rx_deg = random.uniform(-rot_range, rot_range)
#         ry_deg = random.uniform(-rot_range, rot_range)
#         rz_deg = random.uniform(-rot_range, rot_range)
#         rx, ry, rz = map(math.radians, [rx_deg, ry_deg, rz_deg])
        
#         # Translation
#         tx = random.uniform(-trans_range, trans_range)
#         ty = random.uniform(-trans_range, trans_range)
#         tz = random.uniform(-trans_range, trans_range)
    
#     # Apply to Blender Object
#     target_obj.rotation_euler = Euler((rx, ry, rz), 'XYZ')
#     target_obj.location = Vector((tx, ty, tz))
    
#     # Update Dependency Graph (Important!)
#     bpy.context.view_layer.update()

#     # Capture Matrix and Parameters
#     matrix = target_obj.matrix_world.copy()
#     params = {
#         "rx_rad": rx, "ry_rad": ry, "rz_rad": rz,
#         "tx_m": tx,   "ty_m": ty,   "tz_m": tz
#     }
#     return matrix, params

# def create_hud_axes():
#     """Creates a small 3D axis object for visualization."""
#     bpy.ops.object.empty_add(type='PLAIN_AXES')
#     container = bpy.context.active_object
#     container.name = "HUD_Axes_Container"
#     container.empty_display_size = 0.0
    
#     def create_bar(axis_vec, color):
#         mesh = bpy.data.meshes.new("AxisPart")
#         obj = bpy.data.objects.new("AxisPart", mesh)
#         bpy.context.scene.collection.objects.link(obj)
        
#         bm = bmesh.new()
#         rotation = Vector((0,0,1)).rotation_difference(axis_vec).to_matrix().to_4x4()
        
#         bmesh.ops.create_cube(bm, size=1.0)
#         bmesh.ops.scale(bm, verts=bm.verts, vec=(0.05, 0.05, 0.5)) 
#         bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.25))
#         bmesh.ops.transform(bm, verts=bm.verts, matrix=rotation)
        
#         bm.to_mesh(mesh)
#         bm.free()
        
#         obj.parent = container
#         obj.matrix_local = Matrix.Identity(4)
#         obj.color = color
#         return obj

#     create_bar(Vector((1,0,0)), (1,0,0,1)) # Red X
#     create_bar(Vector((0,1,0)), (0,1,0,1)) # Green Y
#     create_bar(Vector((0,0,1)), (0,0,1,1)) # Blue Z
    
#     return container

# def generate_debug_views(output_dir, target_obj, sensor_obj, fov_h, fov_v, max_dist):
#     """Generates images with Sensor Viz + HUD Axes."""
#     print(f"--- Generating Debug Views (Range: {max_dist}m) ---")
    
#     # Temporarily force Reference Position for the photo
#     # This ensures the photo matches 'scan_0000'
#     original_loc = target_obj.location.copy()
#     original_rot = target_obj.rotation_euler.copy()
#     target_obj.location = Vector((0,0,0))
#     target_obj.rotation_euler = Euler((0,0,0))
#     bpy.context.view_layer.update()
    
#     # Setup Render Engine
#     original_engine = bpy.context.scene.render.engine
#     bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
#     bpy.context.scene.display.shading.light = 'FLAT'
#     bpy.context.scene.display.shading.color_type = 'OBJECT'
#     bpy.context.scene.display.shading.show_xray = True
#     bpy.context.scene.display.shading.xray_alpha = 0.5 
    
#     # Sensor Viz (Red Box)
#     mesh_body = bpy.data.meshes.new("TempCamBody")
#     obj_body = bpy.data.objects.new("TempCamViz", mesh_body)
#     bpy.context.scene.collection.objects.link(obj_body)
#     bm = bmesh.new()
#     bmesh.ops.create_cube(bm, size=0.4)
#     bm.to_mesh(mesh_body)
#     bm.free()
#     obj_body.parent = sensor_obj
#     obj_body.matrix_local = Matrix.Identity(4)
#     obj_body.color = (1.0, 0.0, 0.0, 1.0) 

#     # FOV Viz (Cyan Transparent)
#     mesh_fov = bpy.data.meshes.new("TempFOVMesh")
#     obj_fov = bpy.data.objects.new("TempFOVViz", mesh_fov)
#     bpy.context.scene.collection.objects.link(obj_fov)
#     L = max_dist 
#     dx = L * math.tan(math.radians(fov_h / 2.0))
#     dy = L * math.tan(math.radians(fov_v / 2.0))
#     bm = bmesh.new()
#     v_top = bm.verts.new((0,0,0))
#     v1 = bm.verts.new((-dx, -dy, -L))
#     v2 = bm.verts.new((-dx, dy, -L))
#     v3 = bm.verts.new((dx, dy, -L))
#     v4 = bm.verts.new((dx, -dy, -L))
#     bm.verts.ensure_lookup_table()
#     bm.faces.new((v_top, v2, v1))
#     bm.faces.new((v_top, v3, v2))
#     bm.faces.new((v_top, v4, v3))
#     bm.faces.new((v_top, v1, v4))
#     bm.to_mesh(mesh_fov)
#     bm.free()
#     obj_fov.parent = sensor_obj
#     obj_fov.matrix_local = Matrix.Identity(4)
#     obj_fov.color = (0.0, 1.0, 1.0, 0.15)
#     obj_fov.display_type = 'SOLID' 

#     # HUD & Camera
#     hud_axes = create_hud_axes()
#     cam_data = bpy.data.cameras.new("DebugCamData")
#     cam_obj = bpy.data.objects.new("DebugCam", cam_data)
#     bpy.context.scene.collection.objects.link(cam_obj)
#     bpy.context.scene.camera = cam_obj
#     track_con = cam_obj.constraints.new(type='TRACK_TO')
#     track_con.target = target_obj
#     track_con.track_axis = 'TRACK_NEGATIVE_Z'
#     track_con.up_axis = 'UP_Y'
#     cam_data.lens = 35

#     dist = 8.0 
#     height = 4.0
#     views = {
#         "view_iso":   Vector((dist, -dist, height)),
#         "view_front": Vector((0, -dist, 0)),
#         "view_right": Vector((dist, 0, 0)),
#         "view_top":   Vector((0, 0, dist))
#     }

#     for name, pos in views.items():
#         cam_obj.location = pos
#         bpy.context.view_layer.update()
        
#         # Position HUD
#         mat = cam_obj.matrix_world
#         right_vec = Vector((mat[0][0], mat[0][1], mat[0][2]))
#         up_vec    = Vector((mat[1][0], mat[1][1], mat[1][2]))
#         back_vec  = Vector((mat[2][0], mat[2][1], mat[2][2]))
        
#         hud_pos = cam_obj.location + (back_vec * -5.0) + (right_vec * 2.2) + (up_vec * -1.2)
#         hud_axes.location = hud_pos
#         hud_axes.rotation_euler = (0,0,0) 

#         filepath = os.path.join(output_dir, f"setup_{name}.png")
#         bpy.context.scene.render.filepath = filepath
#         bpy.ops.render.render(write_still=True)

#     # Cleanup
#     bpy.context.scene.render.engine = original_engine
#     bpy.context.scene.display.shading.show_xray = False
    
#     # Restore Target Position
#     target_obj.location = original_loc
#     target_obj.rotation_euler = original_rot
    
#     objs_to_delete = [cam_obj, obj_body, obj_fov, hud_axes] + list(hud_axes.children)
#     bpy.ops.object.select_all(action='DESELECT')
#     for obj in objs_to_delete:
#         obj.select_set(True)
#     bpy.ops.object.delete()
    
#     for mesh in [mesh_body, mesh_fov]:
#         bpy.data.meshes.remove(mesh, do_unlink=True)
    
#     print("--- Debug Views Saved ---")

# def perform_raycast_scan(sensor_obj, target_obj, res_w, res_h, fov_h, fov_v, max_dist, noise=0.0):
#     """Simulates the sensor by shooting rays."""
#     hit_points = []
#     depsgraph = bpy.context.evaluated_depsgraph_get()
#     sensor_loc, sensor_mat = sensor_obj.location, sensor_obj.matrix_world
#     fov_h_rad, fov_v_rad = math.radians(fov_h), math.radians(fov_v)
    
#     step_x = 1 
#     step_y = 1
    
#     missed_target_names = set()
    
#     for y in range(0, res_h, step_y):
#         for x in range(0, res_w, step_x):
#             u, v = (x / res_w) - 0.5, (y / res_h) - 0.5
#             angle_x, angle_y = u * fov_h_rad, v * fov_v_rad
#             local_dir = Vector((math.tan(angle_x), math.tan(angle_y), -1.0)).normalized()
#             world_dir = sensor_mat.to_3x3() @ local_dir
            
#             result, location, normal, index, obj, matrix = bpy.context.scene.ray_cast(depsgraph, sensor_loc, world_dir, distance=max_dist)
            
#             if result:
#                 if obj.name == target_obj.name:
#                     if noise > 0:
#                         location = Vector((location.x + random.gauss(0, noise), 
#                                            location.y + random.gauss(0, noise), 
#                                            location.z + random.gauss(0, noise)))
#                     hit_points.append(location)
#                 else:
#                     missed_target_names.add(obj.name)

#     if len(hit_points) == 0:
#         if len(missed_target_names) > 0:
#             print(f"DEBUG: 0 points on target '{target_obj.name}'. Hit these instead: {missed_target_names}")
#         else:
#             print(f"DEBUG: 0 points found. Raycast hit nothing within {max_dist}m.")
            
#     return hit_points

# # --- 3. MAIN EXECUTION ---

# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--sensor_res", required=True)
#     parser.add_argument("--sensor_fov", required=True)
#     parser.add_argument("--position", required=True)
#     parser.add_argument("--samples", type=int, required=True)
#     parser.add_argument("--output", required=True)
    
#     parser.add_argument("--rot_range", type=float, default=180.0)
#     parser.add_argument("--trans_range", type=float, default=0.0)
#     parser.add_argument("--noise", type=float, default=0.0)
#     parser.add_argument("--target_name", default="Cube")
#     parser.add_argument("--max_dist", type=float, default=100.0)
#     parser.add_argument("--viz", action="store_true")

#     args = parser.parse_args(get_args())
    
#     try:
#         res_w, res_h = map(int, args.sensor_res.split('x'))
#         fov_h, fov_v = map(float, args.sensor_fov.split('x'))
#     except ValueError: return print("Error: Resolution or FOV format incorrect.")
    
#     print(f"--- Blender Script Start ---")
#     print(f"DEBUG: Rotation Range = +/- {args.rot_range} degrees")
#     print(f"DEBUG: Translation Range = +/- {args.trans_range} meters")
    
#     if args.target_name not in bpy.data.objects:
#         print(f"CRITICAL ERROR: Target object '{args.target_name}' NOT FOUND in .blend file!")
#         sys.exit(1)
        
#     target_obj = bpy.data.objects[args.target_name]
#     sensor_obj = setup_sensor_object(args.position)
    
#     if not os.path.exists(args.output): os.makedirs(args.output)

#     if args.viz:
#         try:
#             generate_debug_views(args.output, target_obj, sensor_obj, fov_h, fov_v, args.max_dist)
#         except Exception as e:
#             print(f"Warning: Could not generate debug views: {e}")
#             import traceback; traceback.print_exc()

#     gt_filepath = os.path.join(args.output, "ground_truth.csv")
#     with open(gt_filepath, 'w', newline='') as gt_file:
#         gt_writer = csv.writer(gt_file)
#         gt_file.write(f"# Settings: Res={res_w}x{res_h}, FOV={fov_h}x{fov_v}, Pos={args.position}, Range={args.max_dist}\n")
#         header = ['sample_id', 'filename', 'rx_rad', 'ry_rad', 'rz_rad', 'tx_m', 'ty_m', 'tz_m']
#         matrix_headers = [f"m{r}{c}" for r in range(4) for c in range(4)]
#         gt_writer.writerow(header + matrix_headers)

#         for i in range(args.samples):
#             # --- THE FIX: Force Scan 0 to be Zero Position/Rotation ---
#             is_reference = (i == 0)
            
#             gt_matrix, params = apply_target_transform(
#                 target_obj, 
#                 args.trans_range, 
#                 args.rot_range, 
#                 force_zero=is_reference
#             )
            
#             points = perform_raycast_scan(sensor_obj, target_obj, res_w, res_h, fov_h, fov_v, 
#                                           max_dist=args.max_dist, noise=args.noise)
            
#             if len(points) == 0:
#                 print(f"WARNING: Sample {i} produced 0 points!")
            
#             filename = f"scan_{i:04d}.csv"
#             filepath = os.path.join(args.output, filename)
#             with open(filepath, 'w', newline='') as csvfile:
#                 writer = csv.writer(csvfile)
#                 writer.writerow(['X', 'Y', 'Z'])
#                 for p in points: writer.writerow([f"{p.x:.6f}", f"{p.y:.6f}", f"{p.z:.6f}"])
            
#             flat_matrix = [f"{gt_matrix[r][c]:.6f}" for r in range(4) for c in range(4)]
#             row_data = [i, filename, f"{params['rx_rad']:.6f}", f"{params['ry_rad']:.6f}", f"{params['rz_rad']:.6f}", f"{params['tx_m']:.6f}", f"{params['ty_m']:.6f}", f"{params['tz_m']:.6f}"]
#             gt_writer.writerow(row_data + flat_matrix)
            
#             if i % 10 == 0: print(f"Generated sample {i}/{args.samples} - {len(points)} points")

#     print("--- Blender Script Finished ---")

# if __name__ == "__main__":
#     main()

import bpy
import sys
import argparse
import os
import math
import random
import csv
import bmesh
from mathutils import Vector, Euler, Matrix

# --- 1. ARGUMENT PARSING ---
def get_args():
    """Retrieves arguments that follow '--' in the command line."""
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1:]

# --- 2. HELPER FUNCTIONS ---

def setup_sensor_object(location_str):
    """Creates an empty object that serves as our 'Sensor' origin."""
    try:
        x, y, z = map(float, location_str.split(','))
    except ValueError:
        print(f"CRITICAL ERROR: Could not parse position '{location_str}'. Format must be 'X,Y,Z'")
        sys.exit(1)
    
    if "SensorOrigin" in bpy.data.objects:
        sensor = bpy.data.objects["SensorOrigin"]
    else:
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD')
        sensor = bpy.context.active_object
        sensor.name = "SensorOrigin"
    
    sensor.location = Vector((x, y, z))
    
    # Point towards origin (0,0,0)
    direction = Vector((0, 0, 0)) - sensor.location
    if direction.length < 0.001:
        direction = Vector((0,0,-1)) 
        
    sensor.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return sensor

def quantize_value(value, step):
    """Snaps a value to the nearest step if step > 0."""
    if step <= 0.00001:
        return value
    return round(value / step) * step

def apply_target_transform(target_obj, trans_range, trans_step, rot_range, rot_step, force_zero=False):
    """
    Applies transformation to the target object.
    Includes quantization (steps) for rotation and translation.
    """
    if force_zero:
        # --- REFERENCE SCAN (0,0,0) ---
        rx, ry, rz = 0.0, 0.0, 0.0
        tx, ty, tz = 0.0, 0.0, 0.0
    else:
        # --- RANDOM SCAN ---
        
        # 1. Rotation (Degrees first, then quantize, then radians)
        rx_deg = random.uniform(-rot_range, rot_range)
        ry_deg = random.uniform(-rot_range, rot_range)
        rz_deg = random.uniform(-rot_range, rot_range)
        
        # Apply Step (Quantization)
        rx_deg = quantize_value(rx_deg, rot_step)
        ry_deg = quantize_value(ry_deg, rot_step)
        rz_deg = quantize_value(rz_deg, rot_step)
        
        rx, ry, rz = map(math.radians, [rx_deg, ry_deg, rz_deg])
        
        # 2. Translation (Meters)
        tx = random.uniform(-trans_range, trans_range)
        ty = random.uniform(-trans_range, trans_range)
        tz = random.uniform(-trans_range, trans_range)
        
        # Apply Step
        tx = quantize_value(tx, trans_step)
        ty = quantize_value(ty, trans_step)
        tz = quantize_value(tz, trans_step)
    
    # Apply to Blender Object
    target_obj.rotation_euler = Euler((rx, ry, rz), 'XYZ')
    target_obj.location = Vector((tx, ty, tz))
    
    # Update Dependency Graph
    bpy.context.view_layer.update()

    # Capture Matrix and Parameters
    matrix = target_obj.matrix_world.copy()
    params = {
        "rx_rad": rx, "ry_rad": ry, "rz_rad": rz,
        "tx_m": tx,   "ty_m": ty,   "tz_m": tz
    }
    return matrix, params

def create_hud_axes():
    """Creates a small 3D axis object for visualization."""
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    container = bpy.context.active_object
    container.name = "HUD_Axes_Container"
    container.empty_display_size = 0.0
    
    def create_bar(axis_vec, color):
        mesh = bpy.data.meshes.new("AxisPart")
        obj = bpy.data.objects.new("AxisPart", mesh)
        bpy.context.scene.collection.objects.link(obj)
        bm = bmesh.new()
        rotation = Vector((0,0,1)).rotation_difference(axis_vec).to_matrix().to_4x4()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, verts=bm.verts, vec=(0.05, 0.05, 0.5)) 
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.25))
        bmesh.ops.transform(bm, verts=bm.verts, matrix=rotation)
        bm.to_mesh(mesh)
        bm.free()
        obj.parent = container
        obj.matrix_local = Matrix.Identity(4)
        obj.color = color
        return obj

    create_bar(Vector((1,0,0)), (1,0,0,1)) # Red X
    create_bar(Vector((0,1,0)), (0,1,0,1)) # Green Y
    create_bar(Vector((0,0,1)), (0,0,1,1)) # Blue Z
    return container

def generate_debug_views(output_dir, target_obj, sensor_obj, fov_h, fov_v, max_dist):
    """Generates images with Sensor Viz + HUD Axes."""
    print(f"--- Generating Debug Views (Range: {max_dist}m) ---")
    
    original_loc = target_obj.location.copy()
    original_rot = target_obj.rotation_euler.copy()
    target_obj.location = Vector((0,0,0))
    target_obj.rotation_euler = Euler((0,0,0))
    bpy.context.view_layer.update()
    
    original_engine = bpy.context.scene.render.engine
    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
    bpy.context.scene.display.shading.light = 'FLAT'
    bpy.context.scene.display.shading.color_type = 'OBJECT'
    bpy.context.scene.display.shading.show_xray = True
    bpy.context.scene.display.shading.xray_alpha = 0.5 
    
    # Viz Objects
    mesh_body = bpy.data.meshes.new("TempCamBody")
    obj_body = bpy.data.objects.new("TempCamViz", mesh_body)
    bpy.context.scene.collection.objects.link(obj_body)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=0.4)
    bm.to_mesh(mesh_body)
    bm.free()
    obj_body.parent = sensor_obj
    obj_body.matrix_local = Matrix.Identity(4)
    obj_body.color = (1.0, 0.0, 0.0, 1.0) 

    mesh_fov = bpy.data.meshes.new("TempFOVMesh")
    obj_fov = bpy.data.objects.new("TempFOVViz", mesh_fov)
    bpy.context.scene.collection.objects.link(obj_fov)
    L = max_dist 
    dx = L * math.tan(math.radians(fov_h / 2.0))
    dy = L * math.tan(math.radians(fov_v / 2.0))
    bm = bmesh.new()
    v_top = bm.verts.new((0,0,0))
    v1 = bm.verts.new((-dx, -dy, -L))
    v2 = bm.verts.new((-dx, dy, -L))
    v3 = bm.verts.new((dx, dy, -L))
    v4 = bm.verts.new((dx, -dy, -L))
    bm.verts.ensure_lookup_table()
    bm.faces.new((v_top, v2, v1))
    bm.faces.new((v_top, v3, v2))
    bm.faces.new((v_top, v4, v3))
    bm.faces.new((v_top, v1, v4))
    bm.to_mesh(mesh_fov)
    bm.free()
    obj_fov.parent = sensor_obj
    obj_fov.matrix_local = Matrix.Identity(4)
    obj_fov.color = (0.0, 1.0, 1.0, 0.15)
    obj_fov.display_type = 'SOLID' 

    hud_axes = create_hud_axes()
    cam_data = bpy.data.cameras.new("DebugCamData")
    cam_obj = bpy.data.objects.new("DebugCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    track_con = cam_obj.constraints.new(type='TRACK_TO')
    track_con.target = target_obj
    track_con.track_axis = 'TRACK_NEGATIVE_Z'
    track_con.up_axis = 'UP_Y'
    cam_data.lens = 35

    dist = 8.0 
    height = 4.0
    views = {
        "view_iso":   Vector((dist, -dist, height)),
        "view_front": Vector((0, -dist, 0)),
        "view_right": Vector((dist, 0, 0)),
        "view_top":   Vector((0, 0, dist))
    }

    for name, pos in views.items():
        cam_obj.location = pos
        bpy.context.view_layer.update()
        
        mat = cam_obj.matrix_world
        right_vec = Vector((mat[0][0], mat[0][1], mat[0][2]))
        up_vec    = Vector((mat[1][0], mat[1][1], mat[1][2]))
        back_vec  = Vector((mat[2][0], mat[2][1], mat[2][2]))
        
        hud_pos = cam_obj.location + (back_vec * -5.0) + (right_vec * 2.2) + (up_vec * -1.2)
        hud_axes.location = hud_pos
        hud_axes.rotation_euler = (0,0,0) 

        filepath = os.path.join(output_dir, f"setup_{name}.png")
        bpy.context.scene.render.filepath = filepath
        bpy.ops.render.render(write_still=True)

    # Cleanup
    bpy.context.scene.render.engine = original_engine
    bpy.context.scene.display.shading.show_xray = False
    
    target_obj.location = original_loc
    target_obj.rotation_euler = original_rot
    
    objs_to_delete = [cam_obj, obj_body, obj_fov, hud_axes] + list(hud_axes.children)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs_to_delete:
        obj.select_set(True)
    bpy.ops.object.delete()
    
    for mesh in [mesh_body, mesh_fov]:
        bpy.data.meshes.remove(mesh, do_unlink=True)
    
    print("--- Debug Views Saved ---")

def perform_raycast_scan(sensor_obj, target_obj, res_w, res_h, fov_h, fov_v, max_dist, noise=0.0):
    """Simulates the sensor by shooting rays."""
    hit_points = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    sensor_loc, sensor_mat = sensor_obj.location, sensor_obj.matrix_world
    fov_h_rad, fov_v_rad = math.radians(fov_h), math.radians(fov_v)
    
    step_x = 1 
    step_y = 1
    
    missed_target_names = set()
    
    for y in range(0, res_h, step_y):
        for x in range(0, res_w, step_x):
            u, v = (x / res_w) - 0.5, (y / res_h) - 0.5
            angle_x, angle_y = u * fov_h_rad, v * fov_v_rad
            local_dir = Vector((math.tan(angle_x), math.tan(angle_y), -1.0)).normalized()
            world_dir = sensor_mat.to_3x3() @ local_dir
            
            result, location, normal, index, obj, matrix = bpy.context.scene.ray_cast(depsgraph, sensor_loc, world_dir, distance=max_dist)
            
            if result:
                if obj.name == target_obj.name:
                    if noise > 0:
                        location = Vector((location.x + random.gauss(0, noise), 
                                           location.y + random.gauss(0, noise), 
                                           location.z + random.gauss(0, noise)))
                    hit_points.append(location)
                else:
                    missed_target_names.add(obj.name)

    if len(hit_points) == 0:
        if len(missed_target_names) > 0:
            print(f"DEBUG: 0 points on target '{target_obj.name}'. Hit these instead: {missed_target_names}")
        else:
            print(f"DEBUG: 0 points found. Raycast hit nothing within {max_dist}m.")
            
    return hit_points

# --- 3. MAIN EXECUTION ---

def main():
    parser = argparse.ArgumentParser()
    # Basic Args
    parser.add_argument("--sensor_res", required=True)
    parser.add_argument("--sensor_fov", required=True)
    parser.add_argument("--position", required=True)
    parser.add_argument("--samples", type=int, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--target_name", default="Cube")
    parser.add_argument("--max_dist", type=float, default=100.0)
    parser.add_argument("--noise", type=float, default=0.0)
    parser.add_argument("--viz", action="store_true")

    # Range Args
    parser.add_argument("--rot_range", type=float, default=180.0)
    parser.add_argument("--trans_range", type=float, default=0.0)
    
    # NEW Step Args
    parser.add_argument("--rot_step", type=float, default=0.0)
    parser.add_argument("--trans_step", type=float, default=0.0)

    args = parser.parse_args(get_args())
    
    try:
        res_w, res_h = map(int, args.sensor_res.split('x'))
        fov_h, fov_v = map(float, args.sensor_fov.split('x'))
    except ValueError: return print("Error: Resolution or FOV format incorrect.")
    
    print(f"--- Blender Script Start ---")
    print(f"DEBUG: Rotation Range = +/- {args.rot_range} deg (Step: {args.rot_step})")
    print(f"DEBUG: Translation Range = +/- {args.trans_range} m (Step: {args.trans_step})")
    
    if args.target_name not in bpy.data.objects:
        print(f"CRITICAL ERROR: Target object '{args.target_name}' NOT FOUND in .blend file!")
        sys.exit(1)
        
    target_obj = bpy.data.objects[args.target_name]
    sensor_obj = setup_sensor_object(args.position)
    
    if not os.path.exists(args.output): os.makedirs(args.output)

    if args.viz:
        try:
            generate_debug_views(args.output, target_obj, sensor_obj, fov_h, fov_v, args.max_dist)
        except Exception as e:
            print(f"Warning: Could not generate debug views: {e}")

    gt_filepath = os.path.join(args.output, "ground_truth.csv")
    with open(gt_filepath, 'w', newline='') as gt_file:
        gt_writer = csv.writer(gt_file)
        gt_file.write(f"# Settings: Res={res_w}x{res_h}, FOV={fov_h}x{fov_v}, Pos={args.position}, Range={args.max_dist}\n")
        header = ['sample_id', 'filename', 'rx_rad', 'ry_rad', 'rz_rad', 'tx_m', 'ty_m', 'tz_m']
        matrix_headers = [f"m{r}{c}" for r in range(4) for c in range(4)]
        gt_writer.writerow(header + matrix_headers)

        for i in range(args.samples):
            # Force Scan 0 to Zero
            is_reference = (i == 0)
            
            gt_matrix, params = apply_target_transform(
                target_obj, 
                args.trans_range, args.trans_step,
                args.rot_range, args.rot_step,
                force_zero=is_reference
            )
            
            points = perform_raycast_scan(sensor_obj, target_obj, res_w, res_h, fov_h, fov_v, 
                                          max_dist=args.max_dist, noise=args.noise)
            
            if len(points) == 0:
                print(f"WARNING: Sample {i} produced 0 points!")
            
            filename = f"scan_{i:04d}.csv"
            filepath = os.path.join(args.output, filename)
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['X', 'Y', 'Z'])
                for p in points: writer.writerow([f"{p.x:.6f}", f"{p.y:.6f}", f"{p.z:.6f}"])
            
            flat_matrix = [f"{gt_matrix[r][c]:.6f}" for r in range(4) for c in range(4)]
            row_data = [i, filename, f"{params['rx_rad']:.6f}", f"{params['ry_rad']:.6f}", f"{params['rz_rad']:.6f}", f"{params['tx_m']:.6f}", f"{params['ty_m']:.6f}", f"{params['tz_m']:.6f}"]
            gt_writer.writerow(row_data + flat_matrix)
            
            if i % 10 == 0: print(f"Generated sample {i}/{args.samples} - {len(points)} points")

    print("--- Blender Script Finished ---")

if __name__ == "__main__":
    main()