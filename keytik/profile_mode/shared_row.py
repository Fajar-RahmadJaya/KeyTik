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

"""Row utility used across profile mode."""

from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QCompleter,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QWidget,
)

from keytik.profile_mode.profile_mode_core import ProfileModeCore
from keytik.utility import style, utils


class SharedRow:  # pylint: disable=R0903
    """Shared row for remap and shortcut row."""

    def separator_widget(self, plus_event, parent_widget: QWidget):
        """Remap row separator widget."""
        separator_widget = QWidget()
        separator_layout = QHBoxLayout(separator_widget)
        separator_widget.setLayout(separator_layout)
        separator_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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

    def remap_entry_template(self) -> QLineEdit:
        """Entry template used across remap row."""
        auto_complete_model = list(ProfileModeCore().load_key_list().values())
        auto_complete_config = utils.get_config().auto_complete

        completer = QCompleter(auto_complete_model)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        if auto_complete_config == "inline":
            completer.setCompletionMode(QCompleter.InlineCompletion)
        elif auto_complete_config == "popup":
            completer.setCompletionMode(QCompleter.PopupCompletion)
        elif auto_complete_config == "unfiltered_popup":
            completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)

        entry = QLineEdit()
        if auto_complete_config != "disable":
            entry.setCompleter(completer)
        entry.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return entry
