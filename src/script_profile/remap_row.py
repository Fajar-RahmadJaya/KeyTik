"Remap and shortctu row"

from dataclasses import dataclass
from pynput import mouse
import keyboard
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QLabel, QPushButton, QCheckBox, QLineEdit, QFrame, QHBoxLayout,
    QVBoxLayout, QWidget, QSizePolicy, QGridLayout, QTextEdit, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer  # pylint: disable=E0611
from PySide6.QtSvgWidgets import QSvgWidget  # pylint: disable=E0611
from utility import utils
from utility import icons
from utility import constant
from utility.diff import Diff
from script_profile.parse_script import ParseScript
from script_profile.profile_core import ProfileCore
from select_key.select_key_ui import SelectKeyUI


@dataclass
class ParsedRemap:
    "Data class containing parsed remap"
    default_key: str
    remap_key: str
    hold_interval: int
    is_hold_format: bool
    is_first_key: bool
    is_sc: bool
    is_text_format: bool


class RemapRow():
    "Remap & shortcut row on profile creation"
    request_timer_start = Signal(object)
    def __init__(self, edit_frame, edit_window):
        super().__init__()
        # Parameter
        self.edit_frame = edit_frame
        self.edit_window = edit_window

        # Composition
        self.diff = Diff()
        self.parse_script = ParseScript()
        self.profile_core = ProfileCore()
        self.select_key_ui = SelectKeyUI()

        # Signal
        self.request_timer_start.connect(self.profile_core.release_timer)

        # Parameter
        self.edit_frame = edit_frame

        # Variables
        self.is_listening = False
        self.use_scan_code = False
        self.mapping_row_widgets = []
        self.shortcut_row_widgets = []
        self.key_rows = []
        self.shortcut_rows = []
        self.copas_rows = []
        self.files_opener_rows = []
        self.files_opener_row_widgets = []
        self.row_num = 0
        self.previous_button_text = None
        self.entries_to_disable = []

        # UI
        self.edit_frame_layout = None
        self.text_block = None
        self.shortcut_entry = None
        self.is_text_mode = None

    def handle_mode_changed(self, index):
        "Action when mode changed from combobox (can be moved)"
        while self.edit_frame_layout.count():
            item = self.edit_frame_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        self.key_rows = []
        self.shortcut_rows = []
        if hasattr(self, "files_opener_rows"):
            self.files_opener_rows = []
        if hasattr(self, "files_opener_row_widgets"):
            self.files_opener_row_widgets = []
        if hasattr(self, "text_block"):
            self.text_block = None
        self.is_text_mode = False

        if index == 0:
            self.is_text_mode = False
            self.shortcut_title()
            self.shortcut_row()
            self.remap_title()
            self.remap_row()
            self.edit_frame_layout.addItem(QSpacerItem(20, 40,
                                            QSizePolicy.Minimum,
                                            QSizePolicy.Expanding))

        elif index == 1:
            self.is_text_mode = True
            self.shortcut_title()
            self.shortcut_row()
            self.edit_frame_layout.addItem(QSpacerItem(20, 40,
                                            QSizePolicy.Minimum,
                                            QSizePolicy.Expanding))

        else:
            self.diff.pro_mode(index)

    def handle_parser(self, lines, first_line):
        "Action when editing profile (Can be moved)"
        key_map = self.profile_core.load_key_list()
        mode_line = lines[0].strip() if lines else "; default"

        if mode_line == "; default":
            self.default_mode_widget(lines, key_map)

        elif mode_line == "; text":
            self.text_mode_widget(lines, key_map)

        else:
            self.diff.pro_parser(lines, first_line)

    def default_mode_widget(self, lines, key_map):
        "Default mode frame"

        parsed_shortcut_tuple = self.parse_script.parse_shortcuts(lines, key_map)

        self.shortcut_title()

        if parsed_shortcut_tuple:
            for parsed_shortcut in parsed_shortcut_tuple:
                self.shortcut_row(parsed_shortcut)
        else:
            self.shortcut_row()

        self.remap_title()

        parsed_remap_tuple = self.parse_script.parse_default_mode(lines, key_map)

        if parsed_remap_tuple:
            # Unpack tuple
            for (default_key, remap_key, is_text_format,
                 is_hold_format, hold_interval, is_first_key,
                 is_sc) in parsed_remap_tuple:

                # Add unpacked tople to dataclass
                parsed_remap = ParsedRemap(
                    default_key = default_key,
                    remap_key = remap_key,
                    is_text_format = is_text_format,
                    is_hold_format = is_hold_format,
                    hold_interval = hold_interval,
                    is_first_key = is_first_key,
                    is_sc = is_sc
                    )
                self.remap_row(parsed_remap)
        else:
            self.remap_row()


        # if parsed_remap_tuple:
        #     # For edit profile
        #     self.remap_row(parsed_remap)
        # else:
        #     # For create new profile
        #     self.remap_row()

        self.update_plus_visibility('shortcut')
        self.update_plus_visibility('remap')

    def remap_title(self):
        "Key remap row tittle label"
        remap_label_layout = QGridLayout()
        remap_label_layout.setContentsMargins(0, 0, 0, 0)
        default_key_label = QLabel("Default Key", self.edit_frame)
        default_key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_key_label.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
        """)
        remap_key_label = QLabel("Remap Key", self.edit_frame)
        remap_key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        remap_key_label.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
        """)
        remap_label_layout.addWidget(default_key_label, 0, 0, 1, 2)
        remap_label_layout.addWidget(remap_key_label, 0, 2, 1, 2)
        remap_label_widget = QWidget(self.edit_frame)
        remap_label_widget.setLayout(remap_label_layout)
        self.edit_frame_layout.addWidget(remap_label_widget)
        return remap_label_widget

    def remap_row(self, parsed_remap=None, insert_after=None):
        "Remap row"
        if not hasattr(self.edit_frame, 'layout'):
            self.edit_frame_layout = QVBoxLayout(self.edit_frame)
            self.edit_frame.setLayout(self.edit_frame_layout)
        else:
            self.edit_frame_layout = self.edit_frame.layout()

        # Remap row card
        card_frame = QFrame(self.edit_frame)
        card_frame.setFrameShape(QFrame.NoFrame)
        if utils.theme == "dark":
            card_frame.setStyleSheet("""
            QFrame {
                background: #313131;
                border: 1px solid #404040;
                border-radius: 10px;
            }
            """)
        else:
            card_frame.setStyleSheet("""
            QFrame {
                background: #f8f8f8;
                border: 1px solid #c9c9c9;
                border-radius: 10px;
            }
            """)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(0)

        # Remap row layout
        row_widget = QWidget(self.edit_frame)
        row_widget.setSizePolicy(QSizePolicy.Policy.Preferred,
                                 QSizePolicy.Policy.Fixed)
        card_layout.addWidget(row_widget)

        row_layout = QGridLayout(row_widget)
        row_widget.setLayout(row_layout)
        row_layout.setContentsMargins(10, 5, 10, 5)
        row_layout.setHorizontalSpacing(10)
        row_layout.setVerticalSpacing(5)

        # Separator widget
        separator_widget, on_plus_click = self.separator_widget(row_widget, row_type="remap row")

        # Arrow Widget
        arrow_icon = QSvgWidget(icons.arrow)
        arrow_icon.setFixedSize(32, 24)
        row_layout.addWidget(arrow_icon, 0, 2, 2, 1)

        # Set widget and configure key rows tuple
        self.set_key_rows(row_widget, row_layout, parsed_remap, on_plus_click)

        # The order where the widget will be added
        if insert_after is not None:
            idx = self.edit_frame_layout.indexOf(insert_after[1]) + 1
            self.edit_frame_layout.insertWidget(idx, card_frame)
            self.edit_frame_layout.insertWidget(idx + 1, separator_widget)
            self.mapping_row_widgets.insert(idx // 2, (card_frame,
                                                        separator_widget))
        else:
            self.edit_frame_layout.addWidget(card_frame)
            self.edit_frame_layout.addWidget(separator_widget)
            self.mapping_row_widgets.append((card_frame, separator_widget))

        # Unused for now
        # def auto_remove_row():
        #     "Auto remove row if all entry don't have text"
        #     if idx == len(self.key_rows) - 2:
        #         if (not default_key_entry.text().strip() and
        #                 not remap_key_entry.text().strip()):
        #             for i, (sw) in enumerate(self.mapping_row_widgets):
        #                 # plus = sw.findChild(QLabel, None)
        #                 # frames = sw.findChildren(QFrame)
        #                 # left_sep = frames[0] if len(frames) > 0 else None
        #                 # right_sep = frames[2] if len(frames) > 1 else None
        #                 # is_last = i == len(self.mapping_row_widgets) - 1
        #                 # if plus:
        #                 #     plus.setVisible(is_last)
        #                 # if left_sep:
        #                 #     left_sep.setVisible(is_last)
        #                 # if right_sep:
        #                 #     right_sep.setVisible(is_last)
        # default_key_entry.textChanged.connect(
        #     auto_remove_row)
        # remap_key_entry.textChanged.connect(
        #     auto_remove_row)

        self.edit_frame.setUpdatesEnabled(True)
        self.edit_frame.update()
        self.edit_frame.adjustSize()

    def set_key_rows(self, row_widget, row_layout, parsed_remap, on_plus_click):
        "Set widget and configure key rows tuple"
        # Default Key Widget
        (default_key_entry, default_key_select
            ) = self.default_key_widget(row_widget, row_layout, parsed_remap)

        # Remap Key Widget
        (remap_key_entry, remap_key_select
            ) = self.remap_key_widget(row_widget, row_layout, parsed_remap)

        # Option Widget
        (text_format_checkbox, hold_format_checkbox,
            hold_interval_entry, first_key_checkbox,
            sc_checkbox) = self.option_widget(row_widget, row_layout, parsed_remap)

        # Add or remove row when entry changed
        def auto_add_row():
            "Auto add row if all entry have text"
            if self.key_rows and (default_key_entry, remap_key_entry) == self.key_rows[-1][:2]:
                if (default_key_entry.text().strip()
                    and remap_key_entry.text().strip()):
                    on_plus_click(None)

        default_key_entry.textChanged.connect(auto_add_row)
        remap_key_entry.textChanged.connect(auto_add_row)

        self.key_rows.append((default_key_entry, remap_key_entry,
                                default_key_select, remap_key_select,
                                text_format_checkbox, hold_format_checkbox,
                                hold_interval_entry, first_key_checkbox,
                                sc_checkbox))

    def default_key_widget(self, row_widget, row_layout, parsed_remap):
        "Default key widget on remap row"
        default_key_select = QPushButton("Select", row_widget)
        default_key_select.setFixedWidth(140)
        default_key_select.setToolTip("Press any key or shortcut "
                                        "to capture it automatically")
        default_key_select.clicked.connect(lambda:
                                            self.key_listening(
                                                    default_key_entry,
                                                    default_key_select))
        row_layout.addWidget(default_key_select, 0, 0, 1, 2, Qt.AlignCenter)

        default_key_widget = QWidget(row_widget)
        default_key_layout = QHBoxLayout(default_key_widget)
        default_key_layout.setContentsMargins(0, 0, 0, 0)
        default_key_layout.setSpacing(2)

        default_key_entry = QLineEdit(default_key_widget)
        default_key_entry.setFixedWidth(112)
        default_key_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_key_entry.setToolTip("Default key can be a single key, "
                                        "multiple keys, or a double key (eg. double-click)")
        if parsed_remap:
            default_key_entry.setText(parsed_remap.default_key)
        default_key_layout.addWidget(default_key_entry)

        default_key_choose = QPushButton(default_key_widget)
        default_key_choose.setFixedWidth(28)
        default_key_choose.setIcon(icons.get_icon(icons.search))
        default_key_choose.setToolTip("Choose Default/Original key")
        default_key_choose.clicked.connect(
            lambda: self.select_key_ui.select_key(default_key_entry, context="default"))
        default_key_layout.addWidget(default_key_choose)

        row_layout.addWidget(default_key_widget, 1, 0, 1, 2, Qt.AlignCenter)

        return default_key_entry, default_key_select

    def remap_key_widget(self, row_widget, row_layout, parsed_remap):
        "Remap key widget on remap row"
        remap_key_select = QPushButton("Select", row_widget)
        remap_key_select.setFixedWidth(140)
        remap_key_select.setToolTip("Press any key or shortcut to capture it automatically")
        remap_key_select.clicked.connect(lambda:
                                            self.key_listening(
                                                remap_key_entry,
                                                remap_key_select))
        row_layout.addWidget(remap_key_select, 0, 3, 1, 2, Qt.AlignCenter)

        remap_key_widget = QWidget(row_widget)
        remap_key_layout = QHBoxLayout(remap_key_widget)
        remap_key_layout.setContentsMargins(0, 0, 0, 0)
        remap_key_layout.setSpacing(2)

        remap_key_entry = QLineEdit(remap_key_widget)
        remap_key_entry.setFixedWidth(112)
        remap_key_entry.setToolTip("Remap key can be "
                                    "a single key, multiple keys, text, or hold")
        remap_key_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if parsed_remap:
            remap_key_entry.setText(parsed_remap.remap_key)
        remap_key_layout.addWidget(remap_key_entry)

        remap_key_choose = QPushButton(remap_key_widget)
        remap_key_choose.setFixedWidth(28)
        remap_key_choose.setIcon(icons.get_icon(icons.search))
        remap_key_choose.setToolTip("Choose Remap key")
        remap_key_choose.clicked.connect(
            lambda: self.select_key_ui.select_key(remap_key_entry, context="remap"))
        remap_key_layout.addWidget(remap_key_choose)

        row_layout.addWidget(remap_key_widget, 1, 3, 1, 2, Qt.AlignCenter)

        return remap_key_entry, remap_key_select

    def option_widget(self, row_widget, row_layout, parsed_remap):
        "Remap option widget on remap row"
        options_widget = QWidget(row_widget)
        options_layout = QHBoxLayout(options_widget)
        options_layout.setContentsMargins(0, 5, 0, 0)

        first_key_checkbox = QCheckBox("Disable First Key", options_widget)
        first_key_checkbox.setToolTip(
            "Default Key Only: "
            "Check this to disable the first key when using multiple keys.\n"
        )
        if parsed_remap:
            first_key_checkbox.setChecked(parsed_remap.is_first_key)
        options_layout.addWidget(first_key_checkbox)

        sc_checkbox = QCheckBox("Use Scan Code", options_widget)
        sc_checkbox.setObjectName("sc_checkbox")
        sc_checkbox.setToolTip(
            "Default Key Only: "
            "Check this to make the Select button use Scan Code (SC) instead.\n"
            "Scan Code is the hardware coordinate of the key, "
            "use this if the key is not detected or missing from the list."
        )
        if parsed_remap:
            sc_checkbox.setChecked(parsed_remap.is_sc)
        options_layout.addWidget(sc_checkbox)

        text_format_checkbox = QCheckBox("Text Format", options_widget)
        text_format_checkbox.setToolTip("Remap Key Only: "
                                        "Check this to send the actual text instead of a key")
        if parsed_remap:
            text_format_checkbox.setChecked(parsed_remap.is_text_format)
        options_layout.addWidget(text_format_checkbox)

        hold_format_checkbox = QCheckBox("Hold Format", options_widget)
        hold_format_checkbox.setToolTip("Remap Key Only: "
                                        "Simulate holding the key for a set interval")
        if parsed_remap:
            hold_format_checkbox.setChecked(parsed_remap.is_hold_format)
        options_layout.addWidget(hold_format_checkbox)

        hold_interval_entry = QLineEdit(options_widget)
        hold_interval_entry.setPlaceholderText("Int")
        hold_interval_entry.setFixedWidth(40)
        hold_interval_entry.setToolTip("Remap Key Only: "
                                        "Enter the hold interval in seconds (Default is 10 second)")
        hold_interval_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if parsed_remap:
            hold_interval_float = float(parsed_remap.hold_interval)
            hold_interval_str = (str(int(hold_interval_float))
                                    if hold_interval_float.is_integer()
                                    else str(hold_interval_float))
            hold_interval_entry.setText(hold_interval_str)
        options_layout.addWidget(hold_interval_entry)

        row_layout.addWidget(options_widget, 2, 0, 1, 5, Qt.AlignCenter)

        return (text_format_checkbox, hold_format_checkbox,
                hold_interval_entry, first_key_checkbox, sc_checkbox)

    def separator_widget(self, row_widget, row_type):
        "Remap row separator widget"
        separator_widget = QWidget(self.edit_frame)
        separator_layout = QHBoxLayout(separator_widget)
        separator_widget.setLayout(separator_layout)
        separator_widget.setSizePolicy(QSizePolicy.Policy.Expanding,
                                        QSizePolicy.Policy.Fixed)
        separator_layout.setContentsMargins(0, 0, 0, 0)
        separator_layout.setSpacing(0)

        left_sep = QFrame(separator_widget)
        left_sep.setObjectName("left_sep")
        left_sep.setFrameShape(QFrame.Shape.HLine)
        left_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(left_sep)

        plus_label = QLabel("+", separator_widget)
        plus_label.setStyleSheet("""
            color: gray;
            padding: 0 5px;
            font-size: 14px;
            font-weight: bold;
        """)
        plus_label.setCursor(Qt.CursorShape.PointingHandCursor)
        plus_label.setFixedWidth(20)
        plus_label.setFixedHeight(20)
        plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator_layout.addWidget(plus_label)

        right_sep = QFrame(separator_widget)
        right_sep.setObjectName("right_sep")
        right_sep.setFrameShape(QFrame.Shape.HLine)
        right_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(right_sep)

        # Add row below when pressing plus
        def on_plus_click(_):
            "Pressing tow will add a new row below via insert after"
            plus_label.setVisible(False)
            right_sep.setVisible(False)
            left_sep.setVisible(False)
            if row_type == "remap row":
                self.remap_row(insert_after=(row_widget, separator_widget))
            elif row_type == "shortcut row":
                self.shortcut_row(insert_after=(row_widget, separator_widget))

        plus_label.mousePressEvent = on_plus_click

        return separator_widget, on_plus_click

    def shortcut_title(self):
        "Shortcuts row tittle label"
        shortcut_label = QLabel("Shortcut", self.edit_frame)
        shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcut_label.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
        """)
        self.edit_frame_layout.addWidget(shortcut_label)
        return shortcut_label

    def shortcut_row(self, parsed_shortcut=None, insert_after=None):
        "Shortcut row"
        if not hasattr(self.edit_frame, 'layout'):
            self.edit_frame_layout = QVBoxLayout(self.edit_frame)
            self.edit_frame.setLayout(self.edit_frame_layout)
        else:
            self.edit_frame_layout = self.edit_frame.layout()

        # For text mode
        if self.is_text_mode and (not hasattr(self, 'text_block') or
        self.text_block is None):
            self.text_block = QTextEdit(self.edit_frame)
            self.text_block.setReadOnly(False)
            self.text_block.setStyleSheet(
            "font-family: Consolas; "
            "font-size: 10pt;"
            )
            self.edit_frame_layout.addWidget(self.text_block)

        # Card frame
        card_frame = QFrame(self.edit_frame)
        card_frame.setFrameShape(QFrame.NoFrame)
        if utils.theme == "dark":
            card_frame.setStyleSheet("""
            QFrame {
                background: #313131;
                border: 1px solid #404040;
                border-radius: 10px;
            }
            """)
        else:
            card_frame.setStyleSheet("""
            QFrame {
                background: #f8f8f8;
                border: 1px solid #c9c9c9;
                border-radius: 10px;
            }
            """)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(0)

        row_widget = QWidget(self.edit_frame)
        row_widget.setSizePolicy(QSizePolicy.Policy.Preferred,
                                 QSizePolicy.Policy.Fixed)
        card_layout.addWidget(row_widget)

        row_layout = QGridLayout(row_widget)
        row_widget.setLayout(row_layout)
        row_layout.setContentsMargins(10, 5, 10, 5)
        row_layout.setHorizontalSpacing(10)
        row_layout.setVerticalSpacing(5)

        # Shortcut Widget
        self.shortcut_widget(row_widget, row_layout, parsed_shortcut)

        # Separator widget
        separator_widget, _ = self.separator_widget(row_widget, row_type="shortcut row")

        if insert_after is not None:
            idx = self.edit_frame_layout.indexOf(insert_after[1]) + 1
            self.edit_frame_layout.insertWidget(idx, card_frame)
            self.edit_frame_layout.insertWidget(idx + 1, separator_widget)
            self.shortcut_row_widgets.insert(idx // 2, (card_frame,
                                                        separator_widget))
        else:
            self.edit_frame_layout.addWidget(card_frame)
            self.edit_frame_layout.addWidget(separator_widget)
            self.shortcut_row_widgets.append((card_frame, separator_widget))

        if (self.is_text_mode and
            hasattr(self, 'text_block') and
            self.text_block is not None):

            self.edit_frame_layout.addWidget(self.text_block)

        self.edit_frame.setUpdatesEnabled(True)
        self.edit_frame.update()
        self.edit_frame.adjustSize()

    def shortcut_widget(self, row_widget, row_layout, parsed_shortcut):
        "Shortcut widget"
        shortcut_key_select = QPushButton("Select", row_widget)
        shortcut_key_select.setFixedWidth(280)
        shortcut_key_select.setToolTip("Press any key or shortcut to capture it automatically")
        shortcut_key_select.clicked.connect(lambda:
                                            self.key_listening(
                                                self.shortcut_entry,
                                                shortcut_key_select))
        row_layout.addWidget(shortcut_key_select, 0, 0, 1, 4, Qt.AlignCenter)

        shortcut_widget = QWidget(row_widget)
        shortcut_layout = QHBoxLayout(shortcut_widget)
        shortcut_layout.setContentsMargins(0, 0, 0, 0)
        shortcut_layout.setSpacing(2)

        self.shortcut_entry = QLineEdit(shortcut_widget)
        if parsed_shortcut:
            self.shortcut_entry.setText(parsed_shortcut)
        self.shortcut_entry.setFixedWidth(252)
        self.shortcut_entry.setToolTip("Shortcut can be "
                                        "a single key, multiple keys, or shortcut specials "
                                        "(See select key)")
        self.shortcut_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shortcut_rows.append((self.shortcut_entry, shortcut_key_select))
        shortcut_layout.addWidget(self.shortcut_entry)

        shortcut_choose = QPushButton(shortcut_widget)
        shortcut_choose.setFixedWidth(28)
        shortcut_choose.setIcon(icons.get_icon(icons.search))
        shortcut_choose.setToolTip("Choose Shortcut key")
        shortcut_choose.clicked.connect(
            lambda: self.select_key_ui.select_key(self.shortcut_entry, context="shortcut"))
        shortcut_layout.addWidget(shortcut_choose)

        row_layout.addWidget(shortcut_widget, 1, 0, 1, 4, Qt.AlignCenter)

    def text_mode_widget(self, lines, key_map):
        "Text mode frame(to do: fix)"
        shortcuts = self.parse_script.parse_shortcuts(lines, key_map)

        if not shortcuts:
            self.shortcut_row()
        else:
            for shortcut in shortcuts:
                self.shortcut_row(shortcut)

        self.row_num += 1

        self.text_block = QTextEdit(self.edit_frame)
        self.text_block.setLineWrapMode(QTextEdit.WidgetWidth)
        self.text_block.setFixedHeight(14 * self.text_block.fontMetrics().height())
        self.text_block.setFontPointSize(10)
        self.text_block.setReadOnly(False)
        self.text_block.setStyleSheet(
        "font-family: Consolas; "
        "font-size: 10pt;"
        )
        text_content = self.extract_and_filter_content(lines)
        self.text_block.setPlainText(text_content.strip())
        self.edit_frame_layout.addWidget(self.text_block)

        self.update_plus_visibility('shortcut')

    def extract_and_filter_content(self, lines):
        "Get text block value from the marker"
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
        return ''.join(result_lines)

    def update_plus_visibility(self, row_type):
        "Make sure + only showed up only on the last row"
        if row_type == 'remap':
            widgets = getattr(self, "mapping_row_widgets", [])
        elif row_type == 'shortcut':
            widgets = getattr(self, "shortcut_row_widgets", [])
        else:
            return

        for i, (_, sw) in enumerate(widgets):
            plus = sw.findChild(QLabel, None)
            left_sep = sw.findChild(QFrame, "left_sep")
            right_sep = sw.findChild(QFrame, "right_sep")
            is_last = i == len(widgets) - 1
            if plus:
                plus.setVisible(is_last)
            if left_sep:
                left_sep.setVisible(is_last)
            if right_sep:
                right_sep.setVisible(is_last)

    # ----------- From profile core -----------
    def disable_input(self):
        "Disable input. Used on key listening"
        for key_row in self.key_rows:
            (default_key_entry, remap_key_entry,
                _, _,
                text_format_checkbox, hold_format_checkbox,
                hold_interval_entry, first_key_checkbox,
                sc_checkbox) = key_row
            self.entries_to_disable.append((default_key_entry, None))
            self.entries_to_disable.append((remap_key_entry, None))
            self.entries_to_disable.append((text_format_checkbox, None))
            self.entries_to_disable.append((hold_format_checkbox, None))
            self.entries_to_disable.append((hold_interval_entry, None))
            self.entries_to_disable.append((first_key_checkbox, None))
            self.entries_to_disable.append((sc_checkbox, None))

        for shortcut_entry, _ in self.shortcut_rows:
            self.entries_to_disable.append((shortcut_entry, None))

        # Part of pro version code
        for copas_row in self.copas_rows:
            copy_entry, paste_entry, _, _, _, _ = copas_row
            self.entries_to_disable.append((copy_entry, None))
            self.entries_to_disable.append((paste_entry, None))

    def mouse_listening(self, button, pressed):
        "Get and listen to mouse key press"
        if not (self.is_listening and self.profile_core.active_entry):
            return

        if pressed and hasattr(self, "edit_window"):
            widget = self.edit_window.childAt(
                self.edit_window.mapFromGlobal(
                    self.edit_window.cursor().pos()))
            while widget:
                if isinstance(widget, QPushButton):
                    return
                widget = widget.parent()

        button_map = {
            mouse.Button.left: "Left Button",
            mouse.Button.right: "Right Button",
            mouse.Button.middle: "Middle Button"
        }
        mouse_button = button_map.get(button, getattr(
            button, "name", str(button)))

        if pressed:
            if mouse_button not in self.profile_core.pressed_keys:
                self.profile_core.pressed_keys.append(mouse_button)
                self.profile_core.update_widget(self.profile_core.active_entry)
        else:
            if mouse_button in self.profile_core.pressed_keys:
                self.profile_core.pressed_keys.remove(mouse_button)
                if not self.profile_core.pressed_keys:
                    self.key_listening(self.profile_core.active_entry, None)
                    self.request_timer_start.emit(self.profile_core.active_entry)
                elif hasattr(self, "release_timer"):
                    self.request_timer_start.emit(self.profile_core.active_entry)

    def handle_sc_listening(self, button):
        "Check whether to use scan code listening or not"
        for key_row in self.key_rows:
            (_, _, orig_button, _, _, _, _,_, _) = key_row

            if button == orig_button:
                parent_widget = button.parent()
                if parent_widget:
                    sc_checkboxes = [child for child
                                        in parent_widget.
                                        findChildren(QObject)
                                        if child.objectName() ==
                                        "sc_checkbox"]
                    if sc_checkboxes:
                        self.use_scan_code = sc_checkboxes[0].isChecked()
                        return self.use_scan_code
                    break
        return None

    def toggle_other_buttons(self, state, button):
        "Change the state of non selected button"
        for key_row in self.key_rows:
            (_, _, orig_button, remap_button, _, _, _, _, _) = key_row

            if orig_button != button and orig_button is not None:
                orig_button.setEnabled(state)
            if remap_button != button and remap_button is not None:
                remap_button.setEnabled(state)

        for copas_row in self.copas_rows:
            (_, _, copy_button, paste_button, _, _) = copas_row

            if copy_button != button and copy_button is not None:
                copy_button.setEnabled(state)
            if paste_button != button and paste_button is not None:
                paste_button.setEnabled(state)

        for _, shortcut_button in self.shortcut_rows:
            if shortcut_button != button and shortcut_button is not None:
                shortcut_button.setEnabled(state)

    def multi_key_event(self, event, entry_widget, button):
        "Action when multiple key is pressed, set timer before saving the key"
        if not self.is_listening or self.profile_core.active_entry != entry_widget:
            return

        self.use_scan_code = self.handle_sc_listening(button)
        if hasattr(self, 'use_scan_code') and self.use_scan_code:
            key = f"SC{event.scan_code:02X}"
        else:
            key = event.name

        key_lower = key.lower()
        if key_lower in constant.changes_key:
            key = constant.changes_key[key_lower]

        if (len(key) == 1 and key.isupper() and key.isalpha()):
            key = key.lower()

        if event.event_type == "down":
            if key not in self.profile_core.pressed_keys:
                self.profile_core.pressed_keys.append(key)
                self.profile_core.update_widget(entry_widget)
            if (hasattr(self, "release_timer")
                    and self.profile_core.set_timer.isActive()):
                self.profile_core.set_timer.stop()

        elif event.event_type == "up":
            if key in self.profile_core.pressed_keys:
                self.profile_core.pressed_keys.remove(key)
                if not self.profile_core.pressed_keys:
                    self.key_listening(entry_widget, button)
                    self.request_timer_start.emit(entry_widget)

                else:
                    if hasattr(self, "release_timer"):
                        self.request_timer_start.emit(entry_widget)

    def key_listening(self, entry_widget, button):
        "Get and Listen to key press"
        if not self.is_listening:
            self.is_listening = True
            self.profile_core.active_entry = entry_widget
            self.previous_button_text = button.text()
            self.use_scan_code = False
            self.profile_core.pressed_keys = []
            self.profile_core.last_combination = ""

            # Append entries to disable widget
            self.disable_input()
            # Install disable widget event filter
            for entry_tuple in self.entries_to_disable:
                entry = entry_tuple[0]
                if entry is not None:
                    entry.installEventFilter(self)

            self.edit_window.installEventFilter(self)

            self.toggle_other_buttons(False, button)

            button.clicked.disconnect()
            button.clicked.connect(lambda: self.key_listening
                                    (entry_widget, button))

            self.profile_core.set_timer = QTimer()
            self.profile_core.set_timer.setSingleShot(True)
            self.profile_core.set_timer.timeout.connect(
                lambda: self.profile_core.finalize_combination(entry_widget))

            keyboard.hook(lambda event: self.multi_key_event(event, entry_widget, button))

        else:
            self.is_listening = False
            self.profile_core.active_entry = None
            self.profile_core.pressed_keys = []

            # Remove disable widget event filet
            for entry_tuple in self.entries_to_disable:
                entry = entry_tuple[0]
                if entry is not None:
                    entry.removeEventFilter(self)

            self.toggle_other_buttons(True, button)

            self.edit_window.removeEventFilter(self)

            if button is not None:
                button.clicked.disconnect()
                button.clicked.connect(lambda: self.key_listening
                                        (entry_widget, button))
