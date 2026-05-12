"Main Window"

import os
import winshell
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QFrame, QPushButton, QGroupBox, QLabel, QSizePolicy)
from PySide6.QtGui import QIcon  # pylint: disable=E0611
from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtSvgWidgets import QSvgWidget  # pylint: disable=E0611

from utility import constant
from utility import utils
from utility import icons
from utility import diff
from utility import style
from dashboard.dashboard_core import DashboardCore
from script_profile.profile_ui import ProfileUI
from setting.setting_ui import SettingUI


class DashboardUI(QMainWindow):
    "Main Window"
    def __init__(self):
        super().__init__()
        # Composition
        self.dashboard_core = DashboardCore()
        self.profile_ui = ProfileUI(self.dashboard_core)

        # Signal
        self.dashboard_core.update_script_signal.connect(self.update_script_list)

        # UI initialization
        self.setWindowTitle(diff.PROGRAM_NAME)
        self.setFixedSize(660, 500)
        self.setWindowIcon(QIcon(constant.icon_path))
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        style.apply_mica(self)

        # Startup
        self.create_ui()

    def create_ui(self):
        "Dashboard Window"
        self.frame = QFrame()
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.addWidget(self.frame)
        self.frame_layout = QVBoxLayout(self.frame)

        self.profile_frame = QFrame()
        self.profile_layout = QGridLayout(self.profile_frame)
        self.profile_layout.setContentsMargins(0, 0, 0, 10)
        self.profile_layout.setHorizontalSpacing(15)
        self.profile_layout.setVerticalSpacing(10)
        self.profile_layout.setColumnStretch(0, 1)
        self.profile_layout.setColumnStretch(1, 1)
        self.profile_layout.setRowStretch(0, 1)
        self.profile_layout.setRowStretch(1, 1)
        self.profile_layout.setRowStretch(2, 1)
        self.frame_layout.addWidget(self.profile_frame)

        # Dashboard button widget
        button_frame = self.dashboard_button()

        self.frame_layout.addWidget(button_frame)

        self.dashboard_core.update_script_signal.emit()

    def dashboard_button(self):
        "Dashboard button widget"
        button_frame = QFrame()
        button_layout = QGridLayout(button_frame)
        button_layout.setContentsMargins(36, 8, 36, 8)

        prev_button = QPushButton()
        prev_button.setFixedWidth(84)
        prev_button.setIcon(icons.get_icon(icons.prev))
        prev_button.setToolTip("Previous Profile")
        prev_button.clicked.connect(self.dashboard_core.prev_page)
        button_layout.addWidget(prev_button, 0, 0)

        show_stored = QPushButton()
        show_stored.setFixedWidth(30)
        show_stored.setIcon(icons.get_icon(icons.show_stored))
        show_stored.setToolTip("Show Stored Profile")
        show_stored.clicked.connect(lambda: self.dashboard_core.toggle_script_dir(show_stored))
        button_layout.addWidget(show_stored, 0, 1)

        import_button = QPushButton()
        import_button.setFixedWidth(30)
        import_button.setIcon(icons.get_icon(icons.icon_import))
        import_button.setToolTip("Import AutoHotkey Script")
        import_button.clicked.connect(
            lambda: self.dashboard_core.import_button_clicked(self))
        button_layout.addWidget(import_button, 0, 2)

        # Create new profile button
        self.create_new_button(button_layout)

        always_top = QPushButton()
        always_top.setFixedWidth(30)
        always_top.setIcon(icons.get_icon(icons.on_top))
        always_top.setToolTip("Enable  Window Always on Top")
        always_top.clicked.connect(lambda: self.toggle_on_top(always_top))
        button_layout.addWidget(always_top, 0, 6)

        # Setting button
        setting_ui = SettingUI()  # Composition
        setting_button = QPushButton()
        setting_button.setFixedWidth(30)
        setting_button.setIcon(icons.get_icon(icons.setting))
        setting_button.setToolTip("Setting")
        setting_button.clicked.connect(lambda: setting_ui.setting_window(self))
        button_layout.addWidget(setting_button, 0, 7)

        next_button = QPushButton()
        next_button.setFixedWidth(84)
        next_button.setIcon(icons.get_icon(icons.icon_next))
        next_button.setToolTip("Next Profile")
        next_button.clicked.connect(self.dashboard_core.next_page)
        button_layout.addWidget(next_button, 0, 8)

        return button_frame

    def create_new_button(self, button_layout):
        "Crate new button with dummy label to give it more space"
        dummy_left = QLabel()
        dummy_left.setFixedWidth(12)
        button_layout.addWidget(dummy_left, 0, 3)

        create_button = QPushButton(" Create New Profile")
        create_button.setStyleSheet(style.button_highlight(create_button))
        create_button.setIcon(icons.get_icon(icons.plus, highlighted=True))
        create_button.setFixedWidth(152)
        create_button.setFixedHeight(36)
        create_button.clicked.connect(lambda: self.profile_ui.edit_script(None, self))
        button_layout.addWidget(create_button, 0, 4)

        dummy_right = QLabel()
        dummy_right.setFixedWidth(12)
        button_layout.addWidget(dummy_right, 0, 5)

    def update_script_list(self):
        "! From dashboard"
        for i in reversed(range(self.profile_layout.count())):
            widget = self.profile_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        start_index = self.dashboard_core.current_page * 6
        end_index = start_index + 6
        scripts = self.dashboard_core.list_scripts()
        scripts_to_display = scripts[start_index:end_index]

        for index in range(6):
            row = index // 2
            column = index % 2
            if index < len(scripts_to_display):
                script = scripts_to_display[index]
                self.profile_card(script, row, column)
            else:
                dummy_box = QGroupBox(" ")
                dummy_box.setStyleSheet(
                    "QGroupBox { background: transparent; border-radius: 8px; }")
                self.profile_layout.addWidget(dummy_box, row, column)

    def profile_card(self, script, row, column):
        "Profile action"
        group_box = QGroupBox(os.path.splitext(script)[0])
        group_box.setStyleSheet(style.GROUP_BOX)

        group_layout = QGridLayout(group_box)
        group_layout.setContentsMargins(12, 14, 12, 12)
        group_layout.setHorizontalSpacing(8)
        group_layout.setVerticalSpacing(8)

        # Pin icon
        self.pin_icon(script, parent=group_box)

        # Button
        group_layout.addWidget(self.run_button(script), 0, 0)
        group_layout.addWidget(self.edit_button(script), 0, 1)
        group_layout.addWidget(self.startup_button(script), 0, 2)
        group_layout.addWidget(self.copy_button(script), 1, 0)
        group_layout.addWidget(self.store_button(script), 1, 1)
        group_layout.addWidget(self.delete_button(script), 1, 2)

        self.profile_layout.addWidget(group_box, row, column)

    def pin_icon(self, script, parent):
        "Pin icon"
        if script in self.dashboard_core.pinned_profiles:
            icon_label = QSvgWidget(icons.pin_fill, parent)
        else:
            icon_label = QSvgWidget(icons.pin, parent)

        icon_label.setFixedSize(17, 17)
        icon_label.setToolTip(f'Pin "{os.path.splitext(script)[0]}"')
        icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
        icon_label.mousePressEvent = lambda _: self.dashboard_core.toggle_pin(script)
        icon_label.move(285, 3)

    def run_button(self, script):
        "Profile card run/exit button"
        run_button = QPushButton()
        run_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if script in self.dashboard_core.get_running_ahk():
            self.run_state(run_button, script)
        else:
            self.exit_state(run_button, script)

        return run_button

    def run_state(self, run_button: QPushButton, script, connect=False):
        "Button setting on run state"
        if connect:
            self.dashboard_core.activate_script(script)
            run_button.clicked.disconnect()

        run_button.setText(" Exit")
        run_button.setToolTip(f'Stop "{os.path.splitext(script)[0]}"')
        run_button.setIcon(icons.get_icon(icons.icon_exit))
        run_button.clicked.connect(
            lambda: self.exit_state(run_button, script, connect=True))

        return run_button

    def exit_state(self, run_button: QPushButton, script, connect=False):
        "Button setting on exit state"
        if connect:
            self.dashboard_core.exit_script(script)
            run_button.clicked.disconnect()

        run_button.setText(" Run")
        run_button.setToolTip(f'Start "{os.path.splitext(script)[0]}"')
        run_button.setIcon(icons.get_icon(icons.run))
        run_button.clicked.connect(
            lambda: self.run_state(run_button, script, connect=True))

        return run_button

    def edit_button(self, script):
        "Profile card edit button"
        edit_button = QPushButton(" Edit")
        edit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        edit_button.setIcon(icons.get_icon(icons.edit))
        edit_button.setToolTip(f'Adjust "{os.path.splitext(script)[0]}"')
        edit_button.clicked.connect(lambda: self.handle_edit(script))
        edit_button.setStyleSheet(style.WIN11_BUTTON)

        return edit_button

    def startup_button(self, script):
        "Profile card startup button"
        startup_button = QPushButton(" Startup")
        startup_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if self.is_startup(script):
            startup_button.setIcon(icons.get_icon(icons.rocket_fill))
            startup_button.setToolTip(
                (
                f'Remove from startup: Dont run"{os.path.splitext(script)[0]}" '
                'automatically when computer starts'
                )
            )
            startup_button.clicked.connect(
                lambda: self.dashboard_core.remove_ahk_from_startup(script))
        else:
            startup_button.setIcon(icons.get_icon(icons.rocket))
            startup_button.setToolTip(
                (
                f'Add to startup: Run "{os.path.splitext(script)[0]}" '
                'automatically when computer starts'
                )
            )
            startup_button.clicked.connect(lambda: self.dashboard_core.add_ahk_to_startup(script))

        return startup_button

    def copy_button(self, script):
        "Profile card copy button"
        copy_button = QPushButton(" Copy")
        copy_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        copy_button.setIcon(icons.get_icon(icons.copy))
        copy_button.setToolTip(f'Copy "{os.path.splitext(script)[0]}"')
        copy_button.clicked.connect(lambda: self.dashboard_core.copy_script(script, self))

        return copy_button

    def delete_button(self, script):
        "Profile card delete button"
        delete_button = QPushButton(" Delete")
        delete_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        delete_button.setIcon(icons.get_icon(icons.delete))
        delete_button.setToolTip(f'Remove "{os.path.splitext(script)[0]}"')
        delete_button.clicked.connect(lambda: self.dashboard_core.delete_script(script))

        return delete_button

    def store_button(self, script):
        "Profile card store button"
        store_button = QPushButton(" Store" if
                                    self.dashboard_core.script_dir == utils.active_dir
                                    else " Restore")
        store_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        store_button.setIcon(icons.get_icon(icons.store))
        if self.dashboard_core.script_dir == utils.active_dir:
            store_button.setToolTip(f'Hide "{os.path.splitext(script)[0]}"')
        else:
            store_button.setToolTip(f'Unhide "{os.path.splitext(script)[0]}"')
        store_button.clicked.connect(lambda: self.dashboard_core.store_script(script))

        return store_button

    def handle_edit(self, script):
        "Exit profile if editing and re activate after done"
        run_button = self.find_run_button(script)
        was_running = run_button.text() == " Exit"

        if was_running:
            self.dashboard_core.exit_script(script)

        # Pass script for editing script
        self.profile_ui.edit_script(script, self)

        if was_running:
            self.dashboard_core.activate_script(script)

    def is_startup(self, script):
        "Whether profile is set as startup or not"
        shortcut_name = os.path.splitext(script)[0] + ".lnk"
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, shortcut_name)
        is_startup = os.path.exists(shortcut_path)
        return is_startup

    def find_run_button(self, s):
        "Find run button since it get destroyed on update script list"
        for i in range(self.profile_layout.count()):
            group_box = self.profile_layout.itemAt(i).widget()

            if (isinstance(group_box, QGroupBox) and
                    group_box.title() == os.path.splitext(s)[0]):

                layout = group_box.layout()
                if layout:

                    btn = layout.itemAtPosition(0, 0)

                    if btn:
                        run_btn = btn.widget()
                        if isinstance(run_btn, QPushButton):
                            return run_btn
        return None

    def toggle_on_top(self, always_top):
        "Toggle window always on top"
        is_on_top = bool(self.windowFlags() &
                            Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, not is_on_top)
        self.show()
        on_top_text = (f"KeyTik{' (Always on Top)' if not is_on_top else ''}")
        self.setWindowTitle(on_top_text)
        if not is_on_top:
            always_top.setToolTip("Disable Window Always on Top")
            always_top.setIcon(icons.get_icon(icons.on_top_fill))
        else:
            always_top.setToolTip("Enable  Window Always on Top")
            always_top.setIcon(icons.get_icon(icons.on_top))
