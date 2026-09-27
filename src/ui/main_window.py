from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.network.nt_client import NTClient, RobotSnapshot
from src.ui.auto_page import AutoPage
from src.ui.camera_page import CameraPage
from src.ui.field_page import FieldPage
from src.ui.home_page import HomePage
from src.ui.swerve_page import SwervePage
from src.ui.vision_page import VisionPage


class MainWindow(QMainWindow):
    def __init__(self, nt_client: NTClient) -> None:
        super().__init__()
        self.nt_client = nt_client

        self.setWindowTitle("SSRC Dashboard")
        self.resize(1180, 720)
        self.setMinimumSize(940, 600)

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)

        header = QHBoxLayout()
        title = QLabel("SSRC DASHBOARD")
        title.setObjectName("appTitle")
        self.connection_label = QLabel("ROBOT DISCONNECTED")
        self.connection_label.setObjectName("statusLabel")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.connection_label)
        root_layout.addLayout(header)

        body = QHBoxLayout()
        root_layout.addLayout(body, 1)

        sidebar = QVBoxLayout()
        sidebar.setSpacing(8)
        body.addLayout(sidebar)

        self.stack = QStackedWidget()
        body.addWidget(self.stack, 1)

        self.home_page = HomePage()
        self.field_page = FieldPage()
        self.auto_page = AutoPage()
        self.swerve_page = SwervePage()
        self.vision_page = VisionPage()
        self.camera_page = CameraPage()

        self.pages = [
            ("HOME", self.home_page),
            ("FIELD", self.field_page),
            ("AUTO / PATH", self.auto_page),
            ("SWERVE", self.swerve_page),
            ("VISION", self.vision_page),
            ("CAMERA", self.camera_page),
        ]

        self.nav_buttons = []
        for index, (name, page) in enumerate(self.pages):
            button = QPushButton(name)
            button.setCheckable(True)
            button.setObjectName("navButton")
            button.clicked.connect(lambda checked=False, i=index: self.select_page(i))
            sidebar.addWidget(button)
            self.nav_buttons.append(button)
            self.stack.addWidget(page)

        sidebar.addStretch()
        self.select_page(0)

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
            #pageTitle {
                font-size: 22px;
                font-weight: 700;
                margin-bottom: 8px;
            }
            #statusLabel {
                font-size: 14px;
                font-weight: 700;
                padding: 8px 12px;
                border: 1px solid #4b5563;
                border-radius: 6px;
            }
            #navButton {
                min-width: 112px;
                min-height: 44px;
                text-align: left;
                padding-left: 14px;
                border: 1px solid #343a46;
                border-radius: 7px;
                background: #171a21;
                font-weight: 700;
            }
            #navButton:checked {
                background: #2b3240;
                border: 1px solid #697386;
            }
            #valueCard {
                background: #1b1f27;
                border: 1px solid #343a46;
                border-radius: 10px;
                padding: 12px;
                min-height: 130px;
            }
            #cardTitle {
                color: #aeb6c4;
                font-size: 14px;
                font-weight: 600;
            }
            #cardValue {
                font-size: 32px;
                font-weight: 700;
            }
            #summaryLabel {
                font-size: 15px;
                font-weight: 600;
                padding: 8px 2px;
            }
            #mutedLabel {
                color: #aeb6c4;
                font-size: 13px;
            }
            #modulePending {
                color: #aeb6c4;
                font-size: 22px;
                font-weight: 700;
            }
            #cameraView {
                background: #08090c;
                border: 1px solid #343a46;
                border-radius: 8px;
                color: #8b95a5;
                font-size: 16px;
            }
            QLineEdit {
                min-height: 34px;
                border: 1px solid #343a46;
                border-radius: 6px;
                padding: 0 10px;
                background: #171a21;
                color: #f3f4f6;
            }
            QPushButton {
                min-height: 34px;
                padding: 0 10px;
                border: 1px solid #343a46;
                border-radius: 6px;
                background: #20242d;
                color: #f3f4f6;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #2a303b;
            }
            """
        )

        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def select_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)

        # Camera streaming is deliberately enabled only while the camera page is visible.
        # This reduces network/CPU load and prevents unnecessary video latency elsewhere.
        self.camera_page.set_active(self.stack.currentWidget() is self.camera_page)

    def refresh(self) -> None:
        snapshot = self.nt_client.snapshot()
        self._update_connection(snapshot)

        self.home_page.update_snapshot(snapshot)
        self.field_page.update_snapshot(snapshot)
        self.auto_page.update_snapshot(snapshot)
        self.swerve_page.update_snapshot(snapshot)
        self.vision_page.update_snapshot(snapshot)

    def _update_connection(self, snapshot: RobotSnapshot) -> None:
        self.connection_label.setText(
            "ROBOT CONNECTED" if snapshot.connected else "ROBOT DISCONNECTED"
        )

    def closeEvent(self, event) -> None:
        self.camera_page.shutdown()
        self.nt_client.close()
        super().closeEvent(event)
