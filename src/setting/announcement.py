"Load online announcement from KeyTik Website"

import os
import json
import requests
from markdown import markdown
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton,
    QTextBrowser, QWidget, QFrame)
from PySide6.QtGui import QIcon  # pylint: disable=E0611
from PySide6.QtCore import Qt, QThread, Signal  # pylint: disable=E0611

from utility import constant
from utility import diff


class AnnouncmentThread(QThread):  # pylint: disable=R0903
    "Worker to run get announcement url"
    url_found = Signal()
    def __init__(self):
        super().__init__()
        self.announcement_files = []

    def run(self):
        "Overwrite run method"
        # Loop through announcement file url in order and stop when url invalid
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

        for url in self.announcement_files:
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                md_content = response.text
                constant.announcement_cache[url] = md_content
            except requests.HTTPError:
                constant.announcement_cache[url] = "File not found."

        self.url_found.emit()

class Announcement():
    "Announcement"
    def __init__(self):
        self.current_announcement_index = 0
        self.announcement_thread = AnnouncmentThread()

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

    def show_announcement_window(self, parent):
        "Announcement window"
        try:
            self.current_announcement_index = 0

            announcement_dialog = QDialog(parent)
            announcement_dialog.setWindowTitle("Announcement")
            announcement_dialog.setFixedSize(525, 290)
            announcement_dialog.setWindowIcon(QIcon(constant.icon_path))
            announcement_dialog.setModal(True)
            announcement_dialog.setWindowModality(
                Qt.WindowModality.WindowModal)
            announcement_dialog.setFixedSize(525, 290)

            main_layout = QVBoxLayout(announcement_dialog)
            main_layout.setContentsMargins(10, 10, 10, 10)

            app_palette = announcement_dialog.palette()
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

            html_label.setHtml(
                "<p>Fetching Announcement . . .</p>"
            )

            html_layout.addWidget(html_label)
            main_layout.addWidget(
                html_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

            button_frame = self.announcement_button_frame(html_label)

            main_layout.addWidget(
                button_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

            announcement_dialog.raise_()
            announcement_dialog.activateWindow()
            announcement_dialog.exec()

        except requests.HTTPError as e:
            print(f"Error displaying announcement window: {e}")

    def load_content(self, index, html_label, prev_button, next_button):
        "Get announcement content from official website"
        url = self.announcement_thread.announcement_files[index]
        md_content = constant.announcement_cache[url]
        html_content = markdown(md_content)
        styling = """
        <style>
        ol { -qt-list-indent: 1; margin-left: -20px; padding-left: 0px; }
        ol li { margin-left: -5px; padding-left: 0px; }
        </style>
        """
        html_label.setHtml(styling + html_content)

        prev_button.setEnabled(self.current_announcement_index > 0)
        next_button.setEnabled(
            self.current_announcement_index < len(self.announcement_thread.announcement_files) - 1)

    def next_doc(self, html_label, prev_button, next_button):
        "Next announcement"
        if self.current_announcement_index < len(self.announcement_thread.announcement_files) - 1:
            self.current_announcement_index += 1
            self.load_content(self.current_announcement_index, html_label, prev_button, next_button)

    def prev_doc(self, html_label, prev_button, next_button):
        "previous announcement"
        if self.current_announcement_index > 0:
            self.current_announcement_index -= 1
            self.load_content(self.current_announcement_index, html_label, prev_button, next_button)

    def announcement_button_frame(self, html_label):
        "Button and checkbox"
        button_frame = QWidget()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)

        prev_button = QPushButton("Previous")
        prev_button.setFixedWidth(100)
        prev_button.setEnabled(False)
        prev_button.clicked.connect(lambda: self.prev_doc(html_label, prev_button, next_button))
        button_layout.addWidget(prev_button)

        next_button = QPushButton("Next")
        next_button.setFixedWidth(100)
        next_button.setEnabled(False)
        next_button.clicked.connect(lambda: self.next_doc(html_label, prev_button, next_button))
        button_layout.addWidget(next_button)

        dont_show_checkbox = QCheckBox("Don't show again")
        dont_show_checkbox.setChecked(not self.load_announcement_condition())
        dont_show_checkbox.stateChanged.connect(
            lambda: self.save_announcement_condition(dont_show_checkbox))
        button_layout.addWidget(dont_show_checkbox)

        # After get_announcement_url done, call load content to overwrite html content
        self.announcement_thread.url_found.connect(
            lambda: self.load_content(self.current_announcement_index, html_label,
                                      prev_button, next_button)
        )

        # Start thread running get_annoucement_url
        self.announcement_thread.start()

        return button_frame

    def save_announcement_condition(self, dont_show_checkbox):
        "Save user preference on file when don't show announcement checkbox is checked"
        announcement_condition = not dont_show_checkbox.isChecked()
        try:
            with open(constant.dont_show_path, "w", encoding='utf-8') as f:
                json.dump({"welcome_condition":
                            announcement_condition}, f)
        except FileNotFoundError as e:
            print(f"Error saving condition file: {e}")
