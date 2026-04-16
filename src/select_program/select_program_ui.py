"UI for program selection"

from PySide6.QtWidgets import (  # pylint: disable=E0611
    QDialog, QLabel, QLineEdit, QPushButton, QTreeWidget,
    QVBoxLayout, QHBoxLayout)
from PySide6.QtCore import Qt, QTimer  # pylint: disable=E0611
from PySide6.QtGui import QIcon  # pylint: disable=E0611

from utility import constant
from select_program.select_program_core import SelectProgramCore


class SelectProgramUI():
    "Select program UI"
    def __init__(self, edit_window=None):
        # Parameter
        self.edit_window = edit_window

        # UI
        self.program_tree = None
        self.show_all_button = None
        self.fit_sorted_column = None

    def program_window(self, entry_widget, parent):
        "Select program window"
        select_program_window = None

        select_program_window = QDialog(parent)
        select_program_window.setWindowTitle("Select Programs")
        select_program_window.setWindowIcon(QIcon(constant.icon_path))
        select_program_window.setFixedSize(600, 300)
        select_program_window.setModal(True)
        select_program_window.setAttribute(
            Qt.WidgetAttribute.WA_DeleteOnClose)

        main_layout = QVBoxLayout(select_program_window)

        self.program_tree = QTreeWidget(select_program_window)
        self.program_tree.setHeaderLabels(["Window Title", "Class", "Process"])
        self.program_tree.setSortingEnabled(True)
        self.program_tree.setFixedWidth(580)
        main_layout.addWidget(self.program_tree)

        header = self.program_tree.header()

        for col in range(self.program_tree.columnCount()):
            self.program_tree.setColumnWidth(col, 120)

        def fit_sorted_column():
            sort_col = header.sortIndicatorSection()
            total_width = self.program_tree.viewport().width()
            other_cols = [i for i in range(self.program_tree.columnCount())
                          if i != sort_col]
            for col in other_cols:
                self.program_tree.setColumnWidth(col, 120)
            expanded_width = (total_width -
                              120 * len(other_cols))
            expanded_width = max(expanded_width, 120)

            self.program_tree.setColumnWidth(sort_col, expanded_width)

        self.fit_sorted_column = fit_sorted_column

        header.setSortIndicator(0, Qt.AscendingOrder)
        QTimer.singleShot(0, fit_sorted_column)
        header.sectionClicked.connect(lambda _: fit_sorted_column())

        self.program_window_button(main_layout, entry_widget, select_program_window)

        self.update_program_treeview(show_all_processes=False)
        self.fit_sorted_column()

        select_program_window.exec()

    def program_window_button(self, main_layout, entry_widget, select_program_window):
        "Button on program window"
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        save_button = QPushButton("Select", select_program_window)
        save_button.clicked.connect(
            lambda: self.save_selected_programs(entry_widget, select_program_window))
        button_layout.addWidget(save_button)

        search_layout = QHBoxLayout()
        button_layout.addLayout(search_layout)

        search_label = QLabel("Search:", select_program_window)
        search_layout.addWidget(search_label)

        search_entry = QLineEdit(select_program_window)
        search_layout.addWidget(search_entry)

        search_entry.textChanged.connect(self.search_programs)

        refresh_button = QPushButton("Refresh", select_program_window)
        refresh_button.clicked.connect(lambda: self.update_program_treeview(
            show_all_processes=self.show_all_button.text() == "Show App Only"
        ))
        search_layout.addWidget(refresh_button)

        self.show_all_button = QPushButton(
            "Show All Processes", select_program_window)
        self.show_all_button.clicked.connect(self.toggle_show_all_processes)
        search_layout.addWidget(self.show_all_button)

    def update_program_treeview(self, show_all_processes=None):
        "Populate process into treeview"
        select_program_core = SelectProgramCore()  # Composition

        if show_all_processes is None:
            show_all_processes = (
                self.show_all_button.text()) == "Show All Processes"
        self.program_tree.clear()

        processes = select_program_core.get_running_processes(app_only=not show_all_processes)
        for proc in processes:
            window_title, class_name, proc_name = proc[:3]
            p_type = proc[3] if len(proc) > 3 else "Application"
            if show_all_processes or p_type == "Application":
                item = select_program_core.multi_check([window_title, class_name, proc_name])
                self.program_tree.addTopLevelItem(item)

        if hasattr(self, "fit_sorted_column"):
            self.fit_sorted_column()

    def toggle_show_all_processes(self):
        "Update button and pupulate tree view on 'show all process' button click"
        current_text = self.show_all_button.text()
        if current_text == "Show All Processes":
            self.show_all_button.setText("Show App Only")
            self.update_program_treeview(show_all_processes=True)
        else:
            self.show_all_button.setText("Show All Processes")
            self.update_program_treeview(show_all_processes=False)

    def search_programs(self, query):
        "Search process on searchbox"
        for index in range(self.program_tree.topLevelItemCount()):
            item = self.program_tree.topLevelItem(index)
            item.setHidden(query.lower() not in item.text(0).lower())

    def save_selected_programs(self, entry_widget, select_program_window):
        "Append selected process onto"
        name_checked = []
        class_checked = []
        process_checked = []
        for index in range(self.program_tree.topLevelItemCount()):
            item = self.program_tree.topLevelItem(index)
            if item.checkState(0) == Qt.Checked:
                name_checked.append(f"[Tittle, {item.text(0)}]")
            if item.checkState(1) == Qt.Checked:
                class_checked.append(f"[Class, {item.text(1)}]")
            if item.checkState(2) == Qt.Checked:
                process_checked.append(f"[Process, {item.text(2)}]")
        selected_programs = name_checked + class_checked + process_checked

        if selected_programs:
            entry_widget.setText(" ".join(selected_programs))

        select_program_window.accept()
