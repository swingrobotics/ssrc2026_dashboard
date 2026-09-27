import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.network.nt_client import RobotSnapshot


# PathPlanner's bundled 2026 REBUILT field image metadata:
# image 3508x1814 px, 200 px/m, 0.5 m image margin around the playable field.
FIELD_IMAGE_WIDTH_PX = 3508.0
FIELD_IMAGE_HEIGHT_PX = 1814.0
FIELD_PIXELS_PER_METER = 200.0
FIELD_IMAGE_MARGIN_M = 0.5
FIELD_LENGTH_M = FIELD_IMAGE_WIDTH_PX / FIELD_PIXELS_PER_METER - 2 * FIELD_IMAGE_MARGIN_M
FIELD_WIDTH_M = FIELD_IMAGE_HEIGHT_PX / FIELD_PIXELS_PER_METER - 2 * FIELD_IMAGE_MARGIN_M

ASSET_PATH = Path(__file__).resolve().parents[2] / "assets" / "field26.png"


class FieldCanvas(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(420)
        self._x = 0.0
        self._y = 0.0
        self._heading_deg = 0.0
        self._field_pixmap = QPixmap(str(ASSET_PATH))

    def set_pose(self, x_m: float, y_m: float, heading_deg: float) -> None:
        self._x = x_m
        self._y = y_m
        self._heading_deg = heading_deg
        self.update()

    def _image_rect(self) -> QRectF:
        margin = 12.0
        available_w = max(10.0, self.width() - 2 * margin)
        available_h = max(10.0, self.height() - 2 * margin)

        aspect = FIELD_IMAGE_WIDTH_PX / FIELD_IMAGE_HEIGHT_PX
        if available_w / available_h > aspect:
            draw_h = available_h
            draw_w = draw_h * aspect
        else:
            draw_w = available_w
            draw_h = draw_w / aspect

        left = (self.width() - draw_w) / 2.0
        top = (self.height() - draw_h) / 2.0
        return QRectF(left, top, draw_w, draw_h)

    def _field_rect(self, image_rect: QRectF) -> QRectF:
        scale = image_rect.width() / FIELD_IMAGE_WIDTH_PX
        margin_px = FIELD_IMAGE_MARGIN_M * FIELD_PIXELS_PER_METER * scale
        return QRectF(
            image_rect.left() + margin_px,
            image_rect.top() + margin_px,
            image_rect.width() - 2 * margin_px,
            image_rect.height() - 2 * margin_px,
        )

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QBrush(Qt.GlobalColor.black))

        image_rect = self._image_rect()

        if not self._field_pixmap.isNull():
            painter.drawPixmap(
                image_rect,
                self._field_pixmap,
                QRectF(self._field_pixmap.rect()),
            )
        else:
            painter.setPen(QPen(Qt.GlobalColor.gray, 1))
            painter.drawRect(image_rect)
            painter.drawText(
                image_rect,
                Qt.AlignmentFlag.AlignCenter,
                "2026 field image missing",
            )

        field_rect = self._field_rect(image_rect)

        # WPILib field coordinates: +X runs from the blue end toward red,
        # +Y runs across the field. Clamp only for drawing so bad odometry
        # cannot place the marker outside the widget.
        clamped_x = min(max(self._x, 0.0), FIELD_LENGTH_M)
        clamped_y = min(max(self._y, 0.0), FIELD_WIDTH_M)

        px = field_rect.left() + field_rect.width() * clamped_x / FIELD_LENGTH_M
        py = field_rect.bottom() - field_rect.height() * clamped_y / FIELD_WIDTH_M

        angle = math.radians(-self._heading_deg)
        forward = QPointF(math.cos(angle), math.sin(angle))
        side = QPointF(-forward.y(), forward.x())

        # Small triangular robot marker. The point of the triangle is robot +X.
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

        painter.setBrush(QBrush(Qt.GlobalColor.transparent))
        painter.drawEllipse(QPointF(px, py), 5, 5)


class FieldPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        heading = QLabel("2026 REBUILT FIELD")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        note = QLabel(
            "Official-season field view using the 2026 REBUILT field asset bundled with PathPlanner. "
            "The white marker is the robot odometry pose."
        )
        note.setObjectName("mutedLabel")
        note.setWordWrap(True)
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
