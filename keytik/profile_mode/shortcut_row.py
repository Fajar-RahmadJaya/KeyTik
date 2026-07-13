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

"""Shortcut row used across profile mode."""

from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from keytik.profile_mode.key_listening import KeyListening
from keytik.profile_mode.shared_row import SharedRow
from keytik.select_key.select_key_ui import SelectKeyUI
from keytik.utility import icons, style


class ShortcutRow:
    """Shortcut row on profile creation."""

    def __init__(self, edit_frame):
        # Variable
        self.is_text_mode = None
        self.shortcut_rows = []

        # Composition
        self.key_listening_comp = KeyListening(edit_frame)
        self.shared_row = SharedRow()

    def shortcut_row(self, parent_window, parsed_shortcuts_list: list | None = None, title=True):
        """Build shortcut row."""
        # Widget and layout
        shortcut_widget = QWidget()
        shortcut_widget.setContentsMargins(0, 0, 0, 0)
        shortcut_layout = QVBoxLayout(shortcut_widget)
        shortcut_layout.setContentsMargins(0, 0, 0, 0)

        # Shortcut title
        if title:
            shortcut_title = self.shortcut_title()
            shortcut_layout.addWidget(shortcut_title)

        # Shortcut row
        shared_row = SharedRow()

        def add_empty_row(_):
            """Add empty shortcut row."""
            # Shortcut row without passing parsed shortcut list
            shortcut_row_widget = self.shortcut_card(parent_window)
            shortcut_layout.addWidget(shortcut_row_widget)

            # Separator widget
            separator_widget = shared_row.separator_widget(add_empty_row, shortcut_widget)
            shortcut_layout.addWidget(separator_widget)

        if parsed_shortcuts_list:
            for parsed_shortcut in parsed_shortcuts_list:
                # Shortcut row
                shortcut_row_widget = self.shortcut_card(parent_window, parsed_shortcut)
                shortcut_layout.addWidget(shortcut_row_widget)

                # Separator widget
                separator_widget = shared_row.separator_widget(add_empty_row, shortcut_widget)
                shortcut_layout.addWidget(separator_widget)
        else:
            add_empty_row(None)

        return shortcut_widget

    def shortcut_title(self):
        """Shortcuts row tittle label."""
        shortcut_label = QLabel("Shortcut")
        shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcut_label.setStyleSheet(style.PROFILE_ROW_LABEL)
        return shortcut_label

    def shortcut_card(self, parent_window, parsed_shortcut=None):
        """Shortcut row."""
        # Card frame
        shortcut_card_frame = QFrame()
        shortcut_card_frame.setFrameShape(QFrame.NoFrame)
        shortcut_card_frame.setStyleSheet(style.card())

        card_layout = QVBoxLayout(shortcut_card_frame)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(0)

        shortcut_row_widget = QWidget(shortcut_card_frame)
        shortcut_row_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        card_layout.addWidget(shortcut_row_widget)

        shortcut_row_layout = QGridLayout(shortcut_row_widget)
        shortcut_row_widget.setLayout(shortcut_row_layout)
        shortcut_row_layout.setContentsMargins(80, 0, 80, 0)
        shortcut_row_layout.setVerticalSpacing(0)

        # Shortcut Widget
        self.shortcut_widget(
            shortcut_row_widget, shortcut_row_layout, parsed_shortcut, parent_window
        )

        return shortcut_card_frame

    def shortcut_widget(
        self, shortcut_row_widget, shortcut_row_layout, parsed_shortcut, parent_window
    ):
        """Shortcut widget."""
        shortcut_continer = QWidget(shortcut_row_widget)
        shortcut_layout = QGridLayout(shortcut_continer)

        shortcut_key_select = QPushButton("Select", shortcut_row_widget)
        shortcut_key_select.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        shortcut_key_select.setToolTip("Press any key or shortcut to capture it automatically")
        shortcut_key_select.clicked.connect(
            lambda: self.key_listening_comp.key_listening(shortcut_entry, shortcut_key_select)
        )
        shortcut_layout.addWidget(shortcut_key_select, 0, 0, 1, 2)

        shortcut_entry = self.shared_row.remap_entry_template()
        shortcut_entry.setParent(shortcut_continer)
        shortcut_entry.setToolTip(
            "Shortcut can be a single key, multiple keys, or shortcut specials (See select key)."
            "\nYou can disable auto complete from setting."
        )
        if parsed_shortcut:
            shortcut_entry.setText(parsed_shortcut)
        self.shortcut_rows.append((shortcut_entry, shortcut_key_select))
        shortcut_layout.addWidget(shortcut_entry, 1, 0)

        shortcut_choose = QPushButton(shortcut_continer)
        shortcut_choose.setFixedWidth(28)
        shortcut_choose.setIcon(icons.get_icon(icons.search))
        shortcut_choose.setToolTip("Choose Shortcut key")
        shortcut_choose.clicked.connect(
            lambda: SelectKeyUI().select_key(parent_window, shortcut_entry, context="shortcut")
        )
        shortcut_choose.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        shortcut_layout.addWidget(shortcut_choose, 1, 1)

        shortcut_row_layout.addWidget(shortcut_continer, 0, 0)
