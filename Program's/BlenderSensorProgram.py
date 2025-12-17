import bpy
import sys
import argparse
import os
import math
import random
import csv
import numpy as np
from mathutils import Vector, Euler

# --- 1. ARGUMENT PARSING ---
def get_args():
    """Retrieves arguments that follow '--' in the command line."""
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1:]

# --- 2. HELPER FUNCTIONS ---

def clean_scene(target_name="Cube"):
    """Removes all existing mesh objects to prevent clutter, except the target."""
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.name != target_name:
            obj.select_set(True)
    bpy.ops.object.delete()

def add_noise(point, noise_level):
    """Adds Gaussian noise to a point."""
    if noise_level <= 0:
        return point
    
    # Noise on every axis
    dx = random.gauss(0, noise_level)
    dy = random.gauss(0, noise_level)
    dz = random.gauss(0, noise_level)
    
    return Vector((point.x + dx, point.y + dy, point.z + dz))

def setup_sensor_object(location_str):
    """Creates an empty object that serves as our 'Sensor' origin."""
    x, y, z = map(float, location_str.split(','))
    
    if "SensorOrigin" in bpy.data.objects:
        sensor = bpy.data.objects["SensorOrigin"]
    else:
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD')
        sensor = bpy.context.active_object
        sensor.name = "SensorOrigin"
    
    sensor.location = Vector((x, y, z))
    direction = Vector((0, 0, 0)) - sensor.location
    sensor.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    return sensor

def randomize_target(target_obj, trans_range, rot_range):
    """
    Randomly rotates and translates the target object.
    Returns: 
        1. The new World Matrix
        2. A dictionary with the specific Rx, Ry, Rz, Tx, Ty, Tz values used.
    """
    # 1. Calculate random values
    # Rotation (We store radians for math, but input is degrees)
    rx_deg = random.uniform(-rot_range, rot_range)
    ry_deg = random.uniform(-rot_range, rot_range)
    rz_deg = random.uniform(-rot_range, rot_range)
    
    rx = math.radians(rx_deg)
    ry = math.radians(ry_deg)
    rz = math.radians(rz_deg)
    
    # Translation
    tx = random.uniform(-trans_range, trans_range)
    ty = random.uniform(-trans_range, trans_range)
    tz = random.uniform(-trans_range, trans_range)
    
    # 2. Apply to object
    target_obj.rotation_euler = Euler((rx, ry, rz), 'XYZ')
    target_obj.location = Vector((tx, ty, tz))
    
    # Update scene
    bpy.context.view_layer.update()

    # 3. Return Matrix AND the specific parameters
    matrix = target_obj.matrix_world.copy()
    
    params = {
        "rx_rad": rx, "ry_rad": ry, "rz_rad": rz,
        "tx_m": tx,   "ty_m": ty,   "tz_m": tz
    }
    
    return matrix, params

def generate_debug_views(output_dir, target_obj, sensor_obj):
    """
    Generates 4 visual reference images (Top, Front, Right, Iso) 
    showing the setup, sensor position, and FOV.
    """
    print("--- Generating Debug Views ---")
    
    # 1. Make Sensor Visible
    # Ensure the sensor object is drawn as an identifiable object
    sensor_obj.empty_display_type = 'CONE' # Looks like a camera/sensor
    sensor_obj.empty_display_size = 3    # Make it visible
    sensor_obj.show_name = True            # Show "SensorOrigin" text
    
    # If the sensor has camera data (optional), show limits
    # Since we use an Empty for raycasting, we fake the visual cone:
    # (Optional: You could add a wireframe cone here, but the Empty 'CONE' is usually enough)

    # 2. Create an 'Observer' Camera (The one taking the pictures)
    cam_data = bpy.data.cameras.new("DebugCamData")
    cam_obj = bpy.data.objects.new("DebugCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    
    # Set this new camera as active for rendering
    bpy.context.scene.camera = cam_obj
    
    # Constraint: Always look at the target (Cube)
    track_con = cam_obj.constraints.new(type='TRACK_TO')
    track_con.target = target_obj
    track_con.track_axis = 'TRACK_NEGATIVE_Z'
    track_con.up_axis = 'UP_Y'

    # 3. Define Views (Positions relative to target)
    # Distance to zoom out
    dist = 6.0 
    height = 3.0
    
    views = {
        "view_iso":   Vector((dist, -dist, height)), # 3D Perspective
        "view_front": Vector((0, -dist, 0)),         # Front
        "view_right": Vector((dist, 0, 0)),          # Right side
        "view_top":   Vector((0, 0, dist))           # Top down
    }

    # 4. Render Loop
    # We use 'workbench' engine for quick viewport-like renders
    original_engine = bpy.context.scene.render.engine
    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
    
    # Settings for clear visualization
    bpy.data.scenes[0].display.shading.light = 'FLAT'
    bpy.data.scenes[0].display.shading.color_type = 'OBJECT'
    
    for name, pos in views.items():
        # Move camera
        cam_obj.location = pos
        bpy.context.view_layer.update()
        
        # Set output path
        filepath = os.path.join(output_dir, f"setup_{name}.png")
        bpy.context.scene.render.filepath = filepath
        
        # Render (OpenGL / Viewport render)
        # write_still=True saves the image
        bpy.ops.render.render(write_still=True)

    # 5. Cleanup
    # Restore engine
    bpy.context.scene.render.engine = original_engine
    
    # Delete debug camera
    bpy.ops.object.select_all(action='DESELECT')
    cam_obj.select_set(True)
    bpy.ops.object.delete()
    
    print("--- Debug Views Saved ---")

def perform_raycast_scan(sensor_obj, target_obj, res_w, res_h, fov_h, fov_v, max_dist=100.0, noise=0.0):
    """Simulates the sensor by shooting rays (Raycasting)."""
    hit_points = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    sensor_loc = sensor_obj.location
    sensor_mat = sensor_obj.matrix_world
    
    fov_h_rad = math.radians(fov_h)
    fov_v_rad = math.radians(fov_v)
    
    step_x = 1 
    step_y = 1
    
    for y in range(0, res_h, step_y):
        for x in range(0, res_w, step_x):
            u = (x / res_w) - 0.5
            v = (y / res_h) - 0.5
            
            angle_x = u * fov_h_rad
            angle_y = v * fov_v_rad
            
            local_dir = Vector((math.tan(angle_x), math.tan(angle_y), -1.0))
            local_dir.normalize()
            world_dir = sensor_mat.to_3x3() @ local_dir
            
            result, location, normal, index, obj, matrix = bpy.context.scene.ray_cast(depsgraph, sensor_loc, world_dir, distance=max_dist)
            
            if result and obj.name == target_obj.name:
                final_point = add_noise(location, noise)
                hit_points.append(final_point)

    return hit_points

# --- 3. MAIN EXECUTION ---

def main():
    parser = argparse.ArgumentParser(description="Blender Synthetic Data Generator")
    parser.add_argument("--sensor_res", required=True)
    parser.add_argument("--sensor_fov", required=True)
    parser.add_argument("--position", required=True)
    parser.add_argument("--samples", type=int, required=True)
    parser.add_argument("--output", required=True)
    
    parser.add_argument("--rot_range", type=float, default=180.0)
    parser.add_argument("--trans_range", type=float, default=0.0)
    parser.add_argument("--noise", type=float, default=0.0)
    parser.add_argument("--target_name", default="Cube")

    args = parser.parse_args(get_args())
    
    try:
        res_w, res_h = map(int, args.sensor_res.split('x'))
        fov_h, fov_v = map(float, args.sensor_fov.split('x'))
    except ValueError:
        print("Error: Resolution or FOV format incorrect.")
        return
    
    print(f"--- Blender Script Start ---")
    
    if args.target_name not in bpy.data.objects:
        print(f"ERROR: Object '{args.target_name}' not found!")
        return
    
    target_obj = bpy.data.objects[args.target_name]
    
    # --- FIX IS HERE: Assign the result to 'sensor_obj' ---
    sensor_obj = setup_sensor_object(args.position)
    
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # Now 'sensor_obj' exists and can be passed to the function
    try:
        generate_debug_views(args.output, target_obj, sensor_obj)
    except Exception as e:
        print(f"Warning: Could not generate debug views: {e}")
        import traceback
        traceback.print_exc() # Print full error details if it fails

    # --- SETUP GROUND TRUTH FILE ---
    gt_filepath = os.path.join(args.output, "ground_truth.csv")
    
    with open(gt_filepath, 'w', newline='') as gt_file:
        gt_writer = csv.writer(gt_file)
        
        # 1. Write Metadata
        gt_file.write(f"# Global Settings\n")
        gt_file.write(f"# Sensor Resolution: {res_w}x{res_h}\n")
        gt_file.write(f"# Sensor FOV: {fov_h}x{fov_v}\n")
        gt_file.write(f"# Sensor Position: {args.position}\n")
        gt_file.write(f"# Noise Level: {args.noise}\n")
        gt_file.write(f"# Rotation Range: +/- {args.rot_range}\n")
        gt_file.write(f"# Translation Range: +/- {args.trans_range}\n")
        gt_file.write(f"# --------------------------------\n")
        
        # 2. Write Header
        header = ['sample_id', 'filename', 
                  'rx_rad', 'ry_rad', 'rz_rad', 
                  'tx_m', 'ty_m', 'tz_m']
        
        matrix_headers = [f"m{r}{c}" for r in range(4) for c in range(4)]
        gt_writer.writerow(header + matrix_headers)

        # --- GENERATION LOOP ---
        # Note: sensor_obj is already defined above, so we don't need to find it again
        # but looking it up by name is also fine.
        
        for i in range(args.samples):
            # 1. Randomize
            gt_matrix, params = randomize_target(target_obj, args.trans_range, args.rot_range)
            
            # 2. Scan
            points = perform_raycast_scan(
                sensor_obj, target_obj, 
                res_w, res_h, fov_h, fov_v, 
                noise=args.noise
            )
            
            # 3. Save CSV
            filename = f"scan_{i:04d}.csv"
            filepath = os.path.join(args.output, filename)
            
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['X', 'Y', 'Z'])
                for p in points:
                    writer.writerow([f"{p.x:.6f}", f"{p.y:.6f}", f"{p.z:.6f}"])
            
            # 4. Save Ground Truth
            flat_matrix = [f"{gt_matrix[r][c]:.6f}" for r in range(4) for c in range(4)]
            
            row_data = [
                i, filename,
                f"{params['rx_rad']:.6f}", f"{params['ry_rad']:.6f}", f"{params['rz_rad']:.6f}",
                f"{params['tx_m']:.6f}", f"{params['ty_m']:.6f}", f"{params['tz_m']:.6f}"
            ]
            
            gt_writer.writerow(row_data + flat_matrix)
            
            if i % 10 == 0:
                print(f"Generated sample {i}/{args.samples} - {len(points)} points")

    print("--- Blender Script Finished ---")

if __name__ == "__main__":
    main()