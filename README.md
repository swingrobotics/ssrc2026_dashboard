# SSRC 2026 Dashboard

Custom FRC dashboard for SSRC Team 10958.

## Current features

The dashboard connects to the roboRIO over NetworkTables 4 and currently includes:

- Robot connection status
- Robot pose X / Y / heading
- navX2 connection and calibration state
- Field-relative / robot-relative state
- Vision auto-align state and target yaw
- Field/odometry visualization
- Swerve page scaffold
- Low-latency PhotonVision MJPEG camera page

It reads the current robot topics under `/SmartDashboard` so the dashboard can work with the existing `ssrc2026` robot code.

## Camera architecture

The camera page is intentionally separate from robot vision control.

```text
PhotonVision target processing -> PhotonLib -> robot code -> auto-align
Camera MJPEG stream          -> SSRC Dashboard -> human display only
```

The dashboard never sends displayed video frames back into the auto-align loop.

To avoid building up video delay:

- the MJPEG reader keeps only the newest complete JPEG frame
- old frames are overwritten instead of queued
- the camera stream runs only while the CAMERA page is open
- leaving CAMERA immediately stops the stream
- the UI renders at about 30 FPS

PhotonVision assigns two stream ports per camera. For the first camera, the usual pair is:

- raw stream: 1181
- processed stream: 1182

The CAMERA page defaults to:

```text
http://photonvision.local:1182/?action=stream
```

If `PC_Camera` is hosted elsewhere, paste the stream URL into the CAMERA page. For example, if PhotonVision is running on the same Windows PC, the host may be `localhost` instead of `photonvision.local`.

## Stack

- Python
- PySide6 (Qt)
- pyntcore / NetworkTables 4
- Python standard-library MJPEG client (no OpenCV dependency)

## Setup (Windows)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Or double-click:

```text
SSRC Dashboard.bat
```

Run the dashboard on the Driver Station laptop while connected to the robot network. The NT4 client uses team number **10958** and also starts the Driver Station client so it can obtain the roboRIO address from the Driver Station.

## Current NetworkTables topics

```text
/SmartDashboard/Pose X
/SmartDashboard/Pose Y
/SmartDashboard/Pose Heading
/SmartDashboard/NavX Connected
/SmartDashboard/NavX Calibrating
/SmartDashboard/NavX Yaw
/SmartDashboard/NavX Pitch
/SmartDashboard/NavX Roll
/SmartDashboard/NavX Turn Rate
/SmartDashboard/Field Relative Enabled
/SmartDashboard/Vision Align Enabled
/SmartDashboard/Vision Target Visible
/SmartDashboard/Vision Target Yaw
/SmartDashboard/PathPlanner Configured
```

Later versions can move telemetry into a dedicated `/SSRC/...` namespace and add real swerve module telemetry, official 2026 field assets, PathPlanner target-vs-actual data, match state, diagnostics, and richer AprilTag localization.
