import pytest
from proton.vpn.killswitch.interface import KillSwitch
from proton.vpn.killswitch.interface.enums import KillSwitchStateEnum
from proton.vpn.connection import states


class DummyKillSwitch(KillSwitch):
    def __init__(self, *args, **kwargs):
        self.should_ks_be_active = None
        super().__init__(*args, **kwargs)

    def _disable(self, **kwargs):
        self.should_ks_be_active = False

    def _enable(self, **kwargs):
        self.should_ks_be_active = True


class DummyLoader:
    @staticmethod
    def get(backend_name, class_name=None):
        return DummyKillSwitch


@pytest.fixture
def modified_loader():
    from proton import loader
    orig_loader = loader.Loader
    loader.Loader = DummyLoader
    yield loader.Loader
    loader.Loader = orig_loader


def test_default_init(modified_loader):
    ks = KillSwitch.get_from_factory()()
    assert ks.state == KillSwitchStateEnum.OFF
    assert ks.permanent_mode is False


@pytest.mark.parametrize(
    "state, permanent",
    [
        (True, KillSwitchStateEnum.OFF), ([], {}),
        ("one", 20), (10, 0), (False, False),
        (0, 0), (None, None),
    ]
)
def test_init_with_unexpected_args(modified_loader, state, permanent):
    with pytest.raises(TypeError):
        KillSwitch.get_from_factory()(state, permanent)


@pytest.mark.parametrize(
    "state, permanent",
    [
        (KillSwitchStateEnum.ON, False),
        (KillSwitchStateEnum.ON, True),
        (KillSwitchStateEnum.OFF, False),
        (KillSwitchStateEnum.OFF, True),
    ]
)
def test_init_with_expected_args(modified_loader, state, permanent):
    ks = KillSwitch.get_from_factory()(state, permanent)
    assert ks.state == state
    assert ks.permanent_mode == permanent


@pytest.mark.parametrize(
    "state, permanent, connection_status, initial_is_ks_active, is_ks_active",
    [
        (KillSwitchStateEnum.OFF, False, states.Disconnected(), False, False),
        (KillSwitchStateEnum.OFF, True, states.Disconnected(), False, False),
        (KillSwitchStateEnum.ON, False, states.Disconnected(), None, False),
        (KillSwitchStateEnum.ON, True, states.Disconnected(), True, True),
    ]
)
def test_expected_connection_status_updates_on_disconnected(
    modified_loader, state, permanent,
    connection_status, initial_is_ks_active, is_ks_active
):
    ks = KillSwitch.get_from_factory()(state, permanent)
    assert ks.state == state
    assert ks.permanent_mode == permanent
    assert ks.should_ks_be_active == initial_is_ks_active
    ks.connection_status_update(connection_status)
    assert ks.state == state
    assert ks.permanent_mode == permanent
    assert ks.should_ks_be_active == is_ks_active


@pytest.mark.parametrize(
    "state, permanent, connection_status, initial_is_ks_active, is_ks_active",
    [
        (KillSwitchStateEnum.OFF, False, states.Connecting(), False, False),
        (KillSwitchStateEnum.OFF, True, states.Connecting(), False, False),
        (KillSwitchStateEnum.ON, False, states.Connecting(), None, None),
        (KillSwitchStateEnum.ON, True, states.Connecting(), True, True),
    ]
)
def test_expected_connection_status_updates_on_connecting(
    modified_loader, state, permanent,
    connection_status, initial_is_ks_active, is_ks_active
):
    ks = KillSwitch.get_from_factory()(state, permanent)
    assert ks.state == state
    assert ks.permanent_mode == permanent
    assert ks.should_ks_be_active == initial_is_ks_active
    ks.connection_status_update(connection_status)
    assert ks.state == state
    assert ks.permanent_mode == permanent
    assert ks.should_ks_be_active == is_ks_active


@pytest.mark.parametrize(
    "state, permanent, connection_status, initial_is_ks_active, is_ks_active",
    [
        (KillSwitchStateEnum.OFF, False, states.Connected(), False, False),
        (KillSwitchStateEnum.OFF, True, states.Connected(), False, False),
        (KillSwitchStateEnum.ON, False, states.Connected(), None, True),
        (KillSwitchStateEnum.ON, True, states.Connected(), True, True),
    ]
)
def test_expected_connection_status_updates_on_connected(
    modified_loader, state, permanent,
    connection_status, initial_is_ks_active, is_ks_active
):
    ks = KillSwitch.get_from_factory()(state, permanent)
    assert ks.state == state
    assert ks.permanent_mode == permanent
    assert ks.should_ks_be_active == initial_is_ks_active
    ks.connection_status_update(connection_status)
    assert ks.state == state
    assert ks.permanent_mode == permanent
    assert ks.should_ks_be_active == is_ks_active


@pytest.mark.parametrize(
    "state, permanent, initial_is_ks_active, is_ks_active",
    [
        (KillSwitchStateEnum.OFF, False, False, False),
        (KillSwitchStateEnum.ON, False, None, True),
    ]
)
def test_permanet_mode_enable(modified_loader, state, permanent, initial_is_ks_active, is_ks_active):
    ks = KillSwitch.get_from_factory()(state, permanent)
    assert ks.state == state
    assert ks.permanent_mode == permanent
    assert ks.should_ks_be_active == initial_is_ks_active
    ks.permanent_mode_enable()
    assert ks.state == state
    assert ks.permanent_mode == (not permanent)
    assert ks.should_ks_be_active == is_ks_active


@pytest.mark.parametrize(
    "state, permanent, initial_is_ks_active, is_ks_active",
    [
        (KillSwitchStateEnum.OFF, True, False, False),
        (KillSwitchStateEnum.ON, True, True, False),
    ]
)
def test_permanet_mode_disable(modified_loader, state, permanent, initial_is_ks_active, is_ks_active):
    ks = KillSwitch.get_from_factory()(state, permanent)
    assert ks.state == state
    assert ks.permanent_mode == permanent
    assert ks.should_ks_be_active == initial_is_ks_active
    ks.permanent_mode_disable()
    assert ks.state == state
    assert ks.permanent_mode == (not permanent)
    assert ks.should_ks_be_active == is_ks_active
