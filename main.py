"""Expense Tracker MVP - application entry point."""

import sys
from PyQt5.QtWidgets import QApplication 
from database.db import Database
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Expense Tracker")

    db = Database()
    db.init_db()

    login = LoginWindow(db)
    main_window: MainWindow | None = None

    def on_login(user_id: int, username: str) -> None:
        nonlocal main_window
        main_window = MainWindow(db, user_id, username)
        main_window.show()
        login.close()

    login.login_success.connect(on_login)
    login.show()

    exit_code = app.exec_()
    db.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
