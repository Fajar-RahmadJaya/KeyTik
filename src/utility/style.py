"Contain styling code"

from utility import utils


def card_style(object_name):
    "Card like styling"
    if utils.theme == "dark":
        style_sheet = f"""
        QFrame#{object_name} {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 8;
        }}
        """
    else:
        style_sheet = f"""
        QFrame#{object_name} {{
            background: rgba(255, 255, 255, 0.60);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 8;
        }}
        """
    return style_sheet

def scroll_area_style(object_name):
    "Style for scroll area"
    if utils.theme == "dark":
        style_sheet = f"""
        QScrollArea#{object_name} {{
            background: rgba(255, 255, 255, 0.03);
        }}
        """
    else:
        style_sheet = f"""
        QScrollArea#{object_name} {{
            background: rgba(255, 255, 255, 0.02);
        }}
        """

    return style_sheet

def group_box_style(object_name):
    "Profile card group box styling"
    if utils.theme == "dark":
        style_sheet = f"""
        QGroupBox#{object_name} {{
             background-color: rgba(255, 255, 255, 0.03);
             border: 1px solid rgba(255, 255, 255, 0.18);
             border-radius: 8;
             margin-top: 1.5ex;
        }}
        QGroupBox:title#{object_name} {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 8px;
        }}
        """
    else:
        style_sheet = f"""
        QScrollArea#{object_name} {{
            background: rgba(255, 255, 255, 0.02);
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
