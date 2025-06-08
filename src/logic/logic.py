import os
import winshell
from win32com.client import Dispatch
import keyboard
import time
from pynput import mouse
import win32gui
import win32process
from src.utility.constant import(script_dir, keylist_path)
from src.utility.utils import (active_dir, store_dir, save_pinned_profiles)

class Logic:
    def list_scripts(self):
        # Create a list of all .ahk and .py files
        all_scripts = [f for f in os.listdir(self.SCRIPT_DIR) if f.endswith('.ahk') or f.endswith('.py')]

        # Separate pinned and unpinned profiles
        pinned = [script for script in all_scripts if script in self.pinned_profiles]
        unpinned = [script for script in all_scripts if script not in self.pinned_profiles]

        # Return a combined list with pinned scripts at the top
        self.scripts = pinned + unpinned
        return self.scripts  # Ensure it returns a list of scripts

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

    def cleanup_device_selection_window(self):
        self.device_selection_window.destroy()
        self.device_selection_window = None


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

