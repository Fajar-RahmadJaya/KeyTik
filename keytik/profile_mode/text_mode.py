# Copyright 2024 Fajar Rahmad Jaya
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Text mode."""

import json

from pyqcodeeditor import utils as pyqcodeeditor_utils
from pyqcodeeditor.QCodeEditor import QCodeEditor
from pyqcodeeditor.QSyntaxStyle import QSyntaxStyle
from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtGui import QPalette, QTextCharFormat, QTextCursor  # pylint: disable=E0611
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QFrame,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from keytik.profile_manager.parse_script import ParseScript
from keytik.profile_mode.shortcut_row import ShortcutRow
from keytik.utility import style


class TextMode:
    """Text mode code."""

    def text_mode_widget(self, parent_window, edit_frame, lines=None):
        """Build text mode widget."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        layout.addWidget(self.collapsible_shortcuts(parent_window, edit_frame, lines))
        layout.addWidget(self.text_block(lines))

        return widget

    def collapsible_shortcuts(self, parent_window, edit_frame, lines=None):
        """Hide or unhide shortcuts."""
        widget = QWidget()
        widget.setObjectName("shortcutHeader")
        widget.setStyleSheet("""
        QWidget#shortcutHeader {
            border: 1px solid #444;
            border-radius: 4px;
        }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        widget.setLayout(layout)

        palette = style.get_palette()
        hover_palette = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Midlight)

        header_button = QPushButton()
        header_button.setText("Expand Shortcut")
        header_button.setStyleSheet(f"""
        QPushButton{{
            border: none;
            font-size: 13px;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: {hover_palette.name()};
            border-radius: 4px;
        }}
        """)
        header_button.setFixedHeight(28)
        header_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(header_button)

        shortcut_scrollview = QScrollArea()
        shortcut_scrollview.setWidgetResizable(True)
        shortcut_scrollview.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        shortcut_scrollview.setObjectName("editScroll")
        shortcut_scrollview.setFrameShape(QFrame.Shape.NoFrame)
        shortcut_scrollview.setStyleSheet("""
            #editScroll {
                background-color: transparent;
                margin: 8px;
            }
        """)
        shortcut_scrollview.setFixedHeight(140)
        shortcut_scrollview.setHidden(True)
        layout.addWidget(shortcut_scrollview)

        parsed_shortcuts_list = ParseScript().parse_shortcuts(lines) if lines else None
        shortcut_row_widget = ShortcutRow(edit_frame).shortcut_row(
            parent_window, parsed_shortcuts_list, title=False
        )
        shortcut_scrollview.setWidget(shortcut_row_widget)

        def button_event():
            """Hide shortcut scrollview."""
            if not shortcut_scrollview.isHidden():
                shortcut_scrollview.setHidden(True)
                header_button.setText("Expand Shortcut")
            else:
                shortcut_scrollview.setHidden(False)
                header_button.setText("Collapse Shortcut")

        header_button.clicked.connect(button_event)

        return widget

    def text_block(self, lines=None):
        """Text mode frame."""
        palette = style.get_palette()

        default_style = pyqcodeeditor_utils.get_resource_file("default_style.json")
        try:
            with open(default_style, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print("Can't load pyqcodeeditor default style")

        for item in data.get("style", []):
            if item.get("name") == "Text":
                item["background"] = palette.color(
                    QPalette.ColorGroup.Active, QPalette.ColorRole.Base
                ).name()
                item["foreground"] = palette.color(
                    QPalette.ColorGroup.Active, QPalette.ColorRole.Text
                ).name()
            if item.get("name") == "Selection":
                item["background"] = palette.color(
                    QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight
                ).name()
                item["foreground"] = palette.color(
                    QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText
                ).name()

        syntax_style = QSyntaxStyle()
        syntax_style._processStyleSchema(data)  # pylint: disable=w0212

        code_editor = QCodeEditor()
        code_editor.setSyntaxStyle(syntax_style)
        code_editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        text_content = self.extract_and_filter_content(lines).strip() if lines else None
        code_editor.setPlainText(text_content)
        code_editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.highlight_line(code_editor)
        code_editor.cursorPositionChanged.connect(lambda: self.highlight_line(code_editor))
        return code_editor

    def highlight_line(self, code_editor: QTextEdit) -> QTextEdit.ExtraSelection:
        """Highlight line containing (keytik: highlight)."""
        selections = []
        highlight_syntax = "(keytik: highlight)"
        text_document = code_editor.document()
        line = text_document.firstBlock()

        palette = style.get_palette()
        accent = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Accent)
        accent.setAlpha(20)

        while line.isValid():
            text = line.text()
            if (
                highlight_syntax in text
                and ";" in text
                and text.index(";") < text.index(highlight_syntax)
            ):
                selection = QTextEdit.ExtraSelection()

                text_format = QTextCharFormat()
                text_format.setBackground(accent)

                selection.format = text_format
                selection.cursor = QTextCursor(line)
                selection.cursor.clearSelection()
                selection.cursor.select(QTextCursor.SelectionType.LineUnderCursor)

                selections.append(selection)

            line = line.next()

        code_editor.setExtraSelections(selections)

    def extract_and_filter_content(self, lines):
        """Get text block value from the marker."""
        inside = False
        result_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped == "; Text mode start":
                inside = True
                continue
            if stripped == "; Text mode end":
                inside = False
                continue
            if inside:
                result_lines.append(line)

        return "".join(result_lines)
