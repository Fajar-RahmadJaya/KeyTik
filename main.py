import os
import shutil
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QPushButton, QGroupBox, QFileDialog, QMessageBox, 
    QInputDialog, QSizePolicy
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QThread, Signal  # add QThread, Signal
from pynput.keyboard import Controller, Key
import sys
import winshell
import json
import shutil
from src.utility.constant import (icon_unpinned_path, icon_pinned_path, 
                                  icon_path, exit_keys_file)
from src.utility.utils import (load_pinned_profiles, active_dir, store_dir,
                               save_pinned_profiles, read_running_scripts_temp,
                               add_script_to_temp, remove_script_from_temp)
from src.logic.logic import Logic
from src.ui.setting import Setting
from src.ui.welcome import Welcome
from src.ui.edit_script.edit_script_main import EditScriptMain
from src.ui.edit_script.select_program import SelectProgram
from src.ui.edit_script.select_device import SelectDevice
from src.ui.edit_script.edit_frame_row import EditFrameRow
from src.ui.edit_script.edit_script_logic import EditScriptLogic
from src.ui.edit_script.edit_script_save import EditScriptSave

class StartupWorker(QThread):
    finished = Signal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def run(self):
        # Run the startup checks
        self.main_window.initialize_exit_keys()
        self.main_window.check_ahk_installation(show_installed_message=False)
        self.main_window.check_for_update(show_no_update_message=False)
        self.finished.emit()

class MainApp(QMainWindow, Logic, EditFrameRow, EditScriptMain,
           Setting, Welcome, SelectProgram, SelectDevice,
           EditScriptLogic, EditScriptSave):
    def __init__(self):
        super().__init__()
        # Global variables
        self.first_load = True
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

        # UI initialization
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.current_page = 0
        self.SCRIPT_DIR = active_dir
        self.pinned_profiles = load_pinned_profiles()
        self.icon_unpinned = QPixmap(icon_unpinned_path).scaled(14, 14)
        self.icon_pinned = QPixmap(icon_pinned_path).scaled(14, 14)
        self.scripts = self.list_scripts()
        self.create_ui()
        self.update_script_list()
        self.setWindowTitle("KeyTik")
        self.setGeometry(284, 97, 650, 492)
        self.setWindowIcon(QIcon(icon_path))
        self.setCentralWidget(self.central_widget)
        self.welcome_condition = self.load_welcome_condition()

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

        running_scripts = read_running_scripts_temp()

        for index, script in enumerate(scripts_to_display):
            row = index // 2
            column = index % 2
            icon = self.icon_pinned if script in self.pinned_profiles else self.icon_unpinned

            group_box = QGroupBox(os.path.splitext(script)[0])
            group_layout = QGridLayout(group_box)

            icon_label = QLabel(group_box)
            icon_label.setPixmap(icon)
            icon_label.setFixedSize(18, 18)
            icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
            icon_label.mousePressEvent = lambda event, s=script, l=icon_label: self.toggle_pin(s, l)
            icon_label.move(281, 2)

            run_button = QPushButton()
            run_button.setFixedWidth(80)

            shortcut_name = os.path.splitext(script)[0] + ".lnk"
            startup_folder = winshell.startup()
            shortcut_path = os.path.join(startup_folder, shortcut_name)
            is_startup = os.path.exists(shortcut_path)

            # If script is in startup, always show Exit
            if is_startup or script in running_scripts:
                run_button.setText("Exit")
            else:
                run_button.setText("Run")
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
            if is_startup:
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

        # Ensure both columns have equal width
        self.script_grid.setColumnStretch(0, 1)
        self.script_grid.setColumnStretch(1, 1)

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
                try:
                    exit_key = self.generate_exit_key(file_name)
                    with open(destination_path, 'r', encoding='utf-8') as file:
                        lines = file.readlines()
                    # 1. Remove any line with ::ExitApp
                    lines = [line for line in lines if "::ExitApp" not in line]
                    # 2. Check first line for ; text or ; default
                    first_line = lines[0].strip() if lines else ""
                    has_text_or_default = first_line.startswith("; text") or first_line.startswith("; default")
                    new_lines = []
                    if not has_text_or_default:
                        # 3. Add ; default or ; text as needed
                        if first_line and '::' in first_line:
                            new_lines = [
                                "; default\n",
                                f"{exit_key}::ExitApp\n",
                                "\n"
                            ] + [first_line + '\n'] + lines[1:]
                        else:
                            new_lines = [
                                "; text\n",
                                f"{exit_key}::ExitApp\n",
                                "\n"
                            ] + lines
                    else:
                        # 4. Insert exit key on second line, keep first line
                        new_lines = [lines[0] + f"{exit_key}::ExitApp\n", "\n"] + lines[1:]
                    # 5. Insert ; Text mode start at third line, and ; Text mode end at end
                    # Remove any previous ; Text mode start/end if present
                    content = ''.join(new_lines)
                    content_lines = content.splitlines()
                    content_lines = [line for line in content_lines if line.strip() not in ["; Text mode start", "; Text mode end"]]
                    # Insert ; Text mode start after header (which is 3 lines)
                    header = content_lines[:3]
                    body = content_lines[3:]
                    result_lines = header + ["; Text mode start"] + body + ["; Text mode end"]
                    # Write back
                    with open(destination_path, 'w', encoding='utf-8') as file:
                        file.write('\n'.join(result_lines) + '\n')
                except Exception as e:
                    print(f"Error modifying script: {e}")
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
                self.scripts.append(file_name)
                self.update_script_list()

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
            add_script_to_temp(script_name)
            # Change button to Exit after script is running
            button.setText("Exit")
            button.clicked.disconnect()
            button.clicked.connect(lambda checked=False: self.toggle_run_exit(script_name, button))
        else:
            # Exit the script
            self.exit_script(script_name, button)
            remove_script_from_temp(script_name)
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
            Welcome.show_welcome_window(self)
        except Exception as e:
            print(f"Error displaying welcome window: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        # Only start the worker once, on first show
        if getattr(self, "_startup_worker_started", False):
            return
        self._startup_worker_started = True
        self.startup_worker = StartupWorker(self)
        self.startup_worker.start()

def get_theme_from_themefile():
    from src.utility.constant import theme_path
    try:
        if os.path.exists(theme_path):
            with open(theme_path, 'r') as f:
                theme = f.read().strip().lower()
            if theme in ("dark", "light"):
                return theme
        return "system"
    except Exception:
        return "system"

def main():
    theme = get_theme_from_themefile()
    # Set darkmode=1 for light, darkmode=2 for dark, or use system default if "system"
    if theme == "dark":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
    elif theme == "light":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=1"
    # else: system default, do not set QT_QPA_PLATFORM
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    # Show welcome window after main window is visible, but only if enabled
    if main_window.welcome_condition:
        main_window.show_welcome_window()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()