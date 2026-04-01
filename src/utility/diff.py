"Containing code for pro version and normal version to make migration easier"
import os
import webbrowser
import requests

from PySide6.QtWidgets import (QMessageBox, QTextEdit, QSizePolicy, QSpacerItem)  # pylint: disable=E0611


mode_item = [
    "Default Mode",
    "Text Mode"
]


mode_map = {
    "; default": 0,
    "; text": 1,
}


PROGRAM_NAME = "KeyTik"


CURRENT_VERSION = "v2.3.5"


class Diff():
    "Code difference between normal version and pro version to make migration easier"
    def __init__(self):
        self.is_text_mode = True
        self.key_rows = []
        self.shortcut_rows = []
        self.files_opener_rows = []
        self.files_opener_row_widgets = []

        self.text_block = None

    def check_for_update(self):
        "Check for update comparing current version and latest version from GitHub API"
        github_api_link = "https://api.github.com/repos/Fajar-RahmadJaya/KeyTik/releases/latest"
        try:
            response = requests.get(github_api_link, timeout=5) # noqa
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data.get("tag_name")
                if CURRENT_VERSION != latest_version:
                    return latest_version
        except requests.exceptions.ConnectionError:
            pass
        return None

    def show_update_messagebox(self, latest_version):
        "Show message when there is update avaliable"
        reply = QMessageBox.question(
            self, "Update Available",
            (
            f"New update available: KeyTik {latest_version}\n\n"
            "Would you like to go to the update page?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            webbrowser.open("https://github.com/Fajar-RahmadJaya/KeyTik/releases")

    def handle_parser(self, lines):
        "Action when editing profile"
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
        "Action when mode changed from combobox"
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
        "Action when saving profile"
        output_path = os.path.join(self.script_dir, script_name)
        key_translations = self.load_key_translations()

        with open(output_path, 'w', encoding='utf-8') as file:
            if mode == "text mode":
                self.handle_text_mode(file, key_translations)
            elif mode == "default mode":
                self.handle_default_mode(file, key_translations)
            else:
                self.handle_default_mode(file, key_translations)

    def loop_announcefile(self):
        "Loop through announcement file url in order"
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
            except requests.exceptions.RequestException:
                break

    def update_messagebox(self, latest_version, show_no_update_message=False):
        "Message when there is update avalible"
        if latest_version:
            reply = QMessageBox.question(
                self, "Update Available",
                (
                f"New update available: KeyTik {latest_version}\n\"n"
                "Would you like to go to the update page?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open("https://github.com/Fajar-RahmadJaya/KeyTik/releases") # noqa
        else:
            if show_no_update_message:
                QMessageBox.information(
                    self, "Check For Update",
                    "You are using the latest version of KeyTik.")
