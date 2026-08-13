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

from PySide6.QtCore import QMargins, QSize, Qt  # pylint: disable=E0611
from PySide6.QtGui import QPalette  # pylint: disable=E0611
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QCompleter,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from keytik.profile_mode.profile_mode_core import ProfileModeCore
from keytik.utility import icons
from keytik.utility.style import Palette
from keytik.utility.utils import Config


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
        auto_complete_config = Config().get_config().auto_complete

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

    def expand_button(self, parent_window: QDialog):
        """Button to expand profile mode."""
        button = QToolButton()
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setIcon(icons.get_icon(icons.fullscreen))
        button.setIconSize(QSize(16, 16))
        button.setToolTip("Maximize")
        button.setFixedSize(40, 40)
        button.setCheckable(True)
        palette = Palette().get_palette()
        palette.setColor(QPalette.ColorRole.Accent, palette.color(QPalette.ColorRole.Button))
        button.setPalette(palette)
        button.setStyleSheet("""
        QToolButton{
            margin: 8px;
        }
        """)

        edit_layout = parent_window.findChild(QVBoxLayout, "editLayout")
        prev_layout_margin = edit_layout.contentsMargins()
        button.clicked.connect(
            lambda: self.expand_text_block(button, prev_layout_margin, parent_window)
        )

        return button

    def expand_text_block(
        self, button: QToolButton, prev_layout_margin: QMargins, parent_window: QDialog
    ):
        """Hide other widget except text block."""
        layout = parent_window.findChild(QGridLayout)
        isexpand = button.isChecked()

        if isexpand:
            button.setToolTip("Minimize")
            button.setIcon(icons.get_icon(icons.fullscreen_exit))
            layout.setContentsMargins(0, 0, 0, 0)
        else:
            button.setToolTip("Maximize")
            button.setIcon(icons.get_icon(icons.fullscreen))
            layout.setContentsMargins(prev_layout_margin)

        top_widget = parent_window.findChild(QWidget, "TopWidget")
        top_widget.setHidden(isexpand)

        bottom_widget = parent_window.findChild(QWidget, "BottomWidget")
        bottom_widget.setHidden(isexpand)

        # Collapsible shortcut on text mode
        middle_stack = parent_window.findChild(QStackedWidget)
        collapsible_shortcut = middle_stack.widget(1).findChild(QWidget)
        if collapsible_shortcut:
            collapsible_shortcut.setHidden(isexpand)
