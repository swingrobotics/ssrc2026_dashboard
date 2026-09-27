import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from src.network.nt_client import RobotSnapshot
from src.ui.field_page import (
    ASSET_PATH,
    FIELD_IMAGE_HEIGHT_PX,
    FIELD_IMAGE_MARGIN_M,
    FIELD_IMAGE_WIDTH_PX,
    FIELD_LENGTH_M,
    FIELD_PIXELS_PER_METER,
    FIELD_WIDTH_M,
)


class InfoCard(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("valueCard")

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        self.value_label = QLabel("--")
        self.value_label.setObjectName("cardValue")
        self.value_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)


class AutoFieldCanvas(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(330)
        self._field_pixmap = QPixmap(str(ASSET_PATH))
        self._actual = (0.0, 0.0, 0.0)
        self._target = (0.0, 0.0, 0.0)
        self._target_valid = False
        self._path: list[tuple[float, float, float]] = []

    def update_data(
        self,
        actual: tuple[float, float, float],
        target: tuple[float, float, float],
        target_valid: bool,
        path: list[tuple[float, float, float]],
    ) -> None:
        self._actual = actual
        self._target = target
        self._target_valid = target_valid
        self._path = path
        self.update()

    def _image_rect(self) -> QRectF:
        margin = 10.0
        available_w = max(10.0, self.width() - 2 * margin)
        available_h = max(10.0, self.height() - 2 * margin)
        aspect = FIELD_IMAGE_WIDTH_PX / FIELD_IMAGE_HEIGHT_PX

        if available_w / available_h > aspect:
            draw_h = available_h
            draw_w = draw_h * aspect
        else:
            draw_w = available_w
            draw_h = draw_w / aspect

        return QRectF(
            (self.width() - draw_w) / 2.0,
            (self.height() - draw_h) / 2.0,
            draw_w,
            draw_h,
        )

    def _field_rect(self, image_rect: QRectF) -> QRectF:
        scale = image_rect.width() / FIELD_IMAGE_WIDTH_PX
        margin_px = FIELD_IMAGE_MARGIN_M * FIELD_PIXELS_PER_METER * scale
        return QRectF(
            image_rect.left() + margin_px,
            image_rect.top() + margin_px,
            image_rect.width() - 2 * margin_px,
            image_rect.height() - 2 * margin_px,
        )

    @staticmethod
    def _map_pose(field_rect: QRectF, x_m: float, y_m: float) -> QPointF:
        x_m = min(max(x_m, 0.0), FIELD_LENGTH_M)
        y_m = min(max(y_m, 0.0), FIELD_WIDTH_M)
        return QPointF(
            field_rect.left() + field_rect.width() * x_m / FIELD_LENGTH_M,
            field_rect.bottom() - field_rect.height() * y_m / FIELD_WIDTH_M,
        )

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QBrush(Qt.GlobalColor.black))

        image_rect = self._image_rect()
        if not self._field_pixmap.isNull():
            painter.drawPixmap(image_rect, self._field_pixmap, QRectF(self._field_pixmap.rect()))

        field_rect = self._field_rect(image_rect)

        if len(self._path) >= 2:
            points = QPolygonF(
                [self._map_pose(field_rect, x, y) for x, y, _ in self._path]
            )
            painter.setPen(QPen(Qt.GlobalColor.cyan, 3))
            painter.setBrush(QBrush(Qt.GlobalColor.transparent))
            painter.drawPolyline(points)

        actual_point = self._map_pose(field_rect, self._actual[0], self._actual[1])
        self._draw_robot(
            painter,
            actual_point,
            self._actual[2],
            Qt.GlobalColor.white,
        )

        if self._target_valid:
            target_point = self._map_pose(field_rect, self._target[0], self._target[1])
            painter.setPen(QPen(Qt.GlobalColor.yellow, 3))
            painter.setBrush(QBrush(Qt.GlobalColor.transparent))
            painter.drawEllipse(target_point, 10, 10)
            painter.drawLine(
                QPointF(target_point.x() - 14, target_point.y()),
                QPointF(target_point.x() + 14, target_point.y()),
            )
            painter.drawLine(
                QPointF(target_point.x(), target_point.y() - 14),
                QPointF(target_point.x(), target_point.y() + 14),
            )

    @staticmethod
    def _draw_robot(
        painter: QPainter,
        center: QPointF,
        heading_deg: float,
        color,
    ) -> None:
        angle = math.radians(-heading_deg)
        forward = QPointF(math.cos(angle), math.sin(angle))
        side = QPointF(-forward.y(), forward.x())

        nose = QPointF(
            center.x() + forward.x() * 16,
            center.y() + forward.y() * 16,
        )
        back_left = QPointF(
            center.x() - forward.x() * 11 + side.x() * 9,
            center.y() - forward.y() * 11 + side.y() * 9,
        )
        back_right = QPointF(
            center.x() - forward.x() * 11 - side.x() * 9,
            center.y() - forward.y() * 11 - side.y() * 9,
        )

        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        painter.drawPolygon(QPolygonF([nose, back_left, back_right]))


class AutoPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        heading = QLabel("AUTO / PATH")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        self.status_label = QLabel("PathPlanner: --")
        self.status_label.setObjectName("summaryLabel")
        layout.addWidget(self.status_label)

        cards = QGridLayout()
        self.auto_card = InfoCard("SELECTED AUTO")
        self.error_card = InfoCard("POSITION ERROR")
        self.heading_error_card = InfoCard("HEADING ERROR")
        self.speed_card = InfoCard("ROBOT SPEED")
        self.path_card = InfoCard("PATH POINTS")
        self.mode_card = InfoCard("AUTO MODE")

        cards.addWidget(self.auto_card, 0, 0)
        cards.addWidget(self.error_card, 0, 1)
        cards.addWidget(self.heading_error_card, 0, 2)
        cards.addWidget(self.speed_card, 1, 0)
        cards.addWidget(self.path_card, 1, 1)
        cards.addWidget(self.mode_card, 1, 2)
        layout.addLayout(cards)

        legend = QLabel(
            "White = actual robot pose    Yellow = PathPlanner target pose    Cyan = active path"
        )
        legend.setObjectName("mutedLabel")
        layout.addWidget(legend)

        self.canvas = AutoFieldCanvas()
        layout.addWidget(self.canvas, 1)

    @staticmethod
    def _parse_path(encoded: str) -> list[tuple[float, float, float]]:
        points: list[tuple[float, float, float]] = []
        if not encoded:
            return points

        for item in encoded.split(";"):
            parts = item.split(",")
            if len(parts) != 3:
                continue
            try:
                points.append((float(parts[0]), float(parts[1]), float(parts[2])))
            except ValueError:
                continue
        return points

    def update_snapshot(self, snapshot: RobotSnapshot) -> None:
        self.status_label.setText(
            "PathPlanner: CONFIGURED"
            if snapshot.pathplanner_configured
            else "PathPlanner: NOT CONFIGURED"
        )

        self.auto_card.value_label.setText(snapshot.selected_auto or "None")
        self.path_card.value_label.setText(str(snapshot.pathplanner_path_points))
        self.mode_card.value_label.setText(
            "RUNNING" if snapshot.autonomous_enabled else "NOT ACTIVE"
        )

        robot_speed = math.hypot(
            snapshot.robot_velocity_x_mps,
            snapshot.robot_velocity_y_mps,
        )
        self.speed_card.value_label.setText(f"{robot_speed:.2f} m/s")

        if snapshot.pathplanner_target_valid:
            position_error = math.hypot(
                snapshot.pathplanner_target_x_m - snapshot.pose_x_m,
                snapshot.pathplanner_target_y_m - snapshot.pose_y_m,
            )
            heading_error = (
                snapshot.pathplanner_target_heading_deg
                - snapshot.heading_deg
                + 180.0
            ) % 360.0 - 180.0

            self.error_card.value_label.setText(f"{position_error:.3f} m")
            self.heading_error_card.value_label.setText(f"{heading_error:.1f} deg")
        else:
            self.error_card.value_label.setText("--")
            self.heading_error_card.value_label.setText("--")

        self.canvas.update_data(
            actual=(snapshot.pose_x_m, snapshot.pose_y_m, snapshot.heading_deg),
            target=(
                snapshot.pathplanner_target_x_m,
                snapshot.pathplanner_target_y_m,
                snapshot.pathplanner_target_heading_deg,
            ),
            target_valid=snapshot.pathplanner_target_valid,
            path=self._parse_path(snapshot.pathplanner_active_path),
        )
