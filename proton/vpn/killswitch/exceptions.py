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


class KillSwitchStartError(KillSwitchError):
    """When unable to start killswitch then this exception is raised."""


class KillSwitchStopError(KillSwitchError):
    """When unable to stop killswitch then this exception is raised."""


class MissingKeyValueError(KillSwitchError):
    """When backend expects certain kwargs but none are passed, this exceptions is raised."""
