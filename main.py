import sys

from PySide6.QtWidgets import QApplication

from src.network.nt_client import NTClient
from src.ui.main_window import MainWindow


TEAM_NUMBER = 10958


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("SSRC Dashboard")

    nt_client = NTClient(team_number=TEAM_NUMBER)
    window = MainWindow(nt_client)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
