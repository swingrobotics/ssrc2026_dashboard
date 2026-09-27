from __future__ import annotations

import threading
import time
import urllib.request
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StreamState:
    running: bool
    connected: bool
    status: str
    last_frame_age_s: Optional[float]


class MJPEGStream:
    """Small low-latency MJPEG reader.

    Frames are intentionally not queued. The newest decoded JPEG replaces the
    previous one so the dashboard cannot build up seconds of stale video.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._response = None

        self._url = ""
        self._latest_frame: Optional[bytes] = None
        self._frame_sequence = 0
        self._last_frame_time: Optional[float] = None
        self._status = "STOPPED"
        self._running = False

    def start(self, url: str) -> None:
        url = url.strip()
        if not url:
            return

        self.stop()

        with self._lock:
            self._url = url
            self._latest_frame = None
            self._frame_sequence = 0
            self._last_frame_time = None
            self._status = "CONNECTING"
            self._running = True

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._reader_loop,
            name="SSRC-MJPEG",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

        response = None
        with self._lock:
            response = self._response

        if response is not None:
            try:
                response.close()
            except Exception:
                pass

        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=0.4)

        with self._lock:
            self._thread = None
            self._response = None
            self._running = False
            self._status = "STOPPED"

    def restart(self, url: str) -> None:
        self.start(url)

    def latest_frame(self, after_sequence: int) -> tuple[int, Optional[bytes]]:
        with self._lock:
            if self._frame_sequence == after_sequence:
                return self._frame_sequence, None
            return self._frame_sequence, self._latest_frame

    def state(self) -> StreamState:
        now = time.monotonic()
        with self._lock:
            age = None
            if self._last_frame_time is not None:
                age = max(0.0, now - self._last_frame_time)

            connected = self._running and age is not None and age < 1.5
            return StreamState(
                running=self._running,
                connected=connected,
                status=self._status,
                last_frame_age_s=age,
            )

    def _reader_loop(self) -> None:
        buffer = bytearray()

        try:
            request = urllib.request.Request(
                self._url,
                headers={
                    "User-Agent": "SSRC-Dashboard/1.0",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
            )
            response = urllib.request.urlopen(request, timeout=5.0)

            with self._lock:
                self._response = response
                self._status = "WAITING FOR VIDEO"

            while not self._stop_event.is_set():
                chunk = response.read(16384)
                if not chunk:
                    raise ConnectionError("camera stream closed")

                buffer.extend(chunk)

                # MJPEG is a sequence of JPEG images. Keep only the newest
                # complete JPEG frame and overwrite old frames instead of queueing.
                while True:
                    start = buffer.find(b"\xff\xd8")
                    if start < 0:
                        if len(buffer) > 2_000_000:
                            del buffer[:-2]
                        break

                    end = buffer.find(b"\xff\xd9", start + 2)
                    if end < 0:
                        if start > 0:
                            del buffer[:start]
                        if len(buffer) > 4_000_000:
                            del buffer[:-1_000_000]
                        break

                    frame = bytes(buffer[start : end + 2])
                    del buffer[: end + 2]

                    with self._lock:
                        self._latest_frame = frame
                        self._frame_sequence += 1
                        self._last_frame_time = time.monotonic()
                        self._status = "LIVE"

        except Exception as exc:
            if not self._stop_event.is_set():
                with self._lock:
                    self._status = f"ERROR: {exc}"
        finally:
            with self._lock:
                response = self._response
                self._response = None
                self._running = False

            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass
