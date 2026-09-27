from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from src.network.nt_client import NTClient, RobotSnapshot


class ValueCard(QFrame):
    def __init__(self, title: str, unit: str = "") -> None:
        super().__init__()
        self._unit = unit
        self.setObjectName("valueCard")

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")

        self.value_label = QLabel("--")
        self.value_label.setObjectName("cardValue")

        layout = QVBoxLayout(self)
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_number(self, value: float, decimals: int = 2) -> None:
        suffix = f" {self._unit}" if self._unit else ""
        self.value_label.setText(f"{value:.{decimals}f}{suffix}")


class MainWindow(QMainWindow):
    def __init__(self, nt_client: NTClient) -> None:
        super().__init__()
        self.nt_client = nt_client

        self.setWindowTitle("SSRC Dashboard")
        self.resize(900, 540)

        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)

        header = QHBoxLayout()
        title = QLabel("SSRC DASHBOARD")
        title.setObjectName("appTitle")
        self.connection_label = QLabel("ROBOT DISCONNECTED")
        self.connection_label.setObjectName("statusLabel")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.connection_label)
        main_layout.addLayout(header)

        status_layout = QHBoxLayout()
        self.navx_label = QLabel("navX2: --")
        self.calibration_label = QLabel("Calibration: --")
        self.drive_mode_label = QLabel("Drive: --")
        status_layout.addWidget(self.navx_label)
        status_layout.addWidget(self.calibration_label)
        status_layout.addWidget(self.drive_mode_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        cards = QGridLayout()
        self.pose_x_card = ValueCard("POSE X", "m")
        self.pose_y_card = ValueCard("POSE Y", "m")
        self.heading_card = ValueCard("HEADING", "deg")
        cards.addWidget(self.pose_x_card, 0, 0)
        cards.addWidget(self.pose_y_card, 0, 1)
        cards.addWidget(self.heading_card, 0, 2)
        main_layout.addLayout(cards)
        main_layout.addStretch()

        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #111318;
                color: #f3f4f6;
                font-family: "Segoe UI";
            }
            #appTitle {
                font-size: 28px;
                font-weight: 700;
            }
            #statusLabel {
                font-size: 15px;
                font-weight: 700;
                padding: 8px 12px;
                border: 1px solid #4b5563;
                border-radius: 6px;
            }
            #valueCard {
                background: #1b1f27;
                border: 1px solid #343a46;
                border-radius: 10px;
                padding: 12px;
                min-height: 150px;
            }
            #cardTitle {
                color: #aeb6c4;
                font-size: 14px;
                font-weight: 600;
            }
            #cardValue {
                font-size: 36px;
                font-weight: 700;
            }
            """
        )

        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self) -> None:
        snapshot = self.nt_client.snapshot()
        self._update_status(snapshot)

        self.pose_x_card.set_number(snapshot.pose_x_m)
        self.pose_y_card.set_number(snapshot.pose_y_m)
        self.heading_card.set_number(snapshot.heading_deg, decimals=1)

    def _update_status(self, snapshot: RobotSnapshot) -> None:
        self.connection_label.setText(
            "ROBOT CONNECTED" if snapshot.connected else "ROBOT DISCONNECTED"
        )
        self.navx_label.setText(
            "navX2: CONNECTED" if snapshot.navx_connected else "navX2: DISCONNECTED"
        )
        self.calibration_label.setText(
            "Calibration: RUNNING" if snapshot.navx_calibrating else "Calibration: READY"
        )
        self.drive_mode_label.setText(
            "Drive: FIELD RELATIVE"
            if snapshot.field_relative_enabled
            else "Drive: ROBOT RELATIVE"
        )

    def closeEvent(self, event) -> None:
        self.nt_client.close()
        super().closeEvent(event)
