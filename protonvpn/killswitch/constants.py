from enum import Enum

KILLSWITCH_CONN_NAME = "pvpn-killswitch"
KILLSWITCH_INTERFACE_NAME = "pvpnksintrf0"

ROUTED_CONN_NAME = "pvpn-routed-killswitch"
ROUTED_INTERFACE_NAME = "pvpnroutintrf0"

IPv4_DUMMY_ADDRESS = "100.85.0.1/24"
IPv4_DUMMY_GATEWAY = "100.85.0.1"
IPv6_DUMMY_ADDRESS = "fdeb:446c:912d:08da::/64"
IPv6_DUMMY_GATEWAY = "fdeb:446c:912d:08da::1"

KILLSWITCH_DNS_PRIORITY_VALUE = "-1400"


class KillSwitchInterfaceTrackerEnum(Enum):
    EXISTS = 0
    IS_RUNNING = 1


class KillSwitchActionEnum(Enum):
    PRE_CONNECTION = "pre_connection",
    POST_CONNECTION = "post_connection",
    SOFT = "soft_connection"
    ENABLE = "enable"
    DISABLE = "disable"

class KillswitchStatusEnum(Enum):
    DISABLED = 0
    HARD = 1
    SOFT = 2
