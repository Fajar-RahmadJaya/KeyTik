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

"""Thread handler."""

import os
from datetime import date

import keyboard
from PySide6.QtCore import QThread, Signal  # pylint: disable=E0611

from keytik.dashboard.dashboard_core import DashboardCore
from keytik.profile_manager.write_script import WriteScript
from keytik.utility import diff
from keytik.utility.utils import Config, Data, Utility


class Thread(QThread):  # pylint: disable=R0903
    """Startup thread worker."""

    update_found = Signal(str, str)
    show_announcement = Signal()
    ahk_not_installed = Signal()

    def run(self):
        """Run check update on thread to increase dashborad initialization time."""
        # Composition
        write_script = WriteScript()
        dashboard_core = DashboardCore()

        # Make sure all exit keys on script valid
        write_script.initialize_exit_keys()

        # Check for update
        data = Data().get_data()
        config = Config().get_config()
        latest_version = data.latest_version
        changelog_md = data.changelog

        current_date = str(date.today())

        # Check update only once a day
        if current_date != data.latest_update_check or not latest_version or not changelog_md:
            latest_version, changelog_md = diff.get_update_data()

            # Add to data
            data.latest_update_check = current_date
            data.latest_version = latest_version
            data.changelog = changelog_md
            Data().update_data(data)

        utility = Utility()
        if latest_version not in (utility.current_version, config.skip_update):
            self.update_found.emit(latest_version, changelog_md)

        # Check whether AutoHotkey is installed
        if not os.path.exists(utility.ahkv2_dir):
            self.ahk_not_installed.emit()

        # Whether to show announcement or not
        if Config().get_config().show_announcement:
            self.show_announcement.emit()

        # Check AHI necessary file
        dashboard_core.check_ahi_dir()

        # Initialize keyboard hook thread once
        def _dummy(_):
            pass

        dummy_hook = keyboard.hook(_dummy)
        keyboard.unhook(dummy_hook)
