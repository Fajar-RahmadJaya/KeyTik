"Main Core (Might be changed to shared later)"

import os
import json
import shutil
import webbrowser

import winshell
from win32com.client import Dispatch

from PySide6.QtWidgets import (  # pylint: disable=E0611
    QApplication, QFileDialog, QMessageBox,
    QInputDialog
)
from PySide6.QtGui import QFont, QFontDatabase  # pylint: disable=E0611
from pynput.keyboard import Controller, Key

from utility import constant
from utility import utils
from utility import icons

class MainCore():
    "Main Logic"
    def __init__(self):
        # UI initialization
        self.script_dir = utils.active_dir
        self.pinned_profiles = utils.load_pinned_profiles()

        self.scripts = None

    def import_button_clicked(self):
        "Select AHK script and add necessary line"
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
                destination_path = os.path.join(self.script_dir, file_name)

                try:
                    shutil.move(selected_file, destination_path)
                except NotADirectoryError as e:
                    QMessageBox.warning(self, "Error",
                                        f"Failed to move file: {e}")
                    return

                self.validate_imported_files(destination_path, file_name)

                self.scripts.append(file_name)
                self.update_script_list()

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

            content = ''.join(new_lines)
            content_lines = content.splitlines()
            content_lines = [line for line in content_lines if
                                line.strip() not in ["; Text mode start",
                                                        "; Text mode end"]]

            result_lines = (content_lines[:3] + ["; Text mode start"]
                            + content_lines[3:] + ["; Text mode end"])

            with open(destination_path, 'w', encoding='utf-8') as file:
                file.write('\n'.join(result_lines) + '\n')
        except FileNotFoundError as e:
            print(f"Error modifying script: {e}")
            try:
                if os.path.exists(constant.exit_keys_file):
                    with open(constant.exit_keys_file, 'r', encoding='utf-8') as f:
                        exit_keys = json.load(f)
                    if file_name in exit_keys:
                        del exit_keys[file_name]
                    with open(constant.exit_keys_file, 'w', encoding='utf-8') as f:
                        json.dump(exit_keys, f)
            except FileNotFoundError:
                pass

    def copy_script(self, script):
        "Copy profile"
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
        source_path = os.path.join(self.script_dir, script)
        destination_path = os.path.join(self.script_dir, new_name)
        try:
            shutil.copy(source_path, destination_path)
            self.scripts = self.list_scripts()
            self.update_script_list()
        except NotADirectoryError as e:
            QMessageBox.warning(self, "Error", f"Error copying script: {e}")

    def delete_script(self, script_name):
        "Delete profile"
        script_path = os.path.join(self.script_dir, script_name)
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
            except FileNotFoundError as e:
                QMessageBox.warning(self, "Error",
                                    f"Failed to delete the script: {e}")
        else:
            QMessageBox.warning(self, "Error",
                                f"{script_name} does not exist.")

    def activate_script(self, script_name, button):
        "Run profile"
        script_path = os.path.join(self.script_dir, script_name)

        if os.path.isfile(script_path):

            os.startfile(script_path)

            button.setText(" Exit")
            button.setToolTip(f'Stop "{os.path.splitext(script_name)[0]}"')
            button.setIcon(icons.get_icon(icons.icon_exit))
            button.clicked.disconnect()
            button.clicked.connect(lambda: self.exit_script(script_name,
                                                            button))
        else:
            QMessageBox.critical(self, "Error", f"{script_name} does not exist.")

    def exit_script(self, script_name, button):
        "Exit profile"
        script_path = os.path.join(self.script_dir, script_name)

        if os.path.isfile(script_path):
            try:

                with open(constant.exit_keys_file, 'r', encoding='utf-8') as f:
                    exit_keys = json.load(f)

                exit_combo = exit_keys.get(script_name)
                if not exit_combo:
                    QMessageBox.critical(self,
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

                button.setText(" Run")
                button.setToolTip(f'Start "{os.path.splitext(script_name)[0]}"')
                button.setIcon(icons.get_icon(icons.run))
                button.clicked.disconnect()
                button.clicked.connect(lambda: self.activate_script(
                    script_name, button))

            except FileNotFoundError as e:
                QMessageBox.critical(self, "Error", f"Failed to exit script: {e}")
        else:
            QMessageBox.critical(self, "Error", f"{script_name} does not exist.")

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

                self.scripts = self.list_scripts()
                self.update_script_list()
            except NotADirectoryError as e:
                QMessageBox.critical(self, "Error", f"Failed to move the script: {e}")
        else:
            QMessageBox.critical(self, "Error", f"{script_name} does not exist.")

    def toggle_run_exit(self, script_name, button):
        "Switch between run/exit on profile"
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
        "Change current directory based on store/active profile"
        if self.script_dir == utils.active_dir:
            self.script_dir = utils.store_dir
            self.show_stored.setToolTip("Show Active Profile")
            self.show_stored.setIcon(icons.get_icon(icons.show_stored_fill))
        else:
            self.script_dir = utils.active_dir
            self.show_stored.setToolTip("Show Stored Profile")
            self.show_stored.setIcon(icons.get_icon(icons.show_stored))

        self.list_scripts()
        self.update_script_list()

    def toggle_pin(self, script, icon_label):
        "Pin profile from pinned profile list"
        if script in self.pinned_profiles:

            self.pinned_profiles.remove(script)
            icon_label.load(icons.pin)
        else:

            self.pinned_profiles.insert(0, script)
            icon_label.load(icons.pin_fill)

        utils.save_pinned_profiles(self.pinned_profiles)
        self.list_scripts()
        self.update_script_list()

    def check_ahk_installation(self, show_installed_message=False):
        "Check AutoHotkey installation"
        if os.path.exists(utils.ahkv2_dir):
            if show_installed_message:
                QMessageBox.information(
                    None,
                    "AHK Installation",
                    "AutoHotkey v2 is installed on your system.")
            return True

        reply = QMessageBox.question(
            None,
            "AHK Installation",
            "AutoHotkey v2 is not installed on your system. "
            "AutoHotkey is required for KeyTik to work.\n\n"
            "Would you like to download it now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            webbrowser.open("https://www.autohotkey.com/")
        return False

    def font_fallback(self):
        "Fallback font (Might still not work as expected)"
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

    def list_scripts(self):
        "List profile, with listing all AHK script on active directory"
        all_scripts = [f for f in os.listdir(self.script_dir)
                       if f.endswith('.ahk') or f.endswith('.py')]

        pinned = [script for script in all_scripts
                  if script in self.pinned_profiles]
        unpinned = [script for script in all_scripts
                    if script not in self.pinned_profiles]

        self.scripts = pinned + unpinned
        return self.scripts

    def prev_page(self):
        "Show previous profile list"
        if self.current_page > 0:
            self.current_page -= 1
            self.update_script_list()

    def next_page(self):
        "show next profile list"
        if (self.current_page + 1) * 6 < len(self.scripts):
            self.current_page += 1
            self.update_script_list()

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

        self.update_script_list()
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

            self.update_script_list()

        except NotADirectoryError as e:
            print(f"Error removing {shortcut_path}: {e}")

    def update_script_list(self):
        "! From dashboard"
        for i in reversed(range(self.profile_layout.count())):
            widget = self.profile_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        start_index = self.current_page * 6
        end_index = start_index + 6
        scripts_to_display = self.scripts[start_index:end_index]

        running_scripts = utils.read_running_scripts_temp()

        for index, script in enumerate(scripts_to_display):
            row = index // 2
            column = index % 2
            icon = (icons.pin_fill
                    if script in self.pinned_profiles
                    else icons.pin)

            self.profile_card(script, icon, running_scripts, row, column)

        self.profile_layout.setColumnStretch(0, 1)
        self.profile_layout.setColumnStretch(1, 1)
        self.profile_layout.setRowStretch(0, 1)
        self.profile_layout.setRowStretch(1, 1)
        self.profile_layout.setRowStretch(2, 1)
