"""Enums from the Tesla Fleet Telemetry protobuf."""
# https://github.com/Teslemetry/tesla-fleet-telemetry/blob/main/protos/vehicle_data.proto

class TeslemetryEnum:
    """Helper class to handle options for protobuf enums."""

    def __init__(self, prefix: str, options: list[str]):
        """Create a new options list."""
        self.prefix = prefix
        self.options = options

    def get(self, value, default:str|None=None) -> str | None:
        """Get the value if it is a valid option."""
        if isinstance(value, str):
            option = value.replace(self.prefix, "").lower()
            if option in self.options:
                return option
        return default

DetailedChargeState = TeslemetryEnum("DetailedChargeState",[
    "starting",
    "charging",
    "stopped",
    "complete",
    "disconnected",
    "nopower",
])
ShiftState = TeslemetryEnum("ShiftState",["p", "d", "r", "n"])
FollowDistance = TeslemetryEnum("FollowDistance", [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7"
])
ForwardCollisionSensitivity = TeslemetryEnum("ForwardCollisionSensitivity", [
    "off",
    "late",
    "average",
    "early"
])
GuestModeMobileAccess = TeslemetryEnum("GuestModeMobileAccess", [
    "init",
    "notauthenticated",
    "authenticated",
    "aborteddriving",
    "abortedusingremotestart",
    "abortedusingblekeys",
    "abortedvaletmode",
    "abortedguestmodeoff",
    "aborteddriveauthtimeexceeded",
    "abortednodatareceived",
    "requestingfrommothership",
    "requestingfromauthd",
    "abortedfetchfailed",
    "abortedbaddatareceived",
    "showingqrcode",
    "swipedaway",
    "dismissedqrcodeexpired",
    "succeededpairednewblekey",
])
LaneAssistLevel = TeslemetryEnum("LaneAssistLevel", [
    "off",
    "warning",
    "assist"
])
ScheduledChargingMode = TeslemetryEnum("ScheduledChargingMode", [
    "off",
    "startat",
    "departby"
])
SentryModeState = TeslemetryEnum("SentryModeState", ["off", "idle", "armed", "aware", "panic", "quiet"])
SpeedAssistLevel = TeslemetryEnum("SpeedAssistLevel", ["none", "display", "chime"])
BMSState = TeslemetryEnum("BMSState", ["standby",
    "drive",
    "support",
    "charge",
    "feim",
    "clearfault",
    "fault",
    "weld",
    "test",
    "sna"
])
BuckleStatus = TeslemetryEnum("BuckleStatus", [
    "unlatched",
    "latched",
    "faulted"
])
CarType = TeslemetryEnum("CarType", [
    "models",
    "modelx",
    "model3",
    "modely",
    "semi",
    "cybertruck"
])
ChargePort = TeslemetryEnum("ChargePort", ["us","eu","gb","ccs"])
#ChargePortLatch is a lock
DriveInverterState = TeslemetryEnum("DriveInverterState", [
    "standby",
    "fault",
    "abort",
    "enable"
])
HvilStatus = TeslemetryEnum("HvilStatus", ["fault","ok"])
#WindowState is cover
SeatFoldPosition = TeslemetryEnum("SeatFoldPosition", ["sna",
    "faulted",
    "notconfigured",
    "folded",
    "unfolded"
])
TractorAirStatus = TeslemetryEnum("TractorAirStatus", [
    "error",
    "charged",
    "buildingpressureintermediate",
    "exhaustingpressureintermediate",
    "exhausted"
])
TrailerAirStatus = TeslemetryEnum("TrailerAirStatus", [
    "sna",
    "invalid",
    "bobtailmode",
    "charged",
    "buildingpressureintermediate",
    "exhaustingpressureintermediate",
    "exhausted"
])
DisplayState = TeslemetryEnum("DisplayState", [
    "off",
    "dim",
    "accessory",
    "on",
    "driving",
    "charging",
    "lock",
    "sentry",
    "dog",
    "entertainment"
])
#HvacAutoModeState is climate
#CabinOverheatProtectionModeState and CabinOverheatProtectionModeState is climate
