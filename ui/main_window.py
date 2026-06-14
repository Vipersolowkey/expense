"""Main application window with transactions, dashboard, and export."""

import csv
from datetime import date

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.db import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    Database,
    Transaction,
)
from ui.chart_widget import ChartWidget


class MainWindow(QMainWindow):
    def __init__(self, db: Database, user_id: int, username: str) -> None:
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.username = username
        self.selected_id: int | None = None

        self.setWindowTitle(f"Expense Tracker - {username}")
        self.setMinimumSize(900, 700)
        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        summary_box = QGroupBox("Dashboard")
        summary_layout = QHBoxLayout(summary_box)
        self.balance_label = QLabel("Balance: 0.00")
        self.income_label = QLabel("Income (month): 0.00")
        self.expense_label = QLabel("Expense (month): 0.00")
        for label in (self.balance_label, self.income_label, self.expense_label):
            label.setStyleSheet("font-size: 14px; font-weight: bold;")
            summary_layout.addWidget(label)
        root.addWidget(summary_box)

        form_box = QGroupBox("Transaction")
        form = QFormLayout(form_box)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["income", "expense"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)

        self.category_combo = QComboBox()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search category, note, type, date...")
        self.search_input.textChanged.connect(self._on_search_changed)

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 999_999_999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix("$ ")

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Optional note")

        form.addRow("Type:", self.type_combo)
        form.addRow("Category:", self.category_combo)
        form.addRow("Amount:", self.amount_input)
        form.addRow("Date:", self.date_input)
        form.addRow("Note:", self.note_input)
        form.addRow("Search:", self.search_input)

        self.add_btn = QPushButton("Add")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.clear_btn = QPushButton("Clear Form")
        self.export_btn = QPushButton("Export CSV")

        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn.clicked.connect(self._on_edit)
        self.delete_btn.clicked.connect(self._on_delete)
        self.clear_btn.clicked.connect(self._clear_form)
        self.export_btn.clicked.connect(self._on_export)

        btn_row = QHBoxLayout()
        for btn in (
            self.add_btn,
            self.edit_btn,
            self.delete_btn,
            self.clear_btn,
            self.export_btn,
        ):
            btn_row.addWidget(btn)
        form.addRow(btn_row)

        root.addWidget(form_box)
        self._on_type_changed(self.type_combo.currentText())

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Type", "Category", "Amount", "Note"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        root.addWidget(self.table)

        chart_box = QGroupBox("Expense Chart (This Month)")
        chart_layout = QVBoxLayout(chart_box)
        self.chart = ChartWidget(self.db, self.user_id)
        chart_layout.addWidget(self.chart)
        root.addWidget(chart_box)

    def _on_type_changed(self, tx_type: str) -> None:
        self.category_combo.clear()
        categories = INCOME_CATEGORIES if tx_type == "income" else EXPENSE_CATEGORIES
        self.category_combo.addItems(categories)

    def _on_search_changed(self) -> None:
        self._load_table()

    def _on_row_selected(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        row_idx = rows[0].row()
        tx_id_item = self.table.item(row_idx, 0)
        if tx_id_item is None:
            return
        tx_id = tx_id_item.data(Qt.UserRole)
        if tx_id is None:
            return
        tx = self.db.get_transaction(int(tx_id), self.user_id)
        if tx is None:
            return
        self.selected_id = tx.id
        idx = self.type_combo.findText(tx.type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        cat_idx = self.category_combo.findText(tx.category)
        if cat_idx >= 0:
            self.category_combo.setCurrentIndex(cat_idx)
        self.amount_input.setValue(tx.amount)
        parts = tx.date.split("-")
        if len(parts) == 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            self.date_input.setDate(QDate(y, m, d))
        self.note_input.setText(tx.note)

    def _read_form(self) -> tuple[str, str, float, str, str]:
        tx_type = self.type_combo.currentText()
        category = self.category_combo.currentText()
        amount = float(self.amount_input.value())
        note = self.note_input.text()
        tx_date = self.date_input.date().toString("yyyy-MM-dd")
        return tx_type, category, amount, note, tx_date

    def _on_add(self) -> None:
        tx_type, category, amount, note, tx_date = self._read_form()
        ok, message = self.db.add_transaction(
            self.user_id, tx_type, category, amount, note, tx_date
        )
        if not ok:
            QMessageBox.warning(self, "Error", message)
            return
        self._clear_form()
        self.refresh_all()

    def _on_edit(self) -> None:
        if self.selected_id is None:
            QMessageBox.warning(self, "Edit", "Select a transaction to edit.")
            return
        tx_type, category, amount, note, tx_date = self._read_form()
        ok, message = self.db.update_transaction(
            self.selected_id,
            self.user_id,
            tx_type,
            category,
            amount,
            note,
            tx_date,
        )
        if not ok:
            QMessageBox.warning(self, "Error", message)
            return
        self._clear_form()
        self.refresh_all()

    def _on_delete(self) -> None:
        if self.selected_id is None:
            QMessageBox.warning(self, "Delete", "Select a transaction to delete.")
            return
        confirm = QMessageBox.question(
            self,
            "Confirm delete",
            "Delete this transaction?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        ok, message = self.db.delete_transaction(self.selected_id, self.user_id)
        if not ok:
            QMessageBox.warning(self, "Error", message)
            return
        self._clear_form()
        self.refresh_all()

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            f"transactions_{self.username}.csv",
            "CSV Files (*.csv)",
        )
        if not path:
            return
        transactions = self.db.get_transactions(self.user_id)
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "type", "category", "amount", "note", "date"])
                for tx in transactions:
                    writer.writerow(
                        [tx.id, tx.type, tx.category, tx.amount, tx.note, tx.date]
                    )
            QMessageBox.information(
                self, "Export", f"Exported {len(transactions)} transactions."
            )
        except OSError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))

    def _clear_form(self) -> None:
        self.selected_id = None
        self.type_combo.setCurrentIndex(0)
        self._on_type_changed(self.type_combo.currentText())
        self.amount_input.setValue(0.01)
        self.date_input.setDate(QDate.currentDate())
        self.note_input.clear()
        self.table.clearSelection()

    def _load_table(self) -> None:
        search = self.search_input.text()
        transactions = self.db.get_transactions(self.user_id, search=search)
        self.table.setRowCount(len(transactions))
        for row_idx, tx in enumerate(transactions):
            self._set_cell(row_idx, 0, tx.date, tx.id)
            self._set_cell(row_idx, 1, tx.type)
            self._set_cell(row_idx, 2, tx.category)
            self._set_cell(row_idx, 3, f"{tx.amount:.2f}")
            self._set_cell(row_idx, 4, tx.note)

    def _set_cell(self, row: int, col: int, text: str, tx_id: int | None = None) -> None:
        item = QTableWidgetItem(text)
        if col == 0 and tx_id is not None:
            item.setData(Qt.UserRole, tx_id)
        self.table.setItem(row, col, item)

    def _load_summary(self) -> None:
        today = date.today()
        summary = self.db.get_summary(self.user_id, today.year, today.month)
        self.balance_label.setText(f"Balance: ${summary.balance:.2f}")
        self.income_label.setText(f"Income (month): ${summary.monthly_income:.2f}")
        self.expense_label.setText(f"Expense (month): ${summary.monthly_expense:.2f}")

    def refresh_all(self) -> None:
        self._load_table()
        self._load_summary()
        self.chart.refresh()
