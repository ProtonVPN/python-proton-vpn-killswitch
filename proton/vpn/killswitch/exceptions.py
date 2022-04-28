class KillSwitchError(Exception):
    """Base class for KillSwitch specific exceptions"""
    def __init__(self, message, additional_context=None):
        self.message = message
        self.additional_context = additional_context
        super().__init__(self.message)


class MissingKillSwitchBackendDetails(KillSwitchError):
    """When no KillSwitch backend is found then this exception is thrown.

    In rare cases where it can happen that a user has some default packages installed, where the
    services for those packages are actually not running. Ie:
    NetworkManager is installed but not running and for some reason we can't access it,
    thus this exception is thrown as we can't do anything.
    """


class StartIPv4KillSwitchError:
    """When unable to start killswitch for IPv4 protocol then this exception is raised."""


class StopIPv4KillSwitchError:
    """When unable to stop killswitch for IPv4 protocol then this exception is raised."""


class StartIPv6KillSwitchError:
    """When unable to start killswitch for IPv6 protocol then this exception is raised."""


class StopIPv6KillSwitchError:
    """When unable to stop killswitch for IPv6 protocol then this exception is raised."""
