"""Login and registration window."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database.db import Database


class LoginWindow(QWidget):
    login_success = pyqtSignal(int, str)

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.setWindowTitle("Expense Tracker - Login")
        self.setMinimumWidth(360)
        self._build_ui()

    def _build_ui(self) -> None:
        title = QLabel("Expense Tracker")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        form = QFormLayout()
        form.addRow("Username:", self.username_input)
        form.addRow("Password:", self.password_input)

        self.login_btn = QPushButton("Login")
        self.register_btn = QPushButton("Register")
        self.login_btn.clicked.connect(self._on_login)
        self.register_btn.clicked.connect(self._on_register)

        buttons = QHBoxLayout()
        buttons.addWidget(self.login_btn)
        buttons.addWidget(self.register_btn)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addLayout(buttons)
        self.setLayout(layout)

    def _on_login(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Validation", "Please enter username and password.")
            return

        user_id = self.db.login_user(username, password)
        if user_id is None:
            QMessageBox.warning(self, "Login failed", "Invalid username or password.")
            return

        self.login_success.emit(user_id, username)

    def _on_register(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Validation", "Please enter username and password.")
            return

        ok, message = self.db.register_user(username, password)
        if not ok:
            QMessageBox.warning(self, "Registration failed", message)
            return

        QMessageBox.information(self, "Success", message + " You can log in now.")
