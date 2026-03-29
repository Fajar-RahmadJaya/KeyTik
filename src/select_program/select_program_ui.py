from PySide6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QTreeWidget,
    QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
import utility.constant as constant

from select_program.select_program_core import SelectProgramCore


class SelectProgramUI(SelectProgramCore):
    def program_window(self, entry_widget):
        self.select_program_window = None

        if (self.select_program_window
                and self.select_program_window.isVisible()):
            self.select_program_window.raise_()
            return

        if (hasattr(self, 'edit_window')
                and self.edit_window
                and self.edit_window.isVisible()):
            parent_window = self.edit_window
        else:
            parent_window = self

        self.select_program_window = QDialog(parent_window)
        self.select_program_window.setWindowTitle("Select Programs")
        self.select_program_window.setWindowIcon(QIcon(constant.icon_path))
        self.select_program_window.setFixedSize(600, 300)
        self.select_program_window.setModal(True)
        self.select_program_window.setAttribute(
            Qt.WidgetAttribute.WA_DeleteOnClose)

        main_layout = QVBoxLayout(self.select_program_window)

        self.program_tree = QTreeWidget(self.select_program_window)
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
            if expanded_width < 120:
                expanded_width = 120
            self.program_tree.setColumnWidth(sort_col, expanded_width)

        self.fit_sorted_column = fit_sorted_column

        header.setSortIndicator(0, Qt.AscendingOrder)
        QTimer.singleShot(0, fit_sorted_column)
        header.sectionClicked.connect(lambda _: fit_sorted_column())

        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        save_button = QPushButton("Select", self.select_program_window)
        save_button.clicked.connect(
            lambda: self.save_selected_programs(entry_widget))
        button_layout.addWidget(save_button)

        search_layout = QHBoxLayout()
        button_layout.addLayout(search_layout)

        search_label = QLabel("Search:", self.select_program_window)
        search_layout.addWidget(search_label)

        search_entry = QLineEdit(self.select_program_window)
        search_layout.addWidget(search_entry)

        search_entry.textChanged.connect(self.search_programs)

        refresh_button = QPushButton("Refresh", self.select_program_window)
        refresh_button.clicked.connect(lambda: self.update_program_treeview(
            show_all_processes=self.show_all_button.text() == "Show App Only"
        ))
        search_layout.addWidget(refresh_button)

        self.show_all_button = QPushButton(
            "Show All Processes", self.select_program_window)
        self.show_all_button.clicked.connect(self.toggle_show_all_processes)
        search_layout.addWidget(self.show_all_button)

        self.update_program_treeview(show_all_processes=False)
        fit_sorted_column()

        self.select_program_window.exec()
