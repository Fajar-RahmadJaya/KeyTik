import os
import shutil
import tkinter as tk
from tkinter import messagebox
from pynput.keyboard import Controller, Key
import subprocess
import sys
import winshell
from win32com.client import Dispatch

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

# Build the path to the icon file
if getattr(sys, 'frozen', False):  # Check if the script is running as a bundled executable
    icon_path = os.path.join(sys._MEIPASS, '_internal', "Data", "icon.ico")  # Path for the bundled executable
else:
    icon_path = os.path.join(data_dir, "icon.ico")  # Path for the script

# Build the path to the icon file
if getattr(sys, 'frozen', False):  # Check if the script is running as a bundled executable
    queicon_path = os.path.join(sys._MEIPASS, '_internal', "Data", "que.ico")  # Path for the bundled executable
else:
    queicon_path = os.path.join(data_dir, "que.ico")  # Path for the script

class ScriptManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("650x500+284+97")  # Set initial size (width x height)
        self.root.title("KeyTik")
        self.current_page = 0
        self.SCRIPT_DIR = active_dir 
        self.scripts = self.list_scripts()
        self.frames = []
        self.root.iconbitmap(icon_path)
        self.root.resizable(False, False)
        self.create_ui()
        self.update_script_list()
        self.key_rows = []
        self.is_on_top = False
        self.create_profile_window = None
        self.edit_window = None

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
        """List all .ahk files in the active directory."""
        self.scripts = [f for f in os.listdir(self.SCRIPT_DIR) if f.endswith('.ahk')]
        return self.scripts  # Ensure a list is returned

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

            frame = tk.LabelFrame(self.script_frame, text=os.path.splitext(script)[0], padx=10, pady=10)
            frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

            run_button = tk.Button(frame, text="Run", width=10, height=1)
            run_button.grid(row=0, column=0, padx=2, pady=5)

            exit_button = tk.Button(frame, text="Exit", state="disabled", width=10, height=1)
            exit_button.grid(row=0, column=1, padx=5, pady=5)

            run_button.config(command=lambda s=script, rb=run_button, eb=exit_button: self.activate_script(s, rb, eb))
            exit_button.config(command=lambda s=script, rb=run_button, eb=exit_button: self.exit_script(s, rb, eb))

            delete_button = tk.Button(frame, text="Delete", command=lambda s=script: self.delete_script(s), width=10, height=1)
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

        self.prev_button['state'] = tk.NORMAL if self.current_page > 0 else tk.DISABLED
        self.next_button['state'] = tk.NORMAL if end_index < len(self.scripts) else tk.DISABLED

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
        os.startfile(script_path)
        run_button.config(state='disabled')
        exit_button.config(state='normal')

    def exit_script(self, script_name, run_button, exit_button):
        """Exit the given .ahk script by sending the exit key combination (Ctrl+Alt+P)."""
        # Check if the script file exists
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


        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

        exit_button.config(state='disabled')
        run_button.config(state='normal')

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

    def create_new_profile(self):
        """Create a new AutoHotkey script based on user input."""
        self.create_profile_window = tk.Toplevel(self.root)
        self.create_profile_window.geometry("600x450+295+111")  # Set initial size (width x height)
        self.create_profile_window.title("Create New Profile")
        self.create_profile_window.iconbitmap(icon_path)

        # Set the window as a transient of the root
        self.create_profile_window.transient(self.root)

        # Input for script name
        self.script_name_label = tk.Label(self.create_profile_window, text="Script Name:")
        self.script_name_label.place(relx=0.2, rely=0.062, height=21, width=104)
        self.script_name_entry = tk.Entry(self.create_profile_window)
        self.script_name_entry.place(relx=0.383, rely=0.067, height=20, relwidth=0.557)

        # Scrollable canvas for key mappings
        self.canvas = tk.Canvas(self.create_profile_window)
        self.canvas.place(relx=0.067, rely=0.178, relheight=0.678, relwidth=0.875)
        self.canvas.configure(borderwidth="2")
        self.canvas.configure(relief="ridge")
     

        # Scrollbar for the canvas
        self.scrollbar = tk.Scrollbar(self.create_profile_window, orient="vertical", command=self.canvas.yview)
        self.scrollbar.place(relx=0.942, rely=0.178, relheight=0.678, width=20)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Frame inside the canvas to hold the key mapping entries
        self.key_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.key_frame, anchor='nw')

        # Add initial key mapping row
        self.key_rows = []
        self.add_key_mapping_row()

        # Buttons
        self.continue_button = tk.Button(self.create_profile_window, text="Add Another Row", command=self.add_key_mapping_row)
        self.continue_button.place(relx=0.760, rely=0.889, height=26, width=107)

        self.finish_button = tk.Button(self.create_profile_window, text="Finish", command=self.finish_profile)
        self.finish_button.place(relx=0.070, rely=0.889, height=26, width=107)

        self.text_button = tk.Button(self.create_profile_window, text="Text Mode", command=self.finish_profile)
        self.text_button.place(relx=0.415, rely=0.889, height=26, width=107)

        self.default_key_label = tk.Label(self.key_frame, text="Default Key")
        self.default_key_label.grid(row=0, column=0, padx=100, pady=5)

        self.remap_key_label = tk.Label(self.key_frame, text="Remap Key")
        self.remap_key_label.grid(row=0, column=1, padx=80, pady=5)

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def add_key_mapping_row(self):
        """Add a new row for key mapping inputs dynamically."""
        row_num = len(self.key_rows) + 1  # Start from the next row
        original_key_entry = tk.Entry(self.key_frame, width=35,justify='center')
        original_key_entry.grid(row=row_num, column=0, padx=10, pady=10)

        remap_key_entry = tk.Entry(self.key_frame,width=35,justify='center')
        remap_key_entry.grid(row=row_num, column=1, padx=10, pady=10)

        self.key_rows.append((original_key_entry, remap_key_entry))

        # Update the scrollable region of the canvas
        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def finish_profile(self):
        """Create the .ahk script file based on the key mappings."""
        script_name = self.script_name_entry.get().strip()
        if not script_name:
            messagebox.showwarning("Input Error", "Please enter a script name.")
            return

        if not script_name.endswith('.ahk'):
            script_name += '.ahk'
        output_path = os.path.join(self.SCRIPT_DIR, script_name)

        with open(output_path, 'w') as file:
            file.write("; AutoHotkey Remap Script\n\n")
            file.write("^!p::  ; This means Ctrl+Alt+P\nExitApp  ; This command exits the AHK script\n\n")

            for original_key_entry, remap_key_entry in self.key_rows:
                original_key = original_key_entry.get().strip()
                remap_key = remap_key_entry.get().strip()
                if original_key and remap_key:
                    file.write(f"{original_key}::{remap_key}\n")


        self.scripts = self.list_scripts()
        self.update_script_list()
        self.create_profile_window.destroy()

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

    def edit_script(self, script_name):
        """Open the given .ahk script in an editable UI for modifying key mappings."""
        script_path = os.path.join(self.SCRIPT_DIR, script_name)
        if os.path.isfile(script_path):
            # Read the existing script content
            with open(script_path, 'r') as file:
                lines = file.readlines()
    
            # Create a new window for editing the script
            self.edit_window = tk.Toplevel(self.root)
            self.edit_window.geometry("600x450+295+111")
            self.edit_window.title("Edit Profile")
            self.edit_window.iconbitmap(icon_path)
    
            # Set the window as a transient of the root
            self.edit_window.transient(self.root)
    
            # Input for script name (read-only)
            script_name_label = tk.Label(self.edit_window, text="Script Name:")
            script_name_label.place(relx=0.2, rely=0.062, height=21, width=104)
    
            script_name_entry = tk.Entry(self.edit_window)
            script_name_without_extension = script_name.replace('.ahk', '')
            script_name_entry.insert(0, script_name_without_extension)
            script_name_entry.config(state='readonly')
            script_name_entry.place(relx=0.383, rely=0.067, height=20, relwidth=0.557)
    
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
    
            # Add existing key mappings
            self.key_rows = []
            for line in lines[3:]:  # Skip the header lines
                if "::" in line:
                    original_key, remap_key = line.split("::")
                    self.add_editable_key_mapping_row(original_key.strip(), remap_key.strip())
    
            # Button to add another row
            add_row_button = tk.Button(self.edit_window, text="Add Another Row", command=self.add_editable_key_mapping_row)
            add_row_button.place(relx=0.733, rely=0.889, height=26, width=107)
    
            # Button to save changes
            save_button = tk.Button(self.edit_window, text="Save Changes", command=lambda: self.save_changes(script_name))
            save_button.place(relx=0.067, rely=0.889, height=26, width=107)
    
            # Update the scrollable region of the canvas
            self.update_scroll_region()
    
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")
    
    def add_editable_key_mapping_row(self, original_key='', remap_key=''):
        """Add a new row for editing key mappings."""
        row_num = len(self.key_rows)  # Start from the next row
        original_key_entry = tk.Entry(self.edit_frame, width=35, justify='center')
        original_key_entry.grid(row=row_num, column=0, padx=10, pady=10)
        original_key_entry.insert(0, original_key)
    
        remap_key_entry = tk.Entry(self.edit_frame, width=35, justify='center')
        remap_key_entry.grid(row=row_num, column=1, padx=10, pady=10)
        remap_key_entry.insert(0, remap_key)
    
        self.key_rows.append((original_key_entry, remap_key_entry))
    
        # Update the scrollable region after adding a row
        self.update_scroll_region()
    
    def update_scroll_region(self):
        """Update the scroll region of the canvas to encompass all content."""
        self.edit_frame.update_idletasks()  # Update frame to get the correct size
        self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))  # Set the scroll region
    
    def save_changes(self, script_name):
        """Save the edited key mappings back to the .ahk script file."""
        script_path = os.path.join(self.SCRIPT_DIR, script_name)
        
        with open(script_path, 'w') as file:
            file.write("; AutoHotkey Remap Script\n\n")
            file.write("^!p::  ; This means Ctrl+Alt+P\nExitApp  ; This command exits the AHK script\n\n")
    
            for original_key_entry, remap_key_entry in self.key_rows:
                original_key = original_key_entry.get().strip()
                remap_key = remap_key_entry.get().strip()
                if original_key and remap_key:
                    file.write(f"{original_key}::{remap_key}\n")
    
        self.edit_window.destroy()
        self.scripts = self.list_scripts()
        self.update_script_list()

def main():
    root = tk.Tk()
    app = ScriptManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
