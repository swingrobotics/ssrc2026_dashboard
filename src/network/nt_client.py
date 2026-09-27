from dataclasses import dataclass

import ntcore


@dataclass(frozen=True)
class RobotSnapshot:
    connected: bool
    pose_x_m: float
    pose_y_m: float
    heading_deg: float
    navx_connected: bool
    navx_calibrating: bool
    field_relative_enabled: bool


class NTClient:
    """Small NT4 client for the current SSRC robot telemetry."""

    def __init__(self, team_number: int) -> None:
        self.team_number = team_number
        self.instance = ntcore.NetworkTableInstance.getDefault()
        dashboard = self.instance.getTable("SmartDashboard")

        # Existing topics published by the current ssrc2026 robot code.
        self._pose_x = dashboard.getDoubleTopic("Pose X").subscribe(0.0)
        self._pose_y = dashboard.getDoubleTopic("Pose Y").subscribe(0.0)
        self._pose_heading = dashboard.getDoubleTopic("Pose Heading").subscribe(0.0)
        self._navx_connected = dashboard.getBooleanTopic("NavX Connected").subscribe(False)
        self._navx_calibrating = dashboard.getBooleanTopic("NavX Calibrating").subscribe(False)
        self._field_relative = dashboard.getBooleanTopic("Field Relative Enabled").subscribe(False)

        self.instance.startClient4("SSRC Dashboard")
        self.instance.setServerTeam(team_number)

        # Recommended when the dashboard runs on the Driver Station PC.
        # This allows NetworkTables to obtain the active robot IP from the DS.
        self.instance.startDSClient()

    def is_connected(self) -> bool:
        return len(self.instance.getConnections()) > 0

    def snapshot(self) -> RobotSnapshot:
        return RobotSnapshot(
            connected=self.is_connected(),
            pose_x_m=self._pose_x.get(),
            pose_y_m=self._pose_y.get(),
            heading_deg=self._pose_heading.get(),
            navx_connected=self._navx_connected.get(),
            navx_calibrating=self._navx_calibrating.get(),
            field_relative_enabled=self._field_relative.get(),
        )

    def close(self) -> None:
        self.instance.stopDSClient()
        self.instance.stopClient()
