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

"""Centralize all icon initialization."""

import os

from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtGui import (  # pylint: disable=E0611
    QColor,
    QIcon,
    QPainter,
    QPalette,
    QPixmap,
)
from PySide6.QtSvg import QSvgRenderer  # pylint: disable=E0611
from PySide6.QtWidgets import QApplication  # pylint: disable=E0611

from keytik.utility import constant
from keytik.utility.style import Palette

icon_cache = {}


def get_icon(path, highlighted=False) -> QIcon:
    """Cache icon."""
    # Get palette
    palette = QApplication.palette()
    text_palette = palette.color(QPalette.Text)
    invert_text_palette = Palette().invert_color(text_palette)
    color = invert_text_palette.name() if highlighted else text_palette.name()

    # Apply color
    cache_key = (path, color)
    if cache_key not in icon_cache:
        renderer = QSvgRenderer(path)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color))
        painter.end()
        icon_cache[cache_key] = QIcon(pixmap)

    return icon_cache[cache_key]


def adaptive_icon(fluent_icon: dict[str, str]):
    """Get fluent icon, fallback to material icon."""
    code_glyph = fluent_icon.get("code_glyph")
    if QIcon().hasThemeIcon(code_glyph):
        return QIcon().fromTheme(code_glyph)

    return get_icon(fluent_icon.get("material_path"))


icon_dir = os.path.join(constant.data_dir, "icon")

# Profile Icon
run = os.path.join(icon_dir, "run.svg")
icon_exit = os.path.join(icon_dir, "exit.svg")
edit = os.path.join(icon_dir, "edit.svg")
rocket = os.path.join(icon_dir, "rocket.svg")
rocket_fill = os.path.join(icon_dir, "rocket_fill.svg")
copy = os.path.join(icon_dir, "copy.svg")
store = os.path.join(icon_dir, "store.svg")
delete = os.path.join(icon_dir, "delete.svg")
pin = os.path.join(icon_dir, "thumbtack.svg")
pin_fill = os.path.join(icon_dir, "thumbtack_fill.svg")

# Main Window Icon
plus = os.path.join(icon_dir, "plus.svg")
icon_next = os.path.join(icon_dir, "next.svg")
prev = os.path.join(icon_dir, "prev.svg")
setting = os.path.join(icon_dir, "setting.svg")
icon_import = os.path.join(icon_dir, "import.svg")
on_top = os.path.join(icon_dir, "on_top.svg")
on_top_fill = os.path.join(icon_dir, "on_top_fill.svg")
show_stored = os.path.join(icon_dir, "show_stored.svg")
show_stored_fill = os.path.join(icon_dir, "show_stored_fill.svg")

# Edit Window Icon
arrow = os.path.join(icon_dir, "arrow.svg")
icon_filter = os.path.join(icon_dir, "filter.svg")
search = os.path.join(icon_dir, "search.svg")
file_search = os.path.join(icon_dir, "file_search.svg")
question = os.path.join(icon_dir, "question.svg")

# Material symbols
# https://github.com/google/material-design-icons
_material_symbols_dir = os.path.join(icon_dir, "material-symbols")
fullscreen = os.path.join(_material_symbols_dir, "fullscreen.svg")
fullscreen_exit = os.path.join(_material_symbols_dir, "fullscreen-exit.svg")
keyboard_arrow_up = os.path.join(_material_symbols_dir, "keyboard_arrow_up.svg")
keyboard_arrow_down = os.path.join(_material_symbols_dir, "keyboard_arrow_down.svg")

# Lucide icons
# https://github.com/lucide-icons/lucide
_lucide_icons_dir = os.path.join(icon_dir, "lucide")
eye_closed = os.path.join(_lucide_icons_dir, "eye-closed.svg")
eye = os.path.join(_lucide_icons_dir, "eye.svg")

# Fluent icons
fluent_setting = {
    "code_glyph": "\ue713",
    "material_path": os.path.join(_material_symbols_dir, "settings.svg"),
}

fluent_save = {
    "code_glyph": "\ue74e",
    "material_path": os.path.join(_material_symbols_dir, "save.svg"),
}

fluent_label = {
    "code_glyph": "\ue932",
    "material_path": os.path.join(_material_symbols_dir, "label.svg"),
}

fluent_input = {
    "code_glyph": "\ue961",
    "material_path": os.path.join(_material_symbols_dir, "touchpad.svg"),
}
fluent_apps = {
    "code_glyph": "\ued35",
    "material_path": os.path.join(_material_symbols_dir, "apps.svg"),
}
fluent_hide = {
    "code_glyph": "\ued1a",
    "material_path": os.path.join(_material_symbols_dir, "visibility_off.svg"),
}

fluent_chevron_right = {
    "code_glyph": "\ue76c",
    "material_path": os.path.join(_material_symbols_dir, "chevron_right.svg"),
}

fluent_globe = {
    "code_glyph": "\ue774",
    "material_path": os.path.join(_material_symbols_dir, "globe.svg"),
}
