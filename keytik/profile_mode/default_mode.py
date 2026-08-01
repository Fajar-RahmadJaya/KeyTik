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

"""Remap and shortcut row."""

from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtSvgWidgets import QSvgWidget  # pylint: disable=E0611
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from keytik.profile_manager.parse_script import ParseScript
from keytik.profile_mode.key_listening import KeyListening
from keytik.profile_mode.shared_row import SharedRow
from keytik.select_key.select_key_ui import SelectKeyUI
from keytik.utility import icons, style


class RemapObject:  # pylint: disable=R0903
    """Hold remap widget object name."""

    default_key_select = "DefaultKeySelect"
    default_key_entry = "DefaultKeyEntry"
    remap_key_select = "RemapKeySelect"
    remap_key_entry = "RemapKeyEntry"
    first_key_checkbox = "FirstKeyCheckbox"
    scan_code_checkbox = "ScanCodeCheckbox"
    text_format_checkbox = "TextFormatCheckbox"
    hold_format_checkbox = "HoldFormatCheckbox"
    hold_interval_entry = "HoldIntervalEntry"


class DefaultMode:
    """Remap row on profile creation."""

    def __init__(self, edit_frame):
        super().__init__()
        # Composition
        self.select_key_ui = SelectKeyUI()
        self.key_listening_comp = KeyListening(edit_frame)
        self.shared_row = SharedRow()

        # Variables
        self.remap_frame = None
        self.edit_frame = edit_frame

    def remap_row(self, parent_window, lines=None):
        """Build remap row."""
        # Remap
        remap_widget = QWidget()
        remap_widget.setObjectName("RemapWidget")
        remap_layout = QVBoxLayout(remap_widget)
        remap_layout.setContentsMargins(0, 0, 0, 0)
        remap_layout.setSpacing(8)

        # Remap title
        remap_title_widget = self.remap_title()
        remap_layout.addWidget(remap_title_widget)

        shared_row = SharedRow()

        # Remap row
        def add_empty_row(_):
            """Add empty remap row and separator."""
            # Add empty row
            remap_row_widget = self.remap_card(parent_window)
            remap_layout.addWidget(remap_row_widget)

            # Add separator
            separator_widget = shared_row.separator_widget(add_empty_row, remap_widget)
            remap_layout.addWidget(separator_widget)

            self.entry_subscription(remap_widget, add_empty_row)

        parsed_remap_list = ParseScript().parse_default_mode(lines) if lines else None
        if parsed_remap_list:
            for parsed_remap in parsed_remap_list:
                # Remap row
                # If list empty, add empty row
                remap_row_widget = self.remap_card(parent_window, parsed_remap=parsed_remap)
                remap_layout.addWidget(remap_row_widget)

                # Separator
                separator_widget = shared_row.separator_widget(add_empty_row, remap_widget)
                remap_layout.addWidget(separator_widget)

                self.entry_subscription(remap_widget, add_empty_row)
        else:
            add_empty_row(None)

        return remap_widget

    def entry_subscription(self, remap_widget: QWidget, event):
        """Add event subscription to last entry."""
        default_key_list = remap_widget.findChildren(QLineEdit, "DefaultKeyEntry")
        if len(default_key_list) != 1:
            prev_default = default_key_list[-2]
            prev_default.textChanged.disconnect()
        last_default = default_key_list[-1]

        remap_key_list = remap_widget.findChildren(QLineEdit, "RemapKeyEntry")
        if len(remap_key_list) != 1:
            prev_remap = remap_key_list[-2]
            prev_remap.textChanged.disconnect()
        last_remap = remap_key_list[-1]

        def entry_changed_event():
            """Add row only when both entry is not empty."""
            if last_remap.text() and last_default.text():
                event(None)

        last_default.textChanged.connect(entry_changed_event)
        last_remap.textChanged.connect(entry_changed_event)

    def remap_title(self):
        """Key remap row tittle label."""
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
        """Remap row."""
        # Remap row card
        self.remap_frame = QFrame()
        self.remap_frame.setObjectName("RemapRowWidget")
        self.remap_frame.setFrameShape(QFrame.NoFrame)
        self.remap_frame.setStyleSheet(style.card())
        self.remap_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        card_layout = QGridLayout(self.remap_frame)
        self.remap_frame.setLayout(card_layout)
        card_layout.setContentsMargins(0, 8, 0, 0)
        card_layout.setVerticalSpacing(0)

        # Default Key Widget
        card_layout.addWidget(self.default_key_widget(parsed_remap, parent_window), 0, 0)

        # Arrow Widget
        arrow_icon = QSvgWidget(icons.arrow)
        arrow_icon.setFixedSize(32, 24)
        card_layout.addWidget(arrow_icon, 0, 1)

        # Remap Key Widget
        card_layout.addWidget(self.remap_key_widget(parsed_remap, parent_window), 0, 2)

        # Option widget
        card_layout.addWidget(self.option_widget(parsed_remap), 1, 0, 1, 3)

        return self.remap_frame

    def default_key_widget(self, parsed_remap, parent_window):
        """Default key widget on remap row."""
        default_key_container = QWidget()
        default_key_container.setContentsMargins(32, 0, 8, 0)

        default_key_layout = QGridLayout(default_key_container)

        default_key_select = QPushButton("Select")
        default_key_select.setObjectName(RemapObject.default_key_select)
        default_key_select.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        default_key_select.setToolTip("Press any key or shortcut to capture it automatically")
        default_key_select.clicked.connect(
            lambda: self.key_listening_comp.key_listening(default_key_entry, default_key_select)
        )
        default_key_layout.addWidget(default_key_select, 0, 0, 1, 2)

        default_key_entry = self.shared_row.remap_entry_template()
        default_key_entry.setObjectName("DefaultKeyEntry")
        default_key_entry.setObjectName(RemapObject.default_key_entry)
        default_key_entry.setParent(default_key_container)
        default_key_entry.setToolTip(
            "Default key can be a single key, multiple keys, or a double key (eg. double-click)."
            "\nYou can disable auto complete from setting."
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
        default_key_choose.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        default_key_layout.addWidget(default_key_choose, 1, 1, 1, 1)

        return default_key_container

    def remap_key_widget(self, parsed_remap, parent_window):
        """Remap key widget on remap row."""
        remap_key_container = QWidget()
        remap_key_container.setContentsMargins(8, 0, 32, 0)

        remap_key_layout = QGridLayout(remap_key_container)

        remap_key_select = QPushButton("Select")
        remap_key_select.setObjectName(RemapObject.remap_key_select)
        remap_key_select.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        remap_key_select.setToolTip("Press any key or shortcut to capture it automatically")
        remap_key_select.clicked.connect(
            lambda: self.key_listening_comp.key_listening(remap_key_entry, remap_key_select)
        )
        remap_key_layout.addWidget(remap_key_select, 0, 0, 1, 2)

        remap_key_entry = self.shared_row.remap_entry_template()
        remap_key_entry.setObjectName("RemapKeyEntry")
        remap_key_entry.setObjectName(RemapObject.remap_key_entry)
        remap_key_entry.setParent(remap_key_container)
        remap_key_entry.setToolTip(
            "Remap key can be a single key, multiple keys, text, or hold."
            "\nYou can disable auto complete from setting."
        )
        if parsed_remap:
            remap_key_entry.setText(parsed_remap.remap_key)
        remap_key_layout.addWidget(remap_key_entry, 1, 0, 1, 1)

        remap_key_choose = QPushButton(remap_key_container)
        remap_key_choose.setFixedWidth(28)
        remap_key_choose.setIcon(icons.get_icon(icons.search))
        remap_key_choose.setToolTip("Choose Remap key")
        remap_key_choose.clicked.connect(
            lambda: self.select_key_ui.select_key(parent_window, remap_key_entry, context="remap")
        )
        remap_key_choose.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        remap_key_layout.addWidget(remap_key_choose, 1, 1, 1, 1)

        return remap_key_container

    def option_widget(self, parsed_remap):
        """Remap option collapsible widget."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        widget.setLayout(layout)

        content_widget = QWidget()
        content_widget.setObjectName("OptionContent")
        content_widget.setStyleSheet(f"""
        QWidget#OptionContent {{
            background-color: {style.palette_role.surface};
        }}
        """)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_widget.setLayout(content_layout)

        default_option_content = self.default_option_content(parsed_remap)
        default_option_content.setHidden(True)
        content_layout.addWidget(default_option_content)

        remap_option_content = self.remap_option_content(parsed_remap)
        remap_option_content.setHidden(True)
        content_layout.addWidget(remap_option_content)

        layout.addWidget(self.option_header(default_option_content, remap_option_content))

        layout.addWidget(content_widget)

        return widget

    def option_header(self, default_option_content: QWidget, remap_option_content: QWidget):
        """Get option header widget."""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        widget.setLayout(layout)

        keyboard_arrow_down = icons.get_icon(icons.keyboard_arrow_down).pixmap(16, 16)
        keyboard_arrow_up = icons.get_icon(icons.keyboard_arrow_up).pixmap(16, 16)

        default_header, default_header_icon = self.option_header_button("Default Key Option")
        default_header_icon.setPixmap(keyboard_arrow_down)
        default_header.setStyleSheet(style.option_header_style())
        layout.addWidget(default_header)

        vertical_separator = QWidget()
        vertical_separator.setStyleSheet(f"background-color: {style.palette_role.surface}")
        vertical_separator.setFixedWidth(3)
        vertical_separator.setFixedHeight(20)
        layout.addWidget(vertical_separator)

        remap_header, remap_header_icon = self.option_header_button("Remap Key Option")
        remap_header_icon.setPixmap(keyboard_arrow_down)
        remap_header.setStyleSheet(style.option_header_style())
        layout.addWidget(remap_header)

        def default_click_event(ischecked: bool):
            """Change default option button stylesheet and show default content."""
            if ischecked:
                default_header_icon.setPixmap(keyboard_arrow_up)
                default_header.setStyleSheet(style.option_header_style(isclicked=True))
                default_option_content.setHidden(False)
                remap_click_event(False)
            else:
                default_header_icon.setPixmap(keyboard_arrow_down)
                default_header.setChecked(False)
                default_header.setStyleSheet(style.option_header_style())
                default_option_content.setHidden(True)

        def remap_click_event(ischecked: bool):
            if ischecked:
                remap_header_icon.setPixmap(keyboard_arrow_up)
                remap_header.setStyleSheet(style.option_header_style(isclicked=True))
                remap_option_content.setHidden(False)
                default_click_event(False)
            else:
                remap_header_icon.setPixmap(keyboard_arrow_down)
                remap_header.setChecked(False)
                remap_header.setStyleSheet(style.option_header_style())
                remap_option_content.setHidden(True)

        default_header.clicked.connect(lambda: default_click_event(default_header.isChecked()))
        remap_header.clicked.connect(lambda: remap_click_event(remap_header.isChecked()))

        return widget

    def option_header_button(self, title_string: str):
        """Get remap option header widget."""
        button = QPushButton()
        button.setCheckable(True)
        button.setFlat(True)
        button.setFixedHeight(28)

        layout = QGridLayout(button)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel(title_string)
        title.setStyleSheet("background-color: transparent;")
        layout.addWidget(title, 0, 0, 1, 2, Qt.AlignCenter)

        icon = QLabel()
        icon.setFixedSize(32, 32)
        icon.setStyleSheet("background-color: transparent;")
        icon.setContentsMargins(0, 0, 16, 0)
        layout.addWidget(icon, 0, 1, 1, 1)

        return button, icon

    def default_option_content(self, parsed_remap):
        """Get default key option widget."""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        widget.setLayout(layout)

        first_key_checkbox = QCheckBox("Disable First Key")
        first_key_checkbox.setObjectName(RemapObject.first_key_checkbox)
        first_key_checkbox.setToolTip(
            "Default Key Only: Check this to disable the first key when using multiple keys.\n"
        )
        if parsed_remap:
            first_key_checkbox.setChecked(parsed_remap.is_first_key)
        layout.addWidget(first_key_checkbox, alignment=Qt.AlignCenter)

        sc_checkbox = QCheckBox("Use Scan Code")
        sc_checkbox.setObjectName(RemapObject.scan_code_checkbox)
        sc_checkbox.setToolTip(
            "Default Key Only: "
            "Check this to make the Select button use Scan Code (SC) instead.\n"
            "Scan Code is the hardware coordinate of the key, "
            "use this if the key is not detected or missing from the list."
        )
        if parsed_remap:
            sc_checkbox.setChecked(parsed_remap.is_sc)
        layout.addWidget(sc_checkbox, alignment=Qt.AlignCenter)

        return widget

    def remap_option_content(self, parsed_remap):
        """Get remap key option widget."""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        widget.setLayout(layout)

        text_format_checkbox = QCheckBox("Text Format")
        text_format_checkbox.setObjectName("Test")
        text_format_checkbox.setObjectName(RemapObject.text_format_checkbox)
        text_format_checkbox.setToolTip(
            "Remap Key Only: Check this to send the actual text instead of a key"
        )
        if parsed_remap:
            text_format_checkbox.setChecked(parsed_remap.is_text_format)
        layout.addWidget(text_format_checkbox, alignment=Qt.AlignCenter)

        hold_format_widget = QWidget()
        hold_format_layout = QHBoxLayout()
        hold_format_layout.setContentsMargins(0, 0, 0, 0)
        hold_format_widget.setLayout(hold_format_layout)
        layout.addWidget(hold_format_widget, alignment=Qt.AlignCenter)

        hold_format_checkbox = QCheckBox("Hold Format")
        hold_format_checkbox.setObjectName(RemapObject.hold_format_checkbox)
        hold_format_checkbox.setToolTip(
            "Remap Key Only: Simulate holding the key for a set interval"
        )
        if parsed_remap:
            hold_format_checkbox.setChecked(parsed_remap.is_hold_format)
        hold_format_layout.addWidget(hold_format_checkbox)

        hold_interval_entry = QLineEdit()
        hold_interval_entry.setObjectName(RemapObject.hold_interval_entry)
        hold_interval_entry.setPlaceholderText("Int")
        hold_interval_entry.setFixedWidth(40)
        hold_interval_entry.setFixedHeight(hold_format_checkbox.sizeHint().height())
        hold_interval_entry.setToolTip(
            "Remap Key Only: Enter the hold interval in seconds (Default is 10 second)"
        )
        hold_interval_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)

        def hold_interval_entry_status():
            """Set hold interval entry to be disabled or not."""
            if hold_format_checkbox.isChecked():
                hold_interval_entry.setDisabled(False)
            else:
                hold_interval_entry.setDisabled(True)

        hold_interval_entry_status()
        hold_format_checkbox.toggled.connect(hold_interval_entry_status)

        if parsed_remap:
            hold_interval_float = float(parsed_remap.hold_interval)
            hold_interval_str = (
                str(int(hold_interval_float))
                if hold_interval_float.is_integer()
                else str(hold_interval_float)
            )
            hold_interval_entry.setText(hold_interval_str)
        hold_format_layout.addWidget(hold_interval_entry)

        return widget
