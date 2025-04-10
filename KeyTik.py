import os
import shutil
import tkinter as tk
from tkinter import Tk, filedialog, ttk, messagebox, LabelFrame, TclError
import tkinter.simpledialog
from pynput.keyboard import Controller, Key
import sys
import winshell
from win32com.client import Dispatch
from PIL import Image, ImageTk
import keyboard
import time
from pynput import mouse
import psutil
import win32gui
import win32process
import webbrowser
from markdown import markdown
from tkhtmlview import HTMLLabel
import requests
import json
import re
import random

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
data_dir = os.path.join(script_dir, '_internal', 'Data')
appdata_dir = os.path.join(os.getenv('APPDATA'), 'KeyTik')

current_version = "v2.0.0"

# Define the path to the 'condition.json' file (this path is used before calling load_condition)
condition_path = os.path.join(appdata_dir, "path.json")
dont_show_path = os.path.join(data_dir, "dont_show.json")
exit_keys_file = os.path.join(data_dir, "exit_keys.json")

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

# Path to store pinned profiles
pinned_file = os.path.join(appdata_dir, "pinned_profiles.json")
icon_path = os.path.join(data_dir, "icon.ico")
icon_unpinned_path = os.path.join(data_dir, "icon_a.png")
icon_pinned_path = os.path.join(data_dir, "icon_b.png")
device_list_path = os.path.join(active_dir, "Autohotkey Interception", "shared_device_info.txt")
device_finder_path = os.path.join(active_dir, "Autohotkey Interception", "find_device.ahk")
coordinate_path = os.path.join(active_dir, "Autohotkey Interception", "Coordinate.ahk")
keylist_path = os.path.join(data_dir, "key_list.txt")
welcome_path = os.path.join(data_dir, "welcome.md")
changelog_path = os.path.join(data_dir, "changelog.md")
interception_install_path = os.path.join(data_dir, "inter_install.bat")
interception_uninstall_path = os.path.join(data_dir, "inter_uninstall.bat")

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
        self.device_selection_window = None  # ✅ Initialize as None
        self.select_program_window = None   # ✅ Initialize as None
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
        self.sort_order = [True, True, True]
        self.previous_button_text = None  # Initialize this when the class is created, to store button's original text
        self.check_for_update(show_no_update_message=False)
        self.initialize_exit_keys()
        self.welcome_condition = self.load_welcome_condition()
        self.check_ahk_installation(show_installed_message=False)  # Check AHK installation on startup
        self.check_welcome()

    def load_welcome_condition(self):
        try:
            if os.path.exists(dont_show_path):
                with open(dont_show_path, "r") as f:
                    config = json.load(f)
                    return config.get("welcome_condition", True)  # Default to True if not found
        except Exception as e:
            print(f"Error loading condition file: {e}")
        return True  # Default to True on error

    def save_welcome_condition(self):
        try:
            with open(dont_show_path, "w") as f:
                json.dump({"welcome_condition": self.welcome_condition}, f)
        except Exception as e:
            print(f"Error saving condition file: {e}")

    def check_welcome(self):
        if self.welcome_condition:
            self.show_welcome_window()

    def show_welcome_window(self):
        try:
            # Get all numbered markdown files
            md_files = [f for f in os.listdir(data_dir) if f.endswith(".md") and f[:-3].isdigit()]
            md_files.sort(key=lambda x: int(x[:-3]))  # Sort numerically (1.md, 2.md, 3.md...)

            # Ensure we have at least a welcome file
            if not md_files:
                md_files = ["welcome.md"]  # Fallback if no numbered files exist

            self.current_welcome_index = 0
            self.welcome_files = [os.path.join(data_dir, f) for f in md_files]

            def load_content(index):
                try:
                    with open(self.welcome_files[index], "r", encoding="utf-8") as f:
                        md_content = f.read()
                        html_content = markdown(md_content)

                        # Apply styling to paragraphs, headings, and lists
                        html_content = html_content.replace(
                            "<p>", "<p style='font-family: Open Sans; font-size: 9px; font-weight: 300; margin: 10px;'>"
                        ).replace(
                            "<h1>",
                            "<h1 style='font-family: Open Sans; font-size: 18px; font-weight: 600; margin: 10px;'>"
                        ).replace(
                            "<h2>",
                            "<h2 style='font-family: Open Sans; font-size: 11px; font-weight: 500; margin: 10px;'>"
                        ).replace(
                            "<ul>",
                            "<ul style='font-family: Open Sans; font-size: 9px; font-weight: 300; margin: 10px;'>"
                        ).replace(
                            "<ol>",
                            "<ol style='font-family: Open Sans; font-size: 9px; font-weight: 300; margin: 10px;'>"
                        ).replace(
                            "<li>",
                            "<li style='font-family: Open Sans; font-size: 9px; font-weight: 300; margin: 10px;'>"
                        )

                        html_label.set_html(html_content)
                except FileNotFoundError:
                    html_label.set_html(
                        "<p style='font-family: Open Sans; font-size: 10px; font-weight: 300;'>File not found!</p>"
                    )

            # Create the welcome window
            welcome_window = tk.Toplevel(self.root)
            welcome_window.title("Readme!")
            welcome_window.geometry("525x290+350+220")
            welcome_window.resizable(False, False)
            welcome_window.iconbitmap(icon_path)
            welcome_window.transient(self.root)

            # Frame for HTML content
            html_frame = tk.Frame(welcome_window, width=500, height=230, relief=tk.RIDGE, borderwidth=2)
            html_frame.pack(pady=10)
            html_frame.pack_propagate(False)

            html_label = HTMLLabel(
                html_frame,
                html="",
                background="white",
                padx=11,
                pady=11,
                relief=tk.FLAT,
            )
            html_label.pack(fill=tk.BOTH, expand=True)

            load_content(self.current_welcome_index)

            # Navigation functions
            def next_page():
                if self.current_welcome_index < len(self.welcome_files) - 1:
                    self.current_welcome_index += 1
                    load_content(self.current_welcome_index)
                    update_buttons()

            def prev_page():
                if self.current_welcome_index > 0:
                    self.current_welcome_index -= 1
                    load_content(self.current_welcome_index)
                    update_buttons()

            def update_buttons():
                prev_button.config(state=tk.NORMAL if self.current_welcome_index > 0 else tk.DISABLED)
                next_button.config(
                    state=tk.NORMAL if self.current_welcome_index < len(self.welcome_files) - 1 else tk.DISABLED)

            def toggle_dont_show():
                self.welcome_condition = not dont_show_var.get()
                self.save_welcome_condition()

            # Create a frame for the buttons
            button_frame = tk.Frame(welcome_window)
            button_frame.pack(pady=0)

            # "Don't Show Again" checkbox
            dont_show_var = tk.BooleanVar(value=not self.welcome_condition)
            dont_show_checkbox = tk.Checkbutton(button_frame, text="Don't show again", variable=dont_show_var,
                                                command=toggle_dont_show)
            dont_show_checkbox.grid(row=0, column=2, pady=2)

            # Navigation buttons
            prev_button = tk.Button(button_frame, text="Previous", command=prev_page, width=15)
            next_button = tk.Button(button_frame, text="Next", command=next_page, width=15)

            # Place buttons in grid
            prev_button.grid(row=0, column=0, padx=37, pady=2)
            next_button.grid(row=0, column=1, padx=37, pady=2)

            update_buttons()  # Set correct initial button states

        except Exception as e:
            print(f"Error displaying welcome window: {e}")

    def create_ui(self):
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)  # Fill the entire window

        self.script_frame = tk.Frame(self.frame)
        self.script_frame.pack(pady=10, fill=tk.BOTH, expand=True)  # Fill the parent frame

        self.create_navigation_buttons()
        self.create_action_buttons()

    def create_navigation_buttons(self):
        nav_frame = tk.Frame(self.frame)
        nav_frame.pack(side=tk.TOP, fill=tk.X)  # Align at the top and fill horizontally

        self.prev_button = tk.Button(nav_frame, text="Previous", command=self.prev_page, width=12, height=1)
        self.prev_button.pack(side=tk.LEFT, padx=30)

        self.next_button = tk.Button(nav_frame, text="Next", command=self.next_page, width=12, height=1)
        self.next_button.pack(side=tk.RIGHT, padx=30)

    def create_action_buttons(self):
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

        self.setting_button = tk.Button(self.frame, text="Setting", width=8, command=self.open_settings_window)
        self.setting_button.place(relx=0.85, rely=0.907)  # Adjust placement as needed

        # Center the action_container by expanding the column in its parent frame
        action_container.grid_columnconfigure(0, weight=1)  # Centering by expanding space equally
        action_container.grid_columnconfigure(1, weight=1)

    def open_settings_window(self):
        # Create a new top-level window
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300+400+225")  # Adjust size as needed
        settings_window.resizable(False, False)
        settings_window.configure(padx=10, pady=10)  # Padding around the window
        settings_window.iconbitmap(icon_path)
        settings_window.transient(self.root)
        settings_window.resizable(False, False)

        # Create a LabelFrame inside the settings window
        frame = tk.LabelFrame(settings_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)  # Padding for the LabelFrame

        change_path_button = tk.Button(frame, text="Change Profile Location", command=self.change_data_location, height=2, width=20)
        change_path_button.grid(row=0, column=0, padx=5, pady=5)

        check_update_button = tk.Button(frame, text="Check For Update",
        command=lambda: self.check_for_update(show_no_update_message=True), height=2, width=20)
        check_update_button.grid(row=0, column=1, padx=5, pady=5)

        on_boarding_button = tk.Button(frame, text="On Boarding", command=self.show_welcome_window, height=2, width=20)
        on_boarding_button.grid(row=1, column=0, padx=5, pady=5)

        credit_button = tk.Button(frame, text="Credit", command=lambda: print("Button 4 clicked"), height=2, width=20)
        credit_button.grid(row=1, column=1, padx=5, pady=5)
        credit_button.config(state="disabled")

        sponsor_button = tk.Button(frame, text="Sponsor Me", command=lambda: webbrowser.open("https://github.com/sponsors/Fajar-RahmadJaya"), height=2, width=20)
        sponsor_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        # Configure the frame to ensure equal resizing of rows and columns
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def check_for_update(self, show_no_update_message=False):
        try:

            response = requests.get("https://api.github.com/repos/Fajar-RahmadJaya/KeyTik/releases/latest")
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data["tag_name"]

                if current_version == latest_version:
                    # Only show up-to-date message if explicitly requested (button click)
                    if show_no_update_message:
                        messagebox.showinfo("Check For Update", "You are using the latest version of KeyTik.")
                else:
                    # If update is available, show message with option to update
                    if messagebox.askyesno("Update Available",
                        f"New update available: KeyTik {latest_version}\n\nWould you like to go to the update page?"):
                        webbrowser.open("https://github.com/Fajar-RahmadJaya/KeyTik/releases")
            else:
                messagebox.showerror("Error", "Failed to check for updates. Please try again later.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while checking for updates: {str(e)}")

    def check_ahk_installation(self, show_installed_message=False):
        """
        Check if AutoHotkey v2 is installed
        :param show_installed_message: Boolean to control whether to show success message
        :return: Boolean indicating if AHK is installed
        """
        ahk_path = r"C:\Program Files\AutoHotkey\v2"

        if os.path.exists(ahk_path):
            if show_installed_message:
                messagebox.showinfo("AHK Installation", "AutoHotkey v2 is installed on your system.")
            return True
        else:
            if messagebox.askyesno("AHK Installation",
                "AutoHotkey v2 is not installed on your system. AutoHotkey is required for KeyTik to work.\n\nWould you like to download it now?"):
                webbrowser.open("https://www.autohotkey.com/")
            return False

    def check_interception_driver(self):
        """
        Check if Interception driver is installed
        :return: Boolean indicating if driver is installed
        """
        driver_path = r"C:\Windows\System32\drivers\keyboard.sys"

        if os.path.exists(driver_path):
            return True
        else:
            response = messagebox.askyesno(
                "Driver Not Found",
                "Interception driver is not installed. This driver is required to use assign on specific device feature.\n \n \nNote: Restart your device after installation.\n"
                "Would you like to install it now?"
            )

            if response:
                try:
                    if os.path.exists(interception_install_path):
                        # Get the directory containing the batch file
                        install_dir = os.path.dirname(interception_install_path)

                        # Use ctypes to elevate privileges and run the batch file from its directory
                        import ctypes
                        ctypes.windll.shell32.ShellExecuteW(
                            None,
                            "runas",  # Run as administrator
                            "cmd.exe",
                            f"/k cd /d {install_dir} && {os.path.basename(interception_install_path)}",  # Change to correct directory first
                            None,
                            1  # SW_SHOWNORMAL
                        )
                    else:
                        messagebox.showerror(
                            "Installation Failed",
                            "Installation script not found. Please check your installation."
                        )
                except Exception as e:
                    messagebox.showerror("Error", f"An error occurred during installation: {str(e)}")
            return False

    def change_data_location(self):
        global active_dir, store_dir

        # Open a file dialog for the user to select a new directory
        new_path = filedialog.askdirectory(title="Select a New Path for Active and Store Folders")

        if not new_path:
            print("No directory selected. Operation canceled.")
            return

        try:
            # Check if the selected path is valid
            if not os.path.exists(new_path):
                print(f"The selected path does not exist: {new_path}")
                return

            # Create new Active and Store directories in the chosen path
            new_active_dir = os.path.join(new_path, 'Active')
            new_store_dir = os.path.join(new_path, 'Store')

            # Move the existing Active and Store directories to the new path
            if os.path.exists(active_dir):
                shutil.move(active_dir, new_active_dir)
                print(f"Moved Active folder to {new_active_dir}")
            else:
                print(f"Active folder does not exist at {active_dir}")

            if os.path.exists(store_dir):
                shutil.move(store_dir, new_store_dir)
                print(f"Moved Store folder to {new_store_dir}")
            else:
                print(f"Store folder does not exist at {store_dir}")

            # Update the condition.json file with the new path
            new_condition_data = {"path": new_path}
            with open(condition_path, 'w') as f:
                json.dump(new_condition_data, f)
            print(f"Updated condition.json with the new path: {new_path}")

            # Update the global active_dir and store_dir variables to point to the new locations
            active_dir = new_active_dir
            store_dir = new_store_dir
            print(f"Global active_dir updated to: {active_dir}")
            print(f"Global store_dir updated to: {store_dir}")

            # Refresh the UI and reload the scripts
            self.SCRIPT_DIR = active_dir
            self.scripts = self.list_scripts()
            self.update_script_list()  # Refresh the UI to reflect the updated scripts

            # Show a success message box
            messagebox.showinfo("Change Profile Location", "Profile location changed successfully!")

        except Exception as e:
            print(f"An error occurred: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def toggle_on_top(self):
        self.is_on_top = not self.is_on_top
        try:
            self.root.attributes("-topmost", self.is_on_top)
        except TclError:
            print("Error: Unable to set always-on-top for root window.")

        def set_window_on_top(window, title, parent=None):
            if window is not None and window.winfo_exists():
                try:
                    if parent:
                        window.transient(parent)  # Keep window on top of its parent
                    else:
                        window.transient(self.root)

                    window.attributes("-topmost", self.is_on_top)
                    title_suffix = " (Always on Top)" if self.is_on_top else ""
                    window.title(f"{title}{title_suffix}")

                    # ✅ Fix disappearing icon by reapplying it here
                    window.iconbitmap(icon_path)

                except TclError:
                    print(f"Error: Unable to set always-on-top for {title} window.")

        # Apply Always on Top & Icon Fix to all relevant windows
        parent_window = self.create_profile_window or self.edit_window
        set_window_on_top(self.create_profile_window, "Create New Profile", self.root)
        set_window_on_top(self.edit_window, "Edit Profile", self.root)
        set_window_on_top(self.device_selection_window, "Select Device", parent_window)
        set_window_on_top(self.select_program_window, "Select Program", parent_window)

        # Update main window title and button text
        try:
            self.root.title(f"KeyTik{' (Always on Top)' if self.is_on_top else ''}")
            self.always_top.config(text="Disable Always on Top" if self.is_on_top else "Enable Always on Top")
        except TclError:
            print("Error: Unable to update main window title or button text.")

    def list_scripts(self):
        # Create a list of all .ahk and .py files
        all_scripts = [f for f in os.listdir(self.SCRIPT_DIR) if f.endswith('.ahk') or f.endswith('.py')]

        # Separate pinned and unpinned profiles
        pinned = [script for script in all_scripts if script in self.pinned_profiles]
        unpinned = [script for script in all_scripts if script not in self.pinned_profiles]

        # Return a combined list with pinned scripts at the top
        self.scripts = pinned + unpinned
        return self.scripts  # Ensure it returns a list of scripts

    def update_script_list(self):
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

            # Create the combined button
            combined_button = tk.Button(frame, text='Run', width=10, height=1)
            combined_button.grid(row=0, column=0, padx=2, pady=5)
            combined_button.config(command=lambda s=script, b=combined_button: self.toggle_run_exit(s, b))

            copy_button = tk.Button(frame, text="Copy", command=lambda s=script: self.copy_script(s), width=10,
                                    height=1)
            copy_button.grid(row=1, column=0, padx=8, pady=5)

            delete_button = tk.Button(frame, text="Delete", command=lambda s=script: self.delete_script(s), width=10,
                                    height=1)
            delete_button.grid(row=1, column=2, padx=8, pady=5)

            store_button = tk.Button(frame, text="Store" if self.SCRIPT_DIR == active_dir else "Restore",
                                    command=lambda s=script: self.store_script(s), width=10, height=1)
            store_button.grid(row=1, column=1, padx=2, pady=5)

            edit_button = tk.Button(frame, text="Edit", command=lambda s=script: self.edit_script(s), width=10,
                                    height=1)
            edit_button.grid(row=0, column=1, padx=5, pady=5)

            # Check if the script is in the startup folder
            shortcut_name = os.path.splitext(script)[0] + ".lnk"  # Shortcut name
            startup_folder = winshell.startup()
            shortcut_path = os.path.join(startup_folder, shortcut_name)

            # Update the button text and function based on startup status
            if os.path.exists(shortcut_path):
                startup_button = tk.Button(frame, text="Unstart",
                                        command=lambda s=script: self.remove_ahk_from_startup(s),
                                        width=10, height=1)
            else:
                startup_button = tk.Button(frame, text="Startup",
                                        command=lambda s=script: self.add_ahk_to_startup(s),
                                        width=10, height=1)

            startup_button.grid(row=0, column=2, padx=8, pady=5)

        # Configure grid weights to ensure proper resizing
        for i in range(3):
            self.script_frame.grid_rowconfigure(i, weight=1)
        for i in range(2):
            self.script_frame.grid_columnconfigure(i, weight=1)

        self.first_load = False

    def copy_script(self, script):
        # Change the root's icon globally
        self.root.iconbitmap(icon_path)  # Set your custom icon here

        # Add padding to the prompt string to increase the dialog width
        prompt = "Enter the new script name:".ljust(50)  # Adjust padding as needed

        # Ask for the new script name
        new_name = tkinter.simpledialog.askstring("Copy Script", prompt)

        if not new_name:
            return  # If no name is provided, do nothing

        # Make sure the new name ends with .ahk
        if not new_name.lower().endswith('.ahk'):
            new_name += '.ahk'

        # Get the source file path and the destination path
        source_path = os.path.join(self.SCRIPT_DIR, script)
        destination_path = os.path.join(self.SCRIPT_DIR, new_name)

        try:
            # Copy the script
            shutil.copy(source_path, destination_path)
            print(f"Script copied to {destination_path}")

            # Refresh the scripts list and update the UI
            self.scripts = self.list_scripts()  # Refresh the scripts list
            self.update_script_list()  # Update the UI with the new list
        except Exception as e:
            print(f"Error copying script: {e}")

    def toggle_run_exit(self, script_name, button):
        if button["text"] == "Run":
            # Start the script
            self.activate_script(script_name, button)
            # Change button to Exit after script is running
            button.config(text="Exit", command=lambda: self.toggle_run_exit(script_name, button))
        else:
            # Exit the script
            self.exit_script(script_name, button)
            # Change button to Run after script has exited
            button.config(text="Run", command=lambda: self.toggle_run_exit(script_name, button))

    def activate_script(self, script_name, button):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):
            # Start the script
            os.startfile(script_path)

            # Update button state dynamically
            button.config(text="Exit", command=lambda: self.toggle_run_exit(script_name, button))
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def exit_script(self, script_name, button):
        """Exit the script by sending its stored exit key combination"""
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):
            try:
                # Get the exit key combination from JSON
                with open(exit_keys_file, 'r') as f:
                    exit_keys = json.load(f)

                exit_combo = exit_keys.get(script_name)
                if not exit_combo:
                    messagebox.showerror("Error", f"No exit key found for {script_name}")
                    return

                # Parse the exit combo (e.g., "^!a" -> Ctrl+Alt+a)
                keyboard = Controller()
                if '^' in exit_combo:
                    keyboard.press(Key.ctrl)
                if '!' in exit_combo:
                    keyboard.press(Key.alt)

                # Press and release the final key
                final_key = exit_combo[-1]
                keyboard.press(final_key)
                keyboard.release(final_key)

                # Release modifier keys in reverse order
                if '!' in exit_combo:
                    keyboard.release(Key.alt)
                if '^' in exit_combo:
                    keyboard.release(Key.ctrl)

                # Update button state
                button.config(text="Run", command=lambda: self.toggle_run_exit(script_name, button))

            except Exception as e:
                messagebox.showerror("Error", f"Failed to exit script: {e}")
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def toggle_pin(self, script, icon_label):
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

        # Get the filename from the selected file path
        file_name = os.path.basename(selected_file)

        # Define the destination path in SCRIPT_DIR
        destination_path = os.path.join(self.SCRIPT_DIR, file_name)

        # Move the file to the SCRIPT_DIR
        try:
            shutil.move(selected_file, destination_path)
            print(f"File moved to: {destination_path}")
        except Exception as e:
            print(f"Failed to move file: {e}")
            return

        # Now modify the file contents in its new location
        try:
            # Generate new unique exit key first
            exit_key = self.generate_exit_key(file_name)

            with open(destination_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            # Check if the script already has the required lines
            already_has_exit = any("::ExitApp" in line for line in lines)
            already_has_default = any("; default" in line or "; text" in line for line in lines)

            if not already_has_exit or not already_has_default:
                # Check the format of the first line
                first_line = lines[0].strip() if lines else ''

                # Handle the case for `; text` or `; default`
                if first_line and '::' in first_line:
                    # If the first line is script-like, add `; default`
                    new_lines = [
                        "; default\n",
                        f"{exit_key}::ExitApp\n",
                        "\n"  # Add a new line for better formatting
                    ] + [first_line + '\n'] + lines[1:]
                else:
                    # If the first line is plain text, add `; text`
                    new_lines = [
                        "; text\n",
                        f"{exit_key}::ExitApp\n",
                        "\n"  # Add a new line for better formatting
                    ] + lines
            else:
                # If script already has exit key, replace it with the new one
                new_lines = []
                for line in lines:
                    if "::ExitApp" in line:
                        new_lines.append(f"{exit_key}::ExitApp\n")
                    else:
                        new_lines.append(line)

            # Write the modified contents back to the file
            with open(destination_path, 'w', encoding='utf-8') as file:
                file.writelines(new_lines)

            print(f"Modified script saved at: {destination_path}")

        except Exception as e:
            print(f"Error modifying script: {e}")
            # If there's an error, try to remove the exit key from JSON
            try:
                if os.path.exists(exit_keys_file):
                    with open(exit_keys_file, 'r') as f:
                        exit_keys = json.load(f)
                    if file_name in exit_keys:
                        del exit_keys[file_name]
                    with open(exit_keys_file, 'w') as f:
                        json.dump(exit_keys, f)
            except:
                pass
            return

        # Append the newly added script to self.scripts
        self.scripts.append(file_name)
        self.update_script_list()  # Refresh the UI

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_script_list()

    def next_page(self):
        if (self.current_page + 1) * 6 < len(self.scripts):
            self.current_page += 1
            self.update_script_list()

    def add_ahk_to_startup(self, script_name):
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

    def delete_script(self, script_name):
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
            vid_pid = device[3]  # Use Handle instead

            entry.delete(0, tk.END)  # Clear the entry
            entry.insert(0, f"{device_type}, {vid_pid}")

            # Close the device selection window
            window.destroy()

    def open_device_selection(self):
        # Check for Interception driver first
        if not self.check_interception_driver():
            return  # Don't open the device selection window if driver isn't installed

        if self.device_selection_window and self.device_selection_window.winfo_exists():
            self.device_selection_window.lift()
            return

        self.device_selection_window = tk.Toplevel(self.create_profile_window or self.edit_window)
        self.device_selection_window.geometry("600x300+308+233")
        self.device_selection_window.title("Select Device")
        self.device_selection_window.iconbitmap(icon_path)
        self.device_selection_window.resizable(False, False)
        self.device_selection_window.transient(self.create_profile_window or self.edit_window)  # Keep on top
        self.device_selection_window.attributes("-topmost", self.is_on_top)  # Respect Always on Top setting

        # Cleanup reference when closed
        self.device_selection_window.protocol("WM_DELETE_WINDOW", self.cleanup_device_selection_window)

        tree = ttk.Treeview(self.device_selection_window, columns=("Device Type", "VID", "PID", "Handle"), show="headings")
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
        button_frame = tk.Frame(self.device_selection_window)
        button_frame.pack(pady=5)

        # Select button
        select_button = tk.Button(button_frame, text="Select", width=23,
                                command=lambda: self.select_device(tree, self.keyboard_entry,
                                                                    self.device_selection_window))
        select_button.grid(row=0, column=0, padx=5, pady=5)

        monitor_button = tk.Button(button_frame, text="Open AHI Monitor To Test Device", width=29, command=self.run_monitor)
        monitor_button.grid(row=0, column=2, padx=5, pady=5)

        refresh_button = tk.Button(button_frame, text="Refresh", width=23, command=lambda: self.update_treeview(
                self.refresh_device_list(device_list_path), tree))
        refresh_button.grid(row=0, column=1, padx=5, pady=5)

    def cleanup_device_selection_window(self):
        self.device_selection_window.destroy()
        self.device_selection_window = None

    def create_new_profile(self):
        self.create_profile_window = tk.Toplevel(self.root)
        self.create_profile_window.geometry("600x450+308+130")  # Set initial size (width x height)
        self.create_profile_window.title("Create New Profile")
        self.create_profile_window.iconbitmap(icon_path)
        self.create_profile_window.resizable(False, False)

        # Bind cleanup method to window close event
        self.create_profile_window.protocol("WM_DELETE_WINDOW", self.cleanup_listeners)

        # Set the window as a transient of the root
        self.create_profile_window.transient(self.root)

        script_name_var = tk.StringVar()

        # Input for script name
        self.script_name_label = tk.Label(self.create_profile_window, text="Profile Name    :")
        self.script_name_label.place(relx=0.13, rely=0.006)
        self.script_name_entry = tk.Entry(self.create_profile_window)
        self.script_name_entry.place(relx=0.31, rely=0.01, relwidth=0.557)
        self.script_name_entry.insert(0, "  ")

        self.program_label = tk.Label(self.create_profile_window, text="Program           :")
        self.program_label.place(relx=0.13, rely=0.066)
        self.program_entry = tk.Entry(self.create_profile_window)
        self.program_entry.place(relx=0.31, rely=0.07, relwidth=0.38)
        self.program_entry.insert(0, "  ")
        self.program_select_button = tk.Button(self.create_profile_window, text="Select Program", command=lambda: self.open_select_program_window(self.program_entry))
        self.program_select_button.place(relx=0.71, rely=0.06, width=95)

        self.keyboard_label = tk.Label(self.create_profile_window, text="Device ID           :")
        self.keyboard_label.place(relx=0.13, rely=0.126)
        self.keyboard_entry = tk.Entry(self.create_profile_window)
        self.keyboard_entry.place(relx=0.31, rely=0.13, relwidth=0.38)
        self.keyboard_entry.insert(0, "  ")
        self.keyboard_select_button = tk.Button(self.create_profile_window, text="Select Device", command=self.open_device_selection)
        self.keyboard_select_button.place(relx=0.71, rely=0.12, width=95)


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
        self.add_shortcut_mapping_row()
        self.add_key_mapping_row()

        # Buttons
        self.finish_button = tk.Button(self.create_profile_window, text="Finish", command=self.finish_profile)
        self.finish_button.place(relx=0.070, rely=0.889, height=26, width=110)

        self.text_button = tk.Button(self.create_profile_window, text="Text Mode", command=self.toggle_mode)
        self.text_button.place(relx=0.760, rely=0.889, height=26, width=110)

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def show_tooltip(self, event, tooltip_text):
        self.tooltip = tk.Toplevel()
        self.tooltip.wm_overrideredirect(True)  # Remove window decorations
        self.tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")  # Position near the cursor

        # Create a label for the tooltip
        label = tk.Label(self.tooltip, text=tooltip_text, bg="white", fg="black",
                        relief="solid", borderwidth=1, padx=5, pady=3, justify="left")
        label.pack()

    def hide_tooltip(self, event):
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def is_visible_application(self, pid):
        try:
            def callback(hwnd, pid_list):
                _, process_pid = win32process.GetWindowThreadProcessId(hwnd)
                if process_pid == pid and win32gui.IsWindowVisible(hwnd):
                    pid_list.append(pid)

            visible_pids = []
            win32gui.EnumWindows(callback, visible_pids)
            return len(visible_pids) > 0
        except Exception as e:
            return False

    def get_running_processes(self):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'status']):
            try:
                if proc.info['name'].lower() in ["system", "system idle process", "svchost.exe", "taskhostw.exe",
                                                "explorer.exe"]:
                    continue

                pid = proc.info['pid']
                exe_name = proc.info['exe'] if 'exe' in proc.info else None  # Get executable path (not full path)
                exe_name = os.path.basename(exe_name) if exe_name else proc.info[
                    'name']  # Use executable name (not full path)
                status = proc.info['status']

                if self.is_visible_application(pid):
                    process_type = "Application"
                else:
                    process_type = "System"

                try:
                    def window_callback(hwnd, windows):
                        _, process_pid = win32process.GetWindowThreadProcessId(hwnd)
                        if process_pid == pid and win32gui.IsWindowVisible(hwnd):
                            windows.append((win32gui.GetClassName(hwnd),
                                            win32gui.GetWindowText(hwnd)))  # Get window class and title

                    windows = []
                    win32gui.EnumWindows(window_callback, windows)
                    if windows:
                        class_name, window_title = windows[0]  # Use the first window found
                    else:
                        class_name, window_title = "N/A", "N/A"  # Default to "N/A" if no window title

                except Exception as e:
                    class_name, window_title = "N/A", "N/A"  # Default if unable to retrieve class name or title

                # Add window_title (Name), class_name (window class), and exe_name (process name) to the list
                processes.append((window_title, class_name, exe_name, process_type))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def open_select_program_window(self, entry_widget):
        if self.select_program_window and self.select_program_window.winfo_exists():
            self.select_program_window.lift()
            return

        # Select appropriate parent window
        if hasattr(self, 'create_profile_window') and self.create_profile_window and self.create_profile_window.winfo_exists():
            parent_window = self.create_profile_window
        elif hasattr(self, 'edit_window') and self.edit_window and self.edit_window.winfo_exists():
            parent_window = self.edit_window
        else:
            parent_window = self.root

        self.select_program_window = tk.Toplevel(parent_window)
        self.select_program_window.title("Select Programs")
        self.select_program_window.geometry("600x300+308+217")
        self.select_program_window.iconbitmap(icon_path)
        self.select_program_window.resizable(False, False)
        self.select_program_window.transient(parent_window)  # Keep on top
        self.select_program_window.attributes("-topmost", self.is_on_top)  # Respect Always on Top setting

        # Cleanup reference when closed
        self.select_program_window.protocol("WM_DELETE_WINDOW", self.cleanup_select_program_window)

        # Frame to hold Treeview and scrollbar
        treeview_frame = tk.Frame(self.select_program_window)
        treeview_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Treeview for displaying programs
        treeview = ttk.Treeview(treeview_frame, columns=("Name", "Class", "Process", "Type"), show="headings",
                                selectmode="extended")
        treeview.heading("Name", text="Window Title ↑", command=lambda: self.sort_treeview(treeview, 0))
        treeview.heading("Class", text="Class", command=lambda: self.sort_treeview(treeview, 1))
        treeview.heading("Process", text="Process", command=lambda: self.sort_treeview(treeview, 2))
        treeview.heading("Type", text="Type", command=lambda: self.sort_treeview(treeview, 3))

        # Set column widths
        treeview.column("Name", width=135)
        treeview.column("Class", width=135)
        treeview.column("Process", width=130)
        treeview.column("Type", width=50)

        # Scrollbar for the Treeview
        scrollbar = tk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=treeview.yview)
        treeview.config(yscrollcommand=scrollbar.set)

        # Layout the Treeview and Scrollbar
        treeview.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure the Treeview frame to expand
        treeview_frame.columnconfigure(0, weight=1)
        treeview_frame.rowconfigure(0, weight=1)

        # Populate the Treeview with processes
        show_all = False  # Default to showing only applications

        def update_treeview(show_all_processes):
            treeview.delete(*treeview.get_children())
            processes = self.get_running_processes()
            for window_title, class_name, proc_name, p_type in processes:  # Adjusted unpacking to four values
                if show_all_processes or p_type == "Application":
                    # Inserting Name, Class, Process, Type
                    treeview.insert('', 'end', values=(window_title, class_name, proc_name, p_type))

        update_treeview(show_all)

        selected_programs = []

        def save_selected_programs():
            selected_programs.clear()
            for item in treeview.get_children():
                name, class_name, proc_name, _ = treeview.item(item, "values")
                if "✔" in name:
                    selected_programs.append(f"Name - {name.strip(' ✔')}")
                if "✔" in class_name:
                    selected_programs.append(f"Class - {class_name.strip(' ✔')}")
                if "✔" in proc_name:
                    selected_programs.append(f"Process - {proc_name.strip(' ✔')}")
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, ", ".join(selected_programs))
            self.select_program_window.destroy()

        def search_programs():
            search_query = search_entry.get().lower()
            treeview.delete(*treeview.get_children())
            processes = self.get_running_processes()
            for class_name, proc_name, p_type in processes:
                if search_query in class_name.lower() or search_query in proc_name.lower():
                    if show_all or p_type == "Application":
                        treeview.insert('', 'end', values=(proc_name, class_name, proc_name, p_type))

        def toggle_show_all_processes():
            nonlocal show_all
            show_all = not show_all
            update_treeview(show_all)
            toggle_button_text = "Show App Only" if show_all else "Show All Processes"
            show_all_button.config(text=toggle_button_text)

        # Button Frame
        button_frame = tk.Frame(self.select_program_window)
        button_frame.pack(pady=5)

        # Save button
        save_button = tk.Button(button_frame, text="Select", command=save_selected_programs, width=12)
        save_button.grid(row=0, column=0, padx=1, pady=5)

        # Search label
        search_label = tk.Label(button_frame, text="Search:", anchor="w")
        search_label.grid(row=0, column=1, padx=19, pady=5)

        # Search entry
        search_entry = tk.Entry(button_frame, width=30)
        search_entry.grid(row=0, column=2, padx=5, pady=5)

        # Search button
        search_button = tk.Button(button_frame, text="Search", command=search_programs, width=9)
        search_button.grid(row=0, column=3, padx=5, pady=5)

        # Show All Processes button
        toggle_button_text = "Show All Processes" if not show_all else "Show Applications Only"
        show_all_button = tk.Button(button_frame, text=toggle_button_text, command=toggle_show_all_processes, width=15)
        show_all_button.grid(row=0, column=4, padx=5, pady=5)

        def toggle_checkmark(event):
            item = treeview.identify('item', event.x, event.y)
            if item:
                current_values = treeview.item(item, 'values')
                name, class_name, proc_name, p_type = current_values
                if event.x < treeview.bbox(item, 'Name')[0] + treeview.bbox(item, 'Name')[2] / 2:
                    if "✔" in name:
                        name = name.replace(" ✔", "")
                    else:
                        name += " ✔"
                elif event.x < treeview.bbox(item, 'Class')[0] + treeview.bbox(item, 'Class')[2] / 2:
                    if "✔" in class_name:
                        class_name = class_name.replace(" ✔", "")
                    else:
                        class_name += " ✔"
                else:
                    if "✔" in proc_name:
                        proc_name = proc_name.replace(" ✔", "")
                    else:
                        proc_name += " ✔"
                treeview.item(item, values=(name, class_name, proc_name, p_type))

        treeview.bind('<Button-1>', toggle_checkmark)

    def cleanup_select_program_window(self):
        self.select_program_window.destroy()
        self.select_program_window = None

    def sort_treeview(self, treeview, col_index):
        self.sort_order[col_index] = not self.sort_order[col_index]
        column_headers = treeview['columns']
        header_text = treeview.heading(column_headers[col_index], 'text').split(' ')[0]
        if self.sort_order[col_index]:
            treeview.heading(column_headers[col_index], text=f"{header_text} ↑")
        else:
            treeview.heading(column_headers[col_index], text=f"{header_text} ↓")
        self.reset_column_headers(treeview, col_index)

        items = [(treeview.item(item)['values'], item) for item in treeview.get_children()]
        items.sort(key=lambda x: x[0][col_index].lower(), reverse=not self.sort_order[col_index])

        treeview.delete(*treeview.get_children())
        for values, _ in items:
            treeview.insert('', 'end', values=values)

    def reset_column_headers(self, treeview, exclude_index):
        columns = treeview['columns']
        for i, col in enumerate(columns):
            if i != exclude_index:
                header_text = treeview.heading(col, 'text').split(' ')[0]
                treeview.heading(col, text=header_text)

    def cleanup_listeners(self):
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
        # Add this line to prevent scroll selection
        shortcut_entry.bind('<MouseWheel>', self.handle_combobox_scroll)

        self.row_num += 1

        # Save reference for later
        self.shortcut_rows.append((shortcut_entry, shortcut_key_select))

        self.row_num += 1

        # Create a frame for the separator with + label
        separator_frame = tk.Frame(self.key_frame)
        separator_frame.grid(row=self.row_num, column=0, columnspan=4, sticky="we", padx=0, pady=3)

        # Create left line
        left_sep = tk.Frame(separator_frame, height=1, bg="gray")
        left_sep.pack(side="left", fill="x", expand=True)

        # Create center + label with cursor change and click binding
        plus_label = tk.Label(separator_frame, text="+", fg="gray", cursor="hand2")
        plus_label.pack(side="left", padx=5)

        def on_plus_click(event):
            # Get the current row number from the separator's grid info
            current_row = separator_frame.grid_info()['row']

            # Get all widgets below the current row and sort them by row number in reverse order
            widgets_below = [(w, w.grid_info()) for w in self.key_frame.grid_slaves()
                        if w.grid_info()['row'] > current_row]
            widgets_below.sort(key=lambda x: x[1]['row'], reverse=True)

            # Move all widgets below down by the number of rows a new shortcut mapping takes
            rows_per_mapping = 4  # Each shortcut mapping takes 3 rows (including separator)
            for widget, info in widgets_below:
                new_row = info['row'] + rows_per_mapping
                widget.grid_configure(row=new_row)

            # Save the current row_num
            original_row_num = self.row_num

            # Set row_num to insert the new row
            self.row_num = current_row + 1

            # Remove the + from current separator
            for widget in separator_frame.winfo_children():
                if isinstance(widget, tk.Label) and widget.cget('text') == '+':
                    widget.destroy()
            # Reconfigure the separators to be continuous lines
            for widget in separator_frame.winfo_children():
                if isinstance(widget, tk.Frame):  # This is a separator line
                    widget.pack_configure(side="left", fill="x", expand=True)

            # Add the new row
            self.add_shortcut_mapping_row()

            # Restore the original row_num plus the added rows
            self.row_num = max(original_row_num + rows_per_mapping, self.row_num)

            # Update the scroll region
            self.key_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

        plus_label.bind("<Button-1>", on_plus_click)

        # Create right line
        right_sep = tk.Frame(separator_frame, height=1, bg="gray")
        right_sep.pack(side="left", fill="x", expand=True)

        self.row_num += 1

        # If in Text Mode, re-add the text block below the shortcut rows
        if self.is_text_mode and hasattr(self, 'text_block'):
            self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
            self.row_num += 1  # Update row_num to account for the text block

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def load_key_values(self):
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

    def handle_combobox_scroll(self, event):
        # Instead of blocking the event completely, let it propagate to the canvas
        # but prevent the combobox from changing value
        current_value = event.widget.get()  # Store current value
        self.root.after(1, lambda: event.widget.set(current_value))  # Restore value after event
        return  # Let the event continue to propagate

    def add_key_mapping_row(self, original_key='', remap_key=''):  # Add default parameters
        select_default_key_label = tk.Label(self.key_frame, text="Default Key:")
        select_default_key_label.grid(row=self.row_num, rowspan=2, column=0, padx=10, pady=6)

        select_remap_key_label = tk.Label(self.key_frame, text="Remap Key:")
        select_remap_key_label.grid(row=self.row_num, rowspan=2, column=2, padx=10, pady=6)

        # Create a variable to store the checkbox state
        text_format_var = tk.BooleanVar()
        hold_format_var = tk.BooleanVar()

        original_key_select = tk.Button(self.key_frame, text="Select Default Key", justify='center', width=16,
                                    command=lambda: self.toggle_shortcut_key_listening(original_key_entry, original_key_select))
        original_key_select.grid(row=self.row_num, column=1, columnspan=2, sticky='w', padx=13, pady=5)

        remap_key_select = tk.Button(self.key_frame, text="Select Remap Key", width=16, justify='center',
                                command=lambda: self.toggle_shortcut_key_listening(remap_key_entry, remap_key_select))
        remap_key_select.grid(row=self.row_num, column=3, columnspan=2, sticky='w', padx=13, pady=5)

        # Check if buttons should be disabled
        if self.is_listening:
            original_key_select.config(state=tk.DISABLED)
            remap_key_select.config(state=tk.DISABLED)

        self.row_num += 1

        key_values = self.load_key_values()

        # Create combobox for selecting the default key
        original_key_entry = ttk.Combobox(self.key_frame, width=20, justify='center')
        original_key_entry.grid(row=self.row_num, column=1, sticky='w', padx=13, pady=6)
        self.original_key_entry = original_key_entry  # Save reference for later use
        original_key_entry['values'] = key_values  # Populate combobox with the values
        if original_key:  # Set the value if provided
            original_key_entry.set(original_key)
        # Bind scroll event to prevent selection change
        original_key_entry.bind('<MouseWheel>', self.handle_combobox_scroll)

        # Create combobox for selecting the remap key
        remap_key_entry = ttk.Combobox(self.key_frame, width=20, justify='center')
        remap_key_entry.grid(row=self.row_num, column=3, sticky='w', padx=13, pady=6)
        self.remap_key_entry = remap_key_entry  # Save reference for later use
        remap_key_entry['values'] = key_values  # Populate combobox with the values
        if remap_key:  # Set the value if provided
            remap_key_entry.set(remap_key)
        # Bind scroll event to prevent selection change
        remap_key_entry.bind('<MouseWheel>', self.handle_combobox_scroll)

        # Save button references for managing their states later
        self.key_rows.append((original_key_entry, remap_key_entry, original_key_select, remap_key_select, text_format_var, hold_format_var))

        self.row_num += 1

        format_label = tk.Label(self.key_frame, text="Remap Format:")
        format_label.grid(row=self.row_num, column=0, columnspan=2, padx=10, pady=6, sticky="w")

        text_format_checkbox = tk.Checkbutton(self.key_frame, text="Text Format", variable=text_format_var)
        text_format_checkbox.grid(row=self.row_num, column=1, columnspan=3, padx=30, pady=6, sticky="w")

        hold_format_checkbox = tk.Checkbutton(self.key_frame, text="Hold Format", variable=hold_format_var)
        hold_format_checkbox.grid(row=self.row_num, column=1, columnspan=3, padx=140, pady=6, sticky="w")

        def on_focus_in(event):
            if event.widget.get() == "Hold Interval":
                event.widget.delete(0, "end")
                event.widget.config(fg="black")  # Change text color to black

        def on_focus_out(event):
            if event.widget.get() == "":
                event.widget.insert(0, "Hold Interval")
                event.widget.config(fg="light gray")  # Restore light gray text

        # Create the Entry widget
        hold_interval_entry = tk.Entry(self.key_frame, width=17, justify='center', fg="light gray")
        hold_interval_entry.insert(0, "Hold Interval")

        # Bind events for focus-in and focus-out behavior
        hold_interval_entry.bind("<FocusIn>", on_focus_in)
        hold_interval_entry.bind("<FocusOut>", on_focus_out)

        # Place the Entry widget
        hold_interval_entry.grid(row=self.row_num, column=2, columnspan=3, padx=75, pady=6, sticky="w")
        self.hold_interval_entry=hold_interval_entry

        # Add hold_interval_entry to the key_rows tuple
        self.key_rows[-1] = self.key_rows[-1] + (hold_interval_entry,)

        self.row_num += 1

        # Create a frame for the separator with + label
        separator_frame = tk.Frame(self.key_frame)
        separator_frame.grid(row=self.row_num, column=0, columnspan=4, sticky="we", padx=0, pady=3)

        # Create left line
        left_sep = tk.Frame(separator_frame, height=1, bg="gray")
        left_sep.pack(side="left", fill="x", expand=True)

        # Create center + label with cursor change and click binding
        plus_label = tk.Label(separator_frame, text="+", fg="gray", cursor="hand2")
        plus_label.pack(side="left", padx=5)

        def on_plus_click(event):
            # Get the current row number from the separator's grid info
            current_row = separator_frame.grid_info()['row']

            # Get all widgets below the current row and sort them by row number in reverse order
            widgets_below = [(w, w.grid_info()) for w in self.key_frame.grid_slaves()
                        if w.grid_info()['row'] > current_row]
            widgets_below.sort(key=lambda x: x[1]['row'], reverse=True)

            # Move all widgets below down by the number of rows a new mapping takes
            rows_per_mapping = 4  # Each mapping takes 4 rows (including separator)
            for widget, info in widgets_below:
                new_row = info['row'] + rows_per_mapping
                widget.grid_configure(row=new_row)

            # Save the current row_num
            original_row_num = self.row_num

            # Set row_num to insert the new row
            self.row_num = current_row + 1

            # Remove the + from current separator
            for widget in separator_frame.winfo_children():
                if isinstance(widget, tk.Label) and widget.cget('text') == '+':
                    widget.destroy()
            # Reconfigure the separators to be continuous lines
            for widget in separator_frame.winfo_children():
                if isinstance(widget, tk.Frame):  # This is a separator line
                    widget.pack_configure(side="left", fill="x", expand=True)

            # Add the new row
            if isinstance(self, ScriptManagerApp):
                self.add_key_mapping_row()
            else:
                self.add_shortcut_mapping_row()

            # Restore the original row_num plus the added rows
            self.row_num = max(original_row_num + rows_per_mapping, self.row_num)

            # Update the scroll region
            self.key_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

        plus_label.bind("<Button-1>", on_plus_click)

        # Create right line
        right_sep = tk.Frame(separator_frame, height=1, bg="gray")
        right_sep.pack(side="left", fill="x", expand=True)

        self.row_num += 1

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def toggle_shortcut_key_listening(self, entry_widget, button):
        def toggle_other_buttons(state):
            # Disable/Enable all buttons except the active one
            if hasattr(self, 'key_rows'):  # Only process key_rows if they exist
                for key_row in self.key_rows:
                    # Unpack based on the known structure of key_rows
                    orig_entry, remap_entry, orig_button, remap_button, text_format_var, hold_format_var, hold_interval_entry = key_row
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
            self.previous_button_text = button.cget("text")

            # Disable user input for all relevant entries
            # Create a list of entries to disable
            entries_to_disable = []

            # Add script name entry if it exists
            if hasattr(self, 'script_name_entry'):
                entries_to_disable.append((self.script_name_entry, None))

            # Add keyboard entry if it exists
            if hasattr(self, 'keyboard_entry'):
                entries_to_disable.append((self.keyboard_entry, None))

            # Add program entry if it exists
            if hasattr(self, 'program_entry'):
                entries_to_disable.append((self.program_entry, None))

            # Add original and remap key entries if they exist
            if hasattr(self, 'original_key_entry'):
                entries_to_disable.append((self.original_key_entry, None))
            if hasattr(self, 'remap_key_entry'):
                entries_to_disable.append((self.remap_key_entry, None))

            # Add shortcut entry if it exists
            if hasattr(self, 'shortcut_entry'):
                entries_to_disable.append((self.shortcut_entry, None))

            # Add hold interval entry if it exists
            if hasattr(self, 'hold_interval_entry'):
                entries_to_disable.append((self.hold_interval_entry, None))

            # Disable all collected entries
            self.disable_entry_input(entries_to_disable)

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

            # Enable all entries that were disabled
            entries_to_enable = []

            # Add script name entry if it exists
            if hasattr(self, 'script_name_entry'):
                entries_to_enable.append((self.script_name_entry, None))

            # Add keyboard entry if it exists
            if hasattr(self, 'keyboard_entry'):
                entries_to_enable.append((self.keyboard_entry, None))

            # Add program entry if it exists
            if hasattr(self, 'program_entry'):
                entries_to_enable.append((self.program_entry, None))

            # Add original and remap key entries if they exist
            if hasattr(self, 'original_key_entry'):
                entries_to_enable.append((self.original_key_entry, None))
            if hasattr(self, 'remap_key_entry'):
                entries_to_enable.append((self.remap_key_entry, None))

            # Add shortcut entry if it exists
            if hasattr(self, 'shortcut_entry'):
                entries_to_enable.append((self.shortcut_entry, None))

            # Add hold interval entry if it exists
            if hasattr(self, 'hold_interval_entry'):
                entries_to_enable.append((self.hold_interval_entry, None))

            # Enable all collected entries
            self.enable_entry_input(entries_to_enable)

            # Enable all buttons
            toggle_other_buttons(tk.NORMAL)

            # Reset button text
            button.config(text=self.previous_button_text,
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
        # Process each entry in the key_rows list
        for entry_tuple in key_rows:
            entry = entry_tuple[0]  # Get the entry widget from the tuple
            if entry and entry.winfo_exists():
                # Remove focus from the entry by focusing on its parent
                entry.master.focus_set()

    def enable_entry_input(self, key_rows):
        # Nothing needed here since clicking the entry will naturally give it focus
        pass

    def on_key_event(self, event):
        if self.is_listening and self.active_entry and event.event_type == 'down':
            key_pressed = event.name
            self.active_entry.delete(0, tk.END)  # Clear the current entry field
            self.active_entry.insert(0, key_pressed)  # Insert the pressed key

    def on_mouse_event(self, x, y, button, pressed):
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
        if self.is_listening and self.active_entry is not None:
            # Temporarily set the entry to normal state so we can insert text
            self.active_entry.config(state='normal')  # Ensure it is in 'normal' state

            # Insert the key press into the entry widget
            self.active_entry.insert(tk.END, event.name)  # Insert the key event

            # Optionally change the appearance to make it look "disabled"

            # Re-disable it visually (but still allow programmatic input)
            self.active_entry.config(state='normal')  # Keep the entry active for programmatic input

    def on_shortcut_key_event(self, event):
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
        shortcut_combination = '+'.join(self.pressed_keys)  # Join the keys and buttons into a string
        self.active_entry.config(state='normal')  # Ensure it's in 'normal' state for update
        self.active_entry.delete(0, tk.END)  # Clear the current entry field
        self.active_entry.insert(0, shortcut_combination)  # Insert the combined keys and mouse buttons

    def load_key_translations(self):
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
        keys = key.split('+')  # Split by the "+" symbol for multiple keys
        translated_keys = []

        for single_key in keys:
            translated_key = key_translations.get(single_key.strip().lower(), single_key.strip())
            translated_keys.append(translated_key)

        # Join the keys back together with " & " for AHK format
        return " & ".join(translated_keys)

    def finish_profile(self):
        script_name = self.get_script_name()
        if not script_name:
            return  # If no script name is provided, return early

        output_path = os.path.join(self.SCRIPT_DIR, script_name)
        key_translations = self.load_key_translations()

        # Get the program condition for #HotIf
        program_condition = self.get_program_condition()

        # Get the device condition (whether a device is selected)
        device_condition = self.get_device_condition()

        # Check if there are any shortcuts
        shortcuts_present = any(
            self.is_widget_valid(shortcut_row) and shortcut_row[0].get().strip() for shortcut_row in self.shortcut_rows)

        try:
            with open(output_path, 'w') as file:
                self.write_first_line(file)  # Write initial lines (text/default)

                # Handle device (mouse/keyboard)
                self.handle_device(file)

                # Handle program entry and shortcuts
                if self.is_text_mode:
                    self.handle_text_mode(file, key_translations, program_condition, shortcuts_present,
                                        device_condition)
                else:
                    self.handle_default_mode(file, key_translations, program_condition, shortcuts_present,
                                            device_condition)

                # Finalize and update script list
                self.scripts = self.list_scripts()
                self.update_script_list()
                self.create_profile_window.destroy()

        except Exception as e:
            print(f"Error writing script: {e}")

    def get_program_condition(self):
        program_entry = self.program_entry.get().strip()
        program_condition = ""

        if program_entry:
            program_parts = program_entry.split(",")
            conditions = []

            for part in program_parts:
                part = part.strip()
                if part.lower().startswith("process"):
                    process_name = part.split("-")[1].strip()
                    conditions.append(f'WinActive("ahk_exe {process_name}")')
                elif part.lower().startswith("class"):
                    class_name = part.split("-")[1].strip()
                    conditions.append(f'WinActive("ahk_class {class_name}")')

            program_condition = " || ".join(conditions)

        return program_condition

    def get_device_condition(self):
        device_condition = ""
        device_name = self.keyboard_entry.get().strip()  # Retrieve device info from the entry
        if device_name:
            device_condition = f"cm1.IsActive"  # Modify this if needed to generate the correct condition
        return device_condition

    def handle_text_mode(self, file, key_translations, program_condition, shortcuts_present, device_condition):
        if not shortcuts_present:
            # If no shortcuts, use #HotIf without toggle
            if program_condition:
                file.write(f"#HotIf ({program_condition})\n")
            text_content = self.text_block.get("1.0", 'end').strip()
            if text_content:
                file.write(text_content + '\n')
        else:
            # If shortcuts present, use #HotIf with toggle
            file.write("toggle := false\n\n")

            # Start with the toggle condition and program condition combined
            hotif_condition = "toggle"
            if program_condition:
                hotif_condition += f" && ({program_condition})"

            self.process_shortcuts(file, key_translations)

            # Write the merged #HotIf line
            file.write(f"#HotIf {hotif_condition}\n")

            text_content = self.text_block.get("1.0", 'end').strip()
            if text_content:
                for line in text_content.splitlines():
                    file.write(line + '\n')

        # Close #HotIf for both program and device conditions
        file.write("#HotIf\n")

        if device_condition:
            file.write("#HotIf\n")

    def handle_default_mode(self, file, key_translations, program_condition, shortcuts_present, device_condition):
        if not shortcuts_present:
            # If no shortcuts, use #HotIf without toggle
            if program_condition:
                file.write(f"#HotIf ({program_condition})\n")
            self.process_key_remaps(file, key_translations)
        else:
            # If shortcuts present, use #HotIf with toggle
            file.write("toggle := false\n\n")

            # Start with the toggle condition and program condition combined
            hotif_condition = "toggle"
            if program_condition:
                hotif_condition += f" && ({program_condition})"

            self.process_shortcuts(file, key_translations)

            # Write the merged #HotIf line
            file.write(f"#HotIf {hotif_condition}\n")

            self.process_key_remaps(file, key_translations)

        # Close #HotIf for both program and device conditions
        file.write("#HotIf\n")

        if device_condition:
            file.write("#HotIf\n")

    def process_shortcuts(self, file, key_translations):
        for shortcut_row in self.shortcut_rows:
            if self.is_widget_valid(shortcut_row):
                try:
                    shortcut_entry, _ = shortcut_row
                    shortcut_key = shortcut_entry.get().strip()
                    if shortcut_key:
                        translated_key = self.translate_key(shortcut_key, key_translations)
                        if "&" in translated_key:
                            file.write(f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                        else:
                            file.write(f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                except TclError:
                    continue

    def get_script_name(self):
        script_name = self.script_name_entry.get().strip()
        if not script_name:
            messagebox.showwarning("Input Error", "Please enter a Profile name.")
            return None

        if not script_name.endswith('.ahk'):
            script_name += '.ahk'

        return script_name

    def write_first_line(self, file):
        script_name = os.path.basename(file.name)
        exit_key = self.generate_exit_key(script_name)  # First get the key

        if self.is_text_mode:
            file.write("; text\n")
        else:
            file.write("; default\n")
        file.write(f"{exit_key}::ExitApp \n\n#SingleInstance Force\n")  # Then write it to file

    def generate_exit_key(self, script_name, file=None):
        """Generate random exit key combination, save to JSON, and optionally write to file"""
        possible_keys = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

        try:
            # Load existing exit keys
            if os.path.exists(exit_keys_file):
                try:
                    with open(exit_keys_file, 'r') as f:
                        exit_keys = json.load(f)
                except json.JSONDecodeError:
                    # If JSON is invalid, start fresh
                    exit_keys = {}
            else:
                exit_keys = {}

            # Get all currently used keys
            used_keys = set(key[-1] for key in exit_keys.values())
            available_keys = [k for k in possible_keys if k not in used_keys]

            if not available_keys:  # If all keys are used (unlikely with 26 options)
                available_keys = possible_keys

            # Generate unique exit combo
            exit_combo = f"^!{random.choice(available_keys)}"  # Ctrl+Alt+RandomKey

            # Save to JSON
            exit_keys[script_name] = exit_combo
            with open(exit_keys_file, 'w') as f:
                json.dump(exit_keys, f)

            # If file object is provided, write the exit key to it
            if file is not None:
                file.write(f"{exit_combo}::ExitApp\n\n")

            return exit_combo

        except Exception as e:
            print(f"Error handling exit key: {e}")
            if file is not None:
                file.write("^!p::ExitApp\n\n")  # Fallback to default if writing to file
            return "^!p"  # Return default if error    
            
    def initialize_exit_keys(self):
        """Initialize exit keys for all AHK scripts on startup"""
        try:
            # Check if exit_keys.json exists in data_dir
            if not os.path.exists(exit_keys_file):
                print("No exit_keys.json found. Generating exit keys for all scripts...")
                exit_keys = {}

                # Get all .ahk files in active_dir
                ahk_files = [f for f in os.listdir(active_dir) if f.endswith('.ahk')]

                for script_name in ahk_files:
                    script_path = os.path.join(active_dir, script_name)

                    try:
                        # Read first line to determine script type
                        with open(script_path, 'r', encoding='utf-8') as f:
                            first_line = f.readline().strip()
                            lines = f.readlines()

                        # Generate new random exit key
                        exit_combo = f"^!{random.choice('abcdefghijklmnopqrstuvwxyz')}"
                        exit_keys[script_name] = exit_combo
                        if first_line == "; default":
                            new_content = ["; default\n",
                                        f"{exit_combo}::ExitApp\n\n"]
                            new_content.extend(lines[2:])
                        elif first_line == "; text":
                            new_content = ["; text\n",
                                        f"{exit_combo}::ExitApp\n\n"]
                            new_content.extend(lines[2:])

                        # Write back updated content
                        with open(script_path, 'w', encoding='utf-8') as f:
                            f.writelines(new_content)

                    except Exception as e:
                        print(f"Error processing {script_name}: {e}")
                        continue

                # Save all exit keys to json
                try:
                    with open(exit_keys_file, 'w') as f:
                        json.dump(exit_keys, f)
                except Exception as e:
                    print(f"Error saving exit_keys.json: {e}")

            else:
                print("exit_keys.json found, using existing exit keys.")

        except Exception as e:
            print(f"Error in initialize_exit_keys: {e}")
            
    def handle_device(self, file):
        keyboard_entry = self.keyboard_entry.get().strip()
        if keyboard_entry:
            parts = keyboard_entry.split(",", 1)
            device_type = parts[0].strip().lower()
            vid_pid_or_handle = parts[1].strip()

            if device_type == "mouse":
                is_mouse = True
            elif device_type == "keyboard":
                is_mouse = False
            else:
                raise ValueError(f"Unknown device type: {device_type}")

            if vid_pid_or_handle.startswith("0x"):
                vid, pid = vid_pid_or_handle.split(",")
                file.write(self.generate_device_code(is_mouse, vid.strip(), pid.strip()))
            else:
                file.write(self.generate_device_code_from_handle(is_mouse, vid_pid_or_handle))

    def generate_device_code(self, is_mouse, vid, pid):
        return f"""#SingleInstance force
Persistent
#include AutoHotkey Interception\Lib\AutoHotInterception.ahk

AHI := AutoHotInterception()
id1 := AHI.GetDeviceId({str(is_mouse).lower()}, {vid}, {pid})
cm1 := AHI.CreateContextManager(id1)

#HotIf cm1.IsActive
"""

    def generate_device_code_from_handle(self, is_mouse, handle):
        return f"""#SingleInstance force
Persistent
#include AutoHotkey Interception\Lib\AutoHotInterception.ahk

AHI := AutoHotInterception()
id1 := AHI.GetDeviceIdFromHandle({str(is_mouse).lower()}, "{handle}")
cm1 := AHI.CreateContextManager(id1)

#HotIf cm1.IsActive
"""

    def process_key_remaps(self, file, key_translations):
        for row in self.key_rows:
            if len(row) >= 7:
                original_key_entry, remap_key_entry, original_key_select, remap_key_select, text_format_var, hold_format_var, hold_interval_entry = row
                try:
                    original_key = original_key_entry.get().strip()
                    remap_key = remap_key_entry.get().strip()

                    if original_key and remap_key:
                        # Check if original_key contains multiple keys
                        has_multiple_keys = "+" in original_key
                        original_translated = self.translate_key(original_key, key_translations)

                        # Check for repeated keys first (e.g., "1 + 1")
                        if has_multiple_keys:
                            keys = [k.strip() for k in original_key.split("+")]
                            if len(keys) == 2 and keys[0] == keys[1]:
                                # For repeated keys, use just the single key
                                single_key = self.translate_key(keys[0], key_translations)

                                # Handle repeated keys with different formats
                                if text_format_var.get():  # Text format
                                    file.write(f'*{single_key}::{{\n')
                                    file.write(f'    if (A_PriorHotkey = "*{single_key}") and (A_TimeSincePriorHotkey < 400) {{\n')
                                    file.write(f'        SendText("{remap_key}")\n')
                                    file.write('    }\n')
                                    file.write('}\n')
                                elif hold_format_var.get():  # Hold format
                                    hold_interval = hold_interval_entry.get().strip() if hold_interval_entry.get().strip() != "Hold Interval" else "5"
                                    hold_interval_ms = str(int(float(hold_interval) * 1000))
                                    if "+" in remap_key:
                                        remap_keys = [self.translate_key(key.strip(), key_translations) for key in remap_key.split("+")]
                                        down_sequence = "".join([f"{{{key} Down}}" for key in remap_keys])
                                        up_sequence = "".join([f"{{{key} Up}}" for key in reversed(remap_keys)])
                                        file.write(f'*{single_key}::{{\n')
                                        file.write(f'    if (A_PriorHotkey = "*{single_key}") and (A_TimeSincePriorHotkey < 400) {{\n')
                                        file.write(f'        Send("{down_sequence}"), SetTimer(Send.Bind("{up_sequence}"), -{hold_interval_ms})\n')
                                        file.write('    }\n')
                                        file.write('}\n')
                                    else:
                                        remap_key = self.translate_key(remap_key, key_translations)
                                        file.write(f'*{single_key}::{{\n')
                                        file.write(f'    if (A_PriorHotkey = "*{single_key}") and (A_TimeSincePriorHotkey < 400) {{\n')
                                        file.write(f'        Send("{{{remap_key} Down}}")\n')
                                        file.write(f'        SetTimer(() => Send("{{{remap_key} Up}}"), -{hold_interval_ms})\n')
                                        file.write('    }\n')
                                        file.write('}\n')
                                else:  # Regular key press for repeated keys
                                    if "+" in remap_key:
                                        keys = [self.translate_key(key.strip(), key_translations) for key in remap_key.split("+")]
                                        key_down = "".join([f"{{{key} down}}" for key in keys])
                                        key_up = "".join([f"{{{key} up}}" for key in reversed(keys)])
                                        file.write(f'*{single_key}::{{\n')
                                        file.write(f'    if (A_PriorHotkey = "*{single_key}") and (A_TimeSincePriorHotkey < 400) {{\n')
                                        file.write(f'        Send("{key_down}{key_up}")\n')
                                        file.write('    }\n')
                                        file.write('}\n')
                                    else:
                                        remap_key = self.translate_key(remap_key, key_translations)
                                        file.write(f'*{single_key}::{{\n')
                                        file.write(f'    if (A_PriorHotkey = "*{single_key}") and (A_TimeSincePriorHotkey < 400) {{\n')
                                        file.write(f'        Send("{remap_key}")\n')
                                        file.write('    }\n')
                                        file.write('}\n')
                                continue

                        # Add ~ prefix if original_key has multiple keys (for non-repeated keys)
                        if has_multiple_keys:
                            original_translated = "~" + original_translated

                        # Handle normal (non-repeated) key combinations
                        if text_format_var.get():  # Text format
                            file.write(f'{original_translated}::SendText("{remap_key}")\n')
                        elif hold_format_var.get():  # Hold format
                            hold_interval = hold_interval_entry.get().strip() if hold_interval_entry.get().strip() != "Hold Interval" else "5"
                            hold_interval_ms = str(int(float(hold_interval) * 1000))

                            if "+" in remap_key:
                                remap_keys = [self.translate_key(key.strip(), key_translations) for key in remap_key.split("+")]
                                down_sequence = "".join([f"{{{key} Down}}" for key in remap_keys])
                                up_sequence = "".join([f"{{{key} Up}}" for key in reversed(remap_keys)])

                                if has_multiple_keys:
                                    file.write(f'{original_translated}:: Send("{down_sequence}"), SetTimer(Send.Bind("{up_sequence}"), -{hold_interval_ms})\n')
                                else:
                                    file.write(f'*{original_translated}:: Send("{down_sequence}"), SetTimer(Send.Bind("{up_sequence}"), -{hold_interval_ms})\n')
                            else:
                                remap_key = self.translate_key(remap_key, key_translations)
                                if has_multiple_keys:
                                    file.write(f'{original_translated}:: Send("{{{remap_key} Down}}"), SetTimer(Send.Bind("{{{remap_key} Up}}"), -{hold_interval_ms})\n')
                                else:
                                    file.write(f'*{original_translated}:: Send("{{{remap_key} Down}}"), SetTimer(Send.Bind("{{{remap_key} Up}}"), -{hold_interval_ms})\n')
                        elif "+" in remap_key:
                            keys = [key.strip() for key in remap_key.split("+")]
                            key_down = "".join([f"{{{key} down}}" for key in keys])
                            key_up = "".join([f"{{{key} up}}" for key in reversed(keys)])
                            file.write(f'{original_translated}::Send("{key_down}{key_up}")\n')
                        else:
                            remap_key = self.translate_key(remap_key, key_translations)
                            file.write(f'{original_translated}::{remap_key}\n')
                except TclError:
                    continue

    def save_changes(self, script_name):
        script_name = self.get_script_name()
        if not script_name:
            return

        output_path = os.path.join(self.SCRIPT_DIR, script_name)
        key_translations = self.load_key_translations()

        try:
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    first_line = f.readline().strip()

            with open(output_path, 'w') as file:

                self.write_first_line(file)
                self.handle_device(file)

                program_condition = self.get_program_condition()
                device_condition = self.get_device_condition()
                shortcuts_present = any(
                    self.is_widget_valid(shortcut_row) and shortcut_row[0].get().strip()
                    for shortcut_row in self.shortcut_rows
                )

                if self.is_text_mode:
                    self.handle_text_mode(file, key_translations, program_condition, shortcuts_present,
                                        device_condition)
                else:
                    self.handle_default_mode(file, key_translations, program_condition, shortcuts_present,
                                            device_condition)

            # Finalize and update script list
            self.scripts = self.list_scripts()
            self.update_script_list()
            self.edit_window.destroy()

        except Exception as e:
            print(f"Error writing script: {e}")

    def is_widget_valid(self, widget_tuple):
        """Check if a widget tuple exists and is valid"""
        try:
            # Check if both widgets in the tuple exist
            entry_widget, button_widget = widget_tuple
            return entry_widget.winfo_exists() and button_widget.winfo_exists()
        except (TclError, AttributeError, ValueError):
            return False

    def update_edit_text_block_height(self, event=None):
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
        if not self.check_interception_driver():
            return  # Don't open the device selection window if driver isn't installed

        if self.device_selection_window and self.device_selection_window.winfo_exists():
            self.device_selection_window.lift()
            return

        # Check if the parent window exists
        parent_window = self.create_profile_window if self.create_profile_window and self.create_profile_window.winfo_exists() else self.edit_window
        if not parent_window or not parent_window.winfo_exists():
            messagebox.showerror("Error", "Parent window no longer exists.")
            return

        self.device_selection_window = tk.Toplevel(parent_window)
        self.device_selection_window.geometry("600x300+308+233")
        self.device_selection_window.title("Select Device")
        self.device_selection_window.iconbitmap(icon_path)
        self.device_selection_window.resizable(False, False)
        self.device_selection_window.transient(parent_window)  # Keep on top
        self.device_selection_window.attributes("-topmost", self.is_on_top)  # Respect Always on Top setting

        # Cleanup reference when closed
        self.device_selection_window.protocol("WM_DELETE_WINDOW", self.cleanup_device_selection_window)


        tree = ttk.Treeview(self.device_selection_window, columns=("Device Type", "VID", "PID", "Handle"), show="headings")
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
        button_frame = tk.Frame(self.device_selection_window)
        button_frame.pack(pady=5)

        # Select button
        select_button = tk.Button(button_frame, text="Select", width=23,
                                command=lambda: self.select_device(tree, self.keyboard_entry,
                                                                    self.device_selection_window))
        select_button.grid(row=0, column=0, padx=5, pady=5)

        monitor_button = tk.Button(button_frame, text="Open AHI Monitor To Test Device", width=29, command=self.run_monitor)
        monitor_button.grid(row=0, column=2, padx=5, pady=5)

        refresh_button = tk.Button(button_frame, text="Refresh", width=23, command=lambda: self.update_treeview(
                self.refresh_device_list(device_list_path), tree))
        refresh_button.grid(row=0, column=1, padx=5, pady=5)

    def replace_raw_keys(self, key, key_map):
        return key_map.get(key, key)  # If key not found in the map, return the key as is.

    def load_key_list(self):
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
        self.is_text_mode = False  # Initialize is_text_mode to False

        script_path = os.path.join(self.SCRIPT_DIR, script_name)
        if os.path.isfile(script_path):
            # Read the existing script content
            with open(script_path, 'r') as file:
                lines = file.readlines()

            if not lines:
                return

            first_line = lines[0].strip()

            # Load the key list (mapping raw keys to human-readable names)
            key_map = self.load_key_list()

            # Determine the mode based on the first relevant line
            mode_line = lines[0].strip() if lines else "; default"  # Default to remap mode if empty

            # Create a new window for editing the script
            self.edit_window = tk.Toplevel(self.root)
            self.edit_window.geometry("600x450+308+130")
            self.edit_window.title("Edit Profile")
            self.edit_window.iconbitmap(icon_path)
            self.edit_window.resizable(False, False)

            # Bind cleanup method to window close event
            self.edit_window.protocol("WM_DELETE_WINDOW", self.edit_cleanup_listeners)

            # Set the window as a transient of the root
            self.edit_window.transient(self.root)

            # Input for script name (read-only)
            script_name_label = tk.Label(self.edit_window, text="Profile Name    :")
            script_name_label.place(relx=0.13, rely=0.006)
            script_name_entry = tk.Entry(self.edit_window)
            script_name_without_extension = script_name.replace('.ahk', '')
            script_name_entry.insert(0, "  ")
            script_name_entry.insert(4, script_name_without_extension)  # Start after the 4 spaces
            script_name_entry.config(state='readonly')
            script_name_entry.place(relx=0.31, rely=0.01, relwidth=0.557)
            self.script_name_entry = script_name_entry

            program_label = tk.Label(self.edit_window, text="Program           :")
            program_label.place(relx=0.13, rely=0.066)
            program_entry = tk.Entry(self.edit_window)
            program_entry.place(relx=0.31, rely=0.07, relwidth=0.38)
            program_select_button = tk.Button(self.edit_window, text="Select Program",
                                            command=lambda: self.edit_open_select_program_window(self.program_entry))
            program_select_button.place(relx=0.71, rely=0.06, width=95)
            self.program_entry = program_entry

            keyboard_label = tk.Label(self.edit_window, text="Device ID           :")
            keyboard_label.place(relx=0.13, rely=0.126)
            keyboard_entry = tk.Entry(self.edit_window)
            keyboard_entry.place(relx=0.31, rely=0.13, relwidth=0.38)
            keyboard_entry.insert(0, "  ")
            keyboard_select_button = tk.Button(self.edit_window, text="Select Device",
                                            command=self.edit_open_device_selection)
            keyboard_select_button.place(relx=0.71, rely=0.12, width=95)
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

            # Extract the program names from the script content
            programs = []
            for line in lines:
                line = line.strip()
                if line.startswith("#HotIf"):
                    # Extract program references in `WinActive` conditions
                    import re
                    matches = re.findall(r'WinActive\("ahk_(exe|class)\s+([^"]+)"\)', line)
                    for match in matches:
                        program_type, program_name = match
                        if program_type == "exe":
                            programs.append(f"Process - {program_name}")
                        elif program_type == "class":
                            programs.append(f"Class - {program_name}")

            # Join all programs into a single string separated by commas
            program_entry_value = ", ".join(programs)

            # Insert the extracted program names into the program_entry field
            if program_entry_value:
                program_entry.insert(4, program_entry_value)

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

            # Parsing remaps and shortcuts
            if mode_line == "; default":
                in_hotif_block = False  # Track if we are inside a #HotIf block

                # Track current block to handle multi-line script blocks
                current_block = []
                in_block = False

                for line in lines[3:]:  # Skip the header lines
                    line = line.strip()  # Clean whitespace
                    if not line or line.startswith(";"):  # Skip empty lines and comments
                        continue

                    if line.startswith("#HotIf"):
                        in_hotif_block = not in_hotif_block
                        continue

                    # Handle script block start
                    if line.startswith("*") and "::{" in line:
                        original_key = line[1:line.index("::{")]  # Extract key (remove * and ::{)
                        in_block = True
                        current_block = []
                        continue

                    # Collect block content
                    if in_block:
                        if line == "}":
                            in_block = False

                            # Process the collected block
                            block_text = " ".join(current_block)

                            # Check for double-click pattern
                            if 'A_PriorHotkey' in block_text and 'A_TimeSincePriorHotkey < 400' in block_text:
                                is_text_format = False
                                is_hold_format = False
                                hold_interval = "5"
                                remap_key = ""

                                # Extract the action from the block
                                if 'SendText' in block_text:
                                    # Handle text format
                                    text_match = re.search(r'SendText\("(.+?)"\)', block_text)
                                    if text_match:
                                        remap_key = text_match.group(1)
                                        is_text_format = True
                                elif 'SetTimer' in block_text:
                                    # Handle hold format
                                    is_hold_format = True
                                    if 'Send.Bind' in block_text:
                                        # Multiple keys hold format
                                        down_keys = re.findall(r'{(\w+) Down}', block_text)
                                        if down_keys:
                                            remap_key = " + ".join(down_keys)
                                        # Extract hold interval
                                        interval_match = re.search(r'-(\d+)', block_text)
                                        if interval_match:
                                            hold_interval = str(int(interval_match.group(1)) / 1000)
                                    else:
                                        # Single key hold format
                                        down_match = re.search(r'{(\w+) Down}', block_text)
                                        if down_match:
                                            remap_key = down_match.group(1)
                                        # Extract hold interval
                                        interval_match = re.search(r'-(\d+)', block_text)
                                        if interval_match:
                                            hold_interval = str(int(interval_match.group(1)) / 1000)
                                else:
                                    # Handle regular Send format
                                    send_match = re.search(r'Send\("(.+?)"\)', block_text)
                                    if send_match:
                                        content = send_match.group(1)
                                        if '{' in content:
                                            # Handle key combinations
                                            keys = re.findall(r'{(\w+)[^}]*}', content)
                                            unique_keys = []
                                            for k in keys:
                                                if k not in unique_keys:
                                                    unique_keys.append(k)
                                            remap_key = " + ".join(unique_keys)
                                        else:
                                            remap_key = content

                                # Add to remaps with double-click format
                                remaps.append((f"{original_key} + {original_key}", remap_key, is_text_format, is_hold_format, hold_interval))
                            current_block = []
                            continue
                        current_block.append(line)
                        continue

                    # Handle regular remaps
                    if "::" in line:
                        # Split the line into key parts
                        parts = line.split("::")
                        original_key = parts[0].strip()
                        remap_or_action = parts[1].strip() if len(parts) > 1 else ""

                        # Process original key
                        original_key = self.replace_raw_keys(original_key, key_map).replace("~", "").replace(" & ", "+").replace("*", "")

                        if remap_or_action:  # Remap case
                            is_text_format = False
                            is_hold_format = False
                            remap_key = ""
                            hold_interval = "5"  # Default hold interval
                            if remap_or_action.startswith('SendText'):
                                # Extract the text from SendText and remove quotes
                                text = remap_or_action[len("SendText("):-1]  # Remove the 'SendText(' and ')'
                                text = text.strip('"')  # Remove surrounding quotes
                                remap_key = text  # Store just the raw text
                                is_text_format = True
                            elif 'SetTimer' in remap_or_action:
                                # This is a hold format command
                                # Extract keys from Send part - look for key pattern in the first part
                                send_match = re.search(r'Send\("(.*?)"\)', remap_or_action)
                                if send_match:
                                    down_sequence = send_match.group(1)
                                    # Extract individual keys from the down sequence
                                    down_keys = re.findall(r'{(.*?) Down}', down_sequence)
                                    if down_keys:
                                        # Join keys with + to create the combined remap key
                                        remap_key = " + ".join(down_keys)
                                        is_hold_format = True

                                        # Extract the hold interval from SetTimer
                                        interval_match = re.search(r'SetTimer\(Send\.Bind\(".*?"\), -(\d+)\)', remap_or_action)
                                        if interval_match:
                                            hold_interval = str(int(interval_match.group(1)) / 1000)  # Convert ms to seconds
                                is_hold_format = True
                            elif remap_or_action.startswith('Send'):
                                # Extract the keys from Send command
                                key_sequence = remap_or_action[len("Send("):-1]  # Remove the 'Send(' and ')'
                                keys = []

                                # Find the individual keys and maintain their order
                                matches = re.findall(r'{(.*?)( down| up)}', key_sequence)
                                if matches:
                                    # Process keys in pairs (down/up) to maintain order
                                    seen_keys = set()  # To track keys we've already processed
                                    for match in matches:
                                        key = match[0]  # Get the key name
                                        if key not in seen_keys:
                                            seen_keys.add(key)
                                            keys.append(key)  # Add key in order of appearance
                                    remap_key = " + ".join(keys)  # Join the keys with ' + '
                                else:
                                    # If no matches, it's a simple key press
                                    remap_key = key_sequence.strip('{}')  # Remove curly braces if present

                            else:
                                remap_key = remap_or_action  # If it's just a regular remap

                            # Now insert the processed values into the remap
                            remaps.append((original_key, remap_key, is_text_format, is_hold_format, hold_interval))

                        else:  # Shortcut case (no remap key, just action or toggle logic)
                            shortcuts.append(original_key)


            elif mode_line == "; text":
                self.is_text_mode = True
                self.text_block = tk.Text(self.edit_frame, wrap='word', height=14, width=70, font=("Consolas", 10))
                self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
                self.text_block.bind("<KeyRelease>", self.update_edit_text_block_height)
                self.row_num += 1

                text_content = self.extract_and_filter_content(lines)
                self.text_block.insert('1.0', text_content.strip())
                self.update_edit_text_block_height()

            with open(script_path, 'r', encoding='utf-8') as file:
                first_line = file.readline().strip()

                        # Add shortcut rows to UI
            for shortcut in shortcuts:
                self.add_edit_shortcut_mapping_row(shortcut)

            # Add remap rows to UI
            for original_key, remap_key, is_text_format, is_hold_format, hold_interval in remaps:
                self.add_edit_mapping_row(original_key, remap_key)
                # Set the text format checkbox state for the last added row
                if self.key_rows and len(self.key_rows[-1]) == 7:  # Changed from 5 to 7 to account for hold_format_var and hold_interval_entry
                    _, _, _, _, text_format_var, hold_format_var, hold_interval_entry = self.key_rows[-1]
                    text_format_var.set(is_text_format)
                    hold_format_var.set(is_hold_format)
                    if is_hold_format and hold_interval:
                        hold_interval_entry.delete(0, "end")
                        # Convert string to float first, then format as integer if whole number
                        hold_interval_float = float(hold_interval)
                        hold_interval_str = str(int(hold_interval_float)) if hold_interval_float.is_integer() else str(hold_interval_float)
                        hold_interval_entry.insert(0, hold_interval_str)
                        hold_interval_entry.config(fg="black")

            save_button = tk.Button(self.edit_window, text="Save Changes",
                                    command=lambda: self.save_changes(script_name))
            save_button.place(relx=0.070, rely=0.889, height=26, width=107)

            # Update the scrollable region of the canvas
            self.update_scroll_region()
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def convert_milliseconds_to_time_units(self, milliseconds):
        """
        Convert milliseconds to hours, minutes, seconds, and milliseconds
        Returns a tuple of (hours, minutes, seconds, milliseconds)
        """
        # Constants for conversion
        MILLISECONDS_PER_SECOND = 1000
        SECONDS_PER_MINUTE = 60
        MINUTES_PER_HOUR = 60

        # Calculate hours
        total_seconds = milliseconds / MILLISECONDS_PER_SECOND
        total_minutes = total_seconds / SECONDS_PER_MINUTE
        hours = int(total_minutes / MINUTES_PER_HOUR)

        # Calculate remaining minutes
        remaining_milliseconds = milliseconds - (hours * MINUTES_PER_HOUR * SECONDS_PER_MINUTE * MILLISECONDS_PER_SECOND)
        minutes = int(remaining_milliseconds / (SECONDS_PER_MINUTE * MILLISECONDS_PER_SECOND))

        # Calculate remaining seconds
        remaining_milliseconds -= minutes * SECONDS_PER_MINUTE * MILLISECONDS_PER_SECOND
        seconds = int(remaining_milliseconds / MILLISECONDS_PER_SECOND)

        # Calculate remaining milliseconds
        remaining_milliseconds -= seconds * MILLISECONDS_PER_SECOND

        return hours, minutes, seconds, int(remaining_milliseconds)

    def edit_open_select_program_window(self, entry_widget):
        if self.select_program_window and self.select_program_window.winfo_exists():
            self.select_program_window.lift()
            return

        # Select appropriate parent window
        if hasattr(self, 'edit_window') and self.edit_window and self.edit_window.winfo_exists():
            parent_window = self.edit_window
        else:
            parent_window = self.root

        self.select_program_window = tk.Toplevel(parent_window)
        self.select_program_window.title("Select Programs")
        self.select_program_window.geometry("600x300+308+217")
        self.select_program_window.iconbitmap(icon_path)
        self.select_program_window.resizable(False, False)
        self.select_program_window.transient(parent_window)  # Keep on top
        self.select_program_window.attributes("-topmost", self.is_on_top)  # Respect Always on Top setting

        # Cleanup reference when closed
        self.select_program_window.protocol("WM_DELETE_WINDOW", self.cleanup_select_program_window)

        # Frame to hold Treeview and scrollbar
        treeview_frame = tk.Frame(self.select_program_window)
        treeview_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Treeview for displaying programs
        treeview = ttk.Treeview(treeview_frame, columns=("Name", "Class", "Process", "Type"), show="headings",
                                selectmode="extended")
        treeview.heading("Name", text="Window Title ↑", command=lambda: self.sort_treeview(treeview, 0))
        treeview.heading("Class", text="Class", command=lambda: self.sort_treeview(treeview, 1))
        treeview.heading("Process", text="Process", command=lambda: self.sort_treeview(treeview, 2))
        treeview.heading("Type", text="Type", command=lambda: self.sort_treeview(treeview, 3))

        # Set column widths
        treeview.column("Name", width=135)
        treeview.column("Class", width=135)
        treeview.column("Process", width=130)
        treeview.column("Type", width=50)

        # Scrollbar for the Treeview
        scrollbar = tk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=treeview.yview)
        treeview.config(yscrollcommand=scrollbar.set)

        # Layout the Treeview and Scrollbar
        treeview.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure the Treeview frame to expand
        treeview_frame.columnconfigure(0, weight=1)
        treeview_frame.rowconfigure(0, weight=1)

        # Populate the Treeview with processes
        show_all = False  # Default to showing only applications

        def update_treeview(show_all_processes):
            treeview.delete(*treeview.get_children())
            processes = self.get_running_processes()
            for window_title, class_name, proc_name, p_type in processes:  # Adjusted unpacking to four values
                if show_all_processes or p_type == "Application":
                    # Inserting Name, Class, Process, Type
                    treeview.insert('', 'end', values=(window_title, class_name, proc_name, p_type))

        update_treeview(show_all)

        selected_programs = []

        def save_selected_programs():
            selected_programs.clear()
            for item in treeview.get_children():
                name, class_name, proc_name, _ = treeview.item(item, "values")
                if "✔" in name:
                    selected_programs.append(f"Name - {name.strip(' ✔')}")
                if "✔" in class_name:
                    selected_programs.append(f"Class - {class_name.strip(' ✔')}")
                if "✔" in proc_name:
                    selected_programs.append(f"Process - {proc_name.strip(' ✔')}")
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, ", ".join(selected_programs))
            self.select_program_window.destroy()

        def search_programs():
            search_query = search_entry.get().lower()
            treeview.delete(*treeview.get_children())
            processes = self.get_running_processes()
            for class_name, proc_name, p_type in processes:
                if search_query in class_name.lower() or search_query in proc_name.lower():
                    if show_all or p_type == "Application":
                        treeview.insert('', 'end', values=(proc_name, class_name, proc_name, p_type))

        def toggle_show_all_processes():
            nonlocal show_all
            show_all = not show_all
            update_treeview(show_all)
            toggle_button_text = "Show App Only" if show_all else "Show All Processes"
            show_all_button.config(text=toggle_button_text)

        # Button Frame
        button_frame = tk.Frame(self.select_program_window)
        button_frame.pack(pady=5)

        # Save button
        save_button = tk.Button(button_frame, text="Select", command=save_selected_programs, width=12)
        save_button.grid(row=0, column=0, padx=1, pady=5)

        # Search label
        search_label = tk.Label(button_frame, text="Search:", anchor="w")
        search_label.grid(row=0, column=1, padx=19, pady=5)

        # Search entry
        search_entry = tk.Entry(button_frame, width=30)
        search_entry.grid(row=0, column=2, padx=5, pady=5)

        # Search button
        search_button = tk.Button(button_frame, text="Search", command=search_programs, width=9)
        search_button.grid(row=0, column=3, padx=5, pady=5)

        # Show All Processes button
        toggle_button_text = "Show All Processes" if not show_all else "Show Applications Only"
        show_all_button = tk.Button(button_frame, text=toggle_button_text, command=toggle_show_all_processes, width=15)
        show_all_button.grid(row=0, column=4, padx=5, pady=5)

        def toggle_checkmark(event):
            item = treeview.identify('item', event.x, event.y)
            if item:
                current_values = treeview.item(item, 'values')
                name, class_name, proc_name, p_type = current_values
                if event.x < treeview.bbox(item, 'Name')[0] + treeview.bbox(item, 'Name')[2] / 2:
                    if "✔" in name:
                        name = name.replace(" ✔", "")
                    else:
                        name += " ✔"
                elif event.x < treeview.bbox(item, 'Class')[0] + treeview.bbox(item, 'Class')[2] / 2:
                    if "✔" in class_name:
                        class_name = class_name.replace(" ✔", "")
                    else:
                        class_name += " ✔"
                else:
                    if "✔" in proc_name:
                        proc_name = proc_name.replace(" ✔", "")
                    else:
                        proc_name += " ✔"
                treeview.item(item, values=(name, class_name, proc_name, p_type))

        treeview.bind('<Button-1>', toggle_checkmark)

    def edit_cleanup_listeners(self):
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

        # Clean up any existing device selection window
        if hasattr(self, 'device_selection_window') and self.device_selection_window and self.device_selection_window.winfo_exists():
            self.device_selection_window.destroy()
            self.device_selection_window = None

        # Clean up the edit window reference
        if hasattr(self, 'edit_window'):
            self.edit_window.destroy()
            self.edit_window = None

    def extract_and_filter_content(self, lines):
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
        select_default_key_label = tk.Label(self.edit_frame, text="Default Key:")
        select_default_key_label.grid(row=self.row_num, rowspan=2, column=0, padx=10, pady=6)

        select_remap_key_label = tk.Label(self.edit_frame, text="Remap Key:")
        select_remap_key_label.grid(row=self.row_num, rowspan=2, column=2, padx=10, pady=6)

        # Create a variable to store the checkbox state
        text_format_var = tk.BooleanVar()
        hold_format_var = tk.BooleanVar()

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
        if original_key:  # Set the value if provided
            original_key_entry.set(original_key)
        # Bind scroll event to prevent selection change
        original_key_entry.bind('<MouseWheel>', self.handle_combobox_scroll)

        # Create combobox for selecting the remap key
        remap_key_entry = ttk.Combobox(self.edit_frame, width=20, justify='center')
        remap_key_entry.grid(row=self.row_num, column=3, sticky='w', padx=13, pady=6)
        self.remap_key_entry = remap_key_entry  # Save reference for later use
        remap_key_entry['values'] = key_values  # Populate combobox with the values
        if remap_key:  # Set the value if provided
            remap_key_entry.set(remap_key)
        # Bind scroll event to prevent selection change
        remap_key_entry.bind('<MouseWheel>', self.handle_combobox_scroll)

        # Save button references for managing their states later
        self.key_rows.append((original_key_entry, remap_key_entry, original_key_select, remap_key_select, text_format_var, hold_format_var))

        self.row_num += 1

        format_label = tk.Label(self.edit_frame, text="Remap Format:")
        format_label.grid(row=self.row_num, column=0, columnspan=2, padx=10, pady=6, sticky="w")

        text_format_checkbox = tk.Checkbutton(self.edit_frame, text="Text Format", variable=text_format_var)
        text_format_checkbox.grid(row=self.row_num, column=1, columnspan=3, padx=30, pady=6, sticky="w")

        hold_format_checkbox = tk.Checkbutton(self.edit_frame, text="Hold Format", variable=hold_format_var)
        hold_format_checkbox.grid(row=self.row_num, column=1, columnspan=3, padx=140, pady=6, sticky="w")

        def on_focus_in(event):
            if event.widget.get() == "Hold Interval":
                event.widget.delete(0, "end")
                event.widget.config(fg="black")  # Change text color to black

        def on_focus_out(event):
            if event.widget.get() == "":
                event.widget.insert(0, "Hold Interval")
                event.widget.config(fg="light gray")  # Restore light gray text

        # Create the Entry widget
        hold_interval_entry = tk.Entry(self.edit_frame, width=17, justify='center', fg="light gray")
        hold_interval_entry.insert(0, "Hold Interval")

        # Bind events for focus-in and focus-out behavior
        hold_interval_entry.bind("<FocusIn>", on_focus_in)
        hold_interval_entry.bind("<FocusOut>", on_focus_out)

        # Place the Entry widget
        hold_interval_entry.grid(row=self.row_num, column=2, columnspan=3, padx=75, pady=6, sticky="w")
        self.hold_interval_entry=hold_interval_entry

        # Add hold_interval_entry to the key_rows tuple
        self.key_rows[-1] = self.key_rows[-1] + (hold_interval_entry,)

        self.row_num += 1

        # Remove + from previous last separator if it exists - Add safety check
        if hasattr(self, 'last_separator_frame') and self.last_separator_frame.winfo_exists():
            for widget in self.last_separator_frame.winfo_children():
                if isinstance(widget, tk.Label) and widget.cget('text') == '+':
                    widget.destroy()
            # Reconfigure the right separator in the previous last frame
            for widget in self.last_separator_frame.winfo_children():
                if isinstance(widget, tk.Frame):  # This is a separator line
                    widget.pack_configure(side="left", fill="x", expand=True)

        # Create a frame for the separator with + label
        separator_frame = tk.Frame(self.edit_frame)
        separator_frame.grid(row=self.row_num, column=0, columnspan=4, sticky="we", padx=0, pady=3)
        self.last_separator_frame = separator_frame  # Store reference to current separator

        # Create left line
        left_sep = tk.Frame(separator_frame, height=1, bg="gray")
        left_sep.pack(side="left", fill="x", expand=True)

        # Create center + label with cursor change and click binding
        plus_label = tk.Label(separator_frame, text="+", fg="gray", cursor="hand2")
        plus_label.pack(side="left", padx=5)

        def on_plus_click(event):
            # Get the current row number from the separator's grid info
            current_row = separator_frame.grid_info()['row']

            # Get all widgets below the current row and sort them by row number in reverse order
            widgets_below = [(w, w.grid_info()) for w in self.edit_frame.grid_slaves()
                        if w.grid_info()['row'] > current_row]
            widgets_below.sort(key=lambda x: x[1]['row'], reverse=True)

            # Move all widgets below down by the number of rows a new mapping takes
            rows_per_mapping = 4  # Each mapping takes 4 rows (including separator)
            for widget, info in widgets_below:
                new_row = info['row'] + rows_per_mapping
                widget.grid_configure(row=new_row)

            # Save the current row_num
            original_row_num = self.row_num

            # Set row_num to insert the new row
            self.row_num = current_row + 1

            # Add the new row
            self.add_edit_mapping_row()

            # Restore the original row_num plus the added rows
            self.row_num = max(original_row_num + rows_per_mapping, self.row_num)

            # Update the scroll region
            self.edit_frame.update_idletasks()
            self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))

        plus_label.bind("<Button-1>", on_plus_click)

        # Create right line
        right_sep = tk.Frame(separator_frame, height=1, bg="gray")
        right_sep.pack(side="left", fill="x", expand=True)

        self.row_num += 1

        self.edit_frame.update_idletasks()
        self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))

    def add_edit_shortcut_mapping_row(self, shortcut=''):
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
        # Add this line to prevent scroll selection
        shortcut_entry.bind('<MouseWheel>', self.handle_combobox_scroll)

        # Save reference for later
        self.shortcut_rows.append((shortcut_entry, shortcut_key_select))

        # Move to the next row for the separator
        self.row_num += 1

        # Remove + from previous last separator if it exists - Add safety check
        if hasattr(self, 'last_shortcut_separator_frame') and self.last_shortcut_separator_frame.winfo_exists():
            for widget in self.last_shortcut_separator_frame.winfo_children():
                if isinstance(widget, tk.Label) and widget.cget('text') == '+':
                    widget.destroy()
            # Reconfigure the right separator in the previous last frame
            for widget in self.last_shortcut_separator_frame.winfo_children():
                if isinstance(widget, tk.Frame):  # This is a separator line
                    widget.pack_configure(side="left", fill="x", expand=True)

        # Create a frame for the separator with + label
        separator_frame = tk.Frame(self.edit_frame)
        separator_frame.grid(row=self.row_num, column=0, columnspan=4, sticky="we", padx=0, pady=3)
        self.last_shortcut_separator_frame = separator_frame  # Store reference to current separator

        # Create left line
        left_sep = tk.Frame(separator_frame, height=1, bg="gray")
        left_sep.pack(side="left", fill="x", expand=True)

        # Create center + label with cursor change and click binding
        plus_label = tk.Label(separator_frame, text="+", fg="gray", cursor="hand2")
        plus_label.pack(side="left", padx=5)

        def on_plus_click(event):
            # Get the current row number from the separator's grid info
            current_row = separator_frame.grid_info()['row']

            # Get all widgets below the current row and sort them by row number in reverse order
            widgets_below = [(w, w.grid_info()) for w in self.edit_frame.grid_slaves()
                        if w.grid_info()['row'] > current_row]
            widgets_below.sort(key=lambda x: x[1]['row'], reverse=True)

            # Move all widgets below down by the number of rows a new shortcut mapping takes
            rows_per_mapping = 4  # Each shortcut mapping takes 3 rows (including separator)
            for widget, info in widgets_below:
                new_row = info['row'] + rows_per_mapping
                widget.grid_configure(row=new_row)

            # Save the current row_num
            original_row_num = self.row_num

            # Set row_num to insert the new row
            self.row_num = current_row + 1

            # Remove the + from current separator
            for widget in separator_frame.winfo_children():
                if isinstance(widget, tk.Label) and widget.cget('text') == '+':
                    widget.destroy()
            # Reconfigure the separators to be continuous lines
            for widget in separator_frame.winfo_children():
                if isinstance(widget, tk.Frame):  # This is a separator line
                    widget.pack_configure(side="left", fill="x", expand=True)

            # Add the new row
            self.add_edit_shortcut_mapping_row()

            # Restore the original row_num plus the added rows
            self.row_num = max(original_row_num + rows_per_mapping, self.row_num)

            # Update the scroll region
            self.edit_frame.update_idletasks()
            self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))

        plus_label.bind("<Button-1>", on_plus_click)

        # Create right line
        right_sep = tk.Frame(separator_frame, height=1, bg="gray")
        right_sep.pack(side="left", fill="x", expand=True)

        # Only add + button if not a special script
        script_name = self.script_name_entry.get().strip().lower()

        plus_label = tk.Label(separator_frame, text="+", fg="gray", cursor="hand2")
        plus_label.pack(side="left", padx=5)
        plus_label.bind("<Button-1>", on_plus_click)

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
        self.edit_frame.update_idletasks()  # Update frame to get the correct size
        self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))  # Set the scroll region

def main():
    root = tk.Tk()
    app = ScriptManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()