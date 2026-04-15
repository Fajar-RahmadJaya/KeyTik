"Main Window"

import os
import winshell
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QFrame, QPushButton, QGroupBox, QLabel
)
from PySide6.QtGui import QIcon  # pylint: disable=E0611
from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtSvgWidgets import QSvgWidget  # pylint: disable=E0611

from utility import constant
from utility import utils
from utility import icons
from utility import diff
from core.main_core import MainCore
from script_profile.parse_script import ParseScript
from script_profile.profile_ui import ProfileUI
from setting.setting_ui import SettingUI


class Dashboard(QMainWindow):
    "Main Window"
    def __init__(self):
        super().__init__()
        # Composition
        self.main_core = MainCore()
        self.parse_script = ParseScript()
        self.profile_ui = ProfileUI(self.main_core)
        self.setting_ui = SettingUI()

        # Signal
        self.main_core.update_script_signal.connect(self.update_script_list)

        # Key Listening
        self.is_listening = False
        self.active_entry = None
        self.pressed_keys = []
        # Variable
        self.row_num = 0

        # UI initialization
        self.main_core.check_ahk_installation(show_installed_message=False)
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.script_dir = utils.active_dir
        self.pinned_profiles = utils.load_pinned_profiles()
        self.create_ui()
        self.update_script_list()
        self.setWindowTitle(diff.PROGRAM_NAME)
        self.setFixedSize(650, 492)
        self.setWindowIcon(QIcon(constant.icon_path))
        self.setCentralWidget(self.central_widget)
        self.main_core.font_fallback()
        self.main_core.check_ahi_dir()
        self.checked_keys_list = []

    def create_ui(self):
        "Dashboard Window"
        self.frame = QFrame()
        self.main_layout.addWidget(self.frame)
        self.frame_layout = QVBoxLayout(self.frame)

        self.profile_frame = QFrame()
        self.profile_frame.setFixedHeight(400)
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

    def dashboard_button(self):
        "Dashboard button widget"
        button_frame = QFrame()
        button_layout = QGridLayout(button_frame)
        button_layout.setContentsMargins(40, 20, 40, 10)

        prev_button = QPushButton()
        prev_button.setFixedWidth(80)
        prev_button.setIcon(icons.get_icon(icons.prev))
        prev_button.setToolTip("Previous Profile")
        prev_button.clicked.connect(self.main_core.prev_page)
        button_layout.addWidget(prev_button, 0, 0)

        show_stored = QPushButton()
        show_stored.setFixedWidth(30)
        show_stored.setIcon(icons.get_icon(icons.show_stored))
        show_stored.setToolTip("Show Stored Profile")
        show_stored.clicked.connect(lambda: self.main_core.toggle_script_dir(show_stored))
        button_layout.addWidget(show_stored, 0, 1)

        import_button = QPushButton()
        import_button.setFixedWidth(30)
        import_button.setIcon(icons.get_icon(icons.icon_import))
        import_button.setToolTip("Import AutoHotkey Script")
        import_button.clicked.connect(self.main_core.import_button_clicked)
        button_layout.addWidget(import_button, 0, 2)

        # Create new profile button
        self.create_new_button(button_layout)

        always_top = QPushButton()
        always_top.setFixedWidth(30)
        always_top.setIcon(icons.get_icon(icons.on_top))
        always_top.setToolTip("Enable  Window Always on Top")
        always_top.clicked.connect(lambda: self.toggle_on_top(always_top))
        button_layout.addWidget(always_top, 0, 6)

        setting_button = QPushButton()
        setting_button.setFixedWidth(30)
        setting_button.setIcon(icons.get_icon(icons.setting))
        setting_button.setToolTip("Setting")
        setting_button.clicked.connect(lambda: self.setting_ui.open_settings_window(self))
        button_layout.addWidget(setting_button, 0, 7)

        next_button = QPushButton()
        next_button.setFixedWidth(80)
        next_button.setIcon(icons.get_icon(icons.icon_next))
        next_button.setToolTip("Next Profile")
        next_button.clicked.connect(self.main_core.next_page)
        button_layout.addWidget(next_button, 0, 8)

        return button_frame

    def create_new_button(self, button_layout):
        "Crate new button with dummy label to give it more space"
        dummy_left = QLabel()
        dummy_left.setFixedWidth(10)
        button_layout.addWidget(dummy_left, 0, 3)

        create_button = QPushButton(" Create New Profile")
        create_button.setIcon(icons.get_icon(icons.plus))
        create_button.setFixedWidth(150)
        create_button.setFixedHeight(30)
        create_button.clicked.connect(lambda: self.profile_ui.edit_script(None, self))
        button_layout.addWidget(create_button, 0, 4)

        dummy_right = QLabel()
        dummy_right.setFixedWidth(10)
        button_layout.addWidget(dummy_right, 0, 5)

    def update_script_list(self):
        "! From dashboard"
        for i in reversed(range(self.profile_layout.count())):
            widget = self.profile_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        start_index = self.main_core.current_page * 6
        end_index = start_index + 6
        scripts = self.main_core.list_scripts()
        scripts_to_display = scripts[start_index:end_index]

        for index, script in enumerate(scripts_to_display):
            row = index // 2
            column = index % 2

            self.profile_card(script, row, column)

    def profile_card(self, script, row, column):
        "Profile action"
        group_box = QGroupBox(os.path.splitext(script)[0])
        group_layout = QGridLayout(group_box)

        # Pin icon
        self.pin_icon(script, group_box)

        # Run/exit button
        run_button = QPushButton()
        run_button.setFixedWidth(80)
        running_scripts = utils.read_running_scripts_temp()
        if self.is_startup(script) or script in running_scripts:
            run_button.setText(" Exit")
            run_button.setToolTip(f'Stop "{os.path.splitext(script)[0]}"')
            run_button.setIcon(icons.get_icon(icons.icon_exit))
        else:
            run_button.setText(" Run")
            run_button.setToolTip(f'Start "{os.path.splitext(script)[0]}"')
            run_button.setIcon(icons.get_icon(icons.run))
        run_button.clicked.connect(lambda: self.main_core.toggle_run_exit(script, run_button))
        group_layout.addWidget(run_button, 0, 0)

        # Edit profile button
        edit_button = QPushButton(" Edit")
        edit_button.setIcon(icons.get_icon(icons.edit))
        edit_button.setFixedWidth(80)
        edit_button.setToolTip(f'Adjust "{os.path.splitext(script)[0]}"')
        edit_button.clicked.connect(lambda: self.handle_edit(script, run_button))
        group_layout.addWidget(edit_button, 0, 1)

        # Copy button
        copy_button = QPushButton(" Copy")
        copy_button.setFixedWidth(80)
        copy_button.setIcon(icons.get_icon(icons.copy))
        copy_button.setToolTip(f'Copy "{os.path.splitext(script)[0]}"')
        copy_button.clicked.connect(lambda: self.main_core.copy_script(script))
        group_layout.addWidget(copy_button, 1, 0)

        # Delete button
        delete_button = QPushButton(" Delete")
        delete_button.setFixedWidth(80)
        delete_button.setIcon(icons.get_icon(icons.delete))
        delete_button.setToolTip(f'Remove "{os.path.splitext(script)[0]}"')
        delete_button.clicked.connect(lambda: self.main_core.delete_script(script))
        group_layout.addWidget(delete_button, 1, 2)

        # Store button
        store_button = QPushButton(" Store" if
                                   self.script_dir == utils.active_dir
                                   else " Restore")
        store_button.setFixedWidth(80)
        store_button.setIcon(icons.get_icon(icons.store))
        if self.script_dir == utils.active_dir:
            store_button.setToolTip(f'Hide "{os.path.splitext(script)[0]}"')
        else:
            store_button.setToolTip(f'Unhide "{os.path.splitext(script)[0]}"')
        store_button.clicked.connect(lambda: self.main_core.store_script(script))
        group_layout.addWidget(store_button, 1, 1)

        # Startup button
        startup_button = self.startup_button(script)
        group_layout.addWidget(startup_button, 0, 2)

        self.profile_layout.addWidget(group_box, row, column)

    def pin_icon(self, script, group_box):
        "Pin icon"
        if script in self.pinned_profiles:
            icon_label = QSvgWidget(icons.pin, group_box)
        else:
            icon_label = QSvgWidget(icons.pin_fill, group_box)

        icon_label.setFixedSize(17, 17)
        icon_label.setToolTip(f'Pin "{os.path.splitext(script)[0]}"')
        icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
        icon_label.mousePressEvent = lambda _: self.main_core.toggle_pin(script, icon_label)
        icon_label.move(285, 3)

    def startup_button(self, script):
        "Startup button"
        if self.is_startup(script):
            startup_button = QPushButton(" Unstartup")
            startup_button.setIcon(icons.get_icon(icons.rocket_fill))
            startup_button.setToolTip(
                (
                f'Remove from startup: Dont run"{os.path.splitext(script)[0]}" '
                'automatically when computer starts'
                )
            )
            startup_button.clicked.connect(lambda: self.main_core.remove_ahk_from_startup(script))
        else:
            startup_button = QPushButton(" Startup")
            startup_button.setIcon(icons.get_icon(icons.rocket))
            startup_button.setToolTip(
                (
                f'Add to startup: Run "{os.path.splitext(script)[0]}" '
                'automatically when computer starts'
                )
            )
            startup_button.clicked.connect(lambda: self.main_core.add_ahk_to_startup(script))
        startup_button.setFixedWidth(80)
        return startup_button

    def handle_edit(self, script, run_button):
        "Exit profile if editing and re activate after done"
        was_running = run_button.text() == " Exit"
        if was_running:
            self.main_core.exit_script(script, run_button)

        # Pass parameter for editing script
        self.profile_ui.edit_script(script, self)

        if was_running:
            run_btn = self.find_run_button(script)
            self.main_core.activate_script(script, run_btn)

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
