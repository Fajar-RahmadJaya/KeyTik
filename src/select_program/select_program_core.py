"Logic for program selection"

import os
import ctypes
from ctypes import wintypes
import win32gui
import win32process
import psutil
from PySide6.QtWidgets import (QTreeWidgetItem)  # pylint: disable=E0611
from PySide6.QtCore import Qt  # pylint: disable=E0611


class SelectProgramCore():
    "Select program Non UI"
    def multi_check(self, texts):
        "Get multiple item from selected/checked checkbox"
        item = QTreeWidgetItem(texts)

        for col in range(3):
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(col, Qt.Unchecked)
        return item

    def get_application_type(self):
        "Check whether the process is a application or not"
        dwmwa_cloaked = 14
        ws_ex_toolwindow = 0x00000080
        ws_ex_appwindow = 0x00040000

        def is_window_cloaked(hwnd):
            try:
                dwmapi = ctypes.WinDLL("dwmapi")
                cloaked = wintypes.DWORD()
                dwmapi.DwmGetWindowAttribute(
                    wintypes.HWND(hwnd),
                    wintypes.DWORD(dwmwa_cloaked),
                    ctypes.byref(cloaked),
                    ctypes.sizeof(cloaked)
                )
                return cloaked.value != 0
            except (AttributeError, OSError, ValueError):
                return False

        pid_name_map = {}
        for proc in psutil.process_iter(['pid', 'name']):
            pid_name_map[proc.info['pid']] = proc.info['name']

        windows = []
        seen = set()

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):  # pylint: disable=I1101
                return
            if win32gui.GetWindowText(hwnd) == "":  # pylint: disable=I1101
                return
            exstyle = win32gui.GetWindowLong(hwnd, -20)  # pylint: disable=I1101
            if exstyle & ws_ex_toolwindow:
                return
            if (not (exstyle & ws_ex_appwindow)
                    and win32gui.GetWindow(hwnd, 4) != 0):  # pylint: disable=I1101
                return
            if win32gui.GetParent(hwnd) != 0:  # pylint: disable=I1101
                return
            if is_window_cloaked(hwnd):
                return
            title = win32gui.GetWindowText(hwnd)  # pylint: disable=I1101
            class_name = win32gui.GetClassName(hwnd) # pylint: disable=I1101
            _, pid = win32process.GetWindowThreadProcessId(hwnd)  # pylint: disable=I1101
            key = (pid, title, class_name)
            if key not in seen:
                seen.add(key)
                proc_name = pid_name_map.get(pid, "")
                windows.append((title, class_name, proc_name, "Application"))
        win32gui.EnumWindows(callback, None)  # pylint: disable=I1101
        return windows

    def get_running_processes(self, app_only=True):
        "Get running process"
        if app_only:
            return self.get_application_type()

        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'status']):
            try:
                if (proc.info['name'].lower() in
                    ["system", "system idle process",
                        "svchost.exe", "taskhostw.exe",
                        "explorer.exe"]):
                    continue
                pid = proc.info['pid']
                exe_name = proc.info['exe'] if 'exe' in proc.info else None
                exe_name = (os.path.basename(exe_name)
                            if exe_name
                            else proc.info['name'])
                process_type = ("Application"
                                if self.is_visible_application(pid)
                                else "System")
                try:
                    def window_callback(hwnd, windows, pid=pid):
                        _, process_pid = (
                            win32process.GetWindowThreadProcessId(hwnd))  # pylint: disable=I1101
                        if (process_pid == pid
                                and win32gui.IsWindowVisible(hwnd)):  # pylint: disable=I1101
                            windows.append(
                                (win32gui.GetClassName(hwnd),  # pylint: disable=I1101
                                    win32gui.GetWindowText(hwnd)))  # pylint: disable=I1101
                    windows = []
                    win32gui.EnumWindows(window_callback, windows)  # pylint: disable=I1101
                    if windows:
                        class_name, window_title = windows[0]
                    else:
                        class_name, window_title = "Unknown", "Unknown"
                except IndexError:
                    class_name, window_title = "Unknown", "Unknown"
                processes.append(
                    (window_title, class_name,
                        exe_name, process_type))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def is_visible_application(self, pid):
        "Check whether the process is an application by checking whether it has window or not"
        try:
            def callback(hwnd, pid_list):
                _, process_pid = win32process.GetWindowThreadProcessId(hwnd)  # pylint: disable=I1101
                if process_pid == pid and win32gui.IsWindowVisible(hwnd):  # pylint: disable=I1101
                    pid_list.append(pid)

            visible_pids = []
            win32gui.EnumWindows(callback, visible_pids)  # pylint: disable=I1101
            return len(visible_pids) > 0
        except win32gui.error: # pylint: disable=I1101
            return False
