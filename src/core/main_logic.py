import os
import winshell
from win32com.client import Dispatch
import win32gui
import win32process
import json
import utility.constant as constant

import shutil
import webbrowser
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QMessageBox,
    QInputDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from pynput.keyboard import Controller, Key

import utility.utils as utils
import utility.icon as icons

from announcement.announcement import Announcement


class MainLogic:
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
                        if os.path.exists(constant.exit_keys_file):
                            with open(constant.exit_keys_file, 'r') as f:
                                exit_keys = json.load(f)
                            if file_name in exit_keys:
                                del exit_keys[file_name]
                            with open(constant.exit_keys_file, 'w') as f:
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
            self.always_top.setIcon(icons.get_icon(icons.on_top_fill))
        else:
            self.always_top.setToolTip("Enable  Window Always on Top")
            self.always_top.setIcon(icons.get_icon(icons.on_top))

    def activate_script(self, script_name, button):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):

            os.startfile(script_path)

            button.setText(" Exit")
            button.setToolTip(f'Stop "{os.path.splitext(script_name)[0]}"') # noqa
            button.setIcon(icons.get_icon(icons.exit))
            button.clicked.disconnect()
            button.clicked.connect(lambda: self.exit_script(script_name,
                                                            button))
        else:
            QMessageBox.critical(self, "Error", f"{script_name} does not exist.") # noqa

    def exit_script(self, script_name, button):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):
            try:

                with open(constant.exit_keys_file, 'r') as f:
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
                button.setIcon(icons.get_icon(icons.run))
                button.clicked.disconnect()
                button.clicked.connect(lambda: self.activate_script(
                    script_name, button))

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to exit script: {e}") # noqa
        else:
            QMessageBox.critical(self, "Error", f"{script_name} does not exist.") # noqa

    def store_script(self, script_name):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if self.SCRIPT_DIR == utils.active_dir:
            target_dir = utils.store_dir
        else:
            target_dir = utils.active_dir

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
            utils.add_script_to_temp(script_name)

            button.clicked.disconnect()
            button.clicked.connect(lambda checked=False: self.toggle_run_exit(
                script_name, button))
        else:

            self.exit_script(script_name, button)
            utils.remove_script_from_temp(script_name)

            button.clicked.disconnect()
            button.clicked.connect(lambda checked=False: self.toggle_run_exit(
                script_name, button))

    def toggle_script_dir(self):
        if self.SCRIPT_DIR == utils.active_dir:
            self.SCRIPT_DIR = utils.store_dir
            self.show_stored.setToolTip("Show Active Profile")
            self.show_stored.setIcon(icons.get_icon(icons.show_stored_fill))
        else:
            self.SCRIPT_DIR = utils.active_dir
            self.show_stored.setToolTip("Show Stored Profile")
            self.show_stored.setIcon(icons.get_icon(icons.show_stored))

        self.list_scripts()
        self.update_script_list()

    def toggle_pin(self, script, icon_label):
        if script in self.pinned_profiles:

            self.pinned_profiles.remove(script)
            icon_label.load(icons.pin)
        else:

            self.pinned_profiles.insert(0, script)
            icon_label.load(icons.pin_fill)

        utils.save_pinned_profiles(self.pinned_profiles)
        self.list_scripts()
        self.update_script_list()

    def show_announcement_window(self):
        try:
            Announcement.show_announcement_window(self)
        except Exception as e:
            print(f"Error displaying announcement window: {e}")

    def check_ahk_installation(self, show_installed_message=False):
        if os.path.exists(utils.ahkv2_dir):
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

    def check_ahi_dir(self):
        target_folder = os.path.join(utils.active_dir,
                                     'AutoHotkey Interception')

        def get_all_relative_paths(base_dir):
            rel_paths = set()
            for root, dirs, files in os.walk(base_dir):
                for name in files:
                    rel_path = os.path.relpath(os.path.join(root, name),
                                               base_dir)
                    rel_paths.add(rel_path)
                for name in dirs:
                    rel_path = os.path.relpath(os.path.join(root, name),
                                               base_dir)
                    rel_paths.add(rel_path)
            return rel_paths

        ahi_paths = get_all_relative_paths(constant.ahi_dir)
        target_paths = get_all_relative_paths(target_folder)

        if (not ahi_paths.issubset(target_paths) or
                not os.path.isdir(target_folder)):
            if os.path.exists(target_folder):
                shutil.rmtree(target_folder)
            shutil.copytree(constant.ahi_dir, target_folder)

    def list_scripts(self):
        all_scripts = [f for f in os.listdir(self.SCRIPT_DIR)
                       if f.endswith('.ahk') or f.endswith('.py')]

        pinned = [script for script in all_scripts
                  if script in self.pinned_profiles]
        unpinned = [script for script in all_scripts
                    if script not in self.pinned_profiles]

        self.scripts = pinned + unpinned
        return self.scripts

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_script_list()

    def next_page(self):
        if (self.current_page + 1) * 6 < len(self.scripts):
            self.current_page += 1
            self.update_script_list()

    def add_ahk_to_startup(self, script_name):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        startup_folder = winshell.startup()

        shortcut_name = os.path.splitext(script_name)[0]
        shortcut_path = os.path.join(startup_folder, f"{shortcut_name}.lnk")

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = script_path
        shortcut.WorkingDirectory = os.path.dirname(script_path)
        shortcut.IconLocation = script_path
        shortcut.save()

        del shell

        self.update_script_list()
        return shortcut_path

    def remove_ahk_from_startup(self, script_name):
        shortcut_name = os.path.splitext(script_name)[0]
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, f"{shortcut_name}.lnk")

        try:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                print(f"Removed {shortcut_path} from startup.")
            else:
                print(f"{shortcut_path} does not exist in startup.")

            self.update_script_list()

        except Exception as e:
            print(f"Error removing {shortcut_path}: {e}")

    def is_visible_application(self, pid):
        try:
            def callback(hwnd, pid_list):
                _, process_pid = win32process.GetWindowThreadProcessId(hwnd)
                if process_pid == pid and win32gui.IsWindowVisible(hwnd):
                    pid_list.append(pid)

            visible_pids = []
            win32gui.EnumWindows(callback, visible_pids)
            return len(visible_pids) > 0
        except Exception:
            return False

    def run_monitor(self):
        script_path = os.path.join(constant.script_dir,
                                   "_internal", "Data", "Active",
                                   "AutoHotkey Interception", "Monitor.ahk")
        if os.path.exists(script_path):
            os.startfile(script_path)
        else:
            print(f"Error: The script at {script_path} does not exist.")

    def load_key_translations(self):
        key_translations = {}
        try:
            with open(constant.keylist_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for category_dict in data:
                    for _, keys in category_dict.items():
                        for key, info in keys.items():
                            readable_key = key.strip().lower()
                            translation = info.get("translate", "").strip()
                            if translation:
                                key_translations[readable_key] = translation

        except Exception as e:
            print(f"Error reading key translations: {e}")
        return key_translations

    def translate_key(self, key, key_translations):
        keys = key.split('+')
        translated_keys = []

        for single_key in keys:
            translated_key = key_translations.get(single_key.strip().lower(),
                                                  single_key.strip())
            translated_keys.append(translated_key)

        return " & ".join(translated_keys)

    def load_key_list(self):
        key_map = {}
        try:
            with open(constant.keylist_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for category_dict in data:
                    for _, keys in category_dict.items():
                        for key, info in keys.items():
                            readable = key
                            raw = info.get("translate", "")
                            if raw:
                                key_map[raw] = readable
        except Exception as e:
            print(f"Error reading key list: {e}")
        return key_map

    def load_key_values(self):
        key_values = []
        try:
            with open(constant.keylist_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for category_dict in data:
                    for _, keys in category_dict.items():
                        for key in keys.keys():
                            key_values.append(key)
        except Exception as e:
            print(f"Error reading key_list.json: {e}")
        return key_values
