from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from src.network.nt_client import RobotSnapshot


class StatusCard(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("valueCard")

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        self.value_label = QLabel("--")
        self.value_label.setObjectName("cardValue")

        layout = QVBoxLayout(self)
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)


class VisionPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        heading = QLabel("VISION")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        cards = QGridLayout()
        self.align = StatusCard("AUTO ALIGN")
        self.target = StatusCard("TARGET")
        self.yaw = StatusCard("TARGET YAW")
        cards.addWidget(self.align, 0, 0)
        cards.addWidget(self.target, 0, 1)
        cards.addWidget(self.yaw, 0, 2)
        layout.addLayout(cards)

        note = QLabel(
            "Tag ID / field coordinates are not published by the robot yet. "
            "Those will be added when remembered-AprilTag alignment is implemented."
        )
        note.setObjectName("mutedLabel")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

    def update_snapshot(self, snapshot: RobotSnapshot) -> None:
        self.align.value_label.setText("ON" if snapshot.vision_align_enabled else "OFF")
        self.target.value_label.setText("VISIBLE" if snapshot.vision_target_visible else "NONE")
        self.yaw.value_label.setText(f"{snapshot.vision_target_yaw_deg:.1f} deg")
