"""
Module that contains the base class for Kill Switch implementations to extend from.
"""

from __future__ import annotations

from proton.loader import Loader

from proton.vpn.killswitch.interface.exceptions import MissingKillSwitchBackendDetails


class KillSwitch:
    """
    The `KillSwitch` is the base class from which all other kill switch
    backends need to derive from.
    """
    @staticmethod
    def get(class_name: str = None) -> KillSwitch:
        """
        Returns the kill switch implementation.

        :param class_name: Name of the class implementing the kill switch. This
        parameter is optional. If it's not provided then the existing implementation
        with the highest priority is returned.
        """
        try:
            return Loader.get("killswitch", class_name=class_name)
        except RuntimeError as excp:
            raise MissingKillSwitchBackendDetails(excp) from excp

    def enable(self, vpn_server):
        """
        Enables the kill switch.

        :raises KillSwitchError: If unable to enable the kill switch.
        """
        raise NotImplementedError

    def disable(self):
        """
        Disables the kill switch.

        :raises KillSwitchError: If unable to disable the kill switch.
        """
        raise NotImplementedError

    def update(self, vpn_server):
        """
        Update the kill switch.

        :raises KillSwitchError: If unable to update the kill switch.
        """
        raise NotImplementedError

    def enable_ipv6_leak_protection(self):
        """
        Enables IPv6 kill switch to prevent leaks.

        :raises KillSwitchError: If unable to enable the kill switch.
        """
        raise NotImplementedError

    def disable_ipv6_leak_protection(self):
        """
        Disables IPv6 kill switch to prevent leaks.

        :raises KillSwitchError: If unable to disable the kill switch.
        """
        raise NotImplementedError

    @classmethod
    def _get_priority(cls) -> int:
        return None

    @classmethod
    def _validate(cls):
        return False
