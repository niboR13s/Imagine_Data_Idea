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

def setup_sensor_object(location_str, target_obj):
    """
    Creates/Moves the sensor RELATIVE to the target object's POSITION,
    but INDEPENDENT of its rotation.
    Standard Blender Axes: Z is UP, Y is DEPTH.
    """
    try:
        # Parse the input coordinates (Offset in meters)
        offset_x, offset_y, offset_z = map(float, location_str.split(','))
        offset_vec = Vector((offset_x, offset_y, offset_z))
    except ValueError:
        print(f"CRITICAL ERROR: Could not parse position '{location_str}'. Format must be 'X,Y,Z'")
        sys.exit(1)
    
    # 1. Find or Create Sensor
    if "SensorOrigin" in bpy.data.objects:
        sensor = bpy.data.objects["SensorOrigin"]
    else:
        sensor = bpy.data.objects.new("SensorOrigin", None)
        sensor.empty_display_type = 'PLAIN_AXES'
        bpy.context.scene.collection.objects.link(sensor)
    
    # --- IMPORTANT: DETACH FROM PARENT ---
    # This ensures the camera does NOT rotate if the object rotates.
    sensor.parent = None 
    # -------------------------------------

    # 2. Position Logic
    # We take the Target's WORLD location + Offset.
    # Because parent is None, we calculate the absolute world position.
    # Note: We use matrix_world.translation to get the true center even if parented.
    sensor.location = target_obj.matrix_world.translation + offset_vec

    # 3. Look At Logic
    # Camera looks at the center of the target
    direction = target_obj.matrix_world.translation - sensor.location
    if direction.length < 0.001:
        direction = Vector((0,0,-1)) 
        
    # Blender Camera looks down -Z, so we track -Z to the target
    sensor.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    bpy.context.view_layer.update()
    
    return sensor

def quantize_value(value, step):
    """Snaps a value to the nearest step if step > 0."""
    if step <= 0.00001:
        return value
    return round(value / step) * step

def apply_target_transform(target_obj, base_loc, base_rot, trans_range, trans_step, rot_range, rot_step, force_zero=False):
    """
    Applies transformation RELATIVE to the object's STARTING pose (base_loc/base_rot).
    """
    if force_zero:
        # Reference Scan: Keep the object exactly as you placed it manually
        rx, ry, rz = 0.0, 0.0, 0.0
        tx, ty, tz = 0.0, 0.0, 0.0
    else:
        # Random Scan: Add noise to the base position
        
        # 1. Rotation offsets
        rx_deg = random.uniform(-rot_range, rot_range)
        ry_deg = random.uniform(-rot_range, rot_range)
        rz_deg = random.uniform(-rot_range, rot_range)
        
        rx_deg = quantize_value(rx_deg, rot_step)
        ry_deg = quantize_value(ry_deg, rot_step)
        rz_deg = quantize_value(rz_deg, rot_step)
        
        rx, ry, rz = map(math.radians, [rx_deg, ry_deg, rz_deg])
        
        # 2. Translation offsets
        tx = random.uniform(-trans_range, trans_range)
        ty = random.uniform(-trans_range, trans_range)
        tz = random.uniform(-trans_range, trans_range)
        
        tx = quantize_value(tx, trans_step)
        ty = quantize_value(ty, trans_step)
        tz = quantize_value(tz, trans_step)
    
    # --- APPLY: Base Pose + Random Offset ---
    # We add the random rotation to the manual rotation (base_rot)
    target_obj.rotation_euler = Euler((base_rot.x + rx, base_rot.y + ry, base_rot.z + rz), 'XYZ')
    target_obj.location = Vector((base_loc.x + tx, base_loc.y + ty, base_loc.z + tz))
    
    bpy.context.view_layer.update()

    # Capture Matrix and Params (We log the OFFSET relative to base)
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
    """
    Generates images with Sensor Viz + HUD Axes.
    UPDATED: Now works correctly with relative coordinates and independent rotation.
    It moves the camera TO the object, instead of moving the object to (0,0,0).
    """
    print(f"--- Generating Debug Views (Range: {max_dist}m) ---")
    
    # 1. Setup Render Engine (Workbench for quick wireframe-ish look)
    original_engine = bpy.context.scene.render.engine
    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
    bpy.context.scene.display.shading.light = 'FLAT'
    bpy.context.scene.display.shading.color_type = 'OBJECT'
    bpy.context.scene.display.shading.show_xray = True
    bpy.context.scene.display.shading.xray_alpha = 0.5 
    
    # 2. Visualize the Sensor (The Red Box + Blue Cone)
    # We create temporary shapes and attach them to the sensor_obj
    
    # -- Red Box (The Camera Body) --
    mesh_body = bpy.data.meshes.new("TempCamBody")
    obj_body = bpy.data.objects.new("TempCamViz", mesh_body)
    bpy.context.scene.collection.objects.link(obj_body)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=0.2) # Small cube
    bm.to_mesh(mesh_body)
    bm.free()
    obj_body.parent = sensor_obj # Attach to sensor
    obj_body.matrix_local = Matrix.Identity(4)
    obj_body.color = (1.0, 0.0, 0.0, 1.0) # Red

    # -- Blue Cone (The FOV) --
    mesh_fov = bpy.data.meshes.new("TempFOVMesh")
    obj_fov = bpy.data.objects.new("TempFOVViz", mesh_fov)
    bpy.context.scene.collection.objects.link(obj_fov)
    L = max_dist 
    # Calculate cone dimensions based on FOV
    dx = L * math.tan(math.radians(fov_h / 2.0))
    dy = L * math.tan(math.radians(fov_v / 2.0))
    
    bm = bmesh.new()
    v_top = bm.verts.new((0,0,0))
    v1 = bm.verts.new((-dx, -dy, -L)) # Blender Camera looks down -Z
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
    obj_fov.parent = sensor_obj # Attach to sensor
    obj_fov.matrix_local = Matrix.Identity(4)
    obj_fov.color = (0.0, 1.0, 1.0, 0.15) # Transparent Cyan
    obj_fov.display_type = 'SOLID' 

    # 3. Setup the "Photographer" (The Debug Camera)
    hud_axes = create_hud_axes()
    cam_data = bpy.data.cameras.new("DebugCamData")
    cam_obj = bpy.data.objects.new("DebugCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj # Set as active camera
    
    # Constraint: Always look at the Target Object
    track_con = cam_obj.constraints.new(type='TRACK_TO')
    track_con.target = target_obj
    track_con.track_axis = 'TRACK_NEGATIVE_Z'
    track_con.up_axis = 'UP_Y'
    cam_data.lens = 50

    # 4. Define View Positions RELATIVE to the Target
    # We take the target's current world location and add offsets
    center = target_obj.matrix_world.translation
    dist = 4.0 # Distance from object to take photo
    
    views = {
        "view_iso":   center + Vector((dist, -dist, dist/2)), # Angle
        "view_front": center + Vector((0, -dist, 0)),         # Front
        "view_side":  center + Vector((dist, 0, 0)),          # Side
        "view_top":   center + Vector((0, 0, dist))           # Top down
    }

    # 5. Render Loop
    for name, pos in views.items():
        cam_obj.location = pos
        bpy.context.view_layer.update()
        
        # Move HUD Axes to the corner of the camera view
        mat = cam_obj.matrix_world
        right_vec = Vector((mat[0][0], mat[0][1], mat[0][2]))
        up_vec    = Vector((mat[1][0], mat[1][1], mat[1][2]))
        back_vec  = Vector((mat[2][0], mat[2][1], mat[2][2]))
        
        # Calculate HUD position relative to camera frame
        hud_pos = cam_obj.location + (back_vec * -5.0) + (right_vec * 2.2) + (up_vec * -1.2)
        hud_axes.location = hud_pos
        hud_axes.rotation_euler = (0,0,0) # Axes always stay world-aligned

        # Save Image
        filepath = os.path.join(output_dir, f"setup_{name}.png")
        bpy.context.scene.render.filepath = filepath
        bpy.ops.render.render(write_still=True)

    # 6. Cleanup (Delete temp objects)
    bpy.context.scene.render.engine = original_engine
    bpy.context.scene.display.shading.show_xray = False
    
    objs_to_delete = [cam_obj, obj_body, obj_fov, hud_axes] + list(hud_axes.children)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs_to_delete:
        obj.select_set(True)
    bpy.ops.object.delete()
    
    # Remove meshes from memory
    for mesh in [mesh_body, mesh_fov]:
        bpy.data.meshes.remove(mesh, do_unlink=True)
    
    print("--- Debug Views Saved ---")

def perform_raycast_scan(sensor_obj, target_obj, res_w, res_h, fov_h, fov_v, max_dist, noise=0.0):
    """
    Simulates the sensor by shooting rays.
    Includes BLOCKER DETECTION and FORCE UPDATE for modifiers.
    """
    hit_points = []
    
    # 1. Force update to apply Modifiers (Boolean/Rig)
    bpy.context.view_layer.update()
    
    # 2. Get evaluated graph
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    sensor_loc, sensor_mat = sensor_obj.location, sensor_obj.matrix_world
    fov_h_rad, fov_v_rad = math.radians(fov_h), math.radians(fov_v)
    
    step_x = 1 
    step_y = 1
    
    # Debug counters
    hits_target = 0
    hits_something_else = 0
    misses_completely = 0
    blocking_objects = {} 
    
    for y in range(0, res_h, step_y):
        for x in range(0, res_w, step_x):
            u, v = (x / res_w) - 0.5, (y / res_h) - 0.5
            angle_x, angle_y = u * fov_h_rad, v * fov_v_rad
            
            local_dir = Vector((math.tan(angle_x), math.tan(angle_y), -1.0)).normalized()
            world_dir = sensor_mat.to_3x3() @ local_dir
            
            # SHOOT RAY
            result, location, normal, index, obj, matrix = bpy.context.scene.ray_cast(depsgraph, sensor_loc, world_dir, distance=max_dist)
            
            if result:
                if obj.name == target_obj.name:
                    hits_target += 1
                    if noise > 0:
                        location = Vector((location.x + random.gauss(0, noise), 
                                           location.y + random.gauss(0, noise), 
                                           location.z + random.gauss(0, noise)))
                    hit_points.append(location)
                else:
                    hits_something_else += 1
                    if obj.name in blocking_objects:
                        blocking_objects[obj.name] += 1
                    else:
                        blocking_objects[obj.name] = 1
            else:
                misses_completely += 1

    # Warning for low data
    if len(hit_points) < 50:
        print(f"\n[Warning] LOW DATA SCAN ({len(hit_points)} points).")
        print(f"  - Rays blocked by other objects: {hits_something_else}")
        if blocking_objects:
             print(f"  - BLOCKERS: {blocking_objects}")
        print(f"  - Rays missed completely: {misses_completely}")

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
    
    # Step Args
    parser.add_argument("--rot_step", type=float, default=0.0)
    parser.add_argument("--trans_step", type=float, default=0.0)

    parser.add_argument("--debug", type=bool, default=False)

    args = parser.parse_args(get_args())

    try:
        res_w, res_h = map(int, args.sensor_res.split('x'))
        fov_h, fov_v = map(float, args.sensor_fov.split('x'))
    except ValueError: return print("Error: Resolution or FOV format incorrect.")

    if args.debug:
        print(f"--- Blender Script Start ---")
        print(f"DEBUG: Rotation Range = +/- {args.rot_range} deg")
        print("\n" + "="*40)
        print("DEBUG: LIST OF ALL OBJECTS IN SCENE")
        print("="*40)
        for obj in bpy.data.objects:
            print(f"  - Name: '{obj.name}' \t(Type: {obj.type})")
        print("="*40 + "\n")
    
    # 1. FIND TARGET
    if args.target_name not in bpy.data.objects:
        print(f"CRITICAL ERROR: Target object '{args.target_name}' NOT FOUND!")
        sys.exit(1)
        
    target_obj = bpy.data.objects[args.target_name]
    
    # --- STORE MANUAL START POSE ---
    base_location = target_obj.location.copy()
    base_rotation = target_obj.rotation_euler.copy()
    # -------------------------------
    
    # 2. SETUP SENSOR (Initial)
    sensor_obj = setup_sensor_object(args.position, target_obj)
    
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
            is_reference = (i == 0)
            
            # Apply transform relative to BASE pose
            gt_matrix, params = apply_target_transform(
                target_obj, 
                base_location, base_rotation,
                args.trans_range, args.trans_step,
                args.rot_range, args.rot_step,
                force_zero=is_reference
            )
            
            # Update sensor position (it follows translation, ignores rotation)
            setup_sensor_object(args.position, target_obj)
            
            # Scan
            points = perform_raycast_scan(sensor_obj, target_obj, res_w, res_h, fov_h, fov_v, 
                                          max_dist=args.max_dist, noise=args.noise)
            
            # Write Scan
            filename = f"scan_{i:04d}.csv"
            filepath = os.path.join(args.output, filename)
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['X', 'Y', 'Z'])
                for p in points: writer.writerow([f"{p.x:.6f}", f"{p.y:.6f}", f"{p.z:.6f}"])
            
            # Write GT
            flat_matrix = [f"{gt_matrix[r][c]:.6f}" for r in range(4) for c in range(4)]
            row_data = [i, filename, f"{params['rx_rad']:.6f}", f"{params['ry_rad']:.6f}", f"{params['rz_rad']:.6f}", f"{params['tx_m']:.6f}", f"{params['ty_m']:.6f}", f"{params['tz_m']:.6f}"]
            gt_writer.writerow(row_data + flat_matrix)
            
            if i % 10 == 0: print(f"Generated sample {i}/{args.samples} - {len(points)} points")

    # Restore Manual Pose
    target_obj.location = base_location
    target_obj.rotation_euler = base_rotation
    
    print("--- Blender Script Finished ---")

if __name__ == "__main__":
    main()