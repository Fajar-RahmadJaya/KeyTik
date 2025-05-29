import os
import shutil
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QPushButton, QGroupBox, QFileDialog, QMessageBox, 
    QInputDialog, QSizePolicy
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt
from pynput.keyboard import Controller, Key
import sys
import winshell
import json
from src.utility.constant import (icon_unpinned_path, icon_pinned_path, 
                                  icon_path, exit_keys_file)
from src.utility.utils import (load_pinned_profiles, active_dir, store_dir,
                               save_pinned_profiles)
from src.logic.logic import logic
from src.ui.edit_frame_row import edit_frame_row
from src.ui.edit_script import EditScript
from src.ui.edit_script_logic import EditScriptLogic
from src.ui.edit_script_save import EditScriptSave

from src.ui.setting_window import setting_window
from src.ui.welcome_window import welcome_window

class MainApp(QMainWindow, logic, edit_frame_row, EditScript,
           setting_window, welcome_window, 
           EditScriptLogic, EditScriptSave):
    def __init__(self):
        super().__init__()
        self.first_load = True
        self.welcome_condition = self.load_welcome_condition()
        self.setWindowTitle("KeyTik Pro")
        self.setGeometry(284, 97, 650, 492)
        self.current_page = 0
        self.SCRIPT_DIR = active_dir
        self.pinned_profiles = load_pinned_profiles()
        self.icon_unpinned = QPixmap(icon_unpinned_path).scaled(14, 14)
        self.icon_pinned = QPixmap(icon_pinned_path).scaled(14, 14)
        self.scripts = self.list_scripts()
        self.device_selection_window = None
        self.select_program_window = None
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
        self.pressed_keys = []
        self.last_key_time = 0
        self.timeout = 1
        self.mouse_listener = None
        self.ignore_next_click = False
        self.shortcut_entry = None
        self.sort_order = [True, True, True]
        self.previous_button_text = None
        self.setWindowIcon(QIcon(icon_path))
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.check_for_update(show_no_update_message=False)
        self.initialize_exit_keys()
        self.welcome_condition = self.load_welcome_condition()
        self.check_ahk_installation(show_installed_message=False)
        # self.check_welcome()  # Moved to main()
        self.create_ui()
        self.update_script_list()

    def create_ui(self):
        # Main vertical layout
        self.frame = QFrame()
        self.main_layout.addWidget(self.frame)
        self.frame_layout = QVBoxLayout(self.frame)

        # Script frame (grid)
        self.script_frame = QFrame()
        self.script_grid = QGridLayout(self.script_frame)
        self.frame_layout.addWidget(self.script_frame)

        # Navigation buttons
        nav_frame = QFrame()
        nav_layout = QHBoxLayout(nav_frame)
        self.prev_button = QPushButton("Previous")
        self.prev_button.setFixedWidth(120)
        self.prev_button.clicked.connect(self.prev_page)
        nav_layout.addWidget(self.prev_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.next_button = QPushButton("Next")
        self.next_button.setFixedWidth(120)
        self.next_button.clicked.connect(self.next_page)
        nav_layout.addWidget(self.next_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.frame_layout.addWidget(nav_frame)

        # Action buttons
        action_container = QFrame()
        action_layout = QGridLayout(action_container)
        self.create_button = QPushButton("Create New Profile")
        self.create_button.setFixedWidth(180)
        self.create_button.clicked.connect(lambda: self.edit_script(None))  # Pass None for new profile
        action_layout.addWidget(self.create_button, 0, 0)
        self.import_button = QPushButton("Import Profile")
        self.import_button.setFixedWidth(180)
        self.import_button.clicked.connect(self.import_button_clicked)
        action_layout.addWidget(self.import_button, 0, 1)
        self.always_top = QPushButton("Always On Top")
        self.always_top.setFixedWidth(180)
        self.always_top.clicked.connect(self.toggle_on_top)
        action_layout.addWidget(self.always_top, 1, 1)
        self.show_stored = QPushButton("Show Stored Profile")
        self.show_stored.setFixedWidth(180)
        self.show_stored.clicked.connect(self.toggle_script_dir)
        action_layout.addWidget(self.show_stored, 1, 0)
        self.setting_button = QPushButton("Setting")
        self.setting_button.setFixedWidth(100)
        self.setting_button.clicked.connect(self.open_settings_window)
        self.frame_layout.addWidget(action_container)
        self.setting_button.move(550, 450)  # Approximate placement

        # Add setting button to main layout (bottom right)
        self.main_layout.addWidget(self.setting_button, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

    def update_script_list(self):
        # Clear previous widgets
        for i in reversed(range(self.script_grid.count())):
            widget = self.script_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        start_index = self.current_page * 6
        end_index = start_index + 6
        scripts_to_display = self.scripts[start_index:end_index]

        for index, script in enumerate(scripts_to_display):
            row = index // 2
            column = index % 2
            icon = self.icon_pinned if script in self.pinned_profiles else self.icon_unpinned

            group_box = QGroupBox(os.path.splitext(script)[0])
            group_layout = QGridLayout(group_box)

            icon_label = QLabel(group_box)  # set the group_box as parent for absolute positioning
            icon_label.setPixmap(icon)
            icon_label.setFixedSize(18, 18)
            icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
            icon_label.mousePressEvent = lambda event, s=script, l=icon_label: self.toggle_pin(s, l)
            icon_label.move(281, 2)  # adjust x, y to fit visually

            run_button = QPushButton("Run")
            run_button.setFixedWidth(80)
            run_button.clicked.connect(lambda checked, s=script, b=run_button: self.toggle_run_exit(s, b))
            group_layout.addWidget(run_button, 0, 0)

            edit_button = QPushButton("Edit")
            edit_button.setFixedWidth(80)
            edit_button.clicked.connect(lambda checked, s=script: self.edit_script(s))
            group_layout.addWidget(edit_button, 0, 1)

            copy_button = QPushButton("Copy")
            copy_button.setFixedWidth(80)
            copy_button.clicked.connect(lambda checked, s=script: self.copy_script(s))
            group_layout.addWidget(copy_button, 1, 0)

            delete_button = QPushButton("Delete")
            delete_button.setFixedWidth(80)
            delete_button.clicked.connect(lambda checked, s=script: self.delete_script(s))
            group_layout.addWidget(delete_button, 1, 2)

            store_button = QPushButton("Store" if self.SCRIPT_DIR == active_dir else "Restore")
            store_button.setFixedWidth(80)
            store_button.clicked.connect(lambda checked, s=script: self.store_script(s))
            group_layout.addWidget(store_button, 1, 1)

            # Startup/Unstart button
            shortcut_name = os.path.splitext(script)[0] + ".lnk"
            startup_folder = winshell.startup()
            shortcut_path = os.path.join(startup_folder, shortcut_name)
            if os.path.exists(shortcut_path):
                startup_button = QPushButton("Unstart")
                startup_button.clicked.connect(lambda checked, s=script: self.remove_ahk_from_startup(s))
            else:
                startup_button = QPushButton("Startup")
                startup_button.clicked.connect(lambda checked, s=script: self.add_ahk_to_startup(s))
            startup_button.setFixedWidth(80)
            group_layout.addWidget(startup_button, 0, 2)

            self.script_grid.addWidget(group_box, row, column)

        # Add empty widgets to fill up to 6 cells
        total_cells = 6
        for i in range(len(scripts_to_display), total_cells):
            row = i // 2
            column = i % 2
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.script_grid.addWidget(spacer, row, column)

    # --- Dialog and file picker replacements ---
    def import_button_clicked(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("AHK Scripts (*.ahk)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                selected_file = selected_files[0]
                if not selected_file.endswith('.ahk'):
                    QMessageBox.warning(self, "Error", "Only .ahk files are allowed.")
                    return
                file_name = os.path.basename(selected_file)
                destination_path = os.path.join(self.SCRIPT_DIR, file_name)
                try:
                    shutil.move(selected_file, destination_path)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to move file: {e}")
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

    def copy_script(self, script):
        new_name, ok = QInputDialog.getText(self, "Copy Script", "Enter the new script name:")
        if not ok or not new_name:
            return
        if not new_name.lower().endswith('.ahk'):
            new_name += '.ahk'
        source_path = os.path.join(self.SCRIPT_DIR, script)
        destination_path = os.path.join(self.SCRIPT_DIR, new_name)
        try:
            shutil.copy(source_path, destination_path)
            self.scripts = self.list_scripts()
            self.update_script_list()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error copying script: {e}")

    def delete_script(self, script_name):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)
        if os.path.isfile(script_path):
            try:
                os.remove(script_path)
                self.scripts = self.list_scripts()
                self.update_script_list()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete the script: {e}")
        else:
            QMessageBox.warning(self, "Error", f"{script_name} does not exist.")

    def toggle_on_top(self):
        self.is_on_top = not self.is_on_top
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.is_on_top)
        self.show()
        self.setWindowTitle(f"KeyTik{' (Always on Top)' if self.is_on_top else ''}")
        self.always_top.setText("Disable Always on Top" if self.is_on_top else "Enable Always on Top")
        # Apply Always on Top & Icon Fix to all relevant windows
        parent_window = self.create_profile_window or self.edit_window
        self.set_on_top(self.create_profile_window, "Create New Profile", parent_window)
        self.set_on_top(self.edit_window, "Edit Profile", parent_window)
        self.set_on_top(self.device_selection_window, "Select Device", parent_window)
        self.set_on_top(self.select_program_window, "Select Program", parent_window)

    def set_on_top(self, window, title, parent=None):
        if window is not None and window.isVisible():
            try:
                if parent:
                    window.setWindowModality(Qt.WindowModality.ApplicationModal)
                else:
                    window.setWindowModality(Qt.WindowModality.NonModal)

                window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.is_on_top)
                title_suffix = " (Always on Top)" if self.is_on_top else ""
                window.setWindowTitle(f"{title}{title_suffix}")

                # Fix disappearing icon by reapplying it here
                window.setWindowIcon(QIcon(icon_path))

            except Exception as e:
                print(f"Error: Unable to set always-on-top for {title} window. {e}")

    def activate_script(self, script_name, button):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):
            # Start the script
            os.startfile(script_path)

            # Update button state dynamically
            button.setText("Exit")
            button.clicked.disconnect()
            button.clicked.connect(lambda: self.exit_script(script_name, button))
        else:
            QMessageBox.critical(self, "Error", f"{script_name} does not exist.")

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
                    QMessageBox.critical(self, "Error", f"No exit key found for {script_name}")
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
                button.setText("Run")
                button.clicked.disconnect()
                button.clicked.connect(lambda: self.activate_script(script_name, button))

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to exit script: {e}")
        else:
            QMessageBox.critical(self, "Error", f"{script_name} does not exist.")

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
                QMessageBox.critical(self, "Error", f"Failed to move the script: {e}")
        else:
            QMessageBox.critical(self, "Error", f"{script_name} does not exist.")

    def toggle_run_exit(self, script_name, button):
        if button.text() == "Run":
            # Start the script
            self.activate_script(script_name, button)
            # Change button to Exit after script is running
            button.setText("Exit")
            button.clicked.disconnect()
            button.clicked.connect(lambda checked=False: self.toggle_run_exit(script_name, button))
        else:
            # Exit the script
            self.exit_script(script_name, button)
            # Change button to Run after script has exited
            button.setText("Run")
            button.clicked.disconnect()
            button.clicked.connect(lambda checked=False: self.toggle_run_exit(script_name, button))

    def toggle_script_dir(self):
        # Toggle between 'Active' and 'Store' directories
        if self.SCRIPT_DIR == active_dir:
            self.SCRIPT_DIR = store_dir
            self.show_stored.setText("Show Active Profile")
        else:
            self.SCRIPT_DIR = active_dir
            self.show_stored.setText("Show Stored Profile")

        # Refresh the script list based on the new SCRIPT_DIR
        self.list_scripts()
        self.update_script_list()

    def toggle_pin(self, script, icon_label):
        if script in self.pinned_profiles:
            # Unpin the script
            self.pinned_profiles.remove(script)
            icon_label.setPixmap(self.icon_unpinned)  # ✅ correct method
        else:
            # Pin the script
            self.pinned_profiles.insert(0, script)
            icon_label.setPixmap(self.icon_pinned)  # ✅ correct method

        # Save the updated pinned profiles and refresh the display
        save_pinned_profiles(self.pinned_profiles)
        self.list_scripts()
        self.update_script_list()

    def show_welcome_window(self):
        # Just call the method to show the welcome dialog
        # Do not assign to self.device_selection_window or call setAttribute/show on welcome_window
        try:
            welcome_window.show_welcome_window(self)
        except Exception as e:
            print(f"Error displaying welcome window: {e}")

def main():
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    # Show welcome window after main window is visible, but only if enabled
    if main_window.welcome_condition:
        main_window.show_welcome_window()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()