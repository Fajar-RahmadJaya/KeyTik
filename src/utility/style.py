"Contain styling code"

from dataclasses import dataclass
import sys
import winreg
from PySide6.QtGui import QPalette, QColor  # pylint: disable=E0611
from PySide6.QtCore import QRect, Qt  # pylint: disable=E0611
from PySide6.QtWidgets import QPushButton, QApplication  # pylint: disable=E0611

import qt_themes
import win32mica

from utility import utils

# ---------------------------- Palatte ------------------------------
def color_rgba(color: QColor, alpha: float):
    "Transform QColor into RGBA"
    red = color.red()
    green = color.green()
    blue = color.blue()

    rgba = f"rgba({red}, {green}, {blue}, {alpha})"
    return rgba

def invert_color(color: QColor):
    "Change color to the oposite of it"
    inverted_color = QColor(255 - color.red(), 255 - color.green(),
    255 - color.blue(), color.alpha())

    return inverted_color

def detect_system_theme():
    "Detecting system theme for Pyside6 default theme handling"
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

@dataclass
class Palette:
    "Dataclass to hold palette used on styling"
    surface: str
    mantle: str
    subtext: str
    overlay: str

def get_palette():
    "Get color palette on various theme"
    config = utils.get_config()
    theme = detect_system_theme() if config.theme == "system" else config.theme

    if theme == "dark":
        surface = "rgba(255, 255, 255, 0.06)"
        mantle = "rgba(255, 255, 255, 0.11)"
        subtext = "rgba(255, 255, 255, 0.566)"
        overlay = "rgba(255, 255, 255, 0.085)"
    elif theme == "light":
        surface = "rgba(255, 255, 255, 0.7)"
        mantle = "rgba(0, 0, 0, 0.06)"
        subtext = "rgba(0, 0, 0, 0.6)"
        overlay = "rgba(0, 0, 0, 0.04)"
    else:
        qt_theme_dict = qt_themes.get_theme(theme)
        surface = qt_theme_dict.surface0.name()
        mantle = qt_theme_dict.mantle.name()
        subtext = qt_theme_dict.subtext0.name()
        overlay = qt_theme_dict.overlay0.name()

    palette = Palette(
        surface=surface,
        mantle=mantle,
        subtext=subtext,
        overlay=overlay
    )

    return palette

PALETTE = get_palette()

mica_supported = bool(sys.getwindowsversion().build >= 22000)
def apply_mica(target_window):
    "Apply mica style on target window using win32mica"
    config = utils.get_config()
    mica_effect = config.mica_effect
    theme = detect_system_theme() if config.theme not in ("dark", "light") else config.theme

    if mica_effect != "disable" and mica_supported:
        target_window.setAttribute(Qt.WA_TranslucentBackground)
        win32mica.ApplyMica(
            HWND=int(target_window.winId()),
            Theme=getattr(win32mica.MicaTheme, theme.upper()),
            Style=getattr(win32mica.MicaStyle, mica_effect.upper())
        )

def set_appearance(app: QApplication):
    "Set global appearance based on user config using palette and style"
    # Variables
    config = utils.get_config()
    theme = config.theme

    # Only set accent palatte if mica enabled and using qt-themes
    qt_themes_dict = qt_themes.get_themes()
    if (config.mica_effect != "disable"
        and config.theme not in ("light", "dark", "system")):

        palette = QPalette()
        accent_palette = qt_themes.get_theme(config.theme).secondary
        palette.setColor(QPalette.ColorRole.Accent, QColor(accent_palette))
        app.setPalette(palette)

    # Set the style and theme
    style_config = utils.get_config().style
    if theme in ("dark", "light"):
        app.setStyle(style_config)
    elif any(theme in theme_name for theme_name, _ in qt_themes_dict.items()):
        qt_themes.set_theme(theme, style_config)

# ---------------------------- Styling ------------------------------
def get_geometry(parent_window, width, height):
    "Get x and y centered relative to parent window"
    parent_geometry = parent_window.geometry()
    parent_x = parent_geometry.x()
    parent_y = parent_geometry.y()
    parent_width = parent_geometry.width()
    parent_height = parent_geometry.height()

    x = parent_x + (parent_width - width) // 2
    y = parent_y + (parent_height - height) // 2
    return QRect(x, y, width, height)

# -------------------- Shared --------------------
WIN11_BUTTON = f"""
QPushButton{{
    background-color: {PALETTE.surface};
    border: 1px solid {PALETTE.mantle};
    border-radius: 4px;
    margin: 2px;
}}

QPushButton:hover {{
    background-color: {PALETTE.overlay};
}}
"""

def card(object_name=None):
    "Card like styling"
    if object_name == "setting":
        border_radius = 4
        widget = f"QFrame#{object_name}"
    else:
        border_radius = 8
        widget = "QFrame"

    style_sheet = f"""
    {widget} {{
        background: {PALETTE.surface};
        border-radius: {border_radius};
    }}
    """

    return style_sheet

# -------------------- Dashboard --------------------
PROFILE_ROW_LABEL = "font-size: 13px; font-weight: bold;"
TEXT_BLOCK = "font-family: Consolas; font-size: 10pt;"
PLUS_LABEL = """
    color: gray;
    padding: 0 5px;
    font-size: 14px;
    font-weight: bold;
"""
GROUP_BOX = f"""
QGroupBox {{
    background-color: {PALETTE.surface};
    border: 1px solid {PALETTE.mantle};
    border-radius: 8;
    margin-top: 1.5ex;
}}

QGroupBox:title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
}}"""

# -------------------- Setting --------------------
HEADING_STYLE = "font-size:13px; margin-bottom:2px"
SUBHEADING_STYLE = f"font-size:11px; color: {PALETTE.subtext};"

def button_highlight(button: QPushButton):
    "Highlighted button, use accent color"
    accent = button.palette().color(QPalette.Accent)
    accent_hover = f"rgba({accent.red()}, {accent.green()}, {accent.blue()}, 0.85)"

    button_text = button.palette().color(QPalette.ButtonText)
    invert_button_text = invert_color(button_text)

    style_sheet = f"""
    QPushButton {{
        background-color: {accent.name()};
        color: {invert_button_text.name()};
    }}
    QPushButton:hover {{
        background-color: {accent_hover};
        color: {invert_button_text.name()};
    }}
    """

    return style_sheet
