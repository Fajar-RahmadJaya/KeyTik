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

from dataclasses import dataclass

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

from keytik.profile_mode.key_listening import KeyListening
from keytik.profile_mode.shared_row import SharedRow
from keytik.select_key.select_key_ui import SelectKeyUI
from keytik.utility import icons, style


@dataclass
class OptionWidget:
    """Data class containing option widget."""

    text_format_checkbox: QCheckBox = None
    hold_format_checkbox: QCheckBox = None
    hold_interval_entry: QLineEdit = None
    first_key_checkbox: QCheckBox = None
    sc_checkbox: QCheckBox = None


@dataclass
class DefaultKeyWidget:
    """Data class containing default key widget."""

    default_key_entry: QLineEdit = None
    default_key_select: QPushButton = None


@dataclass
class RemapKeyWidget:
    """Data class containing remap key widget."""

    remap_key_entry: QLineEdit = None
    remap_key_select: QPushButton = None


@dataclass
class KeyWidget:
    """Data class containing key widget."""

    default_key: DefaultKeyWidget = None
    remap_key: RemapKeyWidget = None
    option: OptionWidget = None


class DefaultMode:
    """Remap row on profile creation."""

    def __init__(self, edit_frame):
        super().__init__()
        # Composition
        self.select_key_ui = SelectKeyUI()
        self.key_listening_comp = KeyListening(edit_frame)
        self.shared_row = SharedRow()

        # Variables
        self.key_rows = []
        self.edit_frame = edit_frame

    def remap_row(self, parent_window, parsed_remap_list: list | None = None):
        """Build remap row."""
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
            """Add empty remap row and separator."""
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
                remap_row_widget = self.remap_card(parent_window, parsed_remap=parsed_remap)
                remap_layout.addWidget(remap_row_widget)

                # Separator
                separator_widget = shared_row.separator_widget(add_empty_row, remap_widget)
                remap_layout.addWidget(separator_widget)
        else:
            add_empty_row(None)

        return remap_widget

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
        remap_card_frame = QFrame()
        remap_card_frame.setFrameShape(QFrame.NoFrame)
        remap_card_frame.setStyleSheet(style.card())

        card_layout = QVBoxLayout(remap_card_frame)
        card_layout.setContentsMargins(8, 8, 8, 8)

        # Remap row layout
        remap_row_widget = QWidget(remap_card_frame)
        remap_row_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        card_layout.addWidget(remap_row_widget)

        remap_row_layout = QGridLayout(remap_row_widget)
        remap_row_widget.setLayout(remap_row_layout)
        remap_row_layout.setContentsMargins(16, 0, 16, 4)
        remap_row_layout.setVerticalSpacing(0)

        # Default Key Widget
        default_key, default_key_widget = self.default_key_widget(parsed_remap, parent_window)
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
        self.key_rows.append(KeyWidget(default_key=default_key, remap_key=remap_key, option=option))

        return remap_card_frame

    def default_key_widget(self, parsed_remap, parent_window):
        """Default key widget on remap row."""
        default_key_container = QWidget()
        default_key_container.setContentsMargins(8, 0, 8, 0)

        default_key_layout = QGridLayout(default_key_container)

        default_key_select = QPushButton("Select")
        default_key_select.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        default_key_select.setToolTip("Press any key or shortcut to capture it automatically")
        default_key_select.clicked.connect(
            lambda: self.key_listening_comp.key_listening(default_key_entry, default_key_select)
        )
        default_key_layout.addWidget(default_key_select, 0, 0, 1, 2)

        default_key_entry = self.shared_row.remap_entry_template()
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

        default_key = DefaultKeyWidget(
            default_key_entry=default_key_entry, default_key_select=default_key_select
        )
        return default_key, default_key_container

    def remap_key_widget(self, parsed_remap, parent_window):
        """Remap key widget on remap row."""
        remap_key_container = QWidget()
        remap_key_container.setContentsMargins(8, 0, 8, 0)

        remap_key_layout = QGridLayout(remap_key_container)

        remap_key_select = QPushButton("Select")
        remap_key_select.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        remap_key_select.setToolTip("Press any key or shortcut to capture it automatically")
        remap_key_select.clicked.connect(
            lambda: self.key_listening_comp.key_listening(remap_key_entry, remap_key_select)
        )
        remap_key_layout.addWidget(remap_key_select, 0, 0, 1, 2)

        remap_key_entry = self.shared_row.remap_entry_template()
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

        remap_key = RemapKeyWidget(
            remap_key_entry=remap_key_entry, remap_key_select=remap_key_select
        )

        return remap_key, remap_key_container

    def option_widget(self, parsed_remap):
        """Remap option widget on remap row."""
        option_widget = QWidget()
        options_layout = QHBoxLayout(option_widget)
        options_layout.setContentsMargins(0, 5, 0, 0)

        first_key_checkbox = QCheckBox("Disable First Key", option_widget)
        first_key_checkbox.setToolTip(
            "Default Key Only: Check this to disable the first key when using multiple keys.\n"
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
        options_layout.addWidget(hold_interval_entry)

        option = OptionWidget(
            text_format_checkbox=text_format_checkbox,
            hold_format_checkbox=hold_format_checkbox,
            hold_interval_entry=hold_interval_entry,
            first_key_checkbox=first_key_checkbox,
            sc_checkbox=sc_checkbox,
        )

        return option, option_widget
