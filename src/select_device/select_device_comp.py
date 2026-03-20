import os
import time
from PySide6.QtWidgets import (
    QTreeWidgetItem)
import utility.utils as utils


class selectDeviceComponent():
    def select_device(self, tree, entry, window):
        selected_items = tree.selectedItems()
        if selected_items:
            device = [selected_items[0].text(i)
                      for i in range(tree.columnCount())]
            device_type = device[0]
            vid_pid = device[3]

            entry.setText(f"{device_type}, {vid_pid}")

            window.accept()

    def update_treeview(self, devices, tree):
        tree.clear()

        for device in devices:
            if (device.get('VID')
                    and device.get('PID')
                    and device.get('Handle')):

                device_type = ("Mouse"
                               if device['Is Mouse'] == "Yes"
                               else "Keyboard")
                item = QTreeWidgetItem(
                    [device_type, device['VID'],
                        device['PID'], device['Handle']])
                tree.addTopLevelItem(item)

    def refresh_device_list(self, file_path):
        os.startfile(utils.device_finder_path)
        time.sleep(1)
        devices = self.parse_device_info(file_path)
        return devices
