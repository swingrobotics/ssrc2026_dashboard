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
    navx_yaw_deg: float
    navx_pitch_deg: float
    navx_roll_deg: float
    navx_turn_rate_dps: float
    field_relative_enabled: bool
    vision_align_enabled: bool
    vision_target_visible: bool
    vision_target_yaw_deg: float
    pathplanner_configured: bool


class NTClient:
    """NT4 client for the current SSRC robot telemetry."""

    def __init__(self, team_number: int) -> None:
        self.team_number = team_number
        self.instance = ntcore.NetworkTableInstance.getDefault()
        dashboard = self.instance.getTable("SmartDashboard")

        # Pose / drivetrain state.
        self._pose_x = dashboard.getDoubleTopic("Pose X").subscribe(0.0)
        self._pose_y = dashboard.getDoubleTopic("Pose Y").subscribe(0.0)
        self._pose_heading = dashboard.getDoubleTopic("Pose Heading").subscribe(0.0)
        self._field_relative = dashboard.getBooleanTopic("Field Relative Enabled").subscribe(False)

        # navX2 values already published by DriveSubsystem.
        self._navx_connected = dashboard.getBooleanTopic("NavX Connected").subscribe(False)
        self._navx_calibrating = dashboard.getBooleanTopic("NavX Calibrating").subscribe(False)
        self._navx_yaw = dashboard.getDoubleTopic("NavX Yaw").subscribe(0.0)
        self._navx_pitch = dashboard.getDoubleTopic("NavX Pitch").subscribe(0.0)
        self._navx_roll = dashboard.getDoubleTopic("NavX Roll").subscribe(0.0)
        self._navx_turn_rate = dashboard.getDoubleTopic("NavX Turn Rate").subscribe(0.0)

        # PhotonVision values already published by RobotContainer.
        self._vision_align = dashboard.getBooleanTopic("Vision Align Enabled").subscribe(False)
        self._vision_target_visible = dashboard.getBooleanTopic("Vision Target Visible").subscribe(False)
        self._vision_target_yaw = dashboard.getDoubleTopic("Vision Target Yaw").subscribe(0.0)

        # PathPlanner setup status.
        self._pathplanner_configured = dashboard.getBooleanTopic("PathPlanner Configured").subscribe(False)

        self.instance.startClient4("SSRC Dashboard")
        self.instance.setServerTeam(team_number)
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
            navx_yaw_deg=self._navx_yaw.get(),
            navx_pitch_deg=self._navx_pitch.get(),
            navx_roll_deg=self._navx_roll.get(),
            navx_turn_rate_dps=self._navx_turn_rate.get(),
            field_relative_enabled=self._field_relative.get(),
            vision_align_enabled=self._vision_align.get(),
            vision_target_visible=self._vision_target_visible.get(),
            vision_target_yaw_deg=self._vision_target_yaw.get(),
            pathplanner_configured=self._pathplanner_configured.get(),
        )

    def close(self) -> None:
        self.instance.stopDSClient()
        self.instance.stopClient()
