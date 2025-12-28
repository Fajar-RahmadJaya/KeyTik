"""Containing code for pro version and normal version to make migration easier""" # noqa
import requests
import os
import webbrowser
from PySide6.QtWidgets import (QMessageBox, QTextEdit, QSizePolicy,
                               QSpacerItem)

from utility.constant import (current_version)


mode_item = [
    "Default Mode",
    "Text Mode"
]


mode_map = {
    "; default": 0,
    "; text": 1,
}


program_name = "KeyTik"


class Diff():
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

    def handle_parser(self, lines, first_line):
        key_map = self.load_key_list()
        mode_line = lines[0].strip() if lines else "; default"

        shortcuts = []
        remaps = []

        if mode_line == "; default":
            shortcuts, remaps = self.parse_default_mode(lines, key_map)

            self.shortcut_title()

            if not shortcuts:
                self.shortcut_row()
            else:
                for shortcut in shortcuts:
                    self.shortcut_row(shortcut)

            self.remap_title()

            if not remaps:
                self.remap_row()
            else:
                for (default_key, remap_key, is_text_format,
                        is_hold_format, hold_interval, is_first_key,
                        is_sc) in remaps:
                    self.remap_row(
                        default_key,
                        remap_key,
                        is_text_format=is_text_format,
                        is_hold_format=is_hold_format,
                        hold_interval=hold_interval,
                        is_first_key=is_first_key,
                        is_sc=is_sc
                    )

            self.update_plus_visibility('shortcut')
            self.update_plus_visibility('remap')

        elif mode_line == "; text":
            self.is_text_mode = True
            self.text_block = QTextEdit(self.edit_frame)
            self.text_block.setLineWrapMode(QTextEdit.WidgetWidth)
            self.text_block.setFixedHeight(14 * self.fontMetrics().height())
            self.text_block.setFontPointSize(10)
            self.edit_frame_layout.addWidget(self.text_block)

            shortcuts = self.parse_shortcuts(lines, key_map)

            self.row_num += 1

            text_content = self.extract_and_filter_content(lines)
            self.text_block.setPlainText(text_content.strip())

            if not shortcuts:
                self.shortcut_row()
            else:
                for shortcut in shortcuts:
                    self.shortcut_row(shortcut)

            self.update_plus_visibility('shortcut')

    def handle_mode_changed(self, index):
        while self.edit_frame_layout.count():
            item = self.edit_frame_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        self.key_rows = []
        self.shortcut_rows = []
        if hasattr(self, "files_opener_rows"):
            self.files_opener_rows = []
        if hasattr(self, "files_opener_row_widgets"):
            self.files_opener_row_widgets = []
        if hasattr(self, "text_block"):
            self.text_block = None
        self.is_text_mode = False

        if index == 0:
            self.is_text_mode = False
            self.shortcut_title()
            self.shortcut_row()
            self.remap_title()
            self.remap_row()
            self.edit_frame_layout.addItem(QSpacerItem(20, 40,
                                           QSizePolicy.Minimum,
                                           QSizePolicy.Expanding))

        elif index == 1:
            self.is_text_mode = True
            self.shortcut_title()
            self.shortcut_row()
            self.edit_frame_layout.addItem(QSpacerItem(20, 40,
                                           QSizePolicy.Minimum,
                                           QSizePolicy.Expanding))

    def handle_write(self, script_name, mode):
        output_path = os.path.join(self.SCRIPT_DIR, script_name)
        key_translations = self.load_key_translations()

        with open(output_path, 'w', encoding='utf-8') as file:
            if mode == "text mode":
                self.handle_text_mode(file, key_translations)
            elif mode == "default mode":
                self.handle_default_mode(file, key_translations)
            else:
                self.handle_default_mode(file, key_translations)

    def loop_announcefile(self):
        i = 1
        while True:
            url = f"https://keytik.com/normal-md/{i}.txt"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 404:
                    break
                response.raise_for_status()
                self.announcement_files.append(url)
                i += 1
            except Exception:
                break

    def update_messagebox(self, latest_version, show_no_update_message=False):
        if latest_version:
            reply = QMessageBox.question(
                self, "Update Available",
                f"New update available: KeyTik {latest_version}\n\nWould you like to go to the update page?", # noqa
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open("https://github.com/Fajar-RahmadJaya/KeyTik/releases") # noqa
        else:
            if show_no_update_message:
                QMessageBox.information(
                    self, "Check For Update",
                    "You are using the latest version of KeyTik.")
