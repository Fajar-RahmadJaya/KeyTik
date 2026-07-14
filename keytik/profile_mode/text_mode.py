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
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPalette, QTextCharFormat, QTextCursor  # pylint: disable=E0611
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QDialog,
    QGridLayout,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from keytik.profile_mode.shortcut_row import ShortcutRow
from keytik.utility import icons, style


class TextMode:
    """Text mode code."""

    def text_mode_widget(self, parent_window: QDialog, edit_frame, lines=None):
        """Build text mode widget."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        layout.addWidget(ShortcutRow(edit_frame).collapsible_shortcuts(parent_window, lines))

        text_block_widget = QWidget()
        layout.addWidget(text_block_widget)

        text_block_layout = QGridLayout()
        text_block_layout.setContentsMargins(0, 0, 0, 0)
        text_block_layout.setSpacing(0)
        text_block_widget.setLayout(text_block_layout)
        text_block = self.text_block(lines)
        text_block_layout.addWidget(text_block, 0, 0, 1, 2)

        expand_button = QToolButton()
        expand_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        expand_button.setIcon(icons.get_icon(icons.fullscreen))
        expand_button.setIconSize(QSize(16, 16))
        expand_button.setToolTip("Maximize")
        expand_button.setFixedSize(40, 40)
        expand_button.setCheckable(True)
        palette = style.get_palette()
        palette.setColor(QPalette.ColorRole.Accent, palette.color(QPalette.ColorRole.Button))
        expand_button.setPalette(palette)
        expand_button.setStyleSheet("""
        QToolButton{
            margin: 8px;
        }
        """)
        text_block_layout.addWidget(expand_button, 0, 1, Qt.AlignTop | Qt.AlignRight)

        edit_layout = parent_window.findChild(QGridLayout)
        prev_layout_margin = edit_layout.contentsMargins()

        def button_click_event():
            """Set expand button icon."""
            ischecked = expand_button.isChecked()

            if ischecked:
                expand_button.setToolTip("Minimize")
                expand_button.setIcon(icons.get_icon(icons.fullscreen_exit))
            else:
                expand_button.setToolTip("Maximize")
                expand_button.setIcon(icons.get_icon(icons.fullscreen))

            self.expand_text_block(parent_window, ischecked, prev_layout_margin)

        expand_button.clicked.connect(button_click_event)

        return widget

    def expand_text_block(self, parent_window: QDialog, ischecked, prev_layout_margin):
        """Hide other widget except text block."""
        hidden = bool(ischecked)

        edit_layout = parent_window.findChild(QGridLayout)
        if ischecked:
            edit_layout.setContentsMargins(0, 0, 0, 0)
        else:
            edit_layout.setContentsMargins(prev_layout_margin)

        top_widget = parent_window.findChild(QWidget, "TopWidget")
        top_widget.setHidden(hidden)

        bottom_widget = parent_window.findChild(QWidget, "BottomWidget")
        bottom_widget.setHidden(hidden)

        middle_stack = parent_window.findChild(QStackedWidget)
        collapsible_shortcut = middle_stack.widget(1).findChild(QWidget)
        collapsible_shortcut.setHidden(hidden)

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
