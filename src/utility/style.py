"Contain styling code"

import sys
import winreg
from PySide6.QtGui import QPalette, QColor  # pylint: disable=E0611
from PySide6.QtCore import QRect, Qt  # pylint: disable=E0611
import qt_themes
import win32mica

from utility import utils

# ---------------------------- Utility ------------------------------
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

mica_supported = bool(sys.getwindowsversion().build >= 22000)

def get_theme():
    "Add system to the theme"
    config = utils.get_config()

    if config.theme == "system":
        theme = detect_system_theme()
    elif config.theme in ("light", "dark"):
        theme = config.theme
    else:
        if config.mica_effect != "disable":
            theme = detect_system_theme()
        else:
            theme = config.theme

    return theme

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

def apply_mica(target_window):
    "Apply mica style on target window using win32mica"
    theme = get_theme().upper()
    mica_effect = utils.get_config().mica_effect.upper()

    if mica_effect != "DISABLE" and mica_supported:
        target_window.setAttribute(Qt.WA_TranslucentBackground)
        win32mica.ApplyMica(
            HWND=int(target_window.winId()),
            Theme=getattr(win32mica.MicaTheme, theme),
            Style=getattr(win32mica.MicaStyle, mica_effect)
        )

def invert_color(color):
    "Change color to the oposite of it"
    inverted_color = QColor(255 - color.red(), 255 - color.green(),
    255 - color.blue(), color.alpha())

    return inverted_color

# ---------------------------- Variables ----------------------------
THEME = get_theme()

if THEME == "dark":
    SURFACE0 = "rgba(255, 255, 255, 0.052)"
    MANTLE = "rgba(255, 255, 255, 0.18)"
    SUBTEXT0 = "rgba(255,255,255,0.8)"
elif THEME == "light":
    SURFACE0 = "rgba(255, 255, 255, 0.60)"
    MANTLE = "rgba(0, 0, 0, 0.08)"
    SUBTEXT0 = "rgba(255,255,255,0.8)"
else:
    qt_theme_dict = qt_themes.get_theme(get_theme())
    SURFACE0 = qt_theme_dict.surface0.name()
    MANTLE = qt_theme_dict.mantle.name()
    SUBTEXT0 = qt_theme_dict.subtext0.name()

# ---------------------------- Create/Edit Profile ----------------------------
def card_style(object_name):
    "Card like styling"
    style_sheet = f"""
    QFrame#{object_name} {{
        background: {SURFACE0};
        border-radius: 8;
    }}
    """
    return style_sheet

# ---------------------------- Dashboard ----------------------------
def group_box_style(object_name):
    "Profile card group box styling"
    style_sheet = f"""
    QGroupBox#{object_name} {{
            background-color: {SURFACE0};
            border: 1px solid {MANTLE};
            border-radius: 8;
            margin-top: 1.5ex;
    }}
    QGroupBox:title#{object_name} {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 8px;
    }}
    """

    return style_sheet

PROFILE_ROW_LABEL = "font-size: 13px; font-weight: bold;"

PLUS_LABEL = """
    color: gray;
    padding: 0 5px;
    font-size: 14px;
    font-weight: bold;
"""

TEXT_BLOCK = "font-family: Consolas; font-size: 10pt;"

# ---------------------------- Setting ----------------------------
def setting_card_style():
    "Setting card, slightly different than create/edit profile card"
    style_sheet = f"""
    QFrame#settingCardFrame {{
        background: {SURFACE0};
        border-radius: 4;
    }}
    """

    return style_sheet

def button_highlight(button):
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

HEADING_STYLE = "font-size:13px; margin-bottom:2px"

SUBHEADING_STYLE = f"font-size:11px; color: {SUBTEXT0};"
