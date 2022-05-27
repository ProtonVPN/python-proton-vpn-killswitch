from __future__ import annotations

from proton.loader import Loader
from proton.vpn.connection import states

from proton.vpn.killswitch.interface.exceptions import MissingKillSwitchBackendDetails, KillSwitchException
from proton.vpn.killswitch.interface.enums import KillSwitchStateEnum
from proton.vpn.connection.states import BaseState


class KillSwitch:
    """
    The `KillSwitch` is the base class from which all other kill switch
    backends need to derive from.

    Given also how the kill switch is dependent on connection states,
    it is thus crucial to be able to receive them so that the kill switch can act upon these states.
    For that reason, the methods that `raise NotImplementedError`
    have to implement their own logic on how to act upon these connection status changes.

    Usage:

    .. code-block::

        from proton.vpn.killswitch import KillSwitch

        killswitch_backend = KillSwitch.get_from_factory()

        # Instantiate the class
        killswitch = killswitch_backend()

        # To turn off (disable) the kill switch:
        killswitch.turn_off()

        # To turn on the kill switch but enable it only when connected to the VPN:
        killswitch.turn_on_non_permanently()

        # To tur on the kill switch and enable it permanently:
        killswitch.permanent_mode_enable()

        # To turn off the kill switch again:
        killswitch.turn_off()
    """
    def __init__(self, state: KillSwitchStateEnum = KillSwitchStateEnum.OFF):
        if not any([state is known_state for known_state in [value for _, value in KillSwitchStateEnum.__members__.items()]]):
            raise TypeError(
                "Wrong type for 'state' argument. Expected {} but got {}"
                .format(KillSwitchStateEnum, type(state))
            )

        self.__update_state(state)

    def __str__(self):
        return "{} <State: {}>".format(type(self).__name__, self.__state.name)

    @classmethod
    def get_from_factory(cls, backend: str = None) -> KillSwitch:
        """
            :param backend: Optional.
                Specific backend name.

        If backend is passed then it will attempt to get that specific
        backend, otherwise it will attempt to get the default backend.
        The definition of default is as follows:
         - The backend exists/is installed
         - The backend passes the `_validate()`
         - The backend with the highest `_get_priority()` value
        """
        try:
            backend = Loader.get("killswitch", class_name=backend)
        except RuntimeError as e:
            raise MissingKillSwitchBackendDetails(e)

        return backend

    def turn_off(self):
        """
        Should be used when it's desired to completely stop the kill switch.
        """
        self.__update_state(KillSwitchStateEnum.OFF)

    def turn_on_non_permanently(self):
        """
        Turns on the component only while connected to the VPN.
        Warning: the kill switch is disabled after disconnecting from the VPN.
        """
        self.__update_state(KillSwitchStateEnum.ON_NON_PERMANENT)

    def turn_on_permanently(self):
        """
        Turns on the component permanently, meaning that the kill switch will always be enabled.
        Network traffic will be permanently blocked until the user connects back to the VPN.
        """
        self.__update_state(KillSwitchStateEnum.ON_PERMANENT)

    @property
    def state(self) -> KillSwitchStateEnum:
        """
            :return: kill switch state
            :rtype: KillSwitchStateEnum
        """
        return self.__state

    def __update_state(self, newstate: KillSwitchStateEnum):
        if newstate is KillSwitchStateEnum.OFF:
            self._disable()
        elif newstate is KillSwitchStateEnum.ON_PERMANENT:
            self._enable()
        else:
            # ON_NON_PERMANENT should only enable the kill switch once we are connected to the VPN
            pass

        self.__state = newstate

    def connection_status_update(self, state: BaseState, **kwargs):
        """
        This method receives connection status updates, so that it can act upon
        each connection state individually. It is up to the backend to implement
        the desired kill switch behaviour in each connection state.
        Additionally, `kwargs` can be passed for any additional/extra
        information that could be necessary for the backends.

        :param state: current connection state.
        """

        if isinstance(state, states.Disconnected):
            self._on_disconnected(**kwargs)
        elif isinstance(state, states.Connecting):
            self._on_connecting(**kwargs)

    def _on_disconnected(self, **kwargs):
        """
        Reacts to the Disconnected event.

        :raises KillSwitchError: If unable to make changes to kill switch.
        """
        if self.state is KillSwitchStateEnum.ON_NON_PERMANENT:
            self._disable(**kwargs)

    def _on_connecting(self, **kwargs):
        """
        Reacts to the Connecting event.

        :raises KillSwitchError: If unable to make changes to kill switch.
        """
        if self.state is KillSwitchStateEnum.ON_NON_PERMANENT:
            self._enable(**kwargs)
        elif self.state is KillSwitchStateEnum.ON_PERMANENT:
            self._update(**kwargs)

    def _disable(self, **kwargs):
        """
        Disables kill switch.

        :raises KillSwitchError: If unable to disable the kill switch.
        """
        raise NotImplementedError

    def _enable(self, **kwargs):
        """
        Enable kill switch instantaneously.

        :raises KillSwitchError: If unable to enable the kill switch.
        """
        raise NotImplementedError

    def _update(self, **kwargs):
        """
        Updates the kill switch to be able to connect to the selected server.

        :raises KillSwitchError: If unable to update the kill switch.
        """
        raise NotImplementedError

    @classmethod
    def _get_priority(cls) -> int:
        return None

    @classmethod
    def _validate(cls):
        return False
