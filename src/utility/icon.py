"Centralize all icon initialization"

import os
from PySide6.QtGui import QIcon # pylint: disable=E0611

from utility import utils
from utility import constant

icon_cache = {}


def get_icon(path):
    "Cache icon"
    if path not in icon_cache:
        icon_cache[path] = QIcon(path)
    return icon_cache[path]


icon_dir = os.path.join(constant.script_dir, '_internal', 'Data', 'icon')
if utils.theme == "dark":
    icon_dir = os.path.join(constant.script_dir, '_internal', 'Data', 'icon', 'dark')
else:
    icon_dir = os.path.join(constant.script_dir, '_internal', 'Data', 'icon', 'light')

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
