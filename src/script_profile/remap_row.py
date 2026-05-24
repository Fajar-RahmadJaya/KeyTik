"Remap and shortctu row"

from dataclasses import dataclass
import pynput
import keyboard
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QLabel,
    QPushButton,
    QCheckBox,
    QLineEdit,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QGridLayout,
)
from PySide6.QtCore import Qt, Signal, QTimer, QEvent, QObject  # pylint: disable=E0611
from PySide6.QtSvgWidgets import QSvgWidget  # pylint: disable=E0611
from PySide6.QtGui import QCursor  # pylint: disable=E0611

from utility import icons
from utility import constant
from utility import style
from script_profile.remap_row_core import RemapRowCore
from select_key.select_key_ui import SelectKeyUI


@dataclass
class OptionWidget:
    "Data class containing option widget"

    text_format_checkbox: QCheckBox = None
    hold_format_checkbox: QCheckBox = None
    hold_interval_entry: QLineEdit = None
    first_key_checkbox: QCheckBox = None
    sc_checkbox: QCheckBox = None


@dataclass
class DefaultKeyWidget:
    "Data class containing default key widget"

    default_key_entry: QLineEdit = None
    default_key_select: QPushButton = None


@dataclass
class RemapKeyWidget:
    "Data class containing remap key widget"

    remap_key_entry: QLineEdit = None
    remap_key_select: QPushButton = None


@dataclass
class KeyWidget:
    "Data class containing key widget"

    default_key: DefaultKeyWidget = None
    remap_key: RemapKeyWidget = None
    option: OptionWidget = None


class SharedRow:  # pylint: disable=R0903
    "Shared row for remap and shortcut row"

    def separator_widget(self, plus_event, parent_widget: QWidget):
        "Remap row separator widget"
        separator_widget = QWidget()
        separator_layout = QHBoxLayout(separator_widget)
        separator_widget.setLayout(separator_layout)
        separator_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        separator_widget.setObjectName("SeparatorWidget")
        separator_layout.setContentsMargins(0, 0, 0, 0)
        separator_layout.setSpacing(0)

        left_sep = QFrame(separator_widget)
        left_sep.setObjectName("left_sep")
        left_sep.setFrameShape(QFrame.Shape.HLine)
        left_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(left_sep)

        plus_label = QLabel("+", separator_widget)
        plus_label.setStyleSheet(style.PLUS_LABEL)
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

        plus_label.mousePressEvent = plus_event

        # Hide old separator
        prev_separator_list = parent_widget.findChildren(QWidget, "SeparatorWidget")
        if prev_separator_list:
            last_separator = prev_separator_list[-1]
            last_separator.setVisible(False)

        return separator_widget


class RemapRow:
    "Remap row on profile creation"

    def __init__(self, edit_frame):
        super().__init__()
        # Composition
        self.select_key_ui = SelectKeyUI()
        self.key_listening_comp = KeyListening(edit_frame)

        # Variables
        self.key_rows = []
        self.edit_frame = edit_frame

    def remap_row(self, parent_window, parsed_remap_list: list = None):
        "Build remap row"
        # Remap
        remap_widget = QWidget()
        remap_widget.setContentsMargins(0, 0, 0, 0)
        remap_layout = QVBoxLayout(remap_widget)
        remap_layout.setContentsMargins(0, 0, 0, 0)

        # Remap title
        remap_title_widget = self.remap_title()
        remap_layout.addWidget(remap_title_widget)

        shared_row = SharedRow()

        # Remap row
        def add_empty_row(_):
            "Add empty remap row and separator"
            # Add empty row
            remap_row_widget = self.remap_card(parent_window)
            remap_layout.addWidget(remap_row_widget)

            # Add separator
            separator_widget = shared_row.separator_widget(add_empty_row, remap_widget)
            remap_layout.addWidget(separator_widget)

        if parsed_remap_list:
            for parsed_remap in parsed_remap_list:
                # Remap row
                # If list empty, add empty row
                remap_row_widget = self.remap_card(
                    parent_window, parsed_remap=parsed_remap
                )
                remap_layout.addWidget(remap_row_widget)

                # Separator
                separator_widget = shared_row.separator_widget(
                    add_empty_row, remap_widget
                )
                remap_layout.addWidget(separator_widget)
        else:
            add_empty_row(None)

        return remap_widget

    def remap_title(self):
        "Key remap row tittle label"
        remap_label_widget = QWidget()

        remap_label_layout = QGridLayout()
        remap_label_layout.setContentsMargins(0, 0, 0, 0)
        remap_label_widget.setLayout(remap_label_layout)

        default_key_label = QLabel("Default Key")
        default_key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_key_label.setStyleSheet(style.PROFILE_ROW_LABEL)
        remap_label_layout.addWidget(default_key_label, 0, 0, 1, 2)

        remap_key_label = QLabel("Remap Key")
        remap_key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        remap_key_label.setStyleSheet(style.PROFILE_ROW_LABEL)
        remap_label_layout.addWidget(remap_key_label, 0, 2, 1, 2)

        return remap_label_widget

    def remap_card(self, parent_window=None, parsed_remap=None):
        "Remap row"
        # Remap row card
        card_frame = QFrame()
        card_frame.setFrameShape(QFrame.NoFrame)
        card_frame.setStyleSheet(style.card())

        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(8, 8, 8, 8)

        # Remap row layout
        remap_row_widget = QWidget(card_frame)
        remap_row_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        card_layout.addWidget(remap_row_widget)

        remap_row_layout = QGridLayout(remap_row_widget)
        remap_row_widget.setLayout(remap_row_layout)
        remap_row_layout.setContentsMargins(16, 0, 16, 4)
        remap_row_layout.setVerticalSpacing(0)

        # Default Key Widget
        default_key, default_key_widget = self.default_key_widget(
            parsed_remap, parent_window
        )
        remap_row_layout.addWidget(default_key_widget, 0, 0)

        # Arrow Widget
        arrow_icon = QSvgWidget(icons.arrow)
        arrow_icon.setFixedSize(32, 24)
        remap_row_layout.addWidget(arrow_icon, 0, 1)

        # Remap Key Widget
        remap_key, remap_key_widget = self.remap_key_widget(parsed_remap, parent_window)
        remap_row_layout.addWidget(remap_key_widget, 0, 2)

        # Option widget
        option, option_widget = self.option_widget(parsed_remap)
        remap_row_layout.addWidget(option_widget, 1, 0, 1, 3)

        # Set key_rows
        self.key_rows.append(
            KeyWidget(default_key=default_key, remap_key=remap_key, option=option)
        )

        return card_frame

    def default_key_widget(self, parsed_remap, parent_window):
        "Default key widget on remap row"
        default_key_container = QWidget()
        default_key_container.setContentsMargins(8, 0, 8, 0)

        default_key_layout = QGridLayout(default_key_container)

        default_key_select = QPushButton("Select")
        default_key_select.setToolTip(
            "Press any key or shortcut to capture it automatically"
        )
        default_key_select.clicked.connect(
            lambda: self.key_listening_comp.key_listening(
                default_key_entry, default_key_select
            )
        )
        default_key_layout.addWidget(default_key_select, 0, 0, 1, 2)

        default_key_entry = QLineEdit(default_key_container)
        default_key_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_key_entry.setToolTip(
            "Default key can be a single key, "
            "multiple keys, or a double key (eg. double-click)"
        )
        if parsed_remap:
            default_key_entry.setText(parsed_remap.default_key)
        default_key_layout.addWidget(default_key_entry, 1, 0, 1, 1)

        default_key_choose = QPushButton(default_key_container)
        default_key_choose.setFixedWidth(28)
        default_key_choose.setIcon(icons.get_icon(icons.search))
        default_key_choose.setToolTip("Choose Default/Original key")
        default_key_choose.clicked.connect(
            lambda: self.select_key_ui.select_key(
                parent_window, default_key_entry, context="default"
            )
        )
        default_key_layout.addWidget(default_key_choose, 1, 1, 1, 1)

        default_key = DefaultKeyWidget(
            default_key_entry=default_key_entry, default_key_select=default_key_select
        )
        return default_key, default_key_container

    def remap_key_widget(self, parsed_remap, parent_window):
        "Remap key widget on remap row"
        remap_key_container = QWidget()
        remap_key_container.setContentsMargins(8, 0, 8, 0)

        remap_key_layout = QGridLayout(remap_key_container)

        remap_key_select = QPushButton("Select")
        remap_key_select.setToolTip(
            "Press any key or shortcut to capture it automatically"
        )
        remap_key_select.clicked.connect(
            lambda: self.key_listening_comp.key_listening(
                remap_key_entry, remap_key_select
            )
        )
        remap_key_layout.addWidget(remap_key_select, 0, 0, 1, 2)

        remap_key_entry = QLineEdit(remap_key_container)
        remap_key_entry.setToolTip(
            "Remap key can be a single key, multiple keys, text, or hold"
        )
        remap_key_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if parsed_remap:
            remap_key_entry.setText(parsed_remap.remap_key)
        remap_key_layout.addWidget(remap_key_entry, 1, 0, 1, 1)

        remap_key_choose = QPushButton(remap_key_container)
        remap_key_choose.setFixedWidth(28)
        remap_key_choose.setIcon(icons.get_icon(icons.search))
        remap_key_choose.setToolTip("Choose Remap key")
        remap_key_choose.clicked.connect(
            lambda: self.select_key_ui.select_key(
                parent_window, remap_key_entry, context="remap"
            )
        )
        remap_key_layout.addWidget(remap_key_choose, 1, 1, 1, 1)

        remap_key = RemapKeyWidget(
            remap_key_entry=remap_key_entry, remap_key_select=remap_key_select
        )

        return remap_key, remap_key_container

    def option_widget(self, parsed_remap):
        "Remap option widget on remap row"
        option_widget = QWidget()
        options_layout = QHBoxLayout(option_widget)
        options_layout.setContentsMargins(0, 5, 0, 0)

        first_key_checkbox = QCheckBox("Disable First Key", option_widget)
        first_key_checkbox.setToolTip(
            "Default Key Only: "
            "Check this to disable the first key when using multiple keys.\n"
        )
        if parsed_remap:
            first_key_checkbox.setChecked(parsed_remap.is_first_key)
        options_layout.addWidget(first_key_checkbox)

        sc_checkbox = QCheckBox("Use Scan Code", option_widget)
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

        text_format_checkbox = QCheckBox("Text Format", option_widget)
        text_format_checkbox.setToolTip(
            "Remap Key Only: Check this to send the actual text instead of a key"
        )
        if parsed_remap:
            text_format_checkbox.setChecked(parsed_remap.is_text_format)
        options_layout.addWidget(text_format_checkbox)

        hold_format_checkbox = QCheckBox("Hold Format", option_widget)
        hold_format_checkbox.setToolTip(
            "Remap Key Only: Simulate holding the key for a set interval"
        )
        if parsed_remap:
            hold_format_checkbox.setChecked(parsed_remap.is_hold_format)
        options_layout.addWidget(hold_format_checkbox)

        hold_interval_entry = QLineEdit(option_widget)
        hold_interval_entry.setPlaceholderText("Int")
        hold_interval_entry.setFixedWidth(40)
        hold_interval_entry.setToolTip(
            "Remap Key Only: Enter the hold interval in seconds (Default is 10 second)"
        )
        hold_interval_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if parsed_remap:
            hold_interval_float = float(parsed_remap.hold_interval)
            hold_interval_str = (
                str(int(hold_interval_float))
                if hold_interval_float.is_integer()
                else str(hold_interval_float)
            )
            hold_interval_entry.setText(hold_interval_str)
        options_layout.addWidget(hold_interval_entry)

        option = OptionWidget(
            text_format_checkbox=text_format_checkbox,
            hold_format_checkbox=hold_format_checkbox,
            hold_interval_entry=hold_interval_entry,
            first_key_checkbox=first_key_checkbox,
            sc_checkbox=sc_checkbox,
        )

        return option, option_widget


class ShortcutRow:
    "Shortcut row on profile creation"

    def __init__(self, edit_frame):
        # Variable
        self.is_text_mode = None
        self.shortcut_rows = []

        # Composition
        self.key_listening_comp = KeyListening(edit_frame)

        # UI
        self.shortcut_entry = None

    def shortcut_row(self, parent_window, parsed_shortcuts_list: list = None):
        "Build shortcut row"
        # Widget and layout
        shortcut_widget = QWidget()
        shortcut_widget.setContentsMargins(0, 0, 0, 0)
        shortcut_layout = QVBoxLayout(shortcut_widget)
        shortcut_layout.setContentsMargins(0, 0, 0, 0)

        # Shortcut title
        shortcut_title = self.shortcut_title()
        shortcut_layout.addWidget(shortcut_title)

        # Shortcut row
        shared_row = SharedRow()

        def add_empty_row(_):
            "Add empty shortcut row"
            # Shortcut row without passing parsed shortcut list
            shortcut_row_widget = self.shortcut_card(parent_window)
            shortcut_layout.addWidget(shortcut_row_widget)

            # Separator widget
            separator_widget = shared_row.separator_widget(
                add_empty_row, shortcut_widget
            )
            shortcut_layout.addWidget(separator_widget)

        if parsed_shortcuts_list:
            for parsed_shortcut in parsed_shortcuts_list:
                # Shortcut row
                shortcut_row_widget = self.shortcut_card(parent_window, parsed_shortcut)
                shortcut_layout.addWidget(shortcut_row_widget)

                # Separator widget
                separator_widget = shared_row.separator_widget(
                    add_empty_row, shortcut_widget
                )
                shortcut_layout.addWidget(separator_widget)
        else:
            add_empty_row(None)

        return shortcut_widget

    def shortcut_title(self):
        "Shortcuts row tittle label"
        shortcut_label = QLabel("Shortcut")
        shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcut_label.setStyleSheet(style.PROFILE_ROW_LABEL)
        return shortcut_label

    def shortcut_card(self, parent_window, parsed_shortcut=None):
        "Shortcut row"
        # Card frame
        card_frame = QFrame()
        card_frame.setFrameShape(QFrame.NoFrame)
        card_frame.setStyleSheet(style.card())

        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(0)

        shortcut_row_widget = QWidget(card_frame)
        shortcut_row_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        card_layout.addWidget(shortcut_row_widget)

        shortcut_row_layout = QGridLayout(shortcut_row_widget)
        shortcut_row_widget.setLayout(shortcut_row_layout)
        shortcut_row_layout.setContentsMargins(80, 0, 80, 0)
        shortcut_row_layout.setVerticalSpacing(0)

        # Shortcut Widget
        self.shortcut_widget(
            shortcut_row_widget, shortcut_row_layout, parsed_shortcut, parent_window
        )

        return card_frame

    def shortcut_widget(
        self, shortcut_row_widget, shortcut_row_layout, parsed_shortcut, parent_window
    ):
        "Shortcut widget"
        shortcut_continer = QWidget(shortcut_row_widget)
        shortcut_layout = QGridLayout(shortcut_continer)
        # shortcut_layout.setContentsMargins(0, 0, 0, 0)
        # shortcut_layout.setSpacing(2)

        shortcut_key_select = QPushButton("Select", shortcut_row_widget)
        shortcut_key_select.setToolTip(
            "Press any key or shortcut to capture it automatically"
        )
        shortcut_key_select.clicked.connect(
            lambda: self.key_listening_comp.key_listening(
                self.shortcut_entry, shortcut_key_select
            )
        )
        shortcut_layout.addWidget(shortcut_key_select, 0, 0, 1, 2)

        self.shortcut_entry = QLineEdit(shortcut_continer)
        self.shortcut_entry.setToolTip(
            "Shortcut can be "
            "a single key, multiple keys, or shortcut specials "
            "(See select key)"
        )
        self.shortcut_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if parsed_shortcut:
            self.shortcut_entry.setText(parsed_shortcut)
        self.shortcut_rows.append((self.shortcut_entry, shortcut_key_select))
        shortcut_layout.addWidget(self.shortcut_entry, 1, 0)

        shortcut_choose = QPushButton(shortcut_continer)
        shortcut_choose.setFixedWidth(28)
        shortcut_choose.setIcon(icons.get_icon(icons.search))
        shortcut_choose.setToolTip("Choose Shortcut key")
        shortcut_choose.clicked.connect(
            lambda: SelectKeyUI().select_key(
                parent_window, self.shortcut_entry, context="shortcut"
            )
        )
        shortcut_layout.addWidget(shortcut_choose, 1, 1)

        shortcut_row_layout.addWidget(shortcut_continer, 0, 0)


class KeyListening(QObject):
    "Listen to key press"

    request_timer_start = Signal()

    def __init__(self, edit_frame):
        super().__init__()
        # Composition
        self.remap_row_core = RemapRowCore()

        # Signal
        self.request_timer_start.connect(self.remap_row_core.release_timer)

        # Variable
        self.mouse_listening_initialized = False
        self.is_listening = False
        self.copas_rows = []

        # UI
        self.edit_frame = edit_frame

    def eventFilter(self, _, event):  # pylint: disable=C0103
        "Filter event by key press and window"
        if event.type() in (
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.KeyPress,
            QEvent.KeyRelease,
            QEvent.FocusIn,
            QEvent.FocusOut,
        ):
            return True
        if event.type() in (
            QEvent.Close,
            QEvent.WindowDeactivate,
            QEvent.Hide,
            QEvent.Leave,
        ):
            return True
        return False

    def toggle_other_buttons(self, target_button, other_button_enabled: bool):
        "Change the state of non selected button"
        button_list = self.edit_frame.findChildren(QPushButton)
        for button in button_list:
            if button != target_button:
                button.setEnabled(other_button_enabled)

    def toggle_other_entry(self, target_entry, other_entry_enabled: bool):
        "Install or remove event filter to enable/disable entry"
        entry_list = self.edit_frame.findChildren(QLineEdit)
        for entry in entry_list:
            if entry != target_entry:
                if other_entry_enabled:
                    entry.removeEventFilter(self)
                else:
                    entry.installEventFilter(self)

    def key_listening(self, target_entry, target_button):
        "Get and Listen to key press"
        # Initialize mouse listening thread once
        if not self.mouse_listening_initialized:
            mouse_listener = pynput.mouse.Listener(on_click=self.mouse_listening)
            mouse_listener.start()
            self.mouse_listening_initialized = True

        if not self.is_listening:
            self.is_listening = True
            self.remap_row_core.active_entry = target_entry
            self.remap_row_core.pressed_keys = []
            self.remap_row_core.last_combination = ""

            # Dsiable other entry
            self.toggle_other_entry(target_entry, other_entry_enabled=False)

            # Disbale other button
            self.toggle_other_buttons(target_button, other_button_enabled=False)

            self.remap_row_core.set_timer = QTimer()
            self.remap_row_core.set_timer.setSingleShot(True)
            self.remap_row_core.set_timer.timeout.connect(
                lambda: self.remap_row_core.finalize_combination(target_entry)
            )

            keyboard.hook(
                lambda event: self.multi_key_event(event, target_entry, target_button)
            )

        else:
            self.is_listening = False
            self.remap_row_core.active_entry = None
            self.remap_row_core.pressed_keys = []

            # Enable other entry
            self.toggle_other_entry(target_entry, other_entry_enabled=True)

            # Enable other button
            self.toggle_other_buttons(target_button, other_button_enabled=True)

    def multi_key_event(self, event, entry_widget, button):
        "Action when multiple key is pressed, set timer before saving the key"
        if not self.is_listening or self.remap_row_core.active_entry != entry_widget:
            return

        # if sc_checkbox.isChecked():
        #     key = f"SC{event.scan_code:02X}"
        # else:
        #     key = event.name

        key = event.name
        key_lower = key.lower()
        if key_lower in constant.changes_key:
            key = constant.changes_key[key_lower]

        if len(key) == 1 and key.isupper() and key.isalpha():
            key = key.lower()

        if event.event_type == "down":
            if key not in self.remap_row_core.pressed_keys:
                self.remap_row_core.pressed_keys.append(key)
                self.remap_row_core.update_widget(entry_widget)
            if (
                hasattr(self, "release_timer")
                and self.remap_row_core.set_timer.isActive()
            ):
                self.remap_row_core.set_timer.stop()

        elif event.event_type == "up":
            if key in self.remap_row_core.pressed_keys:
                self.remap_row_core.pressed_keys.remove(key)
                if not self.remap_row_core.pressed_keys:
                    self.key_listening(entry_widget, button)
                    self.request_timer_start.emit()

                else:
                    if hasattr(self, "release_timer"):
                        self.request_timer_start.emit()

    def mouse_listening(self, x, y, button, pressed):  # pylint: disable=W0613
        "Get and listen to mouse key press. Pynput on_click"
        if not (self.is_listening and self.remap_row_core.active_entry):
            return

        button_map = {
            pynput.mouse.Button.left: "Left Button",
            pynput.mouse.Button.right: "Right Button",
            pynput.mouse.Button.middle: "Middle Button",
        }
        mouse_button = button_map.get(button, getattr(button, "name", str(button)))

        if pressed and not self.check_mouse_event():
            if mouse_button not in self.remap_row_core.pressed_keys:
                self.remap_row_core.pressed_keys.append(mouse_button)
                self.remap_row_core.update_widget(self.remap_row_core.active_entry)
        else:
            if mouse_button in self.remap_row_core.pressed_keys:
                self.remap_row_core.pressed_keys.remove(mouse_button)
                if not self.remap_row_core.pressed_keys:
                    self.key_listening(self.remap_row_core.active_entry, None)
                    self.request_timer_start.emit()

    def check_mouse_event(self):
        "Check if cursor is over any widget in key_rows"
        local_pos = self.edit_frame.mapFromGlobal(QCursor.pos())
        widget = self.edit_frame.childAt(local_pos)
        if isinstance(widget, (QPushButton, QLineEdit, QCheckBox)):
            return True

        return False
