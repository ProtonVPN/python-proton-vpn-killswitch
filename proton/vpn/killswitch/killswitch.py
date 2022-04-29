from .exceptions import MissingKillSwitchBackendDetails
from .enums import KillSwitchStateEnum


class KillSwitch:
    def __init__(self, permanent=False):
        # should have a auto determine method, to understand if there
        self.__permanent = permanent

    def off(self):
        self._setup_off()
        self.__state = KillSwitchStateEnum.OFF

    def on(self):
        self.__state = KillSwitchStateEnum.ON

    @property
    def permanent(self):
        return self.__permanent

    @permanent.setter
    def permanent(self, newvalue):
        if self.__state != KillSwitchStateEnum.OFF:
            self._setup_permanent()

        self.__permanent = newvalue

    @property
    def state(self):
        return self.__state

    def connection_status_update(self, state: "proton.vpn.connection.states.BaseState", **kwargs):
        from proton.vpn.connection import states

        if isinstance(state, states.Disconnected()):
            self._on_disconnected(**kwargs)
        elif isinstance(state, states.Connecting()):
            self._on_connecting(**kwargs)
        elif isinstance(state, states.Connected()):
            self._on_connected(**kwargs)
        elif isinstance(state, states.Error()):
            self._on_error(**kwargs)
        elif isinstance(state, states.Disconnecting()):
            self._on_disconnecting(**kwargs)

    @classmethod
    def get_from_factory(self, backend: str = None):
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

    def _determine_initial_state(self):
        raise NotImplementedError

    def _setup_off(self):
        raise NotImplementedError

    def _setup_permanent(self):
        raise NotImplementedError

    def _on_disconnected(self, **kwargs):
        pass

    def _on_connecting(self, **kwargs):
        raise NotImplementedError

    def _on_connected(self, **kwargs):
        raise NotImplementedError

    def _on_error(self, **kwargs):
        raise NotImplementedError

    def _on_disconnecting(self, **kwargs):
        raise NotImplementedError
