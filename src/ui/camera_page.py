from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.camera.mjpeg_stream import MJPEGStream


DEFAULT_PROCESSED_URL = "http://photonvision.local:1182/?action=stream"
DEFAULT_RAW_URL = "http://photonvision.local:1181/?action=stream"


class CameraPage(QWidget):
    """Human-view camera page, deliberately separate from robot vision control."""

    def __init__(self) -> None:
        super().__init__()

        self._stream = MJPEGStream()
        self._active = False
        self._last_sequence = 0
        self._current_pixmap = QPixmap()

        layout = QVBoxLayout(self)

        heading = QLabel("DRIVER CAMERA")
        heading.setObjectName("pageTitle")
        layout.addWidget(heading)

        info = QLabel(
            "Display only: this video is not used by PhotonVision auto-align. "
            "The stream stops automatically when this page is not open."
        )
        info.setObjectName("mutedLabel")
        info.setWordWrap(True)
        layout.addWidget(info)

        controls = QHBoxLayout()

        self.url_input = QLineEdit(DEFAULT_PROCESSED_URL)
        self.url_input.setPlaceholderText("MJPEG stream URL")
        self.url_input.returnPressed.connect(self.restart_stream)
        controls.addWidget(self.url_input, 1)

        raw_button = QPushButton("RAW 1181")
        raw_button.clicked.connect(lambda: self.use_url(DEFAULT_RAW_URL))
        controls.addWidget(raw_button)

        processed_button = QPushButton("PROCESSED 1182")
        processed_button.clicked.connect(lambda: self.use_url(DEFAULT_PROCESSED_URL))
        controls.addWidget(processed_button)

        restart_button = QPushButton("RECONNECT")
        restart_button.clicked.connect(self.restart_stream)
        controls.addWidget(restart_button)

        layout.addLayout(controls)

        self.status_label = QLabel("CAMERA: STOPPED")
        self.status_label.setObjectName("summaryLabel")
        layout.addWidget(self.status_label)

        self.video_label = QLabel("Open CAMERA to start the stream")
        self.video_label.setObjectName("cameraView")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 360)
        layout.addWidget(self.video_label, 1)

        hint = QLabel(
            "PhotonVision normally uses 1181/1182 for the first camera's raw/processed streams. "
            "If PC_Camera uses a different host or port, paste that stream URL above."
        )
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self.refresh_video)
        self._timer.start()

    def set_active(self, active: bool) -> None:
        if self._active == active:
            return

        self._active = active
        if active:
            self.restart_stream()
        else:
            self._stream.stop()
            self._last_sequence = 0
            self.status_label.setText("CAMERA: STOPPED (PAGE HIDDEN)")

    def use_url(self, url: str) -> None:
        self.url_input.setText(url)
        if self._active:
            self.restart_stream()

    def restart_stream(self) -> None:
        if not self._active:
            return

        self._last_sequence = 0
        self.video_label.setText("Connecting to camera...")
        self._stream.restart(self.url_input.text())

    def refresh_video(self) -> None:
        state = self._stream.state()

        if state.connected:
            age_ms = int((state.last_frame_age_s or 0.0) * 1000)
            self.status_label.setText(f"CAMERA: LIVE    newest frame: {age_ms} ms ago")
        elif state.running:
            self.status_label.setText(f"CAMERA: {state.status}")
        else:
            self.status_label.setText(f"CAMERA: {state.status}")

        sequence, frame = self._stream.latest_frame(self._last_sequence)
        if frame is None:
            return

        self._last_sequence = sequence
        image = QImage.fromData(frame, "JPG")
        if image.isNull():
            return

        self._current_pixmap = QPixmap.fromImage(image)
        self._render_pixmap()

    def resizeEvent(self, event) -> None:
        self._render_pixmap()
        super().resizeEvent(event)

    def _render_pixmap(self) -> None:
        if self._current_pixmap.isNull():
            return

        self.video_label.setPixmap(
            self._current_pixmap.scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
        )

    def shutdown(self) -> None:
        self._stream.stop()
