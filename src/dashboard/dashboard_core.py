"Main Core (Might be changed to shared later)"

import os
import json
import re
import shutil
import webbrowser
import random
import winshell
import win32gui
from win32com.client import Dispatch
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QFileDialog, QMessageBox,
    QInputDialog
)
from PySide6.QtCore import Signal, QObject # pylint: disable=E0611
from pynput.keyboard import Controller, Key

from utility import constant
from utility import utils
from utility import icons

class DashboardCore(QObject):
    "Main Logic"
    update_script_signal = Signal()
    def __init__(self):
        super().__init__()
        # UI initialization
        self.script_dir = utils.active_dir

        # Variable
        self.current_page = 0
        self.pinned_profiles = utils.load_pinned_profiles()

    def import_button_clicked(self, parent):
        "Select AHK script and add necessary line"
        file_dialog = QFileDialog(parent)
        file_dialog.setNameFilter("AHK Scripts (*.ahk)")

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()

            if selected_files:
                selected_file = selected_files[0]

                if not selected_file.endswith('.ahk'):
                    QMessageBox.warning(None, "Error",
                                        "Only .ahk files are allowed.")
                    return

                file_name = os.path.basename(selected_file)
                destination_path = os.path.join(self.script_dir, file_name)

                try:
                    shutil.move(selected_file, destination_path)
                except NotADirectoryError as e:
                    QMessageBox.warning(None, "Error",
                                        f"Failed to move file: {e}")
                    return

                self.validate_imported_files(destination_path, file_name)
                self.update_script_signal.emit()

    def validate_imported_files(self, destination_path, file_name):
        "Add necessary line on imported files"
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

            content_lines = ''.join(new_lines).splitlines()
            content_lines = [line for line in content_lines if
                                line.strip() not in ["; Text mode start",
                                                        "; Text mode end"]]

            result_lines = (content_lines[:3] + ["; Text mode start"]
                            + content_lines[3:] + ["; Text mode end"])

            with open(destination_path, 'w', encoding='utf-8') as file:
                file.write('\n'.join(result_lines) + '\n')
        except FileNotFoundError as e:
            print(f"Error modifying script: {e}")
            exit_keys = utils.load_exit_keys()

            if file_name in exit_keys:
                del exit_keys[file_name]

            try:
                with open(constant.exit_keys_path, 'w', encoding='utf-8') as f:
                    json.dump(exit_keys, f)

            except (json.JSONDecodeError, FileNotFoundError) as error:
                print(f"Error: {error}")

    def generate_exit_key(self, script_name, file=None):
        "Generate key for profile exit"
        possible_keys = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

        exit_keys = utils.load_exit_keys()

        used_keys = set(key[-1] for key in exit_keys.values())
        available_keys = [k for k in possible_keys if k not in used_keys]

        if not available_keys:
            available_keys = possible_keys

        exit_combo = f"^!{random.choice(available_keys)}"

        exit_keys[script_name] = exit_combo

        try:
            with open(constant.exit_keys_path, 'w', encoding='utf-8') as f:
                json.dump(exit_keys, f)
            if file:
                file.write(f"{exit_combo}::ExitApp\n\n")

            return exit_combo

        except FileNotFoundError as e:
            print(f"Error handling exit key: {e}")
            if file:
                file.write("^!p::ExitApp\n\n")
            return "^!p"

    def copy_script(self, script, parent):
        "Copy profile"
        dialog = QInputDialog(parent)
        dialog.setWindowTitle("Copy Script")
        dialog.setLabelText("Enter the new script name:")
        dialog.resize(250, 100)
        ok = dialog.exec()
        new_name = dialog.textValue()
        if not ok or not new_name:
            return
        if not new_name.lower().endswith('.ahk'):
            new_name += '.ahk'
        source_path = os.path.join(self.script_dir, script)
        destination_path = os.path.join(self.script_dir, new_name)
        try:
            shutil.copy(source_path, destination_path)
            self.update_script_signal.emit()
        except NotADirectoryError as e:
            QMessageBox.warning(None, "Error", f"Error copying script: {e}")

    def delete_script(self, script_name):
        "Delete profile"
        script_path = os.path.join(self.script_dir, script_name)
        if os.path.isfile(script_path):
            reply = QMessageBox.question(
                None,
                "Delete Script",
                f"Are you sure you want to delete '{script_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            try:
                os.remove(script_path)
                self.update_script_signal.emit()
            except FileNotFoundError as e:
                QMessageBox.warning(None, "Error",
                                    f"Failed to delete the script: {e}")
        else:
            QMessageBox.warning(None, "Error",
                                f"{script_name} does not exist.")

    def activate_script(self, script_name, button):
        "Run profile"
        if os.path.isfile(os.path.join(utils.active_dir, script_name)):
            script_path = os.path.join(utils.active_dir, script_name)
        else:
            script_path = os.path.join(utils.store_dir, script_name)

        if os.path.isfile(script_path):

            os.startfile(script_path)

            if button:
                button.setText(" Exit")
                button.setToolTip(f'Stop "{os.path.splitext(script_name)[0]}"')
                button.setIcon(icons.get_icon(icons.icon_exit))
                button.clicked.disconnect()
                button.clicked.connect(lambda: self.exit_script(script_name,
                                                                button))
        else:
            QMessageBox.critical(None, "Error", f"{script_name} does not exist.")

    def exit_script(self, script_name, button):
        "Exit profile"
        if os.path.isfile(os.path.join(utils.active_dir, script_name)):
            script_path = os.path.join(utils.active_dir, script_name)
        else:
            script_path = os.path.join(utils.store_dir, script_name)

        if os.path.isfile(script_path):
            exit_keys = utils.load_exit_keys()
            exit_combo = exit_keys.get(script_name)
            if not exit_combo:
                QMessageBox.critical(None,
                                        "Error",
                                        f"No exit key found for {script_name}")
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

            if button:
                button.setText(" Run")
                button.setToolTip(f'Start "{os.path.splitext(script_name)[0]}"')
                button.setIcon(icons.get_icon(icons.run))
                button.clicked.disconnect()
                button.clicked.connect(lambda: self.activate_script(
                    script_name, button))
        else:
            QMessageBox.critical(None, "Error", f"{script_path} does not exist.")

    def store_script(self, script_name):
        "Move profile to store directory"
        script_path = os.path.join(self.script_dir, script_name)

        if self.script_dir == utils.active_dir:
            target_dir = utils.store_dir
        else:
            target_dir = utils.active_dir

        target_path = os.path.join(target_dir, script_name)

        if os.path.isfile(script_path):
            try:

                shutil.move(script_path, target_path)
                self.update_script_signal.emit()
            except NotADirectoryError as e:
                QMessageBox.critical(None, "Error", f"Failed to move the script: {e}")
        else:
            QMessageBox.critical(None, "Error", f"{script_name} does not exist.")

    def toggle_run_exit(self, script_name, button):
        "Switch between run/exit on profile"
        if button.text() == " Run":
            self.activate_script(script_name, button)

            button.clicked.disconnect()
            button.clicked.connect(lambda checked=False: self.toggle_run_exit(
                script_name, button))
        else:
            self.exit_script(script_name, button)

            button.clicked.disconnect()
            button.clicked.connect(lambda checked=False: self.toggle_run_exit(
                script_name, button))

    def toggle_script_dir(self, show_stored):
        "Change current directory based on store/active profile"
        if self.script_dir == utils.active_dir:
            self.script_dir = utils.store_dir
            show_stored.setToolTip("Show Active Profile")
            show_stored.setIcon(icons.get_icon(icons.show_stored_fill))
        else:
            self.script_dir = utils.active_dir
            show_stored.setToolTip("Show Stored Profile")
            show_stored.setIcon(icons.get_icon(icons.show_stored))

        self.current_page = 0
        self.list_scripts()
        self.update_script_signal.emit()

    def ahk_notinstalled_msg(self, parent):
        "Check AutoHotkey installation"
        reply = QMessageBox.question(
            parent,
            "AHK Installation",
            "AutoHotkey v2 is not installed on your system. "
            "AutoHotkey is required for KeyTik to work.\n\n"
            "Would you like to download it now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            webbrowser.open("https://www.autohotkey.com/")
        return False

    def toggle_pin(self, script):
        "Pin profile from pinned profile list"
        if script in self.pinned_profiles:
            self.pinned_profiles.remove(script)
        else:
            self.pinned_profiles.insert(0, script)

        with open(constant.pinned_profile_path, "w", encoding="utf-8") as pin_file:
            json.dump(self.pinned_profiles, pin_file)
        self.update_script_signal.emit()

    def list_scripts(self):
        "List profile, with listing all AHK script on active directory order by pinned first"
        all_scripts = [f for f in os.listdir(self.script_dir)
                       if f.endswith('.ahk') or f.endswith('.py')]

        pinned = [script for script in all_scripts
                  if script in self.pinned_profiles]
        unpinned = [script for script in all_scripts
                    if script not in self.pinned_profiles]

        scripts = pinned + unpinned
        return scripts

    def prev_page(self):
        "Show previous profile list"
        if self.current_page > 0:
            self.current_page -= 1
            self.update_script_signal.emit()

    def next_page(self):
        "show next profile list"
        if (self.current_page + 1) * 6 < len(self.list_scripts()):
            self.current_page += 1
            self.update_script_signal.emit()

    def add_ahk_to_startup(self, script_name):
        "Add profile to startup folder"
        script_path = os.path.join(self.script_dir, script_name)

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

        self.update_script_signal.emit()
        return shortcut_path

    def remove_ahk_from_startup(self, script_name):
        "Add profile to startup folder"
        shortcut_name = os.path.splitext(script_name)[0]
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, f"{shortcut_name}.lnk")

        try:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                print(f"Removed {shortcut_path} from startup.")
            else:
                print(f"{shortcut_path} does not exist in startup.")

            self.update_script_signal.emit()

        except NotADirectoryError as e:
            print(f"Error removing {shortcut_path}: {e}")

    def check_ahi_dir(self):
        "Make sure AutoHotkey Interception folder is in active profile folder"
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

    def get_running_ahk(self):
        "Get running ahk script"
        running_script = set()
        def callback(hwnd, running_script):
            if win32gui.IsWindowVisible(hwnd) or win32gui.IsWindowEnabled(hwnd):  # pylint: disable=I1101
                class_name = win32gui.GetClassName(hwnd)  # pylint: disable=I1101
                if class_name == "AutoHotkey":
                    title = win32gui.GetWindowText(hwnd)  # pylint: disable=I1101
                    title = re.sub(r" - AutoHotkey v[\d\.]+$", "", title)
                    if title:
                        running_script.add(os.path.basename(title))
        win32gui.EnumWindows(callback, running_script)  # pylint: disable=I1101
        return running_script
