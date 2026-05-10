"Contain styling code"

import qt_themes
from PySide6.QtGui import QPalette, QColor  # pylint: disable=E0611

from utility import utils

# ---------------------------- Variables ----------------------------
THEME = utils.get_theme()

if THEME == "dark":
    SURFACE0 = "rgba(255, 255, 255, 0.052)"
    MANTLE = "rgba(255, 255, 255, 0.18)"
    SUBTEXT0 = "rgba(255,255,255,0.8)"
elif THEME == "light":
    SURFACE0 = "rgba(255, 255, 255, 0.60)"
    MANTLE = "rgba(0, 0, 0, 0.08)"
    SUBTEXT0 = "rgba(255,255,255,0.8)"
else:
    qt_theme_dict = qt_themes.get_theme(utils.get_theme())
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
    button_text = button.palette().color(QPalette.ButtonText)
    invert_button_text = QColor(255 - button_text.red(), 255 - button_text.green(),
                                255 - button_text.blue(), button_text.alpha())

    style_sheet = f"""
    QPushButton {{
        background-color: {accent.name()};
        color: {invert_button_text.name()};
    }}
    QPushButton:hover {{
        background-color: {accent.setAlphaF(0.85)};
        color: {invert_button_text.name()};
    }}
    """

    return style_sheet

HEADING_STYLE = "font-size:13px; margin-bottom:2px"

SUBHEADING_STYLE = f"font-size:11px; color: {SUBTEXT0};"
