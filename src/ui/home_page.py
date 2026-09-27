from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from src.network.nt_client import RobotSnapshot


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


class HomePage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        heading = QLabel("HOME")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        cards = QGridLayout()
        self.pose_x = ValueCard("POSE X", "m")
        self.pose_y = ValueCard("POSE Y", "m")
        self.heading = ValueCard("HEADING", "deg")
        self.yaw = ValueCard("NAVX YAW", "deg")
        self.pitch = ValueCard("PITCH", "deg")
        self.roll = ValueCard("ROLL", "deg")

        cards.addWidget(self.pose_x, 0, 0)
        cards.addWidget(self.pose_y, 0, 1)
        cards.addWidget(self.heading, 0, 2)
        cards.addWidget(self.yaw, 1, 0)
        cards.addWidget(self.pitch, 1, 1)
        cards.addWidget(self.roll, 1, 2)
        layout.addLayout(cards)

        self.summary = QLabel("")
        self.summary.setObjectName("summaryLabel")
        layout.addWidget(self.summary)
        layout.addStretch()

    def update_snapshot(self, snapshot: RobotSnapshot) -> None:
        self.pose_x.set_number(snapshot.pose_x_m)
        self.pose_y.set_number(snapshot.pose_y_m)
        self.heading.set_number(snapshot.heading_deg, 1)
        self.yaw.set_number(snapshot.navx_yaw_deg, 1)
        self.pitch.set_number(snapshot.navx_pitch_deg, 1)
        self.roll.set_number(snapshot.navx_roll_deg, 1)

        navx = "OK" if snapshot.navx_connected and not snapshot.navx_calibrating else "CHECK"
        pathplanner = "READY" if snapshot.pathplanner_configured else "NOT READY"
        drive = "FIELD" if snapshot.field_relative_enabled else "ROBOT"
        self.summary.setText(
            f"navX2: {navx}    |    PathPlanner: {pathplanner}    |    Drive mode: {drive} RELATIVE"
        )
