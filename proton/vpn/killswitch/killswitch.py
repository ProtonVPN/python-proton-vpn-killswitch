from .exceptions import MissingKillSwitchBackendDetails
from .enums import KillSwitchStateEnum


class KillSwitch:
    """
    The `KillSwitch` is the base class from which all other kill switch
    backends need to derive from.

    The `on()` and `off()` methods are meant to controll the state of the component,
    akin to a switch. If the component is in `off` state, then the `permament`
    property and any connection updates are disregarded. Thus it will not act
    unless its state is set to `on`, preventing any unwanted behaviours and always giving
    expected results.

    Given also how the kill switch is dependent on connection states (in its `on` state),
    it is thus crucial to be able to receive them so that the kill switch can act upon these states.
    For that reason, the methods that `raise NotImplementedError`
    have to implement their own logic on how to act upon these connection status changes.

    About the permanent mode, given that it's just a variation of the `on` state, it did not make
    sense to have its own "switch mode", but rather be a modifier of the `on` state.

    Usage:

    .. code-block::

        from proton.vpn.killswitch import KillSwitch

        killswitch = KillSwitch.get_from_factory()

        # Change component state to off.
        killswitch.off()

        # Change component state to on.
        killswitch.on()

        # Enable permanent mode. This will directly start the kill switch and
        # you'll be without internet connection.
        killswitch.permanent = True

        # Changing component state back to off will turn off the permanent mode,
        # thus restoring internet connection.
        killswitch.off()
    """
    def __init__(self, state: KillSwitchStateEnum = KillSwitchStateEnum.OFF, permanent: bool = False):
        self.__state = state
        self.__permanent = permanent

    def __str__(self):
        return "{} <State: {} Permanent: {}>".format(type(self).__name__, self.__state, self.__permanent)

    def off(self):
        """
        Turns off the component. In this state it will completly
        disregard connection state updates and the permanent modifier.

        Should be used when it's desired to completly stop the kill switch.
        """
        self._setup_off()
        self.__state = KillSwitchStateEnum.OFF

    def on(self):
        """
        Turns on the component. In this state it will act on state updates
        for a given connection and the permanent modifier.

        If the permanent modifier was enabled before turning the kill switch to
        its `on` state, then all internet connection will be cut straight away.
        """
        if self.__permanent:
            self._setup_killswitch()

        self.__state = KillSwitchStateEnum.ON

    @property
    def permanent(self) -> bool:
        """
            :return: permanent modifier
            :rtype: bool
        """
        return self.__permanent

    @permanent.setter
    def permanent(self, newvalue: bool):
        """
            :param newvalue: permanent modifier value
            :type newvalue: bool
        """
        if self.__state != KillSwitchStateEnum.OFF:
            if newvalue:
                self._setup_killswitch()
            else:
                self._setup_off()

        self.__permanent = newvalue

    @property
    def state(self) -> KillSwitchStateEnum:
        """
            :return: kill switch state
            :rtype: KillSwitchStateEnum
        """
        return self.__state

    def connection_status_update(self, state: "proton.vpn.connection.states.BaseState", **kwargs):
        """
            :param newvalue: permanent modifier value
            :type newvalue: proton.vpn.connection.states.BaseState

        This method receives connection status updates, so that it can act upon
        each connection state invidually. It is up to the backend to implement
        the desired kill switch behaviour in each connection state.
        Additionally `kwargs` can be passed for any additional/extra
        information that could be necessary for the backends.
        """
        from proton.vpn.connection import states

        if isinstance(state, states.Disconnected):
            self._on_disconnected(**kwargs)
        elif isinstance(state, states.Connecting):
            self._on_connecting(**kwargs)
        elif isinstance(state, states.Connected):
            self._on_connected(**kwargs)
        elif isinstance(state, states.Error):
            self._on_error(**kwargs)
        elif isinstance(state, states.Disconnecting):
            self._on_disconnecting(**kwargs)

    @classmethod
    def get_from_factory(self, backend: str = None):
        """
            :param backend: Optional.
                specific backend name
            :type protocol: str

        If backend is passed then it will attempt to get that specific
        backend, otherwise it will attempt to get the default backend.
        The definition of default is as follows:
         - The backend exists/is installed
         - The backend passes the `_validate()`
         - The backend with the highest `_get_priority()` value


        """
        from proton.loader import Loader
        all_backends = Loader.get_all("killswitch")
        sorted_backends = sorted(all_backends, key=lambda _b: _b.priority, reverse=True)

        if backend:
            try:
                return [
                    _b.cls for _b in sorted_backends
                    if _b.class_name == backend and _b.cls._validate()
                ][0]()
            except (IndexError, AttributeError):
                raise MissingKillSwitchBackendDetails(
                    "Backend \"{}\" could not be found".format(backend)
                )

        for backend in sorted_backends:
            if not backend.cls._validate():
                continue

            return backend.cls()

    def _setup_off(self):
        """
        Remove all kill switch constraints.
        Ensure that it totally removes all contraints/rules/limits,
        if that is not possible for some reason, one of the followin exceptions
        can be thrown:

        :raises KillSwitchStopError: When unable to stop the kill switch
        """
        raise NotImplementedError

    def _setup_killswitch(self):
        """
        Add/activate kill switch instantaneously.
        Ensure that it add the contraints/rules/limits,
        if that is not possible for some reason, one of the followin exceptions
        can be thrown:

        :raises KillSwitchStartError: When unable to start the kill switch
        """
        raise NotImplementedError

    def _on_disconnected(self, **kwargs):
        """
        :raises KillSwitchStartError: When unable to start the kill switch
        :raises KillSwitchStopError: When unable to stop the kill switch
        """
        raise NotImplementedError

    def _on_connecting(self, **kwargs):
        """
        :raises KillSwitchStartError: When unable to start the kill switch
        :raises KillSwitchStopError: When unable to stop the kill switch
        :raises KeyError: When the expected key is not passed
        :raises TypeError: When expected value to provided key is `None`
        """
        raise NotImplementedError

    def _on_connected(self, **kwargs):
        """
        :raises KillSwitchStartError: When unable to start the kill switch
        :raises KillSwitchStopError: When unable to stop the kill switch
        """
        raise NotImplementedError

    def _on_error(self, **kwargs):
        """
        :raises KillSwitchStartError: When unable to start the kill switch
        :raises KillSwitchStopError: When unable to stop the kill switch
        """
        raise NotImplementedError

    def _on_disconnecting(self, **kwargs):
        """
        :raises KillSwitchStartError: When unable to start the kill switch
        :raises KillSwitchStopError: When unable to stop the kill switch
        """
        raise NotImplementedError

    @classmethod
    def _get_priority(cls) -> int:
        """*For developers*

        Priority value determines which backend takes precedence.

        If no specific backend has been defined then each connection
        backend class to calculate it's priority value. This priority value is
        then used by the factory to select the optimal backend for
        establishing a connection.

        The lower the value, the more priority it has.

        Network manager will always have priority, thus it will always have the value of 100.
        If NetworkManage packages are installed but are not running, then any other backend
        will take precedence.

        Usage:

        .. code-block::

            from proton.vpn.killswitch import KillSwitch

            class CustomBackend(KillSwitch):
                backend = "custom_backend"

                ...

                @classmethod
                def _get_priority(cls):
                    # Either return a hard-coded value (which is discoureaged),
                    # or calculate it based on some system settings
                    return 150

        Note: Some code has been ommitted for readability.
        """
        return None

    @classmethod
    def _validate(cls):
        return False
