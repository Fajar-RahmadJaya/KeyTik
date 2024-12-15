import os
import shutil
import tkinter as tk
from tkinter import Tk, filedialog
from tkinter import messagebox
from tkinter import ttk
from pynput.keyboard import Controller, Key
import sys
import winshell
from win32com.client import Dispatch
from PIL import Image, ImageTk 
from tkinter import LabelFrame
import json
from tkinter import TclError
import keyboard
import time
from pynput import mouse
from tkinter import ttk
import psutil

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

# Define the path to the 'Data' directory
data_dir = os.path.join(script_dir, '_internal', 'Data')

# Define the path to the 'Active' folder within the 'Data' directory
active_dir = os.path.join(data_dir, 'Active')

# Define the path to the 'Store' folder within the 'Data' directory
store_dir = os.path.join(data_dir, 'Store')

# Check if the 'Active' folder exists
if not os.path.exists(active_dir):
    # Create the 'Active' folder if it does not exist
    os.makedirs(active_dir)

# Check if the 'Active' folder exists
if not os.path.exists(store_dir):
    # Create the 'Store' folder if it does not exist
    os.makedirs(store_dir)

# Define SCRIPT_DIR
SCRIPT_DIR = active_dir

# Path to store pinned profiles
PINNED_FILE = os.path.join(data_dir, "pinned_profiles.json")

# Build the path to the icon file
if getattr(sys, 'frozen', False):
    icon_path = os.path.join(sys._MEIPASS,  "Data", "icon.ico")
    pin_path = os.path.join(sys._MEIPASS, "Data", "que.ico")
    icon_unpinned_path = os.path.join(sys._MEIPASS, "Data", "icon_a.png")
    icon_pinned_path = os.path.join(sys._MEIPASS, "Data", "icon_b.png")
    device_list_path = os.path.join(sys._MEIPASS, "Data", "Active", "AutoHotkey Interception", "shared_device_info.txt")
    device_finder_path = os.path.join(sys._MEIPASS, 'Data', 'Active', "AutoHotkey Interception", "find_device.ahk")
    keylist_path = os.path.join(sys._MEIPASS, "Data", "key_list.txt")
else:
    icon_path = os.path.join(data_dir, "icon.ico")
    pin_path = os.path.join(data_dir, "pin.json")
    icon_unpinned_path = os.path.join(data_dir, "icon_a.png")
    icon_pinned_path = os.path.join(data_dir, "icon_b.png")
    device_list_path = os.path.join(active_dir, "Autohotkey Interception", "shared_device_info.txt")
    device_finder_path = os.path.join(active_dir, "Autohotkey Interception", "find_device.ahk")
    keylist_path = os.path.join(data_dir, "key_list.txt")

# Load the pinned state from a file, if it exists
def load_pinned_profiles():
    try:
        if os.path.exists(PINNED_FILE):
            with open(PINNED_FILE, "r") as f:
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
    with open(PINNED_FILE, "w") as f:
        json.dump(pinned_profiles, f)

class ScriptManagerApp:
    def __init__(self, root):
        self.first_load = True
        self.root = root
        self.root.geometry("650x500+284+97")  # Set initial size (width x height)
        self.root.title("KeyTik")
        self.current_page = 0
        self.SCRIPT_DIR = active_dir
        self.pinned_profiles = load_pinned_profiles()
        self.icon_unpinned = ImageTk.PhotoImage(Image.open(icon_unpinned_path).resize((14, 14)))
        self.icon_pinned = ImageTk.PhotoImage(Image.open(icon_pinned_path).resize((14, 14)))
        self.scripts = self.list_scripts()
        self.frames = []
        self.root.iconbitmap(icon_path)
        self.root.resizable(False, False)
        self.create_ui()
        self.update_script_list()
        self.is_on_top = False
        self.create_profile_window = None
        self.edit_window = None
        self.key_rows = []
        self.shortcut_rows = []
        self.is_listening = False
        self.active_entry = None
        self.hook_registered = False
        self.row_num = 0
        self.shortcut_rows = []
        self.pressed_keys = []  # List to store pressed keys in order
        self.last_key_time = 0  # Time when the last key was pressed
        self.timeout = 1  # Timeout in seconds to finalize the key combination
        self.mouse_listener = None  # Mouse listener instance
        self.ignore_next_click = False  # Flag to ignore the first mouse click after toggling
        self.shortcut_entry = None

    def create_ui(self):
        """Create the main UI components."""
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)  # Fill the entire window

        self.script_frame = tk.Frame(self.frame)
        self.script_frame.pack(pady=10, fill=tk.BOTH, expand=True)  # Fill the parent frame

        self.create_navigation_buttons()
        self.create_action_buttons()

    def create_navigation_buttons(self):
        """Create navigation buttons for paging through scripts."""
        nav_frame = tk.Frame(self.frame)
        nav_frame.pack(side=tk.TOP, fill=tk.X)  # Align at the top and fill horizontally
    
        self.prev_button = tk.Button(nav_frame, text="Previous", command=self.prev_page, width=12, height=1)
        self.prev_button.pack(side=tk.LEFT, padx=30)
    
        self.next_button = tk.Button(nav_frame, text="Next", command=self.next_page, width=12, height=1)
        self.next_button.pack(side=tk.RIGHT, padx=30)
    
    def create_action_buttons(self):
        """Create the action buttons for creating new profiles."""
        # Create a container frame for the action buttons
        action_container = tk.Frame(self.frame)
        action_container.pack(pady=5, side=tk.BOTTOM)  # This will center the group of buttons vertically

        # Create the action buttons inside the container frame
        self.create_button = tk.Button(action_container, text="Create New Profile", command=self.create_new_profile, width=20, height=1)
        self.create_button.grid(row=0, column=0, padx=15, pady=3)
    
        self.always_top = tk.Button(action_container, text="Always On Top", command=self.toggle_on_top, width=20, height=1)
        self.always_top.grid(row=1, column=1, padx=15, pady=3)
    
        self.show_stored = tk.Button(action_container, text="Show Stored Profile", width=20, height=1, command=self.toggle_script_dir)
        self.show_stored.grid(row=1, column=0, padx=15, pady=3)

        self.import_button = tk.Button(action_container, text="Import Profile", width=20, height=1, command=self.import_button)
        self.import_button.grid(row=0, column=1, padx=15, pady=3)
    
        # Center the action_container by expanding the column in its parent frame
        action_container.grid_columnconfigure(0, weight=1)  # Centering by expanding space equally
        action_container.grid_columnconfigure(1, weight=1)

    def toggle_on_top(self):
        """Toggle the always-on-top feature."""
        self.is_on_top = not self.is_on_top
        self.root.attributes("-topmost", self.is_on_top)  # Ensure to toggle 'topmost' on the root window

        if self.create_profile_window is not None:
            self.create_profile_window.attributes("-topmost", self.is_on_top)
            if self.is_on_top:
                self.create_profile_window.title("Create New Profile (Always on Top)")
            else:
                self.create_profile_window.title("Create New Profile")

        # Check if the edit_window exists and is still valid
        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.attributes("-topmost", self.is_on_top)
            if self.is_on_top:
                self.edit_window.title("Edit Profile (Always on Top)")
            else:
                self.edit_window.title("Edit Profile")
        else:
            self.edit_window = None  # Reset the reference if it doesn't exist

        if self.is_on_top:
            self.root.title("KEES (Always on Top)")
            self.always_top.config(text="Disable Always on Top")
        else:
            self.root.title("KEES")
            self.always_top.config(text="Enable Always on Top")

    def list_scripts(self):
        """List all .ahk and .py files in the active directory and return the script list."""
        # Create a list of all .ahk and .py files
        all_scripts = [f for f in os.listdir(self.SCRIPT_DIR) if f.endswith('.ahk') or f.endswith('.py')]

        # Separate pinned and unpinned profiles
        pinned = [script for script in all_scripts if script in self.pinned_profiles]
        unpinned = [script for script in all_scripts if script not in self.pinned_profiles]

        # Return a combined list with pinned scripts at the top
        self.scripts = pinned + unpinned
        return self.scripts  # Ensure it returns a list of scripts

    def is_script_running(self, script_name):
        """Check if the script is running in the background."""
        for process in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if process.info['name'] and 'autohotkey' in process.info['name'].lower():
                    if process.info['cmdline']:
                        for arg in process.info['cmdline']:
                            if arg.endswith(script_name):  # Check if the script is running
                                return True
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
        return False

    def update_script_list(self):
        """Update the script list based on the current page."""

        # Clear previous widgets
        for widget in self.script_frame.winfo_children():
            widget.destroy()

        start_index = self.current_page * 6
        end_index = start_index + 6
        scripts_to_display = self.scripts[start_index:end_index]

        for index, script in enumerate(scripts_to_display):
            row = index // 2  # Determine the row index (0, 1, 2)
            column = index % 2  # Determine the column index (0 or 1)

            # Check if the script is pinned and set the appropriate icon
            icon = self.icon_pinned if script in self.pinned_profiles else self.icon_unpinned

            # Create a LabelFrame with the script name as the title
            frame = LabelFrame(self.script_frame, text=os.path.splitext(script)[0], padx=10, pady=10)
            frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

            # Place the icon in the top-right corner of the LabelFrame using `place()`
            icon_label = tk.Label(frame, image=icon, cursor="hand2")
            icon_label.image = icon  # Keep a reference to avoid garbage collection
            icon_label.place(relx=1.0, rely=0, anchor="ne", x=9, y=-18)

            # Bind the icon click event to pin/unpin the script
            icon_label.bind("<Button-1>",
                            lambda event, script=script, icon_label=icon_label: self.toggle_pin(script, icon_label))

            # Add buttons inside the LabelFrame
            run_button = tk.Button(frame, text="Run", width=10, height=1)
            run_button.grid(row=0, column=0, padx=2, pady=5)

            exit_button = tk.Button(frame, text="Exit", state="disabled", width=10, height=1)
            exit_button.grid(row=0, column=1, padx=5, pady=5)

            # Check if the script is already running and update button states only on first load
            if self.first_load:
                if self.is_script_running(script):
                    run_button.config(state='disabled')
                    exit_button.config(state='normal')
                else:
                    run_button.config(state='normal')
                    exit_button.config(state='disabled')
            else:
                # If not the first load, assume buttons are already set correctly
                run_button.config(state='normal')
                exit_button.config(state='disabled')

            # Configure the button actions
            run_button.config(command=lambda s=script, rb=run_button, eb=exit_button: self.activate_script(s, rb, eb))
            exit_button.config(command=lambda s=script, rb=run_button, eb=exit_button: self.exit_script(s, rb, eb))

            delete_button = tk.Button(frame, text="Delete", command=lambda s=script: self.delete_script(s), width=10,
                                      height=1)
            delete_button.grid(row=0, column=2, padx=8, pady=5)

            store_button = tk.Button(frame, text="Store" if self.SCRIPT_DIR == active_dir else "Restore",
                                     command=lambda s=script: self.store_script(s), width=10, height=1)
            store_button.grid(row=1, column=0, padx=2, pady=5)

            edit_button = tk.Button(frame, text="Edit",
                                    command=lambda s=script, rb=run_button, eb=exit_button: (
                                        self.exit_script(s, rb, eb),  # First, execute exit_script
                                        self.edit_script(s)  # Then, execute edit_script
                                    ),
                                    width=10, height=1)
            edit_button.grid(row=1, column=1, padx=5, pady=5)

            # Check if the script is already in the startup folder
            shortcut_name = os.path.splitext(script)[0] + ".lnk"  # Shortcut name
            startup_folder = winshell.startup()
            shortcut_path = os.path.join(startup_folder, shortcut_name)

            if os.path.exists(shortcut_path):
                # If the shortcut exists, change the button to remove from startup
                startup_button = tk.Button(frame, text="Unstart",
                                           command=lambda s=script: self.remove_ahk_from_startup(s),
                                           width=10, height=1)
            else:
                # If the shortcut doesn't exist, use the original command
                startup_button = tk.Button(frame, text="Startup",
                                           command=lambda s=script: self.add_ahk_to_startup(s),
                                           width=10, height=1)

            startup_button.grid(row=1, column=2, padx=8, pady=5)

        # Configure grid weights to ensure proper resizing
        for i in range(3):
            self.script_frame.grid_rowconfigure(i, weight=1)
        for i in range(2):
            self.script_frame.grid_columnconfigure(i, weight=1)

        # After the first load, set the flag to False
        self.first_load = False
        
    def toggle_pin(self, script, icon_label):
        """Toggle the pin state for a script and update the icon."""
        if script in self.pinned_profiles:
            # Unpin the script
            self.pinned_profiles.remove(script)
            icon_label.config(image=self.icon_unpinned)
        else:
            # Pin the script
            self.pinned_profiles.insert(0, script)
            icon_label.config(image=self.icon_pinned)

        # Save the updated pinned profiles and refresh the display
        save_pinned_profiles(self.pinned_profiles)
        self.list_scripts()
        self.update_script_list()

    def import_button(self):
    
        # Open file manager to choose a file
        Tk().withdraw()  # Hide Tkinter root window
        selected_file = filedialog.askopenfilename(title="Select AHK Script", filetypes=[("AHK Scripts", "*.ahk")])
    
        # Check if a file was selected
        if not selected_file:
            print("No file selected.")
            return
    
        # Ensure the file has .ahk extension
        if not selected_file.endswith('.ahk'):
            print("Error: Only .ahk files are allowed.")
            return
    
        # Assuming SCRIPT_DIR is already defined in your class (modify this if needed)
        SCRIPT_DIR = self.SCRIPT_DIR
    
        # Get the filename from the selected file path
        file_name = os.path.basename(selected_file)
    
        # Define the destination path in SCRIPT_DIR
        destination_path = os.path.join(SCRIPT_DIR, file_name)
    
        # Move the file to the SCRIPT_DIR
        try:
            shutil.move(selected_file, destination_path)
            print(f"File moved to: {destination_path}")
        except Exception as e:
            print(f"Failed to move file: {e}")
            return
    
        # Now modify the file contents in its new location
        with open(destination_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    
        # Check if the script already has the required lines
        already_has_exit = any("^!p::ExitApp" in line for line in lines)
        already_has_default = any("; default" in line or "; text" in line for line in lines)
    
        if not already_has_exit or not already_has_default:
            # Check the format of the first line
            first_line = lines[0].strip() if lines else ''
    
            # Handle the case for `; text` or `; default`
            if first_line and '::' in first_line:
                # If the first line is script-like, add `; default`
                new_lines = [
                    "; default\n",
                    "^!p::ExitApp\n",
                    "\n"  # Add a new line for better formatting
                ] + [first_line + '\n'] + lines[1:]
            else:
                # If the first line is plain text, add `; text`
                new_lines = [
                    "; text\n",
                    "^!p::ExitApp\n",
                    "\n"  # Add a new line for better formatting
                ] + lines

            # Write the modified contents back to the file in SCRIPT_DIR
            with open(destination_path, 'w', encoding='utf-8') as file:
                file.writelines(new_lines)
    
            print(f"Modified script saved at: {destination_path}")
        else:
            print(f"Script already contains `; default` or `; text` and ExitApp. No changes made.")
    
        # Append the newly added script to self.scripts
        self.scripts.append(file_name)  # Ensure file_name is the script's name without path
        self.update_script_list()  # Refresh the UI to show the updated script list

    def prev_page(self):
        """Go to the previous page of scripts."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_script_list()

    def next_page(self):
        """Go to the next page of scripts."""
        if (self.current_page + 1) * 6 < len(self.scripts):
            self.current_page += 1
            self.update_script_list()

    def add_ahk_to_startup(self, script_name):
        """Create a shortcut to the AHK script in the startup folder."""
        # Build the full script path using self.SCRIPT_DIR and script_name
        script_path = os.path.join(self.SCRIPT_DIR, script_name)
    
        # Get the Startup folder path
        startup_folder = winshell.startup()

        # Create a shortcut in the Startup folder
        shortcut_name = os.path.splitext(script_name)[0]  # Remove .ahk extension for shortcut name
        shortcut_path = os.path.join(startup_folder, f"{shortcut_name}.lnk")
    
        # Create the WScript.Shell object
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = script_path  # Path to the AHK script
        shortcut.WorkingDirectory = os.path.dirname(script_path)
        shortcut.IconLocation = script_path
        shortcut.save()

        # Release the COM object
        del shell

        # Refresh the script list to update the button states
        self.update_script_list()

        return shortcut_path

    def remove_ahk_from_startup(self, script_name):
        """Remove the shortcut to the AHK script from the startup folder."""
        # Build the full shortcut name by removing the .ahk extension
        shortcut_name = os.path.splitext(script_name)[0]  # Remove .ahk extension for shortcut name
    
        # Get the Startup folder path
        startup_folder = winshell.startup()
    
        # Build the full path of the shortcut
        shortcut_path = os.path.join(startup_folder, f"{shortcut_name}.lnk")

        try:
            # Remove the shortcut if it exists
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                print(f"Removed {shortcut_path} from startup.")
            else:
                print(f"{shortcut_path} does not exist in startup.")

            # Refresh the script list to update the button states
            self.update_script_list()

        except Exception as e:
            print(f"Error removing {shortcut_path}: {e}")

    def toggle_script_dir(self):
        """Toggle between active_dir and store_dir, update the button text, and refresh the script list."""
        # Toggle between 'Active' and 'Store' directories
        if self.SCRIPT_DIR == active_dir:
            self.SCRIPT_DIR = store_dir
            self.show_stored.config(text="Show Active Profile")
        else:
            self.SCRIPT_DIR = active_dir
            self.show_stored.config(text="Show Stored Profile")

        # Refresh the script list based on the new SCRIPT_DIR
        self.list_scripts()
        self.update_script_list()

    def activate_script(self, script_name, run_button, exit_button):
        """Activate the given .ahk script by double-clicking it."""
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):
            # Start the script
            os.startfile(script_path)

            # Update button states based on script status
            if self.is_script_running(script_name):
                run_button.config(state='disabled')
                exit_button.config(state='normal')
            else:
                run_button.config(state='normal')
                exit_button.config(state='disabled')
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def exit_script(self, script_name, run_button, exit_button):
        """Exit the given .ahk script by sending the exit key combination (Ctrl+Alt+P)."""
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):
            # Simulate pressing Ctrl+Alt+P to exit the AHK script
            keyboard = Controller()

            # Press and release Ctrl+Alt+P
            keyboard.press(Key.ctrl)
            keyboard.press(Key.alt)
            keyboard.press('p')
            keyboard.release('p')
            keyboard.release(Key.alt)
            keyboard.release(Key.ctrl)

            # Update button states after exiting the script
            if not self.is_script_running(script_name):
                run_button.config(state='normal')
                exit_button.config(state='disabled')
            else:
                run_button.config(state='disabled')
                exit_button.config(state='normal')
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def delete_script(self, script_name):
        """Delete the given .ahk script file."""
        script_path = os.path.join(self.SCRIPT_DIR, script_name)
        
        if os.path.isfile(script_path):
            try:
                os.remove(script_path)  # Delete the file

                self.scripts = self.list_scripts()  # Update the list of scripts
                self.update_script_list()  # Refresh the UI
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete the script: {e}")
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def store_script(self, script_name):
        """Move the given .ahk script file between Active and Store directories."""
        script_path = os.path.join(self.SCRIPT_DIR, script_name)  # Current script path
        
        # Determine the target directory based on the current SCRIPT_DIR
        if self.SCRIPT_DIR == active_dir:
            target_dir = store_dir  # Move to Store
        else:
            target_dir = active_dir  # Move back to Active

        target_path = os.path.join(target_dir, script_name)  # Destination path

        if os.path.isfile(script_path):
            try:
                # Move the file to the target directory
                shutil.move(script_path, target_path)

                self.scripts = self.list_scripts()  # Update the list of scripts
                self.update_script_list()  # Refresh the UI
            except Exception as e:
                messagebox.showerror("Error", f"Failed to move the script: {e}")
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def validate_input(entry_var):
        # Ensure that the entry always starts with 4 spaces
        current_value = entry_var.get()
        if not current_value.startswith("    "):  # Check if the text still starts with 4 spaces
            entry_var.set("    " + current_value.strip())  # Re-add the spaces if deleted
        return True

    def parse_device_info(self, file_path):
        devices = []
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()

            # Remove empty or whitespace-only lines
            lines = [line.strip() for line in lines if line.strip()]

            # Parse the lines into devices
            device_info = {}
            for line in lines:
                line = line.strip()
                if line.startswith("Device ID:"):
                    # When a new device is found, store the old one (if it exists)
                    if device_info:
                        if device_info.get('VID') and device_info.get('PID') and device_info.get('Handle'):
                            devices.append(device_info)  # Add only valid devices
                    device_info = {'Device ID': line.split(":")[1].strip()}
                elif line.startswith("VID:"):
                    device_info['VID'] = line.split(":")[1].strip()
                elif line.startswith("PID:"):
                    device_info['PID'] = line.split(":")[1].strip()
                elif line.startswith("Handle:"):
                    device_info['Handle'] = line.split(":")[1].strip()
                elif line.startswith("Is Mouse:"):
                    device_info['Is Mouse'] = line.split(":")[1].strip()

            # Add the last device if it's valid
            if device_info.get('VID') and device_info.get('PID') and device_info.get('Handle'):
                devices.append(device_info)

        except Exception as e:
            print(f"Error reading device info: {e}")

        return devices

    # Function to refresh the device list by re-reading the device file
    def refresh_device_list(self, file_path):
        os.startfile(device_finder_path)  # Use the device finder path
        time.sleep(1)  # Small delay to allow the AHK script to finish
        devices = self.parse_device_info(file_path)
        return devices

    # Function to update the Treeview widget with the device list
    def update_treeview(self, devices, tree):
        for item in tree.get_children():
            tree.delete(item)

        for device in devices:
            if device.get('VID') and device.get('PID') and device.get('Handle'):
                # Replace 'Is Mouse' with 'Mouse' or 'Keyboard'
                device_type = "Mouse" if device['Is Mouse'] == "Yes" else "Keyboard"
                tree.insert("", "end", values=(device_type, device['VID'], device['PID'], device['Handle']))

    # Function to handle the device selection
    def select_device(self, tree, entry, window):
        selected_item = tree.selection()
        if selected_item:
            device = tree.item(selected_item[0])['values']
            device_type = device[0]
            # If VID and PID are both 0x00, use the Handle instead
            if device[1] == "0x0000" and device[2] == "0x0000":
                vid_pid = device[3]  # Use Handle instead
            else:
                vid_pid = f"{device[1]}, {device[2]}"  # Normal VID and PID format

            entry.delete(0, tk.END)  # Clear the entry
            entry.insert(0, f"{device_type}, {vid_pid}")

            # Close the device selection window
            window.destroy()

    def open_device_selection(self):
        """Open a new window to select a device and update the Keyboard_entry field."""
        device_selection_window = tk.Toplevel(self.create_profile_window)
        device_selection_window.geometry("600x300+308+233")
        device_selection_window.title("Select Keyboard Device")
        device_selection_window.iconbitmap(icon_path)
        device_selection_window.transient(self.create_profile_window)

        tree = ttk.Treeview(device_selection_window, columns=("Device Type", "VID", "PID", "Handle"), show="headings")
        tree.heading("Device Type", text="Device Type")
        tree.heading("VID", text="VID")
        tree.heading("PID", text="PID")
        tree.heading("Handle", text="Handle")
        tree.pack(padx=10, pady=10)

        tree.column("Device Type", width=150)  # Set width and alignment
        tree.column("VID", width=100)
        tree.column("PID", width=100)
        tree.column("Handle", width=200)

        devices = self.refresh_device_list(device_list_path)  # Refresh device list
        self.update_treeview(devices, tree)

        # Button Frame
        button_frame = tk.Frame(device_selection_window)
        button_frame.pack(pady=5)

        # Select button
        select_button = tk.Button(button_frame, text="Select", width=23,
                                  command=lambda: self.select_device(tree, self.keyboard_entry,
                                                                     device_selection_window))
        select_button.grid(row=0, column=0, padx=5, pady=5)

        monitor_button = tk.Button(button_frame, text="Open AHI Monitor To Test Device", width=29, command=self.run_monitor)
        monitor_button.grid(row=0, column=2, padx=5, pady=5)

        refresh_button = tk.Button(button_frame, text="Refresh", width=23, command=lambda: self.update_treeview(
                self.refresh_device_list(device_list_path), tree))
        refresh_button.grid(row=0, column=1, padx=5, pady=5)

    def create_new_profile(self):
        """Create a new AutoHotkey script based on user input."""
        self.create_profile_window = tk.Toplevel(self.root)
        self.create_profile_window.geometry("600x450+308+130")  # Set initial size (width x height)
        self.create_profile_window.title("Create New Profile")
        self.create_profile_window.iconbitmap(icon_path)

        # Bind cleanup method to window close event
        self.create_profile_window.protocol("WM_DELETE_WINDOW", self.cleanup_listeners)

        # Set the window as a transient of the root
        self.create_profile_window.transient(self.root)

        script_name_var = tk.StringVar()

        # Input for script name
        self.script_name_label = tk.Label(self.create_profile_window, text="Profile Name    :")
        self.script_name_label.place(relx=0.13, rely=0.026)
        self.script_name_entry = tk.Entry(self.create_profile_window)
        self.script_name_entry.place(relx=0.31, rely=0.03, relwidth=0.557)
        self.script_name_entry.insert(0, "  ")

        self.keyboard_label = tk.Label(self.create_profile_window, text="Device ID           :")
        self.keyboard_label.place(relx=0.13, rely=0.1)
        self.keyboard_entry = tk.Entry(self.create_profile_window)
        self.keyboard_entry.place(relx=0.31, rely=0.104, relwidth=0.38)
        self.keyboard_entry.insert(0, "  ")
        self.keyboard_select_button = tk.Button(self.create_profile_window, text="Select Device", command=self.open_device_selection)
        self.keyboard_select_button.place(relx=0.71, rely=0.094, width=95)

        # Variable to track if in text mode or remap mode
        self.is_text_mode = False

        # Scrollable canvas for key mappings (initial remap mode)
        self.canvas = tk.Canvas(self.create_profile_window)
        self.canvas.place(relx=0.067, rely=0.178, relheight=0.678, relwidth=0.875)
        self.canvas.configure(borderwidth="2", relief="ridge")

        # Scrollbar for the canvas
        self.scrollbar = tk.Scrollbar(self.create_profile_window, orient="vertical", command=self.canvas.yview)
        self.scrollbar.place(relx=0.942, rely=0.178, relheight=0.678, width=20)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Frame inside the canvas to hold the key mapping entries
        self.key_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.key_frame, anchor='nw')

        # Enable mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Add initial key mapping row
        self.key_rows = []
        self.add_key_mapping_row()

        # Buttons
        self.finish_button = tk.Button(self.create_profile_window, text="Finish", command=self.finish_profile)
        self.finish_button.place(relx=0.070, rely=0.889, height=26, width=110)

        self.continue_button = tk.Button(self.create_profile_window, text="Add Remap Row",
                                         command=self.add_key_mapping_row)
        self.continue_button.place(relx=0.300, rely=0.889, height=26, width=110)

        self.shortcut_button = tk.Button(self.create_profile_window, text="Add Shortcut Row",
                                         command=self.add_shortcut_mapping_row)
        self.shortcut_button.place(relx=0.530, rely=0.889, height=26, width=110)

        self.text_button = tk.Button(self.create_profile_window, text="Text Mode", command=self.toggle_mode)
        self.text_button.place(relx=0.760, rely=0.889, height=26, width=110)

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def cleanup_listeners(self):
        """Stop all listeners and close the create profile window."""
        if self.is_listening:
            # Unhook keyboard listener
            if self.hook_registered:
                keyboard.unhook_all()
                self.hook_registered = False

            # Stop mouse listener
            if self.mouse_listener is not None:
                self.mouse_listener.stop()
                self.mouse_listener = None

            self.is_listening = False
            self.active_entry = None

        # Destroy the create profile window
        if self.create_profile_window:
            self.create_profile_window.destroy()

    def run_monitor(self):
        # Define the subdirectory path where the script is located
        script_path = os.path.join(script_dir, "_internal", "Data", "Active", "AutoHotkey Interception", "Monitor.ahk")
        # Ensure the file exists before attempting to run it
        if os.path.exists(script_path):
            os.startfile(script_path)  # Run the script using the default program associated with the file type
        else:
            print(f"Error: The script at {script_path} does not exist.")

    def _on_mousewheel(self, event):
        """Scroll the canvas with the mouse wheel, but stop scrolling at the top/bottom."""
        # Check if the canvas can scroll up or down
        can_scroll_down = self.canvas.yview()[1] < 1  # Check if we're not at the bottom
        can_scroll_up = self.canvas.yview()[0] > 0  # Check if we're not at the top

        if event.num == 5 or event.delta == -120:  # Scroll Down
            if can_scroll_down:  # Only scroll down if we're not at the bottom
                self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120:  # Scroll Up
            if can_scroll_up:  # Only scroll up if we're not at the top
                self.canvas.yview_scroll(-1, "units")

    def toggle_mode(self):
        """Toggle between Remap Mode and Text Mode."""
        if not self.is_text_mode:
            # Switch to Text Mode
            self.is_text_mode = True
            self.text_button.config(text="Default Mode")

            # Remove existing key mapping widgets
            for widget in self.key_frame.winfo_children():
                widget.destroy()

            self.key_rows = []
            self.add_shortcut_mapping_row()
            self.row_num += 1

            # Add a text block for user input, only if it doesn't already exist
            if not hasattr(self, 'text_block'):
                self.text_block = tk.Text(self.key_frame, wrap='word', height=14, width=70, font=("Consolas", 10))
                self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
                self.text_block.bind("<KeyRelease>", self.update_text_block_height)

            # Disable the add row button in Text Mode
            self.continue_button.config(state='disabled')

            # Update the layout after adding the text block
            self.key_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

        else:
            # Switch to Remap Mode
            self.is_text_mode = False
            self.text_button.config(text="Text Mode")

            # Remove text block if it exists
            if hasattr(self, 'text_block'):
                self.text_block.grid_forget()  # Temporarily remove the text block to adjust rows
                del self.text_block  # Remove the text block from the object

            for widget in self.key_frame.winfo_children():
                widget.destroy()

            self.key_rows = []
            self.add_key_mapping_row()

            # Enable the add row button in Remap Mode
            self.continue_button.config(state='normal')

    def update_text_block_height(self, event=None):
        """Adjust the height of the text block based on the number of lines."""
        if hasattr(self, 'text_block'):
            # Get the current number of lines in the text block
            line_count = int(self.text_block.index('end-1c').split('.')[0])

            # Calculate the new height (minimum height of 4)
            min_height = 14
            new_height = max(min_height, line_count)  # Ensure the height is at least `min_height`

            # Update the height of the Text widget
            self.text_block.config(height=new_height)

            # Recalculate the canvas scroll region
            self.key_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def add_shortcut_mapping_row(self):
        """Add a new row for shortcut mapping input."""
        """Add a new row for shortcut mapping input."""
        # Check if text_block exists, and create it if necessary
        if self.is_text_mode and (not hasattr(self, 'text_block') or not self.text_block.winfo_exists()):
            # If text_block doesn't exist, create it
            self.text_block = tk.Text(self.key_frame, wrap='word', height=14, width=70, font=("Consolas", 10))
            self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
            self.row_num += 1  # Increment row_num to account for the new text block

        # Move existing widgets down if in Text Mode to ensure new rows are above the text block
        if self.is_text_mode and hasattr(self, 'text_block'):
            self.text_block.grid_forget()  # Temporarily remove the text block to adjust rows
            self.row_num -= 1  # Adjust row number to place new rows above the text block

        # Add label for shortcut key
        shortcut_label = tk.Label(self.key_frame, text="Shortcut Key:", justify='center')
        shortcut_label.grid(row=self.row_num, rowspan=2, column=0, columnspan=2, padx=20, pady=6, sticky="w")

        # Create a placeholder for the button command
        def shortcut_key_command():
            self.toggle_shortcut_key_listening(shortcut_entry, shortcut_key_select)

        # Initialize the button first, then assign the command
        shortcut_key_select = tk.Button(self.key_frame, text="Select Shortcut Key", justify='center', width=38)
        shortcut_key_select.config(command=shortcut_key_command)
        shortcut_key_select.grid(row=self.row_num, column=1, columnspan=3, padx=20, pady=5, sticky="w")

        # Check if the button should be disabled
        if self.is_listening:
            shortcut_key_select.config(state=tk.DISABLED)

        self.row_num += 1

        key_values = self.load_key_values()

        # Add an entry field for the shortcut key
        shortcut_entry = ttk.Combobox(self.key_frame, width=45, justify='center')
        shortcut_entry.grid(row=self.row_num, column=1, columnspan=3, padx=20, pady=6, sticky="w")
        shortcut_entry['values'] = key_values  # Populate combobox with the values

        self.row_num += 1


        # Save reference for later
        self.shortcut_rows.append((shortcut_entry, shortcut_key_select))

        self.row_num += 1

        # Add a separator line below the entry row
        separator = tk.Frame(self.key_frame, height=1, bg="gray")
        separator.grid(row=self.row_num, column=0, columnspan=4, sticky="we", padx=2, pady=3)

        self.row_num += 1

        # If in Text Mode, re-add the text block below the shortcut rows
        if self.is_text_mode and hasattr(self, 'text_block'):
            self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
            self.row_num += 1  # Update row_num to account for the text block

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def load_key_values(self):
        """Load key values from key_list.txt, only taking the first part before the comma."""
        key_values = []
        try:
            with open(keylist_path, 'r') as file:
                for line in file:
                    # Skip empty lines and comment lines (optional)
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Split by comma and take the first part
                        key = line.split(",")[0].strip()
                        key_values.append(key)
        except Exception as e:
            print(f"Error reading key_list.txt: {e}")
        return key_values

    def add_key_mapping_row(self):
        """Add a new row with buttons and entry fields for key mapping."""

        select_default_key_label = tk.Label(self.key_frame, text="Default Key:")
        select_default_key_label.grid(row=self.row_num, rowspan=2, column=0, padx=10, pady=6)

        select_remap_key_label = tk.Label(self.key_frame, text="Remap Key:")
        select_remap_key_label.grid(row=self.row_num, rowspan=2, column=2, padx=10, pady=6)

        # Placeholder functions for buttons, to be updated after the buttons are initialized
        def default_key_command():
            self.toggle_shortcut_key_listening(original_key_entry, original_key_select)

        def remap_key_command():
            self.toggle_shortcut_key_listening(remap_key_entry, remap_key_select)

        # Create buttons
        original_key_select = tk.Button(self.key_frame, text="Select Default Key", justify='center', width=16,
                                        command=default_key_command)
        original_key_select.grid(row=self.row_num, column=1, columnspan=2, sticky='w', padx=13, pady=5)

        remap_key_select = tk.Button(self.key_frame, text="Select Remap Key", width=16, justify='center',
                                     command=remap_key_command)
        remap_key_select.grid(row=self.row_num, column=3, columnspan=2, sticky='w', padx=13, pady=5)

        # Check if buttons should be disabled
        if self.is_listening:
            original_key_select.config(state=tk.DISABLED)
            remap_key_select.config(state=tk.DISABLED)

        self.row_num += 1

        # Load the key values from key_list.txt
        key_values = self.load_key_values()

        # Create combobox for selecting the default key
        original_key_entry = ttk.Combobox(self.key_frame, width=20, justify='center')
        original_key_entry.grid(row=self.row_num, column=1, sticky='w', padx=13, pady=6)
        self.original_key_entry = original_key_entry  # Save reference for later use
        original_key_entry['values'] = key_values  # Populate combobox with the values

        # Create combobox for selecting the remap key
        remap_key_entry = ttk.Combobox(self.key_frame, width=20, justify='center')
        remap_key_entry.grid(row=self.row_num, column=3, sticky='w', padx=13, pady=6)
        self.remap_key_entry = remap_key_entry  # Save reference for later use
        remap_key_entry['values'] = key_values  # Populate combobox with the values

        # Save button references for managing their states later
        self.key_rows.append((original_key_entry, remap_key_entry, original_key_select, remap_key_select))

        self.row_num += 1

        separator = tk.Frame(self.key_frame, height=1, bg="gray")
        separator.grid(row=self.row_num, column=0, columnspan=4, sticky="we", padx=0, pady=3)

        self.row_num += 1

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def toggle_shortcut_key_listening(self, entry_widget, button):
        """Toggle the shortcut key and mouse listener on and off."""

        def toggle_other_buttons(state):
            # Disable/Enable all buttons except the active one
            for key_row in self.key_rows:
                # Unpack based on the known structure of key_rows
                orig_entry, remap_entry, orig_button, remap_button = key_row
                if orig_button != button and orig_button.winfo_exists():  # Check if the button exists
                    orig_button.config(state=state)
                if remap_button != button and remap_button.winfo_exists():  # Check if the button exists
                    remap_button.config(state=state)

            # Disable/Enable all shortcut buttons as well
            for shortcut_entry, shortcut_button in self.shortcut_rows:
                if shortcut_button != button and shortcut_button.winfo_exists():  # Check if the button exists
                    shortcut_button.config(state=state)

        if not self.is_listening:
            # Start listening
            self.is_listening = True
            self.active_entry = entry_widget

            # Disable user input by binding an empty function to all entries
            self.disable_entry_input(self.key_rows)  # Disable both original and remap entries
            self.disable_entry_input([(self.script_name_entry, None)])  # Disable script name entry
            self.disable_entry_input([(self.shortcut_entry, None)])  # Enable script name entry
            self.disable_entry_input([(self.keyboard_entry, None)])  # Enable script name entry

            # Set the ignore flag to true when starting the listening
            self.ignore_next_click = True  # Ignore the first left-click

            # Disable other buttons
            toggle_other_buttons(tk.DISABLED)

            # Change button text
            button.config(text="Save Selected Key",
                          command=lambda: self.toggle_shortcut_key_listening(entry_widget, button))

            # Start keyboard listener if not already hooked
            if not self.hook_registered:
                keyboard.hook(self.on_shortcut_key_event)
                self.hook_registered = True

            # Start mouse listener if not already running
            if self.mouse_listener is None:
                self.mouse_listener = mouse.Listener(on_click=self.on_shortcut_mouse_event)
                self.mouse_listener.start()

        else:
            # Stop listening
            self.is_listening = False
            self.active_entry = None

            # Unbind the empty function to allow typing again
            self.enable_entry_input(self.key_rows)  # Enable both original and remap entries
            self.enable_entry_input([(self.script_name_entry, None)])  # Enable script name entry
            self.enable_entry_input([(self.shortcut_entry, None)])  # Enable script name entry
            self.enable_entry_input([(self.keyboard_entry, None)])  # Enable script name entry

            # Enable all buttons
            toggle_other_buttons(tk.NORMAL)

            # Reset button text
            button.config(text="Select Shortcut Key",
                          command=lambda: self.toggle_shortcut_key_listening(entry_widget, button))

            # Unhook keyboard listener
            if self.hook_registered:
                keyboard.unhook_all()  # Unhook all keyboard hooks
                self.hook_registered = False

            # Stop mouse listener
            if self.mouse_listener is not None:
                self.mouse_listener.stop()
                self.mouse_listener = None

            print("Shortcut key and mouse listening stopped.")

    def disable_entry_input(self, key_rows):
        """Disable user input for all entries without changing the background color."""

        if self.script_name_entry and self.script_name_entry.winfo_exists():
            self.script_name_entry.bind("<Key>", lambda e: "break")  # Prevent keyboard input for script name

        if self.original_key_entry and self.original_key_entry.winfo_exists():
            self.original_key_entry.bind("<Key>", lambda e: "break")  # Prevent keyboard input for original key

        if self.remap_key_entry and self.remap_key_entry.winfo_exists():
            self.remap_key_entry.bind("<Key>", lambda e: "break")  # Prevent keyboard input for remap key

        # Bind other shortcut entries
        for shortcut_entry in key_rows:
            # Each shortcut_entry is a tuple, so we need to access the individual entries
            for entry in shortcut_entry:
                if entry and entry.winfo_exists():
                    entry.bind("<Key>", lambda e: "break")  # Prevent keyboard input

    def enable_entry_input(self, key_rows):
        """Re-enable user input for all entries."""

        if self.script_name_entry and self.script_name_entry.winfo_exists():
            self.script_name_entry.unbind("<Key>")  # Allow keyboard input again for script name

        if self.original_key_entry and self.original_key_entry.winfo_exists():
            self.original_key_entry.unbind("<Key>")  # Allow keyboard input again for original key

        if self.remap_key_entry and self.remap_key_entry.winfo_exists():
            self.remap_key_entry.unbind("<Key>")  # Allow keyboard input again for remap key

        # Unbind other shortcut entries
        for shortcut_entry in key_rows:
            for entry in shortcut_entry:
                if entry and entry.winfo_exists():
                    entry.unbind("<Key>")  # Allow keyboard input again

    def on_key_event(self, event):
        """Handle key press and insert key into the active entry."""
        if self.is_listening and self.active_entry and event.event_type == 'down':
            key_pressed = event.name
            self.active_entry.delete(0, tk.END)  # Clear the current entry field
            self.active_entry.insert(0, key_pressed)  # Insert the pressed key

    def on_mouse_event(self, x, y, button, pressed):
        """Handle mouse click events and insert the mouse button pressed into the active entry."""
        if self.is_listening and self.active_entry:
            # Check if we need to ignore the left-click
            if self.ignore_next_click and button == mouse.Button.left and pressed:
                self.ignore_next_click = False
                return  # Skip processing the left-click immediately

            if pressed:
                if button == mouse.Button.left:
                    mouse_button = "Left Click"
                elif button == mouse.Button.right:
                    mouse_button = "Right Click"
                elif button == mouse.Button.middle:
                    mouse_button = "Middle Click"

                # Update the active entry with the clicked button name
                self.active_entry.delete(0, tk.END)  # Clear the current entry field
                self.active_entry.insert(0, mouse_button)  # Insert the clicked button name

    def handle_shortcut_key_event(self, event):
        """Handle the key event from the listener."""
        if self.is_listening and self.active_entry is not None:
            # Temporarily set the entry to normal state so we can insert text
            self.active_entry.config(state='normal')  # Ensure it is in 'normal' state

            # Insert the key press into the entry widget
            self.active_entry.insert(tk.END, event.name)  # Insert the key event

            # Optionally change the appearance to make it look "disabled"

            # Re-disable it visually (but still allow programmatic input)
            self.active_entry.config(state='normal')  # Keep the entry active for programmatic input

    def on_shortcut_key_event(self, event):
        """Handle keyboard shortcut key press and insert into the active entry."""
        if self.is_listening and self.active_entry:
            current_time = time.time()
            key = event.name

            if event.event_type == 'down':
                # Reset the sequence if time exceeds the timeout
                if current_time - self.last_key_time > self.timeout:
                    self.pressed_keys = []

                # Add the key and update entry
                if key not in self.pressed_keys:  # Avoid duplicates in the sequence
                    self.pressed_keys.append(key)
                    self.update_entry()

                # Update the last key time
                self.last_key_time = current_time

    def on_shortcut_mouse_event(self, x, y, button, pressed):
        """Handle mouse click event as part of the shortcut sequence."""
        if self.is_listening and self.active_entry and pressed:  # Only handle the "pressed" state
            # Check the ignore flag for left-click
            if self.ignore_next_click and button == mouse.Button.left:
                self.ignore_next_click = False  # Reset the flag immediately after ignoring the click
                return  # Skip processing this left-click immediately

            # Now process the left-click if not ignored
            if button == mouse.Button.left:
                mouse_button = "Left Click"
            elif button == mouse.Button.right:
                mouse_button = "Right Click"
            elif button == mouse.Button.middle:
                mouse_button = "Middle Click"
            else:
                mouse_button = button.name  # Default to the button's name if not standard

            current_time = time.time()

            # Reset the sequence if time exceeds the timeout
            if current_time - self.last_key_time > self.timeout:
                self.pressed_keys = []

            # Add the mouse button and update entry
            if mouse_button not in self.pressed_keys:  # Avoid duplicates in the sequence
                self.pressed_keys.append(mouse_button)
                self.update_entry()

            # Update the last key time
            self.last_key_time = current_time

    def update_entry(self):
        """Update the entry field with the current combination of keys and mouse buttons."""
        shortcut_combination = '+'.join(self.pressed_keys)  # Join the keys and buttons into a string
        self.active_entry.config(state='normal')  # Ensure it's in 'normal' state for update
        self.active_entry.delete(0, tk.END)  # Clear the current entry field
        self.active_entry.insert(0, shortcut_combination)  # Insert the combined keys and mouse buttons

    def load_key_translations(self):
        """Load key translations from the key_list.txt file."""
        key_translations = {}
        try:
            # Read the key translation file
            with open(keylist_path, 'r') as file:
                for line in file:
                    parts = line.strip().split(',')
                    if len(parts) == 2:
                        key_translations[parts[0].strip().lower()] = parts[1].strip()
        except FileNotFoundError:
            print(f"Error: '{keylist_path}' not found.")
        return key_translations

    def translate_key(self, key, key_translations):
        """Translate the key using the key translation dictionary, handling multiple keys."""
        keys = key.split('+')  # Split by the "+" symbol for multiple keys
        translated_keys = []

        for single_key in keys:
            translated_key = key_translations.get(single_key.strip().lower(), single_key.strip())
            translated_keys.append(translated_key)

        # Join the keys back together with " & " for AHK format
        return " & ".join(translated_keys)

    def finish_profile(self):
        """Create the .ahk script file based on the selected mode."""
        script_name = self.script_name_entry.get().strip()
        if not script_name:
            messagebox.showwarning("Input Error", "Please enter a Profile name.")
            return

        if not script_name.endswith('.ahk'):
            script_name += '.ahk'
        output_path = os.path.join(self.SCRIPT_DIR, script_name)

        # Load key translations
        key_translations = self.load_key_translations()

        try:
            with open(output_path, 'w') as file:
                # First line based on mode (Text or Default)
                if self.is_text_mode:
                    file.write("; text\n")  # Only "text" in the first line for text mode
                else:
                    file.write("; default\n")  # Only "default" in the first line for default mode

                file.write("^!p::ExitApp \n\n")

                # ** HANDLE KEYBOARD ENTRY LOGIC **
                keyboard_entry = self.keyboard_entry.get().strip()  # Get the value from keyboard_entry

                if keyboard_entry:
                    # Split by the first comma (to separate device type from vid/pid/handle)
                    parts = keyboard_entry.split(",", 1)  # This splits the string into two parts, handling extra commas
                    device_type = parts[0].strip()  # Device type (e.g., "Keyboard")
                    vid_pid_or_handle = parts[1].strip()  # The rest (vid and pid or handle)

                    # Handle the case for vid/pid and write to file
                    if device_type.lower() == "mouse":
                        is_mouse = True
                    elif device_type.lower() == "keyboard":
                        is_mouse = False
                    else:
                        raise ValueError(f"Unknown device type: {device_type}")

                    # Check if vid_pid_or_handle starts with "0x", indicating it's in the vid, pid format
                    if vid_pid_or_handle.startswith("0x"):
                        # vid and pid format (starts with 0x), split by the comma separating vid and pid
                        vid_pid = vid_pid_or_handle.split(",")
                        vid = vid_pid[0].strip()  # First part: vid
                        pid = vid_pid[1].strip()  # Second part: pid

                        # Writing vid and pid logic
                        file.write(f"""#SingleInstance force
Persistent
#include AutoHotkey Interception\Lib\AutoHotInterception.ahk

AHI := AutoHotInterception()
id1 := AHI.GetDeviceId({str(is_mouse).lower()}, {vid}, {pid})
cm1 := AHI.CreateContextManager(id1)

#HotIf cm1.IsActive
""")
                    else:
                        # handle format (does not start with 0x, assuming handle format)
                        file.write(f"""#SingleInstance force
Persistent
#include AutoHotkey Interception\Lib\AutoHotInterception.ahk

AHI := AutoHotInterception()
id1 := AHI.GetDeviceIdFromHandle({str(is_mouse).lower()}, "{vid_pid_or_handle}")
cm1 := AHI.CreateContextManager(id1)

#HotIf cm1.IsActive
""")

                    # Now handle the shortcut and text logic based on mode
                    if self.is_text_mode:
                        # If in text mode, handle the text logic
                        if not any(
                                self.is_widget_valid(shortcut_row) and shortcut_row[0].get().strip() for shortcut_row in
                                self.shortcut_rows):
                            # No toggle, just write the text
                            text_content = self.text_block.get("1.0", 'end').strip()  # Get text block content
                            if text_content:
                                file.write(text_content + '\n')  # Write text content directly
                        else:
                            # Add toggle functionality if shortcuts exist
                            file.write("toggle := false\n\n")

                            # Write the toggle shortcut if defined
                            for shortcut_row in self.shortcut_rows:
                                if self.is_widget_valid(shortcut_row):
                                    try:
                                        shortcut_entry, _ = shortcut_row  # Unpack the tuple to get the entry widget
                                        shortcut_key = shortcut_entry.get().strip()  # Now call .get() on shortcut_entry
                                        if shortcut_key:
                                            translated_key = self.translate_key(shortcut_key, key_translations)
                                            if "&" in translated_key:  # Combined key like 'a & q'
                                                file.write(
                                                    f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")  # Toggle on a & q
                                            else:
                                                file.write(
                                                    f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                                    except TclError:
                                        continue  # Ignore invalid widget errors if the widget doesn't exist

                            # Now we are in the toggle section
                            file.write("#HotIf toggle\n")

                            # Add the text content from the text block inside the toggle
                            text_content = self.text_block.get("1.0", 'end').strip()  # Get text block content
                            if text_content:
                                for line in text_content.splitlines():
                                    file.write(line + '\n')  # Write each line of the text block

                            file.write("#HotIf")
                    else:
                        # Default mode for key remaps
                        if not any(
                                self.is_widget_valid(shortcut_row) and shortcut_row[0].get().strip() for shortcut_row in
                                self.shortcut_rows):
                            # Write key remaps directly without toggle section
                            for row in self.key_rows:
                                if len(row) == 4:  # Ensure the row has 4 elements (original_key_entry, remap_key_entry, original_key_select, remap_key_select)
                                    original_key_entry, remap_key_entry, original_key_select, remap_key_select = row
                                    try:
                                        original_key = original_key_entry.get().strip()  # Get the original key
                                        remap_key = remap_key_entry.get().strip()  # Get the remap key

                                        if original_key and remap_key:
                                            # Translate the keys
                                            original_key = self.translate_key(original_key, key_translations)
                                            remap_key = self.translate_key(remap_key, key_translations)

                                            # Handle combined keys by adding a "~" prefix
                                            if "&" in original_key:
                                                file.write(f"~{original_key}::{remap_key}\n")
                                            else:
                                                file.write(f"{original_key}::{remap_key}\n")
                                    except TclError:
                                        continue  # Skip invalid widget errors
                        else:
                            # If shortcut rows exist, create the toggle functionality
                            file.write("toggle := false\n\n")

                            # Write the toggle shortcut if defined
                            for shortcut_row in self.shortcut_rows:
                                if self.is_widget_valid(shortcut_row):
                                    try:
                                        shortcut_entry, _ = shortcut_row  # Unpack the tuple to get the entry widget
                                        shortcut_key = shortcut_entry.get().strip()  # Now call .get() on shortcut_entry
                                        if shortcut_key:
                                            translated_key = self.translate_key(shortcut_key, key_translations)
                                            if "&" in translated_key:  # Combined key like 'a & q'
                                                file.write(
                                                    f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")  # Toggle on a & q
                                            else:
                                                file.write(
                                                    f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                                    except TclError:
                                        continue  # Ignore invalid widget errors if the widget doesn't exist

                            # Write the remap keys conditionally (only active when toggle is true)
                            file.write("#HotIf toggle\n")
                            for row in self.key_rows:
                                if len(row) == 4:  # Ensure the row has 4 elements (original_key_entry, remap_key_entry, original_key_select, remap_key_select)
                                    original_key_entry, remap_key_entry, original_key_select, remap_key_select = row
                                    try:
                                        original_key = original_key_entry.get().strip()  # Get the original key
                                        remap_key = remap_key_entry.get().strip()  # Get the remap key

                                        if original_key and remap_key:
                                            # Translate the keys
                                            original_key = self.translate_key(original_key, key_translations)
                                            remap_key = self.translate_key(remap_key, key_translations)

                                            # Handle combined keys by adding a "~" prefix
                                            if "&" in original_key:
                                                file.write(f"~{original_key}::{remap_key}\n")
                                            else:
                                                file.write(f"{original_key}::{remap_key}\n")
                                    except TclError:
                                        continue  # Skip invalid widget errors
                            file.write("#HotIf\n")
                    file.write("\n#HotIf")
                else:
                    # If keyboard_entry is not filled, proceed with the shortcut logic as before
                    if self.is_text_mode:
                        # Handle text mode logic when no keyboard entry is filled
                        if not any(
                                self.is_widget_valid(shortcut_row) and shortcut_row[0].get().strip() for shortcut_row in
                                self.shortcut_rows):
                            text_content = self.text_block.get("1.0", 'end').strip()  # Get text content from text block
                            if text_content:
                                file.write(text_content + '\n')  # Write text content
                        else:
                            file.write("toggle := false\n\n")

                            for shortcut_row in self.shortcut_rows:
                                if self.is_widget_valid(shortcut_row):
                                    try:
                                        shortcut_entry, _ = shortcut_row  # Unpack the tuple to get the entry widget
                                        shortcut_key = shortcut_entry.get().strip()  # Now call .get() on shortcut_entry
                                        if shortcut_key:
                                            translated_key = self.translate_key(shortcut_key, key_translations)
                                            if "&" in translated_key:
                                                file.write(
                                                    f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                                            else:
                                                file.write(
                                                    f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                                    except TclError:
                                        continue

                            file.write("#HotIf toggle\n")
                            text_content = self.text_block.get("1.0", 'end').strip()
                            if text_content:
                                for line in text_content.splitlines():
                                    file.write(line + '\n')

                            file.write("#HotIf")
                    else:
                        # Default mode when no keyboard entry is filled
                        if not any(
                                self.is_widget_valid(shortcut_row) and shortcut_row[0].get().strip() for shortcut_row in
                                self.shortcut_rows):

                            for row in self.key_rows:
                                if len(row) == 4:  # Ensure the row has 4 elements (original_key_entry, remap_key_entry, original_key_select, remap_key_select)
                                    original_key_entry, remap_key_entry, original_key_select, remap_key_select = row
                                    try:
                                        original_key = original_key_entry.get().strip()  # Get the original key
                                        remap_key = remap_key_entry.get().strip()  # Get the remap key

                                        if original_key and remap_key:
                                            # Translate the keys
                                            original_key = self.translate_key(original_key, key_translations)
                                            remap_key = self.translate_key(remap_key, key_translations)

                                            # Handle combined keys by adding a "~" prefix
                                            if "&" in original_key:
                                                file.write(f"~{original_key}::{remap_key}\n")
                                            else:
                                                file.write(f"{original_key}::{remap_key}\n")
                                    except TclError:
                                        continue  # Skip invalid widget errors
                        else:
                            file.write("toggle := false\n\n")

                            for shortcut_row in self.shortcut_rows:
                                if self.is_widget_valid(shortcut_row):
                                    try:
                                        shortcut_entry, _ = shortcut_row  # Unpack the tuple to get the entry widget
                                        shortcut_key = shortcut_entry.get().strip()  # Now call .get() on shortcut_entry
                                        if shortcut_key:
                                            translated_key = self.translate_key(shortcut_key, key_translations)
                                            if "&" in translated_key:
                                                file.write(
                                                    f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                                            else:
                                                file.write(
                                                    f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                                    except TclError:
                                        continue

                            file.write("#HotIf toggle\n")
                            for row in self.key_rows:
                                if len(row) == 4:  # Ensure the row has 4 elements (original_key_entry, remap_key_entry, original_key_select, remap_key_select)
                                    original_key_entry, remap_key_entry, original_key_select, remap_key_select = row
                                    try:
                                        original_key = original_key_entry.get().strip()  # Get the original key
                                        remap_key = remap_key_entry.get().strip()  # Get the remap key

                                        if original_key and remap_key:
                                            # Translate the keys
                                            original_key = self.translate_key(original_key, key_translations)
                                            remap_key = self.translate_key(remap_key, key_translations)

                                            # Handle combined keys by adding a "~" prefix
                                            if "&" in original_key:
                                                file.write(f"~{original_key}::{remap_key}\n")
                                            else:
                                                file.write(f"{original_key}::{remap_key}\n")
                                    except TclError:
                                        continue  # Skip invalid widget errors
                            file.write("#HotIf")

                # Finalize and update script list
                self.scripts = self.list_scripts()
                self.update_script_list()
                self.create_profile_window.destroy()

        except Exception as e:
            print(f"Error writing script: {e}")

    # Helper function to check if widget exists
    def is_widget_valid(self, widget_tuple):
        try:
            # Check if both widgets (entry and button) in the tuple exist
            entry_widget, button_widget = widget_tuple
            return entry_widget.winfo_exists() and button_widget.winfo_exists()
        except TclError:
            # If either widget no longer exists, return False
            return False

    def update_edit_text_block_height(self, event=None):
        """Adjust the height of the text block based on the number of lines."""
        if hasattr(self, 'text_block'):
            # Get the current number of lines in the text block
            line_count = int(self.text_block.index('end-1c').split('.')[0])

            # Calculate the new height (minimum height of 4)
            min_height = 19
            new_height = max(min_height, line_count)  # Ensure the height is at least `min_height`

            # Update the height of the Text widget
            self.text_block.config(height=new_height)

            # Recalculate the canvas scroll region
            self.edit_frame.update_idletasks()
            self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))

    def edit_open_device_selection(self):
        """Open a new window to select a device and update the Keyboard_entry field."""
        device_selection_window = tk.Toplevel(self.edit_window)
        device_selection_window.geometry("600x300+308+233")
        device_selection_window.title("Select Keyboard Device")
        device_selection_window.iconbitmap(icon_path)
        device_selection_window.transient(self.edit_window)

        tree = ttk.Treeview(device_selection_window, columns=("Device Type", "VID", "PID", "Handle"), show="headings")
        tree.heading("Device Type", text="Device Type")
        tree.heading("VID", text="VID")
        tree.heading("PID", text="PID")
        tree.heading("Handle", text="Handle")
        tree.pack(padx=10, pady=10)

        tree.column("Device Type", width=150)  # Set width and alignment
        tree.column("VID", width=100)
        tree.column("PID", width=100)
        tree.column("Handle", width=200)

        devices = self.refresh_device_list(device_list_path)  # Refresh device list
        self.update_treeview(devices, tree)

        # Button Frame
        button_frame = tk.Frame(device_selection_window)
        button_frame.pack(pady=5)

        # Select button
        select_button = tk.Button(button_frame, text="Select", width=23,
                                  command=lambda: self.select_device(tree, self.keyboard_entry,
                                                                     device_selection_window))
        select_button.grid(row=0, column=0, padx=5, pady=5)

        monitor_button = tk.Button(button_frame, text="Open AHI Monitor To Test Device", width=29, command=self.run_monitor)
        monitor_button.grid(row=0, column=2, padx=5, pady=5)

        refresh_button = tk.Button(button_frame, text="Refresh", width=23, command=lambda: self.update_treeview(
                self.refresh_device_list(device_list_path), tree))
        refresh_button.grid(row=0, column=1, padx=5, pady=5)

    def replace_raw_keys(self, key, key_map):
        """Replace raw key with readable key from the key map."""
        return key_map.get(key, key)  # If key not found in the map, return the key as is.

    def load_key_list(self):
        """Load key list from file into a dictionary."""
        key_map = {}
        try:
            with open(keylist_path, 'r') as f:
                for line in f:
                    # Each line should be in the format "key_name, raw_key"
                    parts = line.strip().split(', ')
                    if len(parts) == 2:
                        readable, raw = parts
                        key_map[raw] = readable
        except FileNotFoundError:
            print("Key list file not found.")
        return key_map

    def edit_script(self, script_name):
        """Open the given .ahk script in an editable UI for modifying key mappings."""
        self.is_text_mode = False  # Initialize is_text_mode to False

        script_path = os.path.join(self.SCRIPT_DIR, script_name)
        if os.path.isfile(script_path):
            # Read the existing script content
            with open(script_path, 'r') as file:
                lines = file.readlines()

            # Load the key list (mapping raw keys to human-readable names)
            key_map = self.load_key_list()

            # Determine the mode based on the first relevant line
            mode_line = lines[0].strip() if lines else "; default"  # Default to remap mode if empty

            # Create a new window for editing the script
            self.edit_window = tk.Toplevel(self.root)
            self.edit_window.geometry("600x450+308+130")
            self.edit_window.title("Edit Profile")
            self.edit_window.iconbitmap(icon_path)

            # Bind cleanup method to window close event
            self.edit_window.protocol("WM_DELETE_WINDOW", self.edit_cleanup_listeners)

            # Set the window as a transient of the root
            self.edit_window.transient(self.root)

            # Input for script name (read-only)
            script_name_label = tk.Label(self.edit_window, text="Profile Name    :")
            script_name_label.place(relx=0.13, rely=0.026)
            script_name_entry = tk.Entry(self.edit_window)
            script_name_without_extension = script_name.replace('.ahk', '')
            script_name_entry.insert(0, "  ")
            script_name_entry.insert(4, script_name_without_extension)  # Start after the 4 spaces
            script_name_entry.config(state='readonly')
            script_name_entry.place(relx=0.31, rely=0.03, relwidth=0.557)
            self.script_name_entry = script_name_entry

            keyboard_label = tk.Label(self.edit_window, text="Device ID           :")
            keyboard_label.place(relx=0.13, rely=0.1)

            # Create the keyboard_entry field
            keyboard_entry = tk.Entry(self.edit_window)
            keyboard_entry.place(relx=0.31, rely=0.104, relwidth=0.38)
            keyboard_entry.insert(0, "  ")
            self.keyboard_entry = keyboard_entry

            # Extract the keyboard ID from the script content
            device_id = None
            device_type = "Keyboard"  # Default to "Keyboard" unless determined otherwise

            for line in lines:
                if "AHI.GetDeviceId" in line or "AHI.GetDeviceIdFromHandle" in line:
                    # Extract the parameters from the GetDeviceId/Handle line
                    start = line.find("(") + 1
                    end = line.find(")")
                    params = line[start:end].split(",")

                    # Determine device type based on the first parameter
                    if "false" in params[0].strip():
                        device_type = "Keyboard"
                    elif "true" in params[0].strip():
                        device_type = "Mouse"

                    # Extract the remaining parameters and format them
                    device_id = ", ".join(param.strip().replace('"', '') for param in params)

                    # Replace the leading "false" or "true" with the device type
                    device_id = device_id.replace("false", device_type).replace("true", device_type)
                    break

            # If a device ID was found, insert it into the keyboard_entry
            if device_id:
                keyboard_entry.insert(4, device_id)

            # Add the "Select Device" button
            keyboard_select_button = tk.Button(self.edit_window, text="Select Device",
                                               command=self.edit_open_device_selection)
            keyboard_select_button.place(relx=0.71, rely=0.094, width=95)

            # Scrollable canvas for key mappings
            self.edit_canvas = tk.Canvas(self.edit_window)
            self.edit_canvas.place(relx=0.067, rely=0.178, relheight=0.678, relwidth=0.875)
            self.edit_canvas.configure(borderwidth="2", relief="ridge")

            # Scrollbar for the canvas
            scrollbar = tk.Scrollbar(self.edit_window, orient="vertical", command=self.edit_canvas.yview)
            scrollbar.place(relx=0.942, rely=0.178, relheight=0.678, width=20)
            self.edit_canvas.configure(yscrollcommand=scrollbar.set)

            # Frame inside the canvas to hold the key mapping entries
            self.edit_frame = tk.Frame(self.edit_canvas)
            self.edit_canvas.create_window((0, 0), window=self.edit_frame, anchor='nw')

            # Enable mouse wheel scrolling
            self.edit_canvas.bind_all("<MouseWheel>", self.edit_on_mousewheel)

            # Initialize key_rows and shortcut_rows based on mode
            self.key_rows = []
            self.shortcut_rows = []

            shortcuts = []
            remaps = []

            if mode_line == "; default":
                # Handle remap mode
                in_hotif_block = False  # Track if we are inside a #HotIf block

                for line in lines[3:]:  # Skip the header lines
                    if line.startswith("#HotIf"):
                        in_hotif_block = not in_hotif_block
                        continue

                    if "::" in line:
                        if "~" in line:
                            if in_hotif_block:  # Process remaps with shortcuts inside #HotIf blocks
                                original_key, remap_key = line.split("::")

                                # Process original key
                                original_key = self.replace_raw_keys(original_key.strip(), key_map)
                                original_key = original_key.replace("~", "")
                                original_key = original_key.replace(" & ", "+")

                                # Process remap key
                                remap_key = self.replace_raw_keys(remap_key.strip(), key_map)

                                remaps.append((original_key, remap_key))
                            else:  # Process shortcuts outside #HotIf blocks
                                shortcut = line.split("::")[0].strip()  # Get the part before "::"
                                shortcut = self.replace_raw_keys(shortcut, key_map)
                                shortcut = shortcut.replace("~", "")
                                shortcut = shortcut.replace(" & ", "+")  # Modify the separator for shortcuts
                                shortcuts.append(shortcut)
                        else:  # Handle normal remaps (without ~)
                            original_key, remap_key = line.split("::")

                            # Replace raw keys with readable names
                            original_key = self.replace_raw_keys(original_key.strip(), key_map)
                            remap_key = self.replace_raw_keys(remap_key.strip(), key_map)

                            remaps.append((original_key, remap_key))

            elif mode_line == "; text":
                # Handle text mode
                self.is_text_mode = True  # Set to True if it's text mode
                self.text_block = tk.Text(self.edit_frame, wrap='word', height=14, width=70, font=("Consolas", 10))
                self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
                self.text_block.bind("<KeyRelease>", self.update_edit_text_block_height)
                self.row_num += 1

                # Insert existing text content into the text block using the improved logic
                text_content = self.extract_and_filter_content(lines)  # Extract and clean the text block content

                self.text_block.insert('1.0', text_content.strip())
                self.update_edit_text_block_height()

                # Detect and handle shortcut lines (including toggle lines like "q & e::toggle := !toggle")
                for line in lines:
                    if "::" in line:
                        if "~" in line:
                            shortcut = line.split("::")[0].strip()  # Get the part before "::"
                            shortcut = self.replace_raw_keys(shortcut, key_map)

                            # Replace "&" with "+" for the shortcut
                            shortcut = shortcut.replace("~", "")
                            shortcut = shortcut.replace(" & ", "+")  # Modify the separator for shortcuts
                            shortcuts.append(shortcut)

            # Add remap rows to UI
            for original_key, remap_key in remaps:
                self.add_edit_mapping_row(original_key, remap_key)

            # Add shortcut rows to UI
            for shortcut in shortcuts:
                self.add_edit_shortcut_mapping_row(shortcut)

            # Add a button to add remap rows and shortcut rows
            if not self.is_text_mode:
                add_row_button = tk.Button(self.edit_window, text="Add Another Row", command=self.add_edit_mapping_row)
                add_row_button.place(relx=0.530, rely=0.889, height=26, width=110)

            shortcut_button = tk.Button(self.edit_window, text="Add Shortcut Row",
                                        command=self.add_edit_shortcut_mapping_row)
            shortcut_button.place(relx=0.760, rely=0.889, height=26, width=110)

            save_button = tk.Button(self.edit_window, text="Save Changes",
                                    command=lambda: self.save_changes(script_name))
            save_button.place(relx=0.070, rely=0.889, height=26, width=107)

            # Update the scrollable region of the canvas
            self.update_scroll_region()
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def edit_cleanup_listeners(self):
        """Stop all listeners and close the create profile window."""
        if self.is_listening:
            # Unhook keyboard listener
            if self.hook_registered:
                keyboard.unhook_all()
                self.hook_registered = False

            # Stop mouse listener
            if self.mouse_listener is not None:
                self.mouse_listener.stop()
                self.mouse_listener = None

            self.is_listening = False
            self.active_entry = None

        # Destroy the create profile window
        if self.edit_window:
            self.edit_window.destroy()

    def extract_and_filter_content(self, lines):
        """Extract lines based on #HotIf toggle and #HotIf cm1.IsActive."""
        toggle_lines = []  # Lines captured from #HotIf toggle until next #HotIf
        cm1_lines = []  # Lines captured from #HotIf cm1.IsActive until next #HotIf
        inside_hotif_toggle = False
        inside_hotif_cm1 = False  # To capture lines for #HotIf cm1.IsActive

        for line in lines:
            raw_line = line  # Keep the line unmodified for spacing purposes
            stripped_line = line.strip()

            # Skip lines starting with '^!p' or ';' (header or comment lines)
            if stripped_line.startswith('^!p') or stripped_line.startswith(';'):
                continue

            # First filter: Capture lines between #HotIf toggle and next #HotIf
            if '#HotIf toggle' in stripped_line:
                inside_hotif_toggle = True
                continue  # Skip the '#HotIf toggle' line itself

            if inside_hotif_toggle:
                # If we encounter another #HotIf, stop capturing for toggle
                if '#HotIf' in stripped_line:
                    inside_hotif_toggle = False
                    continue  # Skip the '#HotIf' line (end marker)

                # Otherwise, capture the original line inside #HotIf toggle
                toggle_lines.append(raw_line)

            # Second filter: Capture lines between #HotIf cm1.IsActive and next #HotIf
            if '#HotIf cm1.IsActive' in stripped_line:
                inside_hotif_cm1 = True
                continue  # Skip the '#HotIf cm1.IsActive' line itself

            if inside_hotif_cm1:
                # If we encounter another #HotIf, stop capturing for cm1.IsActive
                if '#HotIf' in stripped_line:
                    inside_hotif_cm1 = False
                    continue  # Skip the '#HotIf' line (end marker)

                # Otherwise, capture the original line inside #HotIf cm1.IsActive
                cm1_lines.append(raw_line)

        # After both filters, combine the lines based on available results
        if toggle_lines:
            print(f"Cleaned toggle lines: {toggle_lines}")
            result = ''.join(toggle_lines)  # Preserve original line breaks
        elif cm1_lines:
            print(f"Cleaned cm1 lines: {cm1_lines}")
            result = ''.join(cm1_lines)  # Preserve original line breaks
        else:
            # If no #HotIf toggle or #HotIf cm1.IsActive lines, return original lines with comments and ^!p removed
            cleaned_lines = [raw_line for raw_line in lines if
                             not raw_line.strip().startswith('^!p') and not raw_line.strip().startswith(';')]
            result = ''.join(cleaned_lines)  # Preserve original line breaks

        return result  # Return the result

    def edit_on_mousewheel(self, event):
        """Scroll the canvas with the mouse wheel, but stop scrolling at the top/bottom."""
        # Check if the canvas can scroll up or down
        can_scroll_down = self.edit_canvas.yview()[1] < 1  # Check if we're not at the bottom
        can_scroll_up = self.edit_canvas.yview()[0] > 0  # Check if we're not at the top

        if event.num == 5 or event.delta == -120:  # Scroll Down
            if can_scroll_down:  # Only scroll down if we're not at the bottom
                self.edit_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120:  # Scroll Up
            if can_scroll_up:  # Only scroll up if we're not at the top
                self.edit_canvas.yview_scroll(-1, "units")

    def add_edit_mapping_row(self, original_key='', remap_key=''):
        """Add a new row with buttons and entry fields for key mapping."""

        select_default_key_label = tk.Label(self.edit_frame, text="Default Key:")
        select_default_key_label.grid(row=self.row_num, rowspan=2, column=0, padx=10, pady=6)

        select_remap_key_label = tk.Label(self.edit_frame, text="Remap Key:")
        select_remap_key_label.grid(row=self.row_num, rowspan=2, column=2, padx=10, pady=6)

        original_key_select = tk.Button(self.edit_frame, text="Select Default Key", justify='center', width=16,
            command=lambda: self.toggle_shortcut_key_listening(original_key_entry, original_key_select))
        original_key_select.grid(row=self.row_num, column=1, columnspan=2, sticky='w', padx=13, pady=5)

        remap_key_select = tk.Button(self.edit_frame, text="Select Remap Key", width=16, justify='center',
            command=lambda: self.toggle_shortcut_key_listening(remap_key_entry, remap_key_select))
        remap_key_select.grid(row=self.row_num, column=3, columnspan=2, sticky='w', padx=13, pady=5)

        # Check if buttons should be disabled
        if self.is_listening:
            original_key_select.config(state=tk.DISABLED)
            remap_key_select.config(state=tk.DISABLED)

        self.row_num += 1

        key_values = self.load_key_values()

        # Create combobox for selecting the default key
        original_key_entry = ttk.Combobox(self.edit_frame, width=20, justify='center')
        original_key_entry.grid(row=self.row_num, column=1, sticky='w', padx=13, pady=6)
        self.original_key_entry = original_key_entry  # Save reference for later use
        original_key_entry['values'] = key_values  # Populate combobox with the values
        original_key_entry.insert(0, original_key)

        # Create combobox for selecting the remap key
        remap_key_entry = ttk.Combobox(self.edit_frame, width=20, justify='center')
        remap_key_entry.grid(row=self.row_num, column=3, sticky='w', padx=13, pady=6)
        self.remap_key_entry = remap_key_entry  # Save reference for later use
        remap_key_entry['values'] = key_values  # Populate combobox with the values
        remap_key_entry.insert(0, remap_key)

        # Save button references for managing their states later
        self.key_rows.append((original_key_entry, remap_key_entry, original_key_select, remap_key_select))

        self.row_num += 1

        separator = tk.Frame(self.edit_frame, height=1, bg="gray")
        separator.grid(row=self.row_num, column=0, columnspan=4, sticky="we", padx=0, pady=3)

        self.row_num += 1

        self.edit_frame.update_idletasks()
        self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))

    def add_edit_shortcut_mapping_row(self, shortcut=''):
        """Add a new row for shortcut mapping input."""
        # Check if text_block exists, and create it if necessary
        if self.is_text_mode and (not hasattr(self, 'text_block') or not self.text_block.winfo_exists()):
            # If text_block doesn't exist, create it
            self.text_block = tk.Text(self.edit_frame, wrap='word', height=14, width=70, font=("Consolas", 10))
            self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
            self.row_num += 1  # Increment row_num to account for the new text block

        # Move existing widgets down if in Text Mode to ensure new rows are above the text block
        if self.is_text_mode and hasattr(self, 'text_block'):
            self.text_block.grid_forget()  # Temporarily remove the text block to adjust rows
            self.row_num -= 1  # Adjust row number to place new rows above the text block

        # Add button for selecting the shortcut key
        shortcut_label = tk.Label(self.edit_frame, text="Shortcut Key:", justify='center')
        shortcut_label.grid(row=self.row_num, rowspan=2, column=0, columnspan=2, padx=20, pady=6, sticky="w")

        # Create a placeholder for the button command
        def shortcut_key_command():
            self.toggle_shortcut_key_listening(shortcut_entry, shortcut_key_select)

        shortcut_key_select = tk.Button(self.edit_frame, text="Select Shortcut Key", justify='center', width=38,
                                        command=lambda: self.toggle_shortcut_key_listening(shortcut_entry,
                                                                                           shortcut_key_select))
        shortcut_key_select.grid(row=self.row_num, column=1, columnspan=3, padx=20, pady=5, sticky="w")

        # Check if the button should be disabled
        if self.is_listening:
            shortcut_key_select.config(state=tk.DISABLED)

        # Move to the next row for entry widget
        self.row_num += 1

        # Add an entry field for the shortcut key
        key_values = self.load_key_values()

        # Add an entry field for the shortcut key
        shortcut_entry = ttk.Combobox(self.edit_frame, width=45, justify='center')
        shortcut_entry.grid(row=self.row_num, column=1, columnspan=3, padx=20, pady=6, sticky="w")
        shortcut_entry['values'] = key_values  # Populate combobox with the values
        shortcut_entry.insert(0, shortcut)
        self.shortcut_entry = shortcut_entry

        # Save reference for later
        self.shortcut_rows.append((shortcut_entry, shortcut_key_select))

        # Move to the next row for the separator
        self.row_num += 1

        # Add a separator line below the entry row
        separator = tk.Frame(self.edit_frame, height=1, bg="gray")
        separator.grid(row=self.row_num, column=0, columnspan=4, sticky="we", padx=2, pady=3)

        # Move to the next row after the separator
        self.row_num += 1

        # If in Text Mode, re-add the text block below the shortcut rows
        if self.is_text_mode and hasattr(self, 'text_block'):
            self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
            self.row_num += 1  # Update row_num to account for the text block

        # Update the scrollable region of the canvas
        self.edit_frame.update_idletasks()
        self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))

    def update_scroll_region(self):
        """Update the scroll region of the canvas to encompass all content."""
        self.edit_frame.update_idletasks()  # Update frame to get the correct size
        self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))  # Set the scroll region

    def save_changes(self, script_name):
        """Save the edited key mappings or text block back to the .ahk script file."""
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        key_translations = self.load_key_translations()

        with open(script_path, 'w') as file:
            # First line based on mode (Text or Default)
            if self.is_text_mode:
                file.write("; text\n")  # Only "text" in the first line for text mode
            else:
                file.write("; default\n")  # Only "default" in the first line for default mode

            # Common AutoHotkey Script header
            file.write("^!p::ExitApp \n\n")

            # ** HANDLE KEYBOARD ENTRY LOGIC **
            keyboard_entry = self.keyboard_entry.get().strip()  # Get the value from keyboard_entry

            if keyboard_entry:
                # Split by the first comma (to separate device type from vid/pid/handle)
                parts = keyboard_entry.split(",", 1)  # This splits the string into two parts, handling extra commas
                device_type = parts[0].strip()  # Device type (e.g., "Keyboard")
                vid_pid_or_handle = parts[1].strip()  # The rest (vid and pid or handle)

                # Handle the case for vid/pid and write to file
                if device_type.lower() == "mouse":
                    is_mouse = True
                elif device_type.lower() == "keyboard":
                    is_mouse = False
                else:
                    raise ValueError(f"Unknown device type: {device_type}")

                # Check if vid_pid_or_handle starts with "0x", indicating it's in the vid, pid format
                if vid_pid_or_handle.startswith("0x"):
                    # vid and pid format (starts with 0x), split by the comma separating vid and pid
                    vid_pid = vid_pid_or_handle.split(",")
                    vid = vid_pid[0].strip()  # First part: vid
                    pid = vid_pid[1].strip()  # Second part: pid

                    # Writing vid and pid logic
                    file.write(f"""#SingleInstance force
Persistent
#include AutoHotkey Interception\Lib\AutoHotInterception.ahk

AHI := AutoHotInterception()
id1 := AHI.GetDeviceId({str(is_mouse).lower()}, {vid}, {pid}) ; This is from keyboard_entry
cm1 := AHI.CreateContextManager(id1)

#HotIf cm1.IsActive
""")
                else:
                    # handle format (does not start with 0x, assuming handle format)
                    file.write(f"""#SingleInstance force
Persistent
#include AutoHotkey Interception\Lib\AutoHotInterception.ahk

AHI := AutoHotInterception()
id1 := AHI.GetDeviceIdFromHandle({str(is_mouse).lower()}, "{vid_pid_or_handle}")
cm1 := AHI.CreateContextManager(id1)

#HotIf cm1.IsActive
""")

                # Now handle the shortcut and text logic based on mode
                if self.is_text_mode:
                    # If in text mode, handle the text logic
                    if not any(
                            self.is_widget_valid(shortcut_row) and shortcut_row[0].get().strip() for shortcut_row in
                            self.shortcut_rows):
                        # No toggle, just write the text
                        text_content = self.text_block.get("1.0", 'end').strip()  # Get text block content
                        if text_content:
                            file.write(text_content + '\n')  # Write text content directly
                    else:
                        # Add toggle functionality if shortcuts exist
                        file.write("toggle := false\n\n")

                        # Write the toggle shortcut if defined
                        for shortcut_row in self.shortcut_rows:
                            if self.is_widget_valid(shortcut_row):
                                try:
                                    shortcut_entry, _ = shortcut_row  # Unpack the tuple to get the entry widget
                                    shortcut_key = shortcut_entry.get().strip()  # Now call .get() on shortcut_entry
                                    if shortcut_key:
                                        translated_key = self.translate_key(shortcut_key, key_translations)
                                        if "&" in translated_key:  # Combined key like 'a & q'
                                            file.write(
                                                f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")  # Toggle on a & q
                                        else:
                                            file.write(
                                                f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                                except TclError:
                                    continue  # Ignore invalid widget errors if the widget doesn't exist

                        # Now we are in the toggle section
                        file.write("#HotIf toggle\n")

                        # Add the text content from the text block inside the toggle
                        text_content = self.text_block.get("1.0", 'end').strip()  # Get text block content
                        if text_content:
                            for line in text_content.splitlines():
                                file.write(line + '\n')  # Write each line of the text block

                        file.write("#HotIf")
                else:
                    # Default mode for key remaps
                    if not any(
                            self.is_widget_valid(shortcut_row) and shortcut_row[0].get().strip() for shortcut_row in
                            self.shortcut_rows):
                        # Write key remaps directly without toggle section
                        for row in self.key_rows:
                            if len(row) == 4:  # Ensure the row has 4 elements (original_key_entry, remap_key_entry, original_key_select, remap_key_select)
                                original_key_entry, remap_key_entry, original_key_select, remap_key_select = row
                                try:
                                    original_key = original_key_entry.get().strip()  # Get the original key
                                    remap_key = remap_key_entry.get().strip()  # Get the remap key

                                    if original_key and remap_key:
                                        # Translate the keys
                                        original_key = self.translate_key(original_key, key_translations)
                                        remap_key = self.translate_key(remap_key, key_translations)

                                        # Handle combined keys by adding a "~" prefix
                                        if "&" in original_key:
                                            file.write(f"~{original_key}::{remap_key}\n")
                                        else:
                                            file.write(f"{original_key}::{remap_key}\n")
                                except TclError:
                                    continue  # Skip invalid widget errors

                    else:
                        # If shortcut rows exist, create the toggle functionality
                        file.write("toggle := false\n\n")

                        # Write the toggle shortcut if defined
                        for shortcut_row in self.shortcut_rows:
                            if self.is_widget_valid(shortcut_row):
                                try:
                                    shortcut_entry, _ = shortcut_row  # Unpack the tuple to get the entry widget
                                    shortcut_key = shortcut_entry.get().strip()  # Now call .get() on shortcut_entry
                                    if shortcut_key:
                                        translated_key = self.translate_key(shortcut_key, key_translations)
                                        if "&" in translated_key:  # Combined key like 'a & q'
                                            file.write(
                                                f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")  # Toggle on a & q
                                        else:
                                            file.write(
                                                f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                                except TclError:
                                    continue  # Ignore invalid widget errors if the widget doesn't exist

                        # Write the remap keys conditionally (only active when toggle is true)
                        file.write("#HotIf toggle\n")
                        for row in self.key_rows:
                            if len(row) == 4:  # Ensure the row has 4 elements (original_key_entry, remap_key_entry, original_key_select, remap_key_select)
                                original_key_entry, remap_key_entry, original_key_select, remap_key_select = row
                                try:
                                    original_key = original_key_entry.get().strip()  # Get the original key
                                    remap_key = remap_key_entry.get().strip()  # Get the remap key

                                    if original_key and remap_key:
                                        # Translate the keys
                                        original_key = self.translate_key(original_key, key_translations)
                                        remap_key = self.translate_key(remap_key, key_translations)

                                        # Handle combined keys by adding a "~" prefix
                                        if "&" in original_key:
                                            file.write(f"~{original_key}::{remap_key}\n")
                                        else:
                                            file.write(f"{original_key}::{remap_key}\n")
                                except TclError:
                                    continue  # Skip invalid widget errors
                        file.write("#HotIf\n")
                file.write("\n#HotIf")
            else:
                # If keyboard_entry is not filled, proceed with the shortcut logic as before
                if self.is_text_mode:
                    # Handle text mode logic when no keyboard entry is filled
                    if not any(
                            self.is_widget_valid(shortcut_row) and shortcut_row[0].get().strip() for shortcut_row in
                            self.shortcut_rows):
                        text_content = self.text_block.get("1.0", 'end').strip()  # Get text content from text block
                        if text_content:
                            file.write(text_content + '\n')  # Write text content
                    else:
                        file.write("toggle := false\n\n")

                        for shortcut_row in self.shortcut_rows:
                            if self.is_widget_valid(shortcut_row):
                                try:
                                    shortcut_entry, _ = shortcut_row  # Unpack the tuple to get the entry widget
                                    shortcut_key = shortcut_entry.get().strip()  # Now call .get() on shortcut_entry
                                    if shortcut_key:
                                        translated_key = self.translate_key(shortcut_key, key_translations)
                                        if "&" in translated_key:
                                            file.write(
                                                f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                                        else:
                                            file.write(
                                                f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                                except TclError:
                                    continue

                        file.write("#HotIf toggle\n")
                        text_content = self.text_block.get("1.0", 'end').strip()
                        if text_content:
                            for line in text_content.splitlines():
                                file.write(line + '\n')

                        file.write("#HotIf")
                else:
                    # Default mode when no keyboard entry is filled
                    if not any(
                            self.is_widget_valid(shortcut_row) and shortcut_row[0].get().strip() for shortcut_row in
                            self.shortcut_rows):
                        for row in self.key_rows:
                            if len(row) == 4:  # Ensure the row has 4 elements (original_key_entry, remap_key_entry, original_key_select, remap_key_select)
                                original_key_entry, remap_key_entry, original_key_select, remap_key_select = row
                                try:
                                    original_key = original_key_entry.get().strip()  # Get the original key
                                    remap_key = remap_key_entry.get().strip()  # Get the remap key

                                    if original_key and remap_key:
                                        # Translate the keys
                                        original_key = self.translate_key(original_key, key_translations)
                                        remap_key = self.translate_key(remap_key, key_translations)

                                        # Handle combined keys by adding a "~" prefix
                                        if "&" in original_key:
                                            file.write(f"~{original_key}::{remap_key}\n")
                                        else:
                                            file.write(f"{original_key}::{remap_key}\n")
                                except TclError:
                                    continue  # Skip invalid widget errors

                    else:
                        file.write("toggle := false\n\n")

                        for shortcut_row in self.shortcut_rows:
                            if self.is_widget_valid(shortcut_row):
                                try:
                                    shortcut_entry, _ = shortcut_row  # Unpack the tuple to get the entry widget
                                    shortcut_key = shortcut_entry.get().strip()  # Now call .get() on shortcut_entry
                                    if shortcut_key:
                                        translated_key = self.translate_key(shortcut_key, key_translations)
                                        if "&" in translated_key:
                                            file.write(
                                                f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                                        else:
                                            file.write(
                                                f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                                except TclError:
                                    continue

                        file.write("#HotIf toggle\n")
                        for row in self.key_rows:
                            if len(row) == 4:  # Ensure the row has 4 elements (original_key_entry, remap_key_entry, original_key_select, remap_key_select)
                                original_key_entry, remap_key_entry, original_key_select, remap_key_select = row
                                try:
                                    original_key = original_key_entry.get().strip()  # Get the original key
                                    remap_key = remap_key_entry.get().strip()  # Get the remap key

                                    if original_key and remap_key:
                                        # Translate the keys
                                        original_key = self.translate_key(original_key, key_translations)
                                        remap_key = self.translate_key(remap_key, key_translations)

                                        # Handle combined keys by adding a "~" prefix
                                        if "&" in original_key:
                                            file.write(f"~{original_key}::{remap_key}\n")
                                        else:
                                            file.write(f"{original_key}::{remap_key}\n")
                                except TclError:
                                    continue  # Skip invalid widget errors
                        file.write("#HotIf")

            # Update the script list and close the profile creation window
            self.scripts = self.list_scripts()
            self.update_script_list()
            self.edit_window.destroy()

def main():
    root = tk.Tk()
    app = ScriptManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
