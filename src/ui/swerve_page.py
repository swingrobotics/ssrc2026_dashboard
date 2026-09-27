from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from src.network.nt_client import RobotSnapshot


class ModuleCard(QFrame):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.setObjectName("valueCard")

        title = QLabel(name)
        title.setObjectName("cardTitle")
        status = QLabel("TELEMETRY\nPENDING")
        status.setObjectName("modulePending")

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(status)


class SwervePage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        heading = QLabel("SWERVE")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        self.mode_label = QLabel("Drive mode: --")
        self.mode_label.setObjectName("summaryLabel")
        layout.addWidget(self.mode_label)

        grid = QGridLayout()
        grid.addWidget(ModuleCard("FRONT LEFT"), 0, 0)
        grid.addWidget(ModuleCard("FRONT RIGHT"), 0, 1)
        grid.addWidget(ModuleCard("REAR LEFT"), 1, 0)
        grid.addWidget(ModuleCard("REAR RIGHT"), 1, 1)
        layout.addLayout(grid)

        note = QLabel(
            "The current robot program does not publish individual module angle/speed topics yet. "
            "This page is ready for those values once robot telemetry is added."
        )
        note.setObjectName("mutedLabel")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

    def update_snapshot(self, snapshot: RobotSnapshot) -> None:
        mode = "FIELD RELATIVE" if snapshot.field_relative_enabled else "ROBOT RELATIVE"
        self.mode_label.setText(f"Drive mode: {mode}")
