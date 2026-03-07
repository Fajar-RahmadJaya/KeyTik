import os
import winshell
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QFrame, QPushButton, QGroupBox, QLabel
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from PySide6.QtSvgWidgets import QSvgWidget

import utility.constant as constant
import utility.utils as utils
import utility.icon as icons
import utility.diff as diff

from component.main_logic import MainLogic
from component.write_script import WriteScript
from component.parse_script import ParseScript

from ui.setting_ui import SettingUI
from ui.announcement import Announcement

from edit_profile.edit_profile_main import EditProfileMain


class MainUI(QMainWindow, MainLogic, EditProfileMain,
             SettingUI, Announcement, WriteScript, ParseScript):
    def __init__(self):
        super().__init__()
        # Key Listening
        self.is_listening = False
        self.active_entry = None
        self.pressed_keys = []
        # Variable
        self.row_num = 0

        # UI initialization
        self.check_ahk_installation(show_installed_message=False)
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.current_page = 0
        self.SCRIPT_DIR = utils.active_dir
        self.pinned_profiles = utils.load_pinned_profiles()
        self.scripts = self.list_scripts()
        self.create_ui()
        self.update_script_list()
        self.setWindowTitle(diff.program_name)
        self.setFixedSize(650, 492)
        self.setWindowIcon(QIcon(constant.icon_path))
        self.setCentralWidget(self.central_widget)
        self.announcement_condition = self.load_announcement_condition()
        self.font_fallback()
        self.check_ahi_dir()

    def create_ui(self):
        self.frame = QFrame()
        self.main_layout.addWidget(self.frame)
        self.frame_layout = QVBoxLayout(self.frame)

        self.profile_frame = QFrame()
        self.profile_layout = QGridLayout(self.profile_frame)
        self.profile_layout.setContentsMargins(0, 0, 0, 10)
        self.profile_frame.setFixedHeight(400)
        self.profile_layout.setHorizontalSpacing(15)
        self.profile_layout.setVerticalSpacing(10)
        self.frame_layout.addWidget(self.profile_frame)

        button_frame = QFrame()
        button_layout = QGridLayout(button_frame)
        button_layout.setContentsMargins(40, 20, 40, 10)

        self.prev_button = QPushButton()
        self.prev_button.setFixedWidth(80)
        self.prev_button.setIcon(icons.get_icon(icons.prev))
        self.prev_button.setToolTip("Previous Profile")
        self.prev_button.clicked.connect(self.prev_page)
        button_layout.addWidget(self.prev_button, 0, 0)

        self.show_stored = QPushButton()
        self.show_stored.setFixedWidth(30)
        self.show_stored.setIcon(icons.get_icon(icons.show_stored))
        self.show_stored.setToolTip("Show Stored Profile")
        self.show_stored.clicked.connect(self.toggle_script_dir)
        button_layout.addWidget(self.show_stored, 0, 1)

        self.import_button = QPushButton()
        self.import_button.setFixedWidth(30)
        self.import_button.setIcon(icons.get_icon(icons.icon_import))
        self.import_button.setToolTip("Import AutoHotkey Script")
        self.import_button.clicked.connect(self.import_button_clicked)
        button_layout.addWidget(self.import_button, 0, 2)

        dummy_left = QLabel()
        dummy_left.setFixedWidth(10)
        button_layout.addWidget(dummy_left, 0, 3)

        self.create_button = QPushButton(" Create New Profile")
        self.create_button.setIcon(icons.get_icon(icons.plus))
        self.create_button.setFixedWidth(150)
        self.create_button.setFixedHeight(30)
        self.create_button.clicked.connect(lambda: self.edit_script(None))
        button_layout.addWidget(self.create_button, 0, 4)

        dummy_right = QLabel()
        dummy_right.setFixedWidth(10)
        button_layout.addWidget(dummy_right, 0, 5)

        self.always_top = QPushButton()
        self.always_top.setFixedWidth(30)
        self.always_top.setIcon(icons.get_icon(icons.on_top))
        self.always_top.setToolTip("Enable  Window Always on Top")
        self.always_top.clicked.connect(self.toggle_on_top)
        button_layout.addWidget(self.always_top, 0, 6)

        self.setting_button = QPushButton()
        self.setting_button.setFixedWidth(30)
        self.setting_button.setIcon(icons.get_icon(icons.setting))
        self.setting_button.setToolTip("Setting")
        self.setting_button.clicked.connect(self.open_settings_window)
        button_layout.addWidget(self.setting_button, 0, 7)

        self.next_button = QPushButton()
        self.next_button.setFixedWidth(80)
        self.next_button.setIcon(icons.get_icon(icons.next))
        self.next_button.setToolTip("Next Profile")
        self.next_button.clicked.connect(self.next_page)
        button_layout.addWidget(self.next_button, 0, 8)

        self.frame_layout.addWidget(button_frame)

    def update_script_list(self):
        for i in reversed(range(self.profile_layout.count())):
            widget = self.profile_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        start_index = self.current_page * 6
        end_index = start_index + 6
        scripts_to_display = self.scripts[start_index:end_index]

        running_scripts = utils.read_running_scripts_temp()

        for index, script in enumerate(scripts_to_display):
            row = index // 2
            column = index % 2
            icon = (icons.pin_fill
                    if script in self.pinned_profiles
                    else icons.pin)

            self.profile_card(script, icon, running_scripts, row, column)

        self.profile_layout.setColumnStretch(0, 1)
        self.profile_layout.setColumnStretch(1, 1)
        self.profile_layout.setRowStretch(0, 1)
        self.profile_layout.setRowStretch(1, 1)
        self.profile_layout.setRowStretch(2, 1)

    def profile_card(self, script, icon, running_scripts, row, column):
        group_box = QGroupBox(os.path.splitext(script)[0])
        group_layout = QGridLayout(group_box)

        icon_label = QSvgWidget(icon, group_box)
        icon_label.setFixedSize(17, 17)
        icon_label.setToolTip(f'Pin "{os.path.splitext(script)[0]}"')
        icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
        icon_label.mousePressEvent = (lambda event, s=script,
                                      i=icon_label: self.toggle_pin(s, i))
        icon_label.move(285, 3)

        run_button = QPushButton()
        run_button.setFixedWidth(80)

        shortcut_name = os.path.splitext(script)[0] + ".lnk"
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, shortcut_name)
        is_startup = os.path.exists(shortcut_path)

        if is_startup or script in running_scripts:
            run_button.setText(" Exit")
            run_button.setToolTip(f'Stop "{os.path.splitext(script)[0]}"')
            run_button.setIcon(icons.get_icon(icons.exit))
        else:
            run_button.setText(" Run")
            run_button.setToolTip(f'Start "{os.path.splitext(script)[0]}"')
            run_button.setIcon(icons.get_icon(icons.run))
        run_button.clicked.connect(lambda checked, s=script, b=run_button:
                                   self.toggle_run_exit(s, b))
        group_layout.addWidget(run_button, 0, 0)

        edit_button = QPushButton(" Edit")
        edit_button.setIcon(icons.get_icon(icons.edit))
        edit_button.setFixedWidth(80)
        edit_button.setToolTip(f'Adjust "{os.path.splitext(script)[0]}"')

        def handle_edit(checked=False, s=script, rb=run_button):
            was_running = rb.text() == " Exit"
            if was_running:
                self.exit_script(s, rb)
            self.edit_script(s)
            if was_running:
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
                                    self.activate_script(s, run_btn)
                                    break

        edit_button.clicked.connect(handle_edit)
        group_layout.addWidget(edit_button, 0, 1)

        copy_button = QPushButton(" Copy")
        copy_button.setFixedWidth(80)
        copy_button.setIcon(icons.get_icon(icons.copy))
        copy_button.setToolTip(f'Copy "{os.path.splitext(script)[0]}"')
        copy_button.clicked.connect(lambda checked,
                                    s=script: self.copy_script(s))
        group_layout.addWidget(copy_button, 1, 0)

        delete_button = QPushButton(" Delete")
        delete_button.setFixedWidth(80)
        delete_button.setIcon(icons.get_icon(icons.delete))
        delete_button.setToolTip(f'Remove "{os.path.splitext(script)[0]}"')
        delete_button.clicked.connect(lambda checked,
                                      s=script: self.delete_script(s))
        group_layout.addWidget(delete_button, 1, 2)

        store_button = QPushButton(" Store" if
                                   self.SCRIPT_DIR == utils.active_dir
                                   else " Restore")
        store_button.setFixedWidth(80)
        store_button.setIcon(icons.get_icon(icons.store))

        if self.SCRIPT_DIR == utils.active_dir:
            store_button.setToolTip(f'Hide "{os.path.splitext(script)[0]}"') # noqa
        else:
            store_button.setToolTip(f'Unhide "{os.path.splitext(script)[0]}"') # noqa

        store_button.clicked.connect(lambda checked,
                                     s=script: self.store_script(s))
        group_layout.addWidget(store_button, 1, 1)

        if is_startup:
            startup_button = QPushButton(" Unstartup")
            startup_button.setIcon(icons.get_icon(icons.rocket_fill))
            startup_button.setToolTip(
                f'Remove from startup: Dont run"{os.path.splitext(script)[0]}" automatically when computer starts') # noqa
            startup_button.clicked.connect(lambda checked, s=script:
                                           self.remove_ahk_from_startup(s))
        else:
            startup_button = QPushButton(" Startup")
            startup_button.setIcon(icons.get_icon(icons.rocket))
            startup_button.setToolTip(
                f'Add to startup: Run "{os.path.splitext(script)[0]}" automatically when computer starts') # noqa
            startup_button.clicked.connect(lambda checked, s=script:
                                           self.add_ahk_to_startup(s))
        startup_button.setFixedWidth(80)
        group_layout.addWidget(startup_button, 0, 2)

        self.profile_layout.addWidget(group_box, row, column)

    def show_announcement_window(self):
        try:
            Announcement.show_announcement_window(self)
        except Exception as e:
            print(f"Error displaying announcement window: {e}")
