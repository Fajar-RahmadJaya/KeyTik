import os
import json
from src.utility.constant import (data_dir, appdata_dir, pinned_file, condition_path)

# Load the condition from the condition.json file
def load_condition():
    try:
        if os.path.exists(condition_path):
            with open(condition_path, "r") as f:
                content = f.read().strip()  # Read and strip any extra whitespace
                if content:
                    data = json.loads(content)
                    if isinstance(data, dict) and "path" in data:
                        return data["path"]
                else:
                    print("Condition file is empty. Returning None.")
    except json.JSONDecodeError:
        print("Error: Condition file is not in valid JSON format. Resetting condition.")
    except Exception as e:
        print(f"An error occurred while loading condition: {e}")
    return None  # Return None if there is an error or the path is not found

# Get the path from condition.json
path_from_condition = load_condition()

# If the path is successfully retrieved from the JSON, define the active and store directories
if path_from_condition:
    active_dir = os.path.join(path_from_condition, 'Active')
    store_dir = os.path.join(path_from_condition, 'Store')
else:
    # Fallback to the default directory structure if the condition path is not available
    active_dir = os.path.join(data_dir, 'Active')
    store_dir = os.path.join(data_dir, 'Store')

# Ensure the Active and Store directories exist
if not os.path.exists(active_dir):
    os.makedirs(active_dir)

if not os.path.exists(store_dir):
    os.makedirs(store_dir)

# Define SCRIPT_DIR
SCRIPT_DIR = active_dir


# Load the pinned state from a file, if it exists
def load_pinned_profiles():
    try:
        if os.path.exists(pinned_file):
            with open(pinned_file, "r") as f:
                content = f.read().strip()  # Read and strip any extra whitespace
                if content:  # Check if there's content in the file
                    data = json.loads(content)  # Use json.loads to handle empty file gracefully
                    if isinstance(data, list):  # Ensure it's a list
                        return data
                else:
                    print("Pinned profiles file is empty. Returning an empty list.")
    except json.JSONDecodeError:
        print("Error: Pinned profiles file is not in valid JSON format. Resetting pinned profiles.")
    except Exception as e:
        print(f"An error occurred while loading pinned profiles: {e}")
    return []  # Default to an empty list if there is an error

# Save the pinned state to a file
def save_pinned_profiles(pinned_profiles):
    with open(pinned_file, "w") as f:
        json.dump(pinned_profiles, f)

if not os.path.exists(appdata_dir):
    os.makedirs(appdata_dir)

# Create path.json if missing
if not os.path.exists(condition_path):
    with open(condition_path, "w") as f:
        json.dump({"path": ""}, f)

# Create pinned_profiles.json if missing
if not os.path.exists(pinned_file):
    with open(pinned_file, "w") as f:
        json.dump([
            "Multiple Files Opener.ahk",
            "Take Coordinate And Copy It For Screen Clicker.ahk",
            "Screen Clicker.ahk",
            "Auto Clicker.ahk"
        ], f)

device_list_path = os.path.join(active_dir, "Autohotkey Interception", "shared_device_info.txt")
device_finder_path = os.path.join(active_dir, "Autohotkey Interception", "find_device.ahk")
coordinate_path = os.path.join(active_dir, "Autohotkey Interception", "Coordinate.ahk")