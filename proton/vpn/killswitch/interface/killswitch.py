"""
Module that contains the base class for Kill Switch implementations to extend from.


Copyright (c) 2023 Proton AG

This file is part of Proton VPN.

Proton VPN is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Proton VPN is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProtonVPN.  If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations
from enum import IntEnum
from concurrent.futures import Future

from proton.loader import Loader

from proton.vpn.killswitch.interface.exceptions import MissingKillSwitchBackendDetails


class KillSwitchState(IntEnum):  # pylint: disable=missing-class-docstring
    OFF = 0
    ON = 1


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

    def enable_ipv6_leak_protection(self) -> Future:
        """
        Enables IPv6 kill switch to prevent leaks.

        :raises KillSwitchError: If unable to enable the kill switch.
        """
        raise NotImplementedError

    def disable_ipv6_leak_protection(self) -> Future:
        """
        Disables IPv6 kill switch to prevent leaks.

        :raises KillSwitchError: If unable to disable the kill switch.
        """
        raise NotImplementedError

    @staticmethod
    def _get_priority() -> int:
        raise NotImplementedError

    @staticmethod
    def _validate():
        raise NotImplementedError
