"Load online announcement from KeyTik Website"

import os
import json
import requests
from markdown import markdown
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton,
    QTextBrowser, QWidget, QFrame
)
from PySide6.QtGui import QIcon  # pylint: disable=E0611
from PySide6.QtCore import Qt  # pylint: disable=E0611
from utility import constant
from utility import diff


class Announcement():
    "Announcement"
    def __init__(self):
        super().__init__()
        self.announcement_files = []
        self.current_announcement_index = 0
        self.announcement_condition = None

        self.announcement_dialog = QDialog()

    def load_announcement_condition(self):
        "Load user preference from file, whether to show announcement or not"
        try:
            if os.path.exists(constant.dont_show_path):
                with open(constant.dont_show_path, "r", encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("welcome_condition", True)
        except FileNotFoundError as e:
            print(f"Error loading condition file: {e}")
        return True

    def get_announcement_url(self):
        "Loop through announcement file url in order and stop when url invalid"
        self.announcement_files = []
        i = 1
        while True:
            url = f"{diff.ANNOUNCEMENT_LINK}/{i}.txt"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 404:
                    break
                response.raise_for_status()
                self.announcement_files.append(url)
                i += 1
            except requests.exceptions.RequestException:
                break

    def show_announcement_window(self):
        "Announcement window"
        try:
            self.get_announcement_url()
            self.current_announcement_index = 0

            self.announcement_dialog = QDialog(self)
            self.announcement_dialog.setWindowTitle("Announcement")
            self.announcement_dialog.setFixedSize(525, 290)
            self.announcement_dialog.setWindowIcon(QIcon(constant.icon_path))
            self.announcement_dialog.setModal(True)
            self.announcement_dialog.setWindowModality(
                Qt.WindowModality.WindowModal)
            self.announcement_dialog.setFixedSize(525, 290)

            main_layout = QVBoxLayout(self.announcement_dialog)
            main_layout.setContentsMargins(10, 10, 10, 10)

            app_palette = self.announcement_dialog.palette()
            bg_color = app_palette.window().color().name()
            text_color = app_palette.windowText().color().name()

            html_frame = QFrame()
            html_frame.setFrameShape(QFrame.Shape.StyledPanel)
            html_frame.setFrameShadow(QFrame.Shadow.Sunken)
            html_frame.setFixedSize(500, 230)
            html_frame.setStyleSheet(f"""
                QFrame {{
                    border: 1px solid {text_color};
                    border-radius: 3px;
                    background-color: {bg_color};
                }}
            """)

            html_layout = QVBoxLayout(html_frame)
            html_layout.setContentsMargins(5, 5, 5, 5)

            html_label = QTextBrowser(html_frame)
            html_label.setOpenExternalLinks(True)
            html_label.setStyleSheet(f"""
                QTextBrowser {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: none;
                    font-family: 'Segoe UI';
                    padding: 2px;
                }}
            """)

            if self.announcement_files:
                # Set html_label text
                self.load_content(self.current_announcement_index, html_label)
            else:
                html_label.setHtml(
                    "<p>Unable to load announcements.</p>"
                )

            html_layout.addWidget(html_label)
            main_layout.addWidget(
                html_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

            button_frame = self.announcement_button_frame(html_label)

            main_layout.addWidget(
                button_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

            self.announcement_dialog.raise_()
            self.announcement_dialog.activateWindow()
            self.announcement_dialog.exec()

        except requests.HTTPError as e:
            print(f"Error displaying announcement window: {e}")

    def announcement_content_frame(self):
        "Frame that hold announcement content"

    def load_content(self, index, html_label):
        "Get announcement content from official website"
        try:
            url = self.announcement_files[index]
            if url in constant.announcement_cache:
                md_content = constant.announcement_cache[url]
            else:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                md_content = response.text
                constant.announcement_cache[url] = md_content
            html_content = markdown(md_content)
            styling = """
            <style>
            ol { -qt-list-indent: 1; margin-left: -20px; padding-left: 0px; } # noqa
            ol li { margin-left: -5px; padding-left: 0px; }
            </style>
            """
            html_label.setHtml(styling + html_content)
        except requests.HTTPError:
            html_label.setHtml(
                "<p>File not found.</p>" # noqa
            )

    def announcement_button_frame(self, html_label):
        "Button and checkbox"
        button_frame = QWidget()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)

        prev_button = QPushButton("Previous")
        prev_button.setFixedWidth(100)
        prev_button.setEnabled(self.current_announcement_index > 0)
        prev_button.clicked.connect(lambda: self.prev_doc(html_label, prev_button, next_button))
        button_layout.addWidget(prev_button)

        next_button = QPushButton("Next")
        next_button.setFixedWidth(100)
        next_button.clicked.connect(lambda: self.next_doc(html_label, prev_button, next_button))
        button_layout.addWidget(next_button)

        dont_show_checkbox = QCheckBox("Don't show again")
        dont_show_checkbox.setChecked(not self.load_announcement_condition())
        dont_show_checkbox.stateChanged.connect(
            lambda: self.save_announcement_condition(dont_show_checkbox))
        button_layout.addWidget(dont_show_checkbox)
        return button_frame

    def save_announcement_condition(self, dont_show_checkbox):
        "Save user preference on file when don't show announcement checkbox is checked"
        self.announcement_condition = (
            not dont_show_checkbox.isChecked())

        try:
            with open(constant.dont_show_path, "w", encoding='utf-8') as f:
                json.dump({"welcome_condition":
                            self.announcement_condition}, f)
        except FileNotFoundError as e:
            print(f"Error saving condition file: {e}")

    def update_buttons(self, prev_button, next_button):
        "Update button enable/disable state"
        prev_button.setEnabled(self.current_announcement_index > 0)
        next_button.setEnabled(
            self.current_announcement_index < len(
                self.announcement_files) - 1)

    def next_doc(self, html_label, prev_button, next_button):
        "Next announcement"
        if self.current_announcement_index < len(
                self.announcement_files) - 1:
            self.current_announcement_index += 1
            self.load_content(self.current_announcement_index, html_label)
            self.update_buttons(prev_button, next_button)

    def prev_doc(self, html_label, prev_button, next_button):
        "previous announcement"
        if self.current_announcement_index > 0:
            self.current_announcement_index -= 1
            self.load_content(self.current_announcement_index, html_label)
            self.update_buttons(prev_button, next_button)
