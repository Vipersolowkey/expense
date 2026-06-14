"""Pie chart for monthly expense categories."""

from datetime import date

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from database.db import Database


class ChartWidget(QWidget):
    def __init__(self, db: Database, user_id: int) -> None:
        super().__init__()
        self.db = db
        self.user_id = user_id

        self.empty_label = QLabel("No expense data for this month.")
        self.empty_label.setAlignment(Qt.AlignCenter)

        self.figure = Figure(figsize=(5, 4), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.empty_label)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.refresh()

    def refresh(self) -> None:
        today = date.today()
        totals = self.db.get_category_totals(self.user_id, today.year, today.month)

        self.figure.clear()
        if not totals:
            self.empty_label.show()
            self.canvas.hide()
            self.canvas.draw()
            return

        self.empty_label.hide()
        self.canvas.show()

        ax = self.figure.add_subplot(111)
        labels = list(totals.keys())
        values = list(totals.values())
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.set_title(f"Expenses by Category ({today.strftime('%B %Y')})")
        self.canvas.draw()
