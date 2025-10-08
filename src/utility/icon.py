import os
from utility.utils import theme
from utility.constant import script_dir

icon_dir = os.path.join(script_dir, '_internal', 'Data', 'icon')
if theme == "dark":
    icon_dir = os.path.join(script_dir, '_internal', 'Data', 'icon', 'dark')
else:
    icon_dir = os.path.join(script_dir, '_internal', 'Data', 'icon', 'light')

# Profile Icon
icon_run = os.path.join(icon_dir, "run.svg")
icon_exit = os.path.join(icon_dir, "exit.svg")
icon_edit = os.path.join(icon_dir, "edit.svg")
icon_rocket = os.path.join(icon_dir, "rocket.svg")
icon_rocket_fill = os.path.join(icon_dir, "rocket_fill.svg")
icon_copy = os.path.join(icon_dir, "copy.svg")
icon_store = os.path.join(icon_dir, "store.svg")
icon_delete = os.path.join(icon_dir, "delete.svg")
icon_pin = os.path.join(icon_dir, "thumbtack.svg")
icon_pin_fill = os.path.join(icon_dir, "thumbtack_fill.svg")

# Main Window Icon
icon_plus = os.path.join(icon_dir, "plus.svg")
icon_next = os.path.join(icon_dir, "next.svg")
icon_prev = os.path.join(icon_dir, "prev.svg")
icon_setting = os.path.join(icon_dir, "setting.svg")
icon_import = os.path.join(icon_dir, "import.svg")
icon_on_top = os.path.join(icon_dir, "on_top.svg")
icon_on_top_fill = os.path.join(icon_dir, "on_top_fill.svg")
icon_show_stored = os.path.join(icon_dir, "show_stored.svg")
icon_show_stored_fill = os.path.join(icon_dir, "show_stored_fill.svg")

# Edit Window Icon
icon_arrow = os.path.join(icon_dir, "arrow.svg")
icon_filter = os.path.join(icon_dir, "filter.svg")
icon_search = os.path.join(icon_dir, "search.svg")
icon_file_search = os.path.join(icon_dir, "file_search.svg")
icon_question = os.path.join(icon_dir, "question.svg")
