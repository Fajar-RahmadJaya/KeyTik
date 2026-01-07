import os
import json
import requests
from markdown import markdown
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton,
    QTextBrowser, QWidget, QFrame
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import utility.constant as constant
from utility.diff import Diff


class Announcement(Diff):
    def load_announcement_condition(self):
        try:
            if os.path.exists(constant.dont_show_path):
                with open(constant.dont_show_path, "r") as f:
                    config = json.load(f)
                    return config.get("welcome_condition", True)
        except Exception as e:
            print(f"Error loading condition file: {e}")
        return True

    def save_announcement_condition(self):
        try:
            with open(constant.dont_show_path, "w") as f:
                json.dump({"welcome_condition":
                           self.announcement_condition}, f)
        except Exception as e:
            print(f"Error saving condition file: {e}")

    def show_announcement_window(self):
        try:
            self.announcement_files = []
            self.loop_announcefile()
            self.current_announcement_index = 0

            announcement_dialog = QDialog(self)
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
            html_layout.addWidget(html_label)
            main_layout.addWidget(
                html_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

            button_frame = QWidget()
            button_layout = QHBoxLayout(button_frame)
            button_layout.setContentsMargins(0, 0, 0, 0)

            prev_button = QPushButton("Previous")
            prev_button.setFixedWidth(100)
            next_button = QPushButton("Next")
            next_button.setFixedWidth(100)

            dont_show_checkbox = QCheckBox("Don't show again")
            dont_show_checkbox.setChecked(not self.announcement_condition)
            button_layout.addWidget(prev_button)
            button_layout.addWidget(next_button)
            button_layout.addWidget(dont_show_checkbox)
            main_layout.addWidget(
                button_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

            def load_content(index):
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
                        f"<p>File not found.</p>" # noqa
                    )

            def update_buttons():
                prev_button.setEnabled(self.current_announcement_index > 0)
                next_button.setEnabled(
                    self.current_announcement_index < len(
                        self.announcement_files) - 1)

            def next_doc():
                if self.current_announcement_index < len(
                       self.announcement_files) - 1:
                    self.current_announcement_index += 1
                    load_content(self.current_announcement_index)
                    update_buttons()

            def prev_doc():
                if self.current_announcement_index > 0:
                    self.current_announcement_index -= 1
                    load_content(self.current_announcement_index)
                    update_buttons()

            prev_button.clicked.connect(prev_doc)
            next_button.clicked.connect(next_doc)

            def toggle_dont_show():
                self.announcement_condition = (
                    not dont_show_checkbox.isChecked())
                self.save_announcement_condition()

            dont_show_checkbox.stateChanged.connect(toggle_dont_show)

            def on_dialog_close(event):
                self.announcement_condition = (
                    not dont_show_checkbox.isChecked())
                self.save_announcement_condition()
                event.accept()
            announcement_dialog.closeEvent = on_dialog_close

            if self.announcement_files:
                load_content(self.current_announcement_index)
                update_buttons()
            else:
                html_label.setHtml(
                    "<p>Unable to load announcements. Please check your internet connection.</p>" # noqa
                )

            announcement_dialog.raise_()
            announcement_dialog.activateWindow()
            announcement_dialog.exec()

        except Exception as e:
            print(f"Error displaying announcement window: {e}")
