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

"""Shared custom setting widget."""

from plwidgets.pl_checkbox import PlCheckBox
from PySide6.QtCore import QSize, Qt  # pylint: disable=E0611
from PySide6.QtGui import (  # pylint: disable=E0611
    QFont,
    QPalette,
)
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QWidget,
)

from keytik.utility import icons
from keytik.utility.style import Palette, Styling
from keytik.utility.utils import Utility


class SettingCombobox(QComboBox):  # pylint: disable=R0903
    """Ignore Wheel Event."""

    def wheelEvent(self, event):  # pylint: disable=C0103
        """Override wheelEvent."""
        event.ignore()


class SettingTemplate:
    """Widget template to use across setting UI."""

    def setting_card(self, icon_code=None, heading=None, subheading=None):
        """Setting card template."""
        card_frame = QFrame()
        card_frame.setFrameShape(QFrame.NoFrame)
        card_frame.setObjectName("setting")
        card_frame.setStyleSheet(Styling().card("setting"))

        card_layout = QHBoxLayout()
        card_frame.setLayout(card_layout)

        if icon_code:
            card_layout.setContentsMargins(20, 16, 16, 16)
            card_layout.setSpacing(20)

            icon = self.adaptive_icon(icon_code, 16)
            icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            card_layout.addWidget(icon)
        else:
            card_layout.setContentsMargins(16, 16, 16, 16)

        if heading and subheading:
            theme_label = QLabel(
                f"<div style='font-size:13px; margin-bottom:2px'> {heading} </div>"
                f""" <div style='font-size:11px; color: {Palette().get_palette_role().subtext};'>
                {subheading} </div>"""
            )

            card_layout.addWidget(theme_label)

        return card_layout, card_frame

    def adaptive_icon(self, icon_code: dict[str, str], size: int) -> QLabel:
        """Adaptive icon supporting fluent and material icons."""
        winver = Utility().get_windows_version()
        fluent_support = 11
        mdl2_support = 10
        font = None

        if winver == fluent_support:
            font = QFont("Segoe Fluent Icons", size)
        elif winver == mdl2_support:
            font = QFont("Segoe MDL2 Assets", size)

        icon = QLabel()
        if winver in (fluent_support, mdl2_support):
            icon.setFont(font)
            icon.setText(icon_code.get("code_glyph"))
            icon.setStyleSheet("background-color: transparent;")
        else:
            material_size = size + 8
            qicon = icons.get_icon(icon_code.get("material_path"))
            icon.setPixmap(qicon.pixmap(QSize(material_size, material_size)))
            icon.setStyleSheet("background-color: transparent;")

        return icon

    def setting_combobox(self):
        """Setting combobox template."""
        setting_combobox = SettingCombobox()
        setting_combobox.setFixedWidth(164)
        setting_combobox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        return setting_combobox

    def setting_button(self):
        """Setting button template."""
        setting_button = QPushButton()
        setting_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        setting_button.setFixedWidth(164)

        return setting_button

    def setting_header_label(self):
        """Setting header label template."""
        setting_header_font = QFont()
        setting_header_font.setBold(True)
        setting_header_font.setPixelSize(13)

        setting_header_label = QLabel()
        setting_header_label.setFont(setting_header_font)
        setting_header_label.setContentsMargins(0, 0, 0, 4)

        return setting_header_label

    def setting_switch(self):
        """Toggle switch template for setting."""
        palett_comp = Palette()
        palette = palett_comp.get_palette()
        accent = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Accent)
        text = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Text)
        inverted_text = palett_comp.invert_color(text)
        window = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window)

        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        widget.setLayout(layout)

        label = QLabel()
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignRight)

        switch = PlCheckBox()
        switch._checkedBackgroundColor = accent  # pylint: disable=W0212
        switch._checkedHandleColor = inverted_text  # pylint: disable=W0212
        switch.backgroundColor = window
        switch.update()
        layout.addWidget(switch)

        def switch_event():
            """Change switch label based on check state."""
            if switch.isChecked():
                label.setText("On")
            else:
                label.setText("Off")

        switch.toggled.connect(switch_event)
        switch_event()

        return widget, switch

    def bread_crumb_bar(self, stack_widget: QStackedWidget):
        """Bread crumb inspired by WinUi3."""
        bread_crumb_bar = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        bread_crumb_bar.setLayout(layout)

        index_list = []

        def stack_change_event(is_start: bool = False):
            """Change breadcrumb based on index."""
            nonlocal index_list

            stack_index = stack_widget.currentIndex()
            object_name = stack_widget.currentWidget().objectName()
            title_name = object_name.replace("-", " ").replace("_", " ").title()

            new_title = self.bread_crumb_title(title_name, is_start)
            new_title.mousePressEvent = lambda _: stack_widget.setCurrentIndex(stack_index)

            if stack_index not in index_list:
                index_list.append(stack_index)
                layout.addWidget(new_title)
                title_list = bread_crumb_bar.findChildren(QLabel, "breadCrumbTitle")
            else:
                deleted_widget_count = len(index_list[index_list.index(stack_index) + 1 :])
                del index_list[-deleted_widget_count:]

                for _ in range(deleted_widget_count):
                    item = layout.takeAt(layout.count() - 1).widget()
                    item.deleteLater()

                title_list = bread_crumb_bar.findChildren(QLabel, "breadCrumbTitle")
                del title_list[-deleted_widget_count:]
                title_list[-1].setDisabled(True)

            for title in title_list[:-1]:
                title.setEnabled(True)

        # Start index
        stack_change_event(is_start=True)

        stack_widget.currentChanged.connect(lambda: stack_change_event(is_start=False))

        return bread_crumb_bar

    def bread_crumb_title(self, title_name: str, is_start: bool = False):
        """Bread crumb title widget."""
        bread_crumb_title = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        bread_crumb_title.setLayout(layout)

        if not is_start:
            chevron = SettingTemplate().adaptive_icon(icons.fluent_chevron_right, 8)
            layout.addWidget(chevron, alignment=Qt.AlignmentFlag.AlignCenter)

        palette = Palette().get_palette()
        text_active = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Text)
        text_disabled = palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text)

        font = QFont()
        font.setBold(True)
        font.setPixelSize(20)

        title = QLabel()
        title.setObjectName("breadCrumbTitle")
        title.setFont(font)
        title.setText(title_name)
        title.setContentsMargins(8, 8, 8, 8)
        title.setStyleSheet(
            f"QLabel {{ color: {text_disabled.name()}; }}"
            f"QLabel:disabled {{ color: {text_active.name()} }}"
        )
        title.setDisabled(True)
        title.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(title)

        return bread_crumb_title
