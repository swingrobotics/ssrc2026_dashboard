import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.network.nt_client import RobotSnapshot


FIELD_LENGTH_M = 17.5
FIELD_WIDTH_M = 8.1


class FieldCanvas(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(360)
        self._x = 0.0
        self._y = 0.0
        self._heading_deg = 0.0

    def set_pose(self, x_m: float, y_m: float, heading_deg: float) -> None:
        self._x = x_m
        self._y = y_m
        self._heading_deg = heading_deg
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        margin = 24.0
        field_rect = QRectF(
            margin,
            margin,
            max(10.0, self.width() - 2 * margin),
            max(10.0, self.height() - 2 * margin),
        )

        painter.setPen(QPen(Qt.GlobalColor.gray, 1))
        painter.setBrush(QBrush(Qt.GlobalColor.transparent))
        painter.drawRoundedRect(field_rect, 8, 8)

        # Simple meter grid for odometry visualization. This is not a season field image.
        painter.setPen(QPen(Qt.GlobalColor.darkGray, 1))
        for meter in range(1, int(FIELD_LENGTH_M)):
            x = field_rect.left() + field_rect.width() * meter / FIELD_LENGTH_M
            painter.drawLine(QPointF(x, field_rect.top()), QPointF(x, field_rect.bottom()))
        for meter in range(1, int(FIELD_WIDTH_M)):
            y = field_rect.bottom() - field_rect.height() * meter / FIELD_WIDTH_M
            painter.drawLine(QPointF(field_rect.left(), y), QPointF(field_rect.right(), y))

        clamped_x = min(max(self._x, 0.0), FIELD_LENGTH_M)
        clamped_y = min(max(self._y, 0.0), FIELD_WIDTH_M)
        px = field_rect.left() + field_rect.width() * clamped_x / FIELD_LENGTH_M
        py = field_rect.bottom() - field_rect.height() * clamped_y / FIELD_WIDTH_M

        angle = math.radians(-self._heading_deg)
        forward = QPointF(math.cos(angle), math.sin(angle))
        side = QPointF(-forward.y(), forward.x())

        nose = QPointF(px + forward.x() * 18, py + forward.y() * 18)
        back_left = QPointF(
            px - forward.x() * 12 + side.x() * 10,
            py - forward.y() * 12 + side.y() * 10,
        )
        back_right = QPointF(
            px - forward.x() * 12 - side.x() * 10,
            py - forward.y() * 12 - side.y() * 10,
        )

        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawPolygon(QPolygonF([nose, back_left, back_right]))


class FieldPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        heading = QLabel("FIELD / ODOMETRY")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        note = QLabel(
            "Current view uses odometry X/Y/heading. It is a coordinate view, not the official season field image."
        )
        note.setObjectName("mutedLabel")
        layout.addWidget(note)

        self.pose_label = QLabel("X: -- m    Y: -- m    Heading: -- deg")
        self.pose_label.setObjectName("summaryLabel")
        layout.addWidget(self.pose_label)

        self.canvas = FieldCanvas()
        layout.addWidget(self.canvas, 1)

    def update_snapshot(self, snapshot: RobotSnapshot) -> None:
        self.pose_label.setText(
            f"X: {snapshot.pose_x_m:.2f} m    Y: {snapshot.pose_y_m:.2f} m    "
            f"Heading: {snapshot.heading_deg:.1f} deg"
        )
        self.canvas.set_pose(snapshot.pose_x_m, snapshot.pose_y_m, snapshot.heading_deg)
