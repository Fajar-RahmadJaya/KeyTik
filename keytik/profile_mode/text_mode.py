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
from PySide6.QtGui import QPalette  # pylint: disable=E0611

from keytik.utility import style


class TextMode:
    """Text mode code."""

    def text_block(self, lines=None):
        """Text mode frame(to do: fix)."""
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

        text_content = self.extract_and_filter_content(lines).strip() if lines else None
        code_editor.setPlainText(text_content)

        return code_editor

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
