from __future__ import annotations

from .exceptions import MissingKillSwitchBackendDetails
from .enums import KillSwitchStateEnum
from proton.vpn.connection.states import BaseState


class KillSwitch:
    """
    The `KillSwitch` is the base class from which all other kill switch
    backends need to derive from.

    The `on()` and `off()` methods are meant to control the state of the component,
    akin to a switch. If the component is in `off` state, then the `permanent`
    property and any connection updates are disregarded. Thus, it will not act
    unless its state is set to `on`, preventing any unwanted behaviours and always giving
    expected results.

    Given also how the kill switch is dependent on connection states (in its `on` state),
    it is thus crucial to be able to receive them so that the kill switch can act upon these states.
    For that reason, the methods that `raise NotImplementedError`
    have to implement their own logic on how to act upon these connection status changes.

    About the permanent mode, given that it's just a variation of the `on` state, thus only taking
    effect only when the kill switch is in its `on` state.

    Usage:

    .. code-block::

        from proton.vpn.killswitch import KillSwitch

        killswitch_backend = KillSwitch.get_from_factory()

        # Instantiate the class
        killswitch = killswitch_backend()

        # Change component state to off.
        killswitch.off()

        # Change component state to on.
        killswitch.on()

        # Enable permanent mode. This will directly start the kill switch and
        # you'll be without internet connection, only if kill switch is `on`.
        killswitch.permanent_mode_enable()

        # Changing component state back to off will turn off the permanent mode,
        # thus restoring internet connection.
        killswitch.off()
    """
    def __init__(self, state: KillSwitchStateEnum = KillSwitchStateEnum.OFF, permanent: bool = False):
        if not any([state is known_state for known_state in [value for _, value in KillSwitchStateEnum.__members__.items()]]):
            raise TypeError(
                "Wrong type for 'state' argument. Expected {} but got {}"
                .format(KillSwitchStateEnum, type(state))
            )

        self.__state = None
        self.__permanent = None

        if state is KillSwitchStateEnum.ON:
            self.on(permanent)
        else:
            self.off()
            if permanent:
                self.permanent_mode_enable()
            else:
                self.permanent_mode_disable()

    def __str__(self):
        return "{} <State: {} Permanent: {}>".format(
            type(self).__name__, self.__state, self.__permanent
        )

    def off(self):
        """
        Turns off the component. In this state it will completely
        disregard connection state updates and the permanent modifier.

        Should be used when it's desired to completely stop the kill switch.
        """
        self._disable()
        self.__state = KillSwitchStateEnum.OFF

    def on(self, permanent: bool):
        """
        Turns on the component. In this state it will act on state updates
        for a given connection and the permanent modifier.

        If the permanent modifier was enabled before turning the kill switch to
        its `on` state, then all internet connection will be cut straight away.
        """
        self.__permanent = permanent
        if self.__permanent:
            self._enable()

        self.__state = KillSwitchStateEnum.ON

    @property
    def state(self) -> KillSwitchStateEnum:
        """
            :return: kill switch state
            :rtype: KillSwitchStateEnum
        """
        return self.__state

    @property
    def permanent_mode(self) -> bool:
        """
            :return: permanent mode
            :rtype: bool
        """
        return self.__permanent

    def permanent_mode_enable(self):
        """
        Enables permanent mode. It will only do so if the
        kill switch state is `on`.
        """
        if self.__state != KillSwitchStateEnum.OFF:
            self._enable()

        self.__permanent = True

    def permanent_mode_disable(self):
        """
        Disables permanent mode. It will only do so if the
        kill switch state is `on`.
        """
        if self.__state != KillSwitchStateEnum.OFF:
            self._disable()

        self.__permanent = False

    def connection_status_update(self, state: BaseState, **kwargs):
        """
            :param state: current connection state.

        This method receives connection status updates, so that it can act upon
        each connection state individually. It is up to the backend to implement
        the desired kill switch behaviour in each connection state.
        Additionally, `kwargs` can be passed for any additional/extra
        information that could be necessary for the backends.
        """
        from proton.vpn.connection import states

        if isinstance(state, states.Disconnected):
            self._on_disconnected(**kwargs)
        elif isinstance(state, states.Connecting):
            self._on_connecting(**kwargs)
        elif isinstance(state, states.Connected):
            self._on_connected(**kwargs)

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
        from proton.loader import Loader
        try:
            backend = Loader.get("killswitch", class_name=backend)
        except RuntimeError as e:
            raise MissingKillSwitchBackendDetails(e)

        return backend

    def _on_disconnected(self, **kwargs):
        """
        :raises KillSwitchError: If unable to make changes to kill switch.
        """
        if self.state == KillSwitchStateEnum.ON and not self.permanent_mode:
            self._disable(**kwargs)

    def _on_connecting(self, **kwargs):
        """
        :raises KillSwitchError: If unable to make changes to kill switch.
        """
        if self.state == KillSwitchStateEnum.ON and self.permanent_mode:
            self._enable(**kwargs)

    def _on_connected(self, **kwargs):
        """
        :raises KillSwitchError: If unable to make changes to kill switch.
        """
        if self.state == KillSwitchStateEnum.ON:
            self._enable(**kwargs)

    def _disable(self, **kwargs):
        """
        Disables kill switch. It completly should
        remove all contraints/rules/limits.

        :raises KillSwitchError: If unable to make changes to kill switch.
        """
        raise NotImplementedError

    def _enable(self, **kwargs):
        """
        Enable kill switch instantaneously.
        Ensure that it add the contraints/rules/limits.

        :raises KillSwitchError: If unable to make changes to kill switch.
        """
        raise NotImplementedError

    @classmethod
    def _get_priority(cls) -> int:
        return None

    @classmethod
    def _validate(cls):
        return False
