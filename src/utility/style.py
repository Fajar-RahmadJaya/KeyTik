"Contain styling code"

from utility import utils


def card_style(object_name):
    "Card like styling"
    if utils.theme == "dark":
        style_sheet = f"""
        QFrame#{object_name} {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 16;
        }}
        """
    else:
        style_sheet = f"""
        QFrame#{object_name} {{
            background: rgba(255, 255, 255, 0.60);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 16;
        }}
        """
    return style_sheet

def scroll_area_style(object_name):
    "Style for scroll area"
    if utils.theme == "dark":
        style_sheet = f"""
        QScrollArea#{object_name} {{
            background: rgba(255, 255, 255, 0.02);
            }}
        """
    else:
        style_sheet = f"""
        QScrollArea#{object_name} {{
            background: rgba(255, 255, 255, 0.02);
            }}
        """

    return style_sheet
