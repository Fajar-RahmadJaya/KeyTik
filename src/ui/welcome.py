import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, 
    QTextBrowser, QWidget, QFrame
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from markdown import markdown
import json
from src.utility.constant import (data_dir, icon_path, dont_show_path)

class Welcome:
    def check_welcome(self):
        if self.welcome_condition:
            self.show_welcome_window()

    def load_welcome_condition(self):
        try:
            if os.path.exists(dont_show_path):
                with open(dont_show_path, "r") as f:
                    config = json.load(f)
                    return config.get("welcome_condition", True)  # Default to True if not found
        except Exception as e:
            print(f"Error loading condition file: {e}")
        return True  # Default to True on error

    def save_welcome_condition(self):
        try:
            with open(dont_show_path, "w") as f:
                json.dump({"welcome_condition": self.welcome_condition}, f)
        except Exception as e:
            print(f"Error saving condition file: {e}")

    def show_welcome_window(self):
        try:
            # Get all numbered markdown files
            md_files = [f for f in os.listdir(data_dir) if f.endswith(".md") and f[:-3].isdigit()]
            md_files.sort(key=lambda x: int(x[:-3]))  # Sort numerically (1.md, 2.md, 3.md...)

            # Ensure we have at least a welcome file
            if not md_files:
                md_files = ["welcome.md"]  # Fallback if no numbered files exist

            self.current_welcome_index = 0
            self.welcome_files = [os.path.join(data_dir, f) for f in md_files]

            # Create the welcome window as a dialog
            welcome_dialog = QDialog(self)
            welcome_dialog.setWindowTitle("Readme!")
            welcome_dialog.setGeometry(350, 220, 525, 290)
            welcome_dialog.setWindowIcon(QIcon(icon_path))
            welcome_dialog.setModal(True)
            welcome_dialog.setWindowModality(Qt.WindowModality.WindowModal)  # Make it transient to main window
            welcome_dialog.setFixedSize(525, 290)

            # Main vertical layout
            main_layout = QVBoxLayout(welcome_dialog)
            main_layout.setContentsMargins(10, 10, 10, 10)

            # Detect current theme colors from the application palette
            app_palette = welcome_dialog.palette()
            bg_color = app_palette.window().color().name()
            text_color = app_palette.windowText().color().name()

            # Frame for HTML content
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
                    font-family: 'Open Sans';
                    font-size: 10px;
                    padding: 2px;
                }}
            """)
            html_layout.addWidget(html_label)
            main_layout.addWidget(html_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

            # Navigation and checkbox layout
            button_frame = QWidget()
            button_layout = QHBoxLayout(button_frame)
            button_layout.setContentsMargins(0, 0, 0, 0)

            prev_button = QPushButton("Previous")
            prev_button.setFixedWidth(100)
            next_button = QPushButton("Next")
            next_button.setFixedWidth(100)

            dont_show_checkbox = QCheckBox("Don't show again")
            dont_show_checkbox.setChecked(not self.welcome_condition)  # Checked means don't show
            button_layout.addWidget(prev_button)
            button_layout.addWidget(next_button)
            button_layout.addWidget(dont_show_checkbox)
            main_layout.addWidget(button_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

            def load_content(index):
                try:
                    with open(self.welcome_files[index], "r", encoding="utf-8") as f:
                        md_content = f.read()
                        html_content = markdown(md_content)
                        # Apply styling to paragraphs, headings, and lists, using theme colors
                        html_content = html_content.replace(
                            "<p>", f"<p style='font-family: Open Sans; font-size: 9px; font-weight: 300; margin: 10px; color: {text_color};'>"
                        ).replace(
                            "<h1>",
                            f"<h1 style='font-family: Open Sans; font-size: 18px; font-weight: 600; margin: 10px; color: {text_color};'>"
                        ).replace(
                            "<h2>",
                            f"<h2 style='font-family: Open Sans; font-size: 11px; font-weight: 500; margin: 10px; color: {text_color};'>"
                        ).replace(
                            "<ul>",
                            f"<ul style='font-family: Open Sans; font-size: 9px; font-weight: 300; margin: 10px; color: {text_color};'>"
                        ).replace(
                            "<ol>",
                            f"<ol style='font-family: Open Sans; font-size: 9px; font-weight: 300; margin: 10px; color: {text_color};'>"
                        ).replace(
                            "<li>",
                            f"<li style='font-family: Open Sans; font-size: 9px; font-weight: 300; margin: 10px; color: {text_color};'>"
                        )
                        html_label.setHtml(html_content)
                except FileNotFoundError:
                    html_label.setHtml(
                        f"<p style='font-family: Open Sans; font-size: 10px; font-weight: 300; color: {text_color};'>File not found!</p>"
                    )

            def update_buttons():
                prev_button.setEnabled(self.current_welcome_index > 0)
                next_button.setEnabled(self.current_welcome_index < len(self.welcome_files) - 1)

            def next_page():
                if self.current_welcome_index < len(self.welcome_files) - 1:
                    self.current_welcome_index += 1
                    load_content(self.current_welcome_index)
                    update_buttons()

            def prev_page():
                if self.current_welcome_index > 0:
                    self.current_welcome_index -= 1
                    load_content(self.current_welcome_index)
                    update_buttons()

            def toggle_dont_show():
                # Checked: don't show again (set to False)
                self.welcome_condition = not dont_show_checkbox.isChecked()
                self.save_welcome_condition()

            dont_show_checkbox.stateChanged.connect(toggle_dont_show)

            # Save state when dialog is closed (in case user closes without toggling)
            def on_dialog_close(event):
                self.welcome_condition = not dont_show_checkbox.isChecked()
                self.save_welcome_condition()
                event.accept()
            welcome_dialog.closeEvent = on_dialog_close

            load_content(self.current_welcome_index)
            update_buttons()

            # Ensure dialog is on top and focused
            welcome_dialog.raise_()
            welcome_dialog.activateWindow()
            welcome_dialog.exec()

        except Exception as e:
            print(f"Error displaying welcome window: {e}")