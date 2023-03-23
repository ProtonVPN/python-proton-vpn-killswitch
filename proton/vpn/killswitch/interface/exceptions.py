"""
This module contains the exceptions to be used by kill swtich backends.
"""


class KillSwitchException(Exception):
    """Base class for KillSwitch specific exceptions."""

    def __init__(self, message: str, additional_context: object = None):  # noqa
        self.message = message
        self.additional_context = additional_context
        super().__init__(self.message)


class MissingKillSwitchBackendDetails(KillSwitchException):
    """When no KillSwitch backend is found then this exception is raised.

    In rare cases where it can happen that a user has some default packages installed, where the
    services for those packages are actually not running. Ie:
    NetworkManager is installed but not running and for some reason we can't access it,
    thus this exception is raised as we can't do anything.
    """
