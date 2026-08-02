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

"""Contain styling code."""

import json
import os
import sys
import winreg
from dataclasses import dataclass

import qt_themes
import win32mica
from PySide6.QtCore import QRect, Qt  # pylint: disable=E0611
from PySide6.QtGui import QColor, QPalette  # pylint: disable=E0611

from keytik.utility import constant, utils


# ---------------------------- Palatte ------------------------------
def color_rgba(color: QColor, alpha: float):
    """Transform QColor into RGBA."""
    red = color.red()
    green = color.green()
    blue = color.blue()

    rgba = f"rgba({red}, {green}, {blue}, {alpha})"
    return rgba


def invert_color(color: QColor):
    """Change color to the oposite of it."""
    inverted_color = QColor(
        255 - color.red(), 255 - color.green(), 255 - color.blue(), color.alpha()
    )

    return inverted_color


def is_light(color: QColor) -> bool:
    """Determine whether the color is dark or light."""
    threshold = 0.5
    r = color.red() / 255.0
    g = color.green() / 255.0
    b = color.blue() / 255.0
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

    return luminance > threshold


def detect_system_theme():
    """Detecting system theme for Pyside6 default theme handling."""
    if sys.platform == "win32":
        try:
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            theme_registry = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            key = winreg.OpenKey(registry, theme_registry)
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "dark" if value == 0 else "light"
        except FileNotFoundError:
            print("Theme registry not found.")
    return "light"


WINDOWS_BUILD_NUMBER = 22000
mica_supported = bool(sys.getwindowsversion().build >= WINDOWS_BUILD_NUMBER)


def apply_mica(target_window):
    """Apply mica style on target window using win32mica."""
    config = utils.get_config()
    mica_effect = config.mica_effect
    palette = get_palette()
    is_base_light = is_light(palette.color(QPalette.ColorRole.Base))
    theme = "LIGHT" if is_base_light else "DARK"

    if mica_effect != "disable" and mica_supported:
        target_window.setAttribute(Qt.WA_TranslucentBackground)
        win32mica.ApplyMica(
            HWND=int(target_window.winId()),
            Theme=getattr(win32mica.MicaTheme, theme),
            Style=getattr(win32mica.MicaStyle, mica_effect.upper()),
        )


def set_custom_palette(palette: QPalette):
    """Apply custom theme to QPalette."""
    config = utils.get_config()
    theme_file = os.path.join(constant.theme_dir, config.theme + ".json")

    try:
        with open(theme_file, encoding="utf-8") as file:
            theme_dict = json.load(file)
    except FileNotFoundError as error:
        print(f"Error: {error}")
        theme_dict = None

    # Create palette
    for color_group, color_role in theme_dict.items():
        if color_group != "attribution":
            for role, color in color_role.items():
                palette.setColor(
                    getattr(palette.ColorGroup, color_group),
                    getattr(palette.ColorRole, role),
                    QColor(color),
                )

                # Set color goup inactive the same as active
                palette.setColor(
                    palette.ColorGroup.Inactive,
                    getattr(palette.ColorRole, role),
                    QColor(color),
                )

    return palette


def set_accent(palette: QPalette):
    """Apply accent to QPalette."""
    accent = utils.get_config().accent

    if accent != "default":
        palette.setColor(QPalette.ColorRole.Accent, QColor(accent))


def get_palette() -> QPalette:
    """Set global appearance based on user config using palette and style."""
    # Variables
    config = utils.get_config()
    theme_type = config.theme_type
    theme = config.theme

    # Apply palette
    palette = QPalette()
    if theme_type == "default":
        set_accent(palette)
    elif theme_type == "qt-themes":
        qt_theme = qt_themes.get_theme(theme)
        # Apply qt_themes palette
        qt_themes.update_palette(palette=palette, theme=qt_theme)
        # Overwrite qt-themes accent palette
        set_accent(palette)
    elif theme_type == "custom":
        set_custom_palette(palette)
        set_accent(palette)

    return palette


PALETTE = get_palette()
IS_BASE_LIGHT = is_light(PALETTE.color(QPalette.Base))


@dataclass
class _PaletteRole:
    """Dataclass to hold palette used on styling."""

    surface: str
    mantle: str
    subtext: str
    overlay: str
    base_rgba: str


def get_palette_role():
    """Get color palette on various theme."""
    config = utils.get_config()
    theme = config.theme
    if theme == "light" or IS_BASE_LIGHT:
        surface = "rgba(255, 255, 255, 0.7)"
        mantle = "rgba(0, 0, 0, 0.06)"
        subtext = "rgba(0, 0, 0, 0.6)"
        overlay = "rgba(0, 0, 0, 0.04)"
        base_rgba = "rgba(255, 255, 255, 0.7)"
    elif theme == "dark" or not IS_BASE_LIGHT:
        surface = "rgba(255, 255, 255, 0.06)"
        mantle = "rgba(255, 255, 255, 0.11)"
        subtext = "rgba(255, 255, 255, 0.566)"
        overlay = "rgba(255, 255, 255, 0.085)"
        base_rgba = "rgba(255, 255, 255, 9)"
    else:
        surface = None
        mantle = None
        subtext = None
        overlay = None
        base_rgba = None

    role = _PaletteRole(
        surface=surface, mantle=mantle, subtext=subtext, overlay=overlay, base_rgba=base_rgba
    )

    return role


palette_role = get_palette_role()


# ---------------------------- Styling ------------------------------
def get_geometry(parent_window, width, height):
    """Get x and y centered relative to parent window."""
    parent_geometry = parent_window.geometry()
    parent_x = parent_geometry.x()
    parent_y = parent_geometry.y()
    parent_width = parent_geometry.width()
    parent_height = parent_geometry.height()

    x = parent_x + (parent_width - width) // 2
    y = parent_y + (parent_height - height) // 2
    return QRect(x, y, width, height)


# -------------------- Shared Stylesheet --------------------
# --- This stylesheet mimix Win11 button style assigned by QT. ---
# --- Currently unused ---
# WIN11_BUTTON = f"""
# QPushButton{{
#     background-color: {COLOR.surface};
#     border: 1px solid {COLOR.mantle};
#     border-radius: 4px;
#     margin: 2px;
# }}

# QPushButton:hover {{
#     background-color: {COLOR.overlay};
# }}
# """


def get_global_stylesheet():
    """Get widget global stylesheet."""
    stylesheet = []
    config = utils.get_config()

    global_treeview = f"""
    QTreeWidget {{
        background-color: {palette_role.base_rgba};
    }}

    QHeaderView {{
        background-color: rgba(255, 255, 255, 0.07)
    }}
    """

    stylesheet.append(button_highlight(style_sheet=True))

    # Only set global tree view on dark mica
    if config.mica_effect != "disable" and mica_supported and config.theme == "dark":
        stylesheet.append(global_treeview)

    return "\n".join(stylesheet)


TREEVIEW = """
QHeaderView::down-arrow, QHeaderView::up-arrow {
    subcontrol-position: center right;
    width: 8;
    height: 8;
    margin-right: 16;
}
"""


def card(object_name=None):
    """Card like styling."""
    if object_name == "setting":
        border_radius = 4
        widget = f"QFrame#{object_name}"
    else:
        border_radius = 8
        widget = "QFrame"

    style_sheet = f"""
    {widget} {{
        background: {palette_role.surface};
        border-radius: {border_radius};
    }}
    """

    return style_sheet


PROFILE_ROW_LABEL = "font-size: 13px; font-weight: bold;"
GROUP_BOX = f"""
QGroupBox {{
    background-color: {palette_role.surface};
    border: 1px solid {palette_role.mantle};
    border-radius: 8;
    margin-top: 1.5ex;
    margin-right: 5px;
}}

QGroupBox:title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 26px;
}}"""


def button_highlight(style_sheet=False):
    """Pass empty parameter to get object name only."""
    object_name = "ButtonHighlight"

    if not style_sheet:
        return object_name

    palette = get_palette()
    accent = palette.color(QPalette.Accent)

    button_text = palette.color(QPalette.ButtonText)
    invert_button_text = invert_color(button_text)

    style_sheet = f"""
    QPushButton#{object_name} {{
        background-color: {accent.name()};
        color: {invert_button_text.name()};
    }}
    QPushButton#{object_name}::hover {{
        background-color: {color_rgba(accent, 0.85)};
        color: {invert_button_text.name()};
    }}
    """

    return style_sheet


def option_header_style(isclicked: bool = False):
    """Get remap option header stylesheet."""
    midlight = get_palette().color(QPalette.ColorGroup.Active, QPalette.ColorRole.Midlight)

    header_style = f"""
    QPushButton {{
        border-radius: 0px;
    }}
    QPushButton:hover {{
        background-color: {midlight.name()}
    }}
    """

    header_clicked_style = f"""
    QPushButton {{
        border-radius: 0px;
        background-color: {palette_role.surface}
    }}
    QPushButton:hover {{
        background-color: {midlight.name()}
    }}
    """

    return header_clicked_style if isclicked else header_style
