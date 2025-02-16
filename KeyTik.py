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

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

# Define the path to the 'Data' directory
data_dir = os.path.join(script_dir, '_internal', 'Data')

current_version = "v1.7.0"

# Define the path to the 'condition.json' file (this path is used before calling load_condition)
if getattr(sys, 'frozen', False):
    condition_path = os.path.join(sys._MEIPASS, "Data", "condition.json")
    dont_show_path = os.path.join(sys._MEIPASS, "Data", "dont_show.json")
else:
    condition_path = os.path.join(data_dir, "condition.json")
    dont_show_path = os.path.join(data_dir, "dont_show.json")

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
    welcome_path = os.path.join(sys._MEIPASS, "Data", "welcome.md")
    changelog_path = os.path.join(sys._MEIPASS, "Data", "changelog.md")
else:
    icon_path = os.path.join(data_dir, "icon.ico")
    pin_path = os.path.join(data_dir, "pin.json")
    icon_unpinned_path = os.path.join(data_dir, "icon_a.png")
    icon_pinned_path = os.path.join(data_dir, "icon_b.png")
    device_list_path = os.path.join(active_dir, "Autohotkey Interception", "shared_device_info.txt")
    device_finder_path = os.path.join(active_dir, "Autohotkey Interception", "find_device.ahk")
    keylist_path = os.path.join(data_dir, "key_list.txt")
    welcome_path = os.path.join(data_dir, "welcome.md")
    changelog_path = os.path.join(data_dir, "changelog.md")

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
        self.sort_order = [True, True, True]
        self.previous_button_text = None  # Initialize this when the class is created, to store button's original text
        self.welcome_condition = self.load_welcome_condition()
        self.check_welcome()

    def load_welcome_condition(self):
        """Load welcomeCondition from the condition.json file."""
        try:
            if os.path.exists(dont_show_path):
                with open(dont_show_path, "r") as f:
                    config = json.load(f)
                    return config.get("welcome_condition", True)  # Default to True if not found
        except Exception as e:
            print(f"Error loading condition file: {e}")
        return True  # Default to True on error

    def save_welcome_condition(self):
        """Save welcomeCondition to the condition.json file."""
        try:
            with open(dont_show_path, "w") as f:
                json.dump({"welcome_condition": self.welcome_condition}, f)
        except Exception as e:
            print(f"Error saving condition file: {e}")

    def check_welcome(self):
        """Check if the welcome window should be shown on startup."""
        if self.welcome_condition:
            self.show_welcome_window()

    def show_welcome_window(self):
        """Display the welcome window with the content of welcome.md."""
        try:
            # Initially load the welcome.md content
            with open(welcome_path, "r") as f:
                md_content = f.read()
                # Convert Markdown to HTML
                html_content = markdown(md_content)
                # Add inline styling for font size and weight
                html_content = html_content.replace(
                    "<p>", "<p style='font-family: Open Sans; font-size: 9px; font-weight: 300; margin: 10px;'>"
                ).replace(
                    "<h1>", "<h1 style='font-family: Open Sans; font-size: 18px; font-weight: 600; margin: 10px;'>"
                ).replace(
                    "<h2>", "<h2 style='font-family: Open Sans; font-size: 11px; font-weight: 500; margin: 10px;'>"
                )
        except FileNotFoundError:
            html_content = """
            <p style='font-family: Open Sans; font-size: 10px; font-weight: 300;'>Welcome file not found!</p>
            """

        welcome_window = tk.Toplevel(self.root)
        welcome_window.title("Readme !")
        welcome_window.geometry("525x290+350+220")
        welcome_window.resizable(False, False)
        welcome_window.iconbitmap(icon_path)
        welcome_window.transient(self.root)

        # Frame to contain the HTMLLabel with a border
        html_frame = tk.Frame(
            welcome_window, width=500, height=230, relief=tk.RIDGE, borderwidth=2
        )
        html_frame.pack(pady=10)
        html_frame.pack_propagate(False)  # Prevent the frame from resizing to fit its content

        # HTMLLabel to display the Markdown content
        html_label = HTMLLabel(
            html_frame,
            html=html_content,
            background="white",
            padx=11,
            pady=11,
            relief=tk.FLAT,
        )
        html_label.pack(fill=tk.BOTH, expand=True)

        # Create a frame for the buttons
        button_frame = tk.Frame(welcome_window)
        button_frame.pack(pady=0)

        # Button actions
        def on_next():
            try:
                # Load changelog.md content after "Next" is pressed
                with open(changelog_path, "r") as f:
                    md_content = f.read()
                    html_content = markdown(md_content)
                    html_content = html_content.replace(
                        "<p>", "<p style='font-family: Open Sans; font-size: 10px; font-weight: 300; margin: 10px;'>"
                    ).replace(
                        "<h1>", "<h1 style='font-family: Open Sans; font-size: 18px; font-weight: 600; margin: 10px;'>"
                    ).replace(
                        "<h2>", "<h2 style='font-family: Open Sans; font-size: 12px; font-weight: 500; margin: 10px;'>"
                    )
                    # Update HTMLLabel with changelog content using the set_html method
                    html_label.set_html(html_content)
                # Change button layout to show "Don't Show Again" and "Close"
                next_button.grid_forget()  # Remove the "Next" button
                dont_show_button.grid(row=0, column=0, padx=50, pady=3)  # Add the "Don't Show Again" button
                close_button.grid(row=0, column=1, padx=50, pady=3)  # Add the "Close" button
            except FileNotFoundError:
                html_label.set_html(
                    "<p style='font-family: Open Sans; font-size: 10px; font-weight: 300;'>Changelog file not found!</p>")

        def on_dont_show_again():
            self.welcome_condition = False
            self.save_welcome_condition()
            welcome_window.destroy()

        def on_close():
            welcome_window.destroy()

        # Initial "Next" button
        next_button = tk.Button(button_frame, text="Next", command=on_next, width=20)
        next_button.grid(row=0, column=0, padx=50, pady=3)

        # Placeholder for the "Don't Show Again" and "Close" buttons (initially hidden)
        dont_show_button = tk.Button(button_frame, text="Don't Show Again", command=on_dont_show_again, width=20)
        close_button = tk.Button(button_frame, text="Close", command=on_close, width=20)

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

        self.setting_button = tk.Button(self.frame, text="Setting", width=8, command=self.open_settings_window)
        self.setting_button.place(relx=0.85, rely=0.907)  # Adjust placement as needed

        # Center the action_container by expanding the column in its parent frame
        action_container.grid_columnconfigure(0, weight=1)  # Centering by expanding space equally
        action_container.grid_columnconfigure(1, weight=1)

    def open_settings_window(self):
        """Open a settings window with a frame containing 5 buttons arranged in a grid."""
        # Create a new top-level window
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300+400+225")  # Adjust size as needed
        settings_window.resizable(False, False)
        settings_window.configure(padx=10, pady=10)  # Padding around the window
        settings_window.iconbitmap(icon_path)
        settings_window.transient(self.root)

        # Create a LabelFrame inside the settings window
        frame = tk.LabelFrame(settings_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)  # Padding for the LabelFrame

        change_path_button = tk.Button(frame, text="Change Profile Location", command=self.change_data_location, height=2, width=20)
        change_path_button.grid(row=0, column=0, padx=5, pady=5)

        check_update_button = tk.Button(frame, text="Check For Update", command=lambda: self.check_for_update(), height=2, width=20)
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

    def check_for_update(self):
        """Check for updates by comparing the current version with the latest release on GitHub."""
        try:
            # Make a GET request to GitHub API to get the latest release information
            response = requests.get("https://api.github.com/repos/Fajar-RahmadJaya/KeyTik/releases/latest")
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data["tag_name"]  # Extract the version from the JSON response

                if current_version == latest_version:
                    # If the versions match, show up-to-date message
                    messagebox.showinfo("Check For Update", "You are using the latest version of KeyTik.")
                else:
                    # If the versions don't match, show a message that a new update is available
                    messagebox.showinfo("Check For Update", f"New update available: KeyTik {latest_version}")
            else:
                messagebox.showerror("Error", "Failed to check for updates. Please try again later.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

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
        """Prompts the user for a new name and copies the script to the active directory."""
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

            # Refresh the UI
            self.update_script_list()
        except Exception as e:
            print(f"Error copying script: {e}")

    def toggle_run_exit(self, script_name, button):
        """Toggle between running and exiting the script."""
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
        """Activate the given .ahk script."""
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):
            # Start the script
            os.startfile(script_path)

            # Update button state dynamically
            button.config(text="Exit", command=lambda: self.toggle_run_exit(script_name, button))
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def exit_script(self, script_name, button):
        """Exit the given .ahk script."""
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):
            # Simulate pressing Ctrl+Alt+P to exit the AHK script
            keyboard = Controller()

            keyboard.press(Key.ctrl)
            keyboard.press(Key.alt)
            keyboard.press('p')
            keyboard.release('p')
            keyboard.release(Key.alt)
            keyboard.release(Key.ctrl)

            # Update button state dynamically
            button.config(text="Run", command=lambda: self.toggle_run_exit(script_name, button))
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

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
            vid_pid = device[3]  # Use Handle instead

            entry.delete(0, tk.END)  # Clear the entry
            entry.insert(0, f"{device_type}, {vid_pid}")

            # Close the device selection window
            window.destroy()

    def open_device_selection(self):
        """Open a new window to select a device and update the Keyboard_entry field."""
        device_selection_window = tk.Toplevel(self.create_profile_window)
        device_selection_window.geometry("600x300+308+233")
        device_selection_window.title("Select Device")
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

    def show_tooltip(self, event, tooltip_text):
        """Show a tooltip near the cursor."""
        self.tooltip = tk.Toplevel()
        self.tooltip.wm_overrideredirect(True)  # Remove window decorations
        self.tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")  # Position near the cursor

        # Create a label for the tooltip
        label = tk.Label(self.tooltip, text=tooltip_text, bg="white", fg="black",
                         relief="solid", borderwidth=1, padx=5, pady=3, justify="left")
        label.pack()

    def hide_tooltip(self, event):
        """Hide the tooltip."""
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
        select_window = tk.Toplevel(self.root)
        select_window.title("Select Programs")
        select_window.geometry("600x300+308+217")  # Set initial size (width x height)
        select_window.iconbitmap(icon_path)
        select_window.transient(self.create_profile_window)

        # Frame to hold Treeview and scrollbar
        treeview_frame = tk.Frame(select_window)
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
            select_window.destroy()

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
        button_frame = tk.Frame(select_window)
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
            self.previous_button_text = button.cget("text")

            # Disable user input by binding an empty function to all entries
            self.disable_entry_input(self.key_rows)  # Disable both original and remap entries
            self.disable_entry_input([(self.script_name_entry, None)])  # Disable script name entry
            self.disable_entry_input([(self.shortcut_entry, None)])  # Enable script name entry
            self.disable_entry_input([(self.keyboard_entry, None)])  # Enable script name entry
            self.disable_entry_input([(self.program_entry, None)])  # Enable script name entry

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
            self.enable_entry_input([(self.program_entry, None)])  # Enable script name entry

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
        """Create the .ahk script file based on user input."""
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
        """Generate the program condition for the #HotIf line."""
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
        """Generate the device condition for the #HotIf line."""
        device_condition = ""
        device_name = self.keyboard_entry.get().strip()  # Retrieve device info from the entry
        if device_name:
            device_condition = f"cm1.IsActive"  # Modify this if needed to generate the correct condition
        return device_condition

    def handle_text_mode(self, file, key_translations, program_condition, shortcuts_present, device_condition):
        """Handle the text mode logic."""
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
        """Handle the default mode logic (key remapping)."""
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
        """Process and write the shortcut toggle functionality."""
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
        """Process the script name and ensure it has the correct file extension."""
        script_name = self.script_name_entry.get().strip()
        if not script_name:
            messagebox.showwarning("Input Error", "Please enter a Profile name.")
            return None

        if not script_name.endswith('.ahk'):
            script_name += '.ahk'

        return script_name

    def write_first_line(self, file):
        """Write the first line based on the mode (Text or Default)."""
        if self.is_text_mode:
            file.write("; text\n")
        else:
            file.write("; default\n")
        file.write("^!p::ExitApp \n\n#SingleInstance Force\n")

    def handle_device(self, file):
        """Handle the device type (mouse or keyboard) and its identifier."""
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
        """Generate the device code for vid/pid format."""
        return f"""#SingleInstance force
Persistent
#include AutoHotkey Interception\Lib\AutoHotInterception.ahk

AHI := AutoHotInterception()
id1 := AHI.GetDeviceId({str(is_mouse).lower()}, {vid}, {pid})
cm1 := AHI.CreateContextManager(id1)

#HotIf cm1.IsActive
"""

    def generate_device_code_from_handle(self, is_mouse, handle):
        """Generate the device code for handle format."""
        return f"""#SingleInstance force
Persistent
#include AutoHotkey Interception\Lib\AutoHotInterception.ahk

AHI := AutoHotInterception()
id1 := AHI.GetDeviceIdFromHandle({str(is_mouse).lower()}, "{handle}")
cm1 := AHI.CreateContextManager(id1)

#HotIf cm1.IsActive
"""

    def process_key_remaps(self, file, key_translations):
        """Process and write the key remaps."""
        for row in self.key_rows:
            if len(row) == 4:
                original_key_entry, remap_key_entry, original_key_select, remap_key_select = row
                try:
                    original_key = original_key_entry.get().strip()
                    remap_key = remap_key_entry.get().strip()

                    if original_key and remap_key:
                        original_key = self.translate_key(original_key, key_translations)
                        if remap_key.startswith('"') and remap_key.endswith('"'):
                            file.write(f'{original_key}::SendText({remap_key})\n')
                        elif "+" in remap_key:
                            keys = [key.strip() for key in remap_key.split("+")]
                            key_down = "".join([f"{{{key} down}}" for key in keys])
                            key_up = "".join([f"{{{key} up}}" for key in reversed(keys)])
                            file.write(f'{original_key}::Send("{key_down}{key_up}")\n')
                        else:
                            remap_key = self.translate_key(remap_key, key_translations)
                            file.write(f'{original_key}::{remap_key}\n')
                except TclError:
                    continue

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
        device_selection_window.title("Select Device")
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
            program_entry.insert(0, "  ")
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

                for line in lines[3:]:  # Skip the header lines
                    line = line.strip()  # Clean whitespace
                    if not line or line.startswith(";"):  # Skip empty lines and comments
                        continue

                    if line.startswith("#HotIf"):
                        in_hotif_block = not in_hotif_block
                        continue

                    if "::" in line:
                        # Split the line into key parts
                        parts = line.split("::")
                        original_key = parts[0].strip()
                        remap_or_action = parts[1].strip() if len(parts) > 1 else ""

                        # Process original key
                        original_key = self.replace_raw_keys(original_key, key_map).replace("~", "").replace(" & ", "+")

                        if remap_or_action:  # Remap case
                            if remap_or_action.startswith('SendText'):
                                # Extract the text from SendText
                                text = remap_or_action[len("SendText("):-1]  # Remove the 'SendText(' and ')'
                                remap_key = f'{text}'  # Format as "text" (no extra quotes)

                            elif remap_or_action.startswith('Send'):
                                # Extract the keys from Send command
                                key_sequence = remap_or_action[len("Send("):-1]  # Remove the 'Send(' and ')'
                                keys = []

                                # Find the individual keys and construct the key combination (key1 + key2 format)
                                import re
                                matches = re.findall(r'{(.*?)( down| up)}', key_sequence)
                                if matches:
                                    # Extract just the key names and remove duplicates using set
                                    keys = list(set(match[0] for match in matches))  # Remove duplicates
                                    remap_key = " + ".join(keys)  # Join the keys with ' + '
                                else:
                                    remap_key = remap_or_action  # Default, just use the original action

                            else:
                                remap_key = remap_or_action  # If it's just a regular remap

                            # Now insert the processed values into the remap
                            remaps.append((original_key, remap_key))

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

    def edit_open_select_program_window(self, entry_widget):
        select_window = tk.Toplevel(self.root)
        select_window.title("Select Programs")
        select_window.geometry("600x300+308+217")  # Set initial size (width x height)
        select_window.iconbitmap(icon_path)
        select_window.transient(self.edit_window)

        # Frame to hold Treeview and scrollbar
        treeview_frame = tk.Frame(select_window)
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
            select_window.destroy()

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
        button_frame = tk.Frame(select_window)
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
        """Create the .ahk script file based on user input."""
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
                self.edit_window.destroy()

        except Exception as e:
            print(f"Error writing script: {e}")

def main():
    root = tk.Tk()
    app = ScriptManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
