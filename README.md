# SSRC 2026 Dashboard

Custom FRC dashboard for SSRC Team 10958.

## First milestone

The first version connects to the roboRIO over NetworkTables 4 and displays:

- Robot connection status
- Robot pose X
- Robot pose Y
- Robot heading
- navX2 connection/calibration status

It currently reads the existing robot topics under `/SmartDashboard` so it can work with the current `ssrc2026` robot code without changing the robot program first.

## Stack

- Python
- PySide6 (Qt)
- pyntcore / NetworkTables 4

## Setup (Windows)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Run the dashboard on the Driver Station laptop while connected to the robot network. The NT4 client uses team number **10958** and also starts the Driver Station client so it can obtain the roboRIO address from the Driver Station.

## Current NetworkTables topics

```text
/SmartDashboard/Pose X
/SmartDashboard/Pose Y
/SmartDashboard/Pose Heading
/SmartDashboard/NavX Connected
/SmartDashboard/NavX Calibrating
```

Later versions can migrate these into a dedicated `/SSRC/...` namespace and add Field, Swerve, Vision, Auto, graphing, and diagnostics pages.
