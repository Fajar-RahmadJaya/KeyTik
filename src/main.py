import os
import shutil
import webbrowser
import sys
import winshell
import json
import requests
import keyboard
import pynput
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QFrame, QPushButton, QGroupBox, QFileDialog, QMessageBox,
    QInputDialog, QLabel
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtGui import QFont, QFontDatabase
from pynput.keyboard import Controller, Key
from utility.constant import (icon_path, exit_keys_file, current_version)
from utility.utils import (load_pinned_profiles, active_dir, store_dir,
                           save_pinned_profiles, read_running_scripts_temp,
                           add_script_to_temp, remove_script_from_temp,
                           theme, ahkv2_dir)
from utility.icon import (get_icon, icon_pin, icon_pin_fill,
                          icon_rocket, icon_rocket_fill, icon_exit, icon_run,
                          icon_copy, icon_delete, icon_store, icon_plus,
                          icon_next, icon_prev, icon_setting, icon_import,
                          icon_on_top, icon_on_top_fill, icon_show_stored,
                          icon_show_stored_fill, icon_edit)
from logic.logic import Logic
from ui.setting import Setting
from ui.welcome import Welcome

from ui.edit_script.edit_script_main import EditScriptMain
from ui.edit_script.select_program import SelectProgram
from ui.edit_script.select_device import SelectDevice
from ui.edit_script.edit_frame_row import EditFrameRow
from ui.edit_script.edit_script_logic import EditScriptLogic
from ui.edit_script.write_script import WriteScript
from ui.edit_script.parse_script import ParseScript
from ui.edit_script.choose_key import ChooseKey


class StartupWorker(QThread):
    finished = Signal()
    update_found = Signal(str)
    show_welcome = Signal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def run(self):
        self.main_window.initialize_exit_keys()

        latest_version = self.main_window.check_for_update()
        if latest_version:
            self.update_found.emit(latest_version)
        self.finished.emit()

        if self.main_window.welcome_condition:
            self.show_welcome.emit()

        if not hasattr(self.main_window, "keyboard_hook_initialized"):
            keyboard.hook(lambda event: self.main_window.multi_key_event(
                event, self.main_window.active_entry, None))
            self.main_window.mouse_listener = pynput.mouse.Listener(
                on_click=lambda *args: self.main_window.mouse_listening(*args)
            )
            self.main_window.mouse_listener.start()
            self.main_window.keyboard_hook_initialized = True


class MainApp(QMainWindow, Logic, EditFrameRow, EditScriptMain,
              Setting, Welcome, SelectProgram, SelectDevice,
              EditScriptLogic, WriteScript, ParseScript, ChooseKey):
    def __init__(self):
        super().__init__()
        # Key Listening
        self.is_listening = False
        self.active_entry = None
        # Mouse Listening
        self.last_key_time = 0
        self.timeout = 1
        self.pressed_keys = []
        self.ignore_next_click = False

        # UI initialization
        self.check_ahk_installation(show_installed_message=False)
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.current_page = 0
        self.SCRIPT_DIR = active_dir
        self.pinned_profiles = load_pinned_profiles()
        self.scripts = self.list_scripts()
        self.create_ui()
        self.update_script_list()
        self.setWindowTitle("KeyTik")
        self.setFixedSize(650, 492)
        self.setWindowIcon(QIcon(icon_path))
        self.setCentralWidget(self.central_widget)
        self.welcome_condition = self.load_welcome_condition()
        self.font_fallback()

    def create_ui(self):
        self.frame = QFrame()
        self.main_layout.addWidget(self.frame)
        self.frame_layout = QVBoxLayout(self.frame)

        self.profile_frame = QFrame()
        self.profile_layout = QGridLayout(self.profile_frame)
        self.profile_layout.setContentsMargins(0, 0, 0, 10)
        self.profile_frame.setFixedHeight(400)
        self.profile_layout.setHorizontalSpacing(15)
        self.profile_layout.setVerticalSpacing(10)
        self.frame_layout.addWidget(self.profile_frame)

        button_frame = QFrame()
        button_layout = QGridLayout(button_frame)
        button_layout.setContentsMargins(40, 20, 40, 10)

        self.prev_button = QPushButton()
        self.prev_button.setFixedWidth(80)
        self.prev_button.setIcon(get_icon(icon_prev))
        self.prev_button.setToolTip("Previous Profile")
        self.prev_button.clicked.connect(self.prev_page)
        button_layout.addWidget(self.prev_button, 0, 0)

        self.show_stored = QPushButton()
        self.show_stored.setFixedWidth(30)
        self.show_stored.setIcon(get_icon(icon_show_stored))
        self.show_stored.setToolTip("Show Stored Profile")
        self.show_stored.clicked.connect(self.toggle_script_dir)
        button_layout.addWidget(self.show_stored, 0, 1)

        self.import_button = QPushButton()
        self.import_button.setFixedWidth(30)
        self.import_button.setIcon(get_icon(icon_import))
        self.import_button.setToolTip("Import AutoHotkey Script")
        self.import_button.clicked.connect(self.import_button_clicked)
        button_layout.addWidget(self.import_button, 0, 2)

        dummy_left = QLabel()
        dummy_left.setFixedWidth(10)
        button_layout.addWidget(dummy_left, 0, 3)

        self.create_button = QPushButton(" Create New Profile")
        self.create_button.setIcon(get_icon(icon_plus))
        self.create_button.setFixedWidth(150)
        self.create_button.setFixedHeight(30)
        self.create_button.clicked.connect(lambda: self.edit_script(None))
        button_layout.addWidget(self.create_button, 0, 4)

        dummy_right = QLabel()
        dummy_right.setFixedWidth(10)
        button_layout.addWidget(dummy_right, 0, 5)

        self.always_top = QPushButton()
        self.always_top.setFixedWidth(30)
        self.always_top.setIcon(get_icon(icon_on_top))
        self.always_top.setToolTip("Enable  Window Always on Top")
        self.always_top.clicked.connect(self.toggle_on_top)
        button_layout.addWidget(self.always_top, 0, 6)

        self.setting_button = QPushButton()
        self.setting_button.setFixedWidth(30)
        self.setting_button.setIcon(get_icon(icon_setting))
        self.setting_button.setToolTip("Setting")
        self.setting_button.clicked.connect(self.open_settings_window)
        button_layout.addWidget(self.setting_button, 0, 7)

        self.next_button = QPushButton()
        self.next_button.setFixedWidth(80)
        self.next_button.setIcon(get_icon(icon_next))
        self.next_button.setToolTip("Next Profile")
        self.next_button.clicked.connect(self.next_page)
        button_layout.addWidget(self.next_button, 0, 8)

        self.frame_layout.addWidget(button_frame)

    def update_script_list(self):
        for i in reversed(range(self.profile_layout.count())):
            widget = self.profile_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        start_index = self.current_page * 6
        end_index = start_index + 6
        scripts_to_display = self.scripts[start_index:end_index]

        running_scripts = read_running_scripts_temp()

        for index, script in enumerate(scripts_to_display):
            row = index // 2
            column = index % 2
            icon = (icon_pin_fill
                    if script in self.pinned_profiles
                    else icon_pin)

            group_box = QGroupBox(os.path.splitext(script)[0])
            group_layout = QGridLayout(group_box)

            icon_label = QSvgWidget(icon, group_box)
            icon_label.setFixedSize(17, 17)
            icon_label.setToolTip(f'Pin "{os.path.splitext(script)[0]}"')
            icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
            icon_label.mousePressEvent = (lambda event, s=script,
                                          i=icon_label: self.toggle_pin(s, i))
            icon_label.move(285, 3)

            run_button = QPushButton()
            run_button.setFixedWidth(80)

            shortcut_name = os.path.splitext(script)[0] + ".lnk"
            startup_folder = winshell.startup()
            shortcut_path = os.path.join(startup_folder, shortcut_name)
            is_startup = os.path.exists(shortcut_path)

            if is_startup or script in running_scripts:
                run_button.setText(" Exit")
                run_button.setToolTip(f'Stop "{os.path.splitext(script)[0]}"')
                run_button.setIcon(get_icon(icon_exit))
            else:
                run_button.setText(" Run")
                run_button.setToolTip(f'Start "{os.path.splitext(script)[0]}"')
                run_button.setIcon(get_icon(icon_run))
            run_button.clicked.connect(lambda checked, s=script, b=run_button:
                                       self.toggle_run_exit(s, b))
            group_layout.addWidget(run_button, 0, 0)

            edit_button = QPushButton(" Edit")
            edit_button.setIcon(get_icon(icon_edit))
            edit_button.setFixedWidth(80)
            edit_button.setToolTip(f'Adjust "{os.path.splitext(script)[0]}"')

            def handle_edit(checked=False, s=script, rb=run_button):
                was_running = rb.text() == " Exit"
                if was_running:
                    self.exit_script(s, rb)
                self.edit_script(s)
                if was_running:
                    for i in range(self.profile_layout.count()):
                        group_box = self.profile_layout.itemAt(i).widget()
                        if (isinstance(group_box, QGroupBox) and
                                group_box.title() == os.path.splitext(s)[0]):
                            layout = group_box.layout()
                            if layout:
                                btn = layout.itemAtPosition(0, 0)
                                if btn:
                                    run_btn = btn.widget()
                                    if isinstance(run_btn, QPushButton):
                                        self.activate_script(s, run_btn)
                                        break

            edit_button.clicked.connect(handle_edit)
            group_layout.addWidget(edit_button, 0, 1)

            copy_button = QPushButton(" Copy")
            copy_button.setFixedWidth(80)
            copy_button.setIcon(get_icon(icon_copy))
            copy_button.setToolTip(f'Copy "{os.path.splitext(script)[0]}"')
            copy_button.clicked.connect(lambda checked,
                                        s=script: self.copy_script(s))
            group_layout.addWidget(copy_button, 1, 0)

            delete_button = QPushButton(" Delete")
            delete_button.setFixedWidth(80)
            delete_button.setIcon(get_icon(icon_delete))
            delete_button.setToolTip(f'Remove "{os.path.splitext(script)[0]}"')
            delete_button.clicked.connect(lambda checked,
                                          s=script: self.delete_script(s))
            group_layout.addWidget(delete_button, 1, 2)

            store_button = QPushButton(" Store" if
                                       self.SCRIPT_DIR == active_dir
                                       else " Restore")
            store_button.setFixedWidth(80)
            store_button.setIcon(get_icon(icon_store))
            if self.SCRIPT_DIR == active_dir:
                store_button.setToolTip(f'Hide "{os.path.splitext(script)[0]}"') # noqa
            else:
                store_button.setToolTip(f'Unhide "{os.path.splitext(script)[0]}"') # noqa
            store_button.clicked.connect(lambda checked,
                                         s=script: self.store_script(s))
            group_layout.addWidget(store_button, 1, 1)

            if is_startup:
                startup_button = QPushButton(" Unstartup")
                startup_button.setIcon(get_icon(icon_rocket_fill))
                startup_button.setToolTip(
                    f'Remove from startup: Dont run"{os.path.splitext(script)[0]}" automatically when computer starts') # noqa
                startup_button.clicked.connect(lambda checked, s=script:
                                               self.remove_ahk_from_startup(s))
            else:
                startup_button = QPushButton(" Startup")
                startup_button.setIcon(get_icon(icon_rocket))
                startup_button.setToolTip(
                    f'Add to startup: Run "{os.path.splitext(script)[0]}" automatically when computer starts') # noqa
                startup_button.clicked.connect(lambda checked, s=script:
                                               self.add_ahk_to_startup(s))
            startup_button.setFixedWidth(80)
            group_layout.addWidget(startup_button, 0, 2)

            self.profile_layout.addWidget(group_box, row, column)

        self.profile_layout.setColumnStretch(0, 1)
        self.profile_layout.setColumnStretch(1, 1)
        self.profile_layout.setRowStretch(0, 1)
        self.profile_layout.setRowStretch(1, 1)
        self.profile_layout.setRowStretch(2, 1)

    def import_button_clicked(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("AHK Scripts (*.ahk)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                selected_file = selected_files[0]
                if not selected_file.endswith('.ahk'):
                    QMessageBox.warning(self, "Error",
                                        "Only .ahk files are allowed.")
                    return
                file_name = os.path.basename(selected_file)
                destination_path = os.path.join(self.SCRIPT_DIR, file_name)
                try:
                    shutil.move(selected_file, destination_path)
                except Exception as e:
                    QMessageBox.warning(self, "Error",
                                        f"Failed to move file: {e}")
                    return
                try:
                    exit_key = self.generate_exit_key(file_name)
                    with open(destination_path, 'r', encoding='utf-8') as file:
                        lines = file.readlines()

                    lines = [line for line in lines if "::ExitApp" not in line]

                    first_line = lines[0].strip() if lines else ""
                    has_text_or_default = (first_line.startswith("; text") or
                                           first_line.startswith("; default"))
                    new_lines = []
                    if not has_text_or_default:

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

                        new_lines = [lines[0] + f"{exit_key}::ExitApp\n",
                                     "\n"] + lines[1:]

                    content = ''.join(new_lines)
                    content_lines = content.splitlines()
                    content_lines = [line for line in content_lines if
                                     line.strip() not in ["; Text mode start",
                                                          "; Text mode end"]]

                    header = content_lines[:3]
                    body = content_lines[3:]
                    result_lines = (header + ["; Text mode start"]
                                    + body + ["; Text mode end"])

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
                    except Exception:
                        pass
                    return
                self.scripts.append(file_name)
                self.update_script_list()

    def copy_script(self, script):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Copy Script")
        dialog.setLabelText("Enter the new script name:")
        dialog.resize(250, 100)
        ok = dialog.exec()
        new_name = dialog.textValue()
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
            reply = QMessageBox.question(
                self,
                "Delete Script",
                f"Are you sure you want to delete '{script_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            try:
                os.remove(script_path)
                self.scripts = self.list_scripts()
                self.update_script_list()
            except Exception as e:
                QMessageBox.warning(self, "Error",
                                    f"Failed to delete the script: {e}")
        else:
            QMessageBox.warning(self, "Error",
                                f"{script_name} does not exist.")

    def toggle_on_top(self):
        is_on_top = bool(self.windowFlags() &
                         Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, not is_on_top)
        self.show()
        onTopText = (f"KeyTik{' (Always on Top)' if not is_on_top else ''}")
        self.setWindowTitle(onTopText)
        if not is_on_top:
            self.always_top.setToolTip("Disable Window Always on Top")
            self.always_top.setIcon(get_icon(icon_on_top_fill))
        else:
            self.always_top.setToolTip("Enable  Window Always on Top")
            self.always_top.setIcon(get_icon(icon_on_top))

    def activate_script(self, script_name, button):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):

            os.startfile(script_path)

            button.setText(" Exit")
            button.setToolTip(f'Stop "{os.path.splitext(script_name)[0]}"') # noqa
            button.setIcon(get_icon(icon_exit))
            button.clicked.disconnect()
            button.clicked.connect(lambda: self.exit_script(script_name,
                                                            button))
        else:
            QMessageBox.critical(self, "Error", f"{script_name} does not exist.") # noqa

    def exit_script(self, script_name, button):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):
            try:

                with open(exit_keys_file, 'r') as f:
                    exit_keys = json.load(f)

                exit_combo = exit_keys.get(script_name)
                if not exit_combo:
                    QMessageBox.critical(self, "Error", f"No exit key found for {script_name}") # noqa
                    return

                keyboard = Controller()
                if '^' in exit_combo:
                    keyboard.press(Key.ctrl)
                if '!' in exit_combo:
                    keyboard.press(Key.alt)

                final_key = exit_combo[-1]
                keyboard.press(final_key)
                keyboard.release(final_key)

                if '!' in exit_combo:
                    keyboard.release(Key.alt)
                if '^' in exit_combo:
                    keyboard.release(Key.ctrl)

                button.setText(" Run")
                button.setToolTip(f'Start "{os.path.splitext(script_name)[0]}"') # noqa
                button.setIcon(get_icon(icon_run))
                button.clicked.disconnect()
                button.clicked.connect(lambda: self.activate_script(
                    script_name, button))

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to exit script: {e}") # noqa
        else:
            QMessageBox.critical(self, "Error", f"{script_name} does not exist.") # noqa

    def store_script(self, script_name):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if self.SCRIPT_DIR == active_dir:
            target_dir = store_dir
        else:
            target_dir = active_dir

        target_path = os.path.join(target_dir, script_name)

        if os.path.isfile(script_path):
            try:

                shutil.move(script_path, target_path)

                self.scripts = self.list_scripts()
                self.update_script_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to move the script: {e}") # noqa
        else:
            QMessageBox.critical(self, "Error", f"{script_name} does not exist.") # noqa

    def toggle_run_exit(self, script_name, button):
        if button.text() == " Run":

            self.activate_script(script_name, button)
            add_script_to_temp(script_name)

            button.clicked.disconnect()
            button.clicked.connect(lambda checked=False: self.toggle_run_exit(
                script_name, button))
        else:

            self.exit_script(script_name, button)
            remove_script_from_temp(script_name)

            button.clicked.disconnect()
            button.clicked.connect(lambda checked=False: self.toggle_run_exit(
                script_name, button))

    def toggle_script_dir(self):
        if self.SCRIPT_DIR == active_dir:
            self.SCRIPT_DIR = store_dir
            self.show_stored.setToolTip("Show Active Profile")
            self.show_stored.setIcon(get_icon(icon_show_stored_fill))
        else:
            self.SCRIPT_DIR = active_dir
            self.show_stored.setToolTip("Show Stored Profile")
            self.show_stored.setIcon(get_icon(icon_show_stored))

        self.list_scripts()
        self.update_script_list()

    def toggle_pin(self, script, icon_label):
        if script in self.pinned_profiles:

            self.pinned_profiles.remove(script)
            icon_label.load(icon_pin)
        else:

            self.pinned_profiles.insert(0, script)
            icon_label.load(icon_pin_fill)

        save_pinned_profiles(self.pinned_profiles)
        self.list_scripts()
        self.update_script_list()

    def show_welcome_window(self):
        try:
            Welcome.show_welcome_window(self)
        except Exception as e:
            print(f"Error displaying welcome window: {e}")

    def check_for_update(self):
        try:
            response = requests.get("https://api.github.com/repos/Fajar-RahmadJaya/KeyTik/releases/latest", timeout=5) # noqa
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data.get("tag_name")
                if current_version != latest_version:
                    return latest_version
        except Exception:
            pass
        return None

    def show_update_messagebox(self, latest_version):
        reply = QMessageBox.question(
            self, "Update Available",
            f"New update available: KeyTik {latest_version}\n\nWould you like to go to the update page?", # noqa
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            webbrowser.open("https://github.com/Fajar-RahmadJaya/KeyTik/releases") # noqa

    def check_ahk_installation(self, show_installed_message=False):
        if os.path.exists(ahkv2_dir):
            if show_installed_message:
                QMessageBox.information(None, "AHK Installation", "AutoHotkey v2 is installed on your system.") # noqa
            return True
        else:
            reply = QMessageBox.question(
                None,
                "AHK Installation",
                "AutoHotkey v2 is not installed on your system. AutoHotkey is required for KeyTik to work.\n\nWould you like to download it now?", # noqa
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open("https://www.autohotkey.com/")
            return False

    def font_fallback(self):
        available_fonts = []
        all_fonts = QFontDatabase.families()
        for font_name in all_fonts:
            is_scalable = QFontDatabase.isSmoothlyScalable(font_name)
            if is_scalable:
                available_fonts.append(font_name)

        default_font = QApplication.font()
        default_font_family = default_font.family()

        fallback_font = QFont(default_font_family, 9, QFont.Normal, False)

        for font_name in available_fonts:
            if font_name != default_font_family:
                fallback_font.insertSubstitution(default_font_family,
                                                 font_name)

        QApplication.setFont(fallback_font)


def main():
    if theme == "dark":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
    elif theme == "light":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=1"

    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()

    main_window.startup_worker = StartupWorker(main_window)
    main_window.startup_worker.update_found.connect(
        main_window.show_update_messagebox)
    main_window.startup_worker.show_welcome.connect(
        main_window.show_welcome_window)
    main_window.startup_worker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
