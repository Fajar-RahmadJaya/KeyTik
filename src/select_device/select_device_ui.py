"UI for device selection"

import os
import time
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QDialog, QPushButton,
    QVBoxLayout, QHBoxLayout, QTreeWidget
)
from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtGui import QIcon  # pylint: disable=E0611
from utility import constant
from utility import utils

from select_device.select_device_core import SelectDeviceCore


class SelectDeviceUI(SelectDeviceCore):
    "Device selecition UI for device binding"
    def __init__(self):
        super().__init__()
        self.device_selection_window = None
        self.device_tree = None

    def open_device_selection(self):
        "Device selection window"
        # Make sure interception driver installed
        if not self.check_interception_driver():
            return
        self.device_selection_window = None

        # Make device selection window on top of root
        if (self.device_selection_window
                and self.device_selection_window.isVisible()):
            self.device_selection_window.raise_()
            return

        # Run device finder first
        os.startfile(utils.device_finder_path)
        time.sleep(1)

        self.device_selection_window = QDialog(self.edit_window)
        self.device_selection_window.setWindowTitle("Select Device")
        self.device_selection_window.setWindowIcon(QIcon(constant.icon_path))
        self.device_selection_window.setFixedSize(600, 300)
        self.device_selection_window.setModal(True)
        self.device_selection_window.setAttribute(
            Qt.WidgetAttribute.WA_DeleteOnClose)

        main_layout = QVBoxLayout(self.device_selection_window)

        self.device_tree = QTreeWidget(self.device_selection_window)
        self.device_tree.setHeaderLabels(
            ["Device Type", "VID", "PID", "Handle"])
        main_layout.addWidget(self.device_tree)

        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        select_button = QPushButton("Select", self.device_selection_window)
        select_button.clicked.connect(
            lambda: self.select_device(
                self.device_tree,
                self.keyboard_entry,
                self.device_selection_window))
        button_layout.addWidget(select_button)

        monitor_button = QPushButton(
            "Open AHI Monitor To Test Device", self.device_selection_window)
        monitor_button.clicked.connect(self.run_monitor)
        button_layout.addWidget(monitor_button)

        refresh_button = QPushButton("Refresh", self.device_selection_window)
        refresh_button.clicked.connect(lambda: self.update_treeview(
                self.refresh_device_list(utils.device_list_path),
                self.device_tree))
        button_layout.addWidget(refresh_button)

        devices = self.refresh_device_list(utils.device_list_path)
        self.update_treeview(devices, self.device_tree)

        self.device_selection_window.exec()
