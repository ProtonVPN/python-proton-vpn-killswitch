from enum import IntEnum
from unittest.mock import patch

import pytest
from proton.vpn.connection import states
from proton.vpn.killswitch.interface import KillSwitch
from proton.vpn.killswitch.interface.enums import KillSwitchStateEnum
from proton.vpn.killswitch.interface.exceptions import \
    MissingKillSwitchBackendDetails, KillSwitchException


class RandomEnum(IntEnum):
    RANDOM = 1


class DummyKillSwitch(KillSwitch):
    def __init__(self, *args, **kwargs):
        self.should_ks_be_enabled = None
        super().__init__(*args, **kwargs)

    def _disable(self, **kwargs):
        self.should_ks_be_enabled = False

    def _enable(self, **kwargs):
        self.should_ks_be_enabled = True


class NotImplementedEnable(KillSwitch):
    def _disable(self, **kwargs):
        pass


class NotImplementedDisable(KillSwitch):
    def _enable(self, **kwargs):
        pass


@pytest.fixture
def modified_loader():
    with patch("proton.loader.Loader") as dummy_loader:
        dummy_loader.get.return_value = DummyKillSwitch
        yield dummy_loader


def test_not_implemented_enable(modified_loader):
    with pytest.raises(NotImplementedError):
        NotImplementedEnable(KillSwitchStateEnum.ON, True)


def test_not_implemented_disable(modified_loader):
    with pytest.raises(NotImplementedError):
        NotImplementedDisable()


def test_default_init(modified_loader):
    ks = KillSwitch.get_from_factory()()
    assert ks.state == KillSwitchStateEnum.OFF
    assert not ks.permanent_mode


def test_get_from_factory_raises_exception_when_called_with_invalid_state(modified_loader):
    with pytest.raises(TypeError):
        KillSwitch.get_from_factory()(RandomEnum.RANDOM, False)


def test_get_from_factory_raises_exception_when_called_with_permanent_modifier(modified_loader):
    with pytest.raises(TypeError):
        KillSwitch.get_from_factory()(KillSwitchStateEnum.ON, "On")


def test_get_from_factory_raises_exception_when_called_with_state_off_and_permanent_modifier_true(modified_loader):
    with pytest.raises(KillSwitchException):
        KillSwitch.get_from_factory()(KillSwitchStateEnum.OFF, True)


@pytest.mark.parametrize(
    "state, permanent, should_ks_be_enabled",
    [
        (KillSwitchStateEnum.ON, False, None),
        (KillSwitchStateEnum.ON, True,  True),
        (KillSwitchStateEnum.OFF, False, False),
    ]
)
def test_init_with_expected_args(modified_loader, state, permanent, should_ks_be_enabled):
    ks = KillSwitch.get_from_factory()(state, permanent)
    assert ks.state == state
    assert ks.permanent_mode == permanent
    assert ks.should_ks_be_enabled == should_ks_be_enabled


@pytest.mark.parametrize(
    "state, permanent, connection_status, initial_should_ks_be_enabled, should_ks_be_enabled",
    [
        (KillSwitchStateEnum.OFF, False, states.Disconnected(), False, False),
        (KillSwitchStateEnum.ON, False, states.Disconnected(), None, False),
        (KillSwitchStateEnum.ON, True, states.Disconnected(), True, True),
    ]
)
def test_expected_connection_status_updates_on_disconnected(
    modified_loader, state, permanent,
    connection_status, initial_should_ks_be_enabled, should_ks_be_enabled
):
    _test_on_connection_status_update(
        state, permanent, connection_status,
        initial_should_ks_be_enabled, should_ks_be_enabled
    )


@pytest.mark.parametrize(
    "state, permanent, connection_status, initial_should_ks_be_enabled, should_ks_be_enabled",
    [
        (KillSwitchStateEnum.OFF, False, states.Connecting(), False, False),
        (KillSwitchStateEnum.ON, False, states.Connecting(), None, None),
        (KillSwitchStateEnum.ON, True, states.Connecting(), True, True),
    ]
)
def test_expected_connection_status_updates_on_connecting(
    modified_loader, state, permanent,
    connection_status, initial_should_ks_be_enabled, should_ks_be_enabled
):
    _test_on_connection_status_update(
        state, permanent, connection_status,
        initial_should_ks_be_enabled, should_ks_be_enabled
    )


@pytest.mark.parametrize(
    "state, permanent, connection_status, initial_should_ks_be_enabled, should_ks_be_enabled",
    [
        (KillSwitchStateEnum.OFF, False, states.Connected(), False, False),
        (KillSwitchStateEnum.ON, False, states.Connected(), None, True),
        (KillSwitchStateEnum.ON, True, states.Connected(), True, True),
    ]
)
def test_expected_connection_status_updates_on_connected(
    modified_loader, state, permanent,
    connection_status, initial_should_ks_be_enabled, should_ks_be_enabled
):
    _test_on_connection_status_update(
        state, permanent, connection_status,
        initial_should_ks_be_enabled, should_ks_be_enabled
    )


def _test_on_connection_status_update(state, permanent, connection_status, initial_should_ks_be_enabled, should_ks_be_enabled):
    ks = DummyKillSwitch(state, permanent)
    ks.connection_status_update(connection_status)
    assert ks.state == state
    assert ks.permanent_mode == permanent
    assert ks.should_ks_be_enabled == should_ks_be_enabled


@pytest.mark.parametrize(
    "state, permanent, initial_should_ks_be_enabled, should_ks_be_enabled",
    [
        (KillSwitchStateEnum.OFF, False, False, False),
        (KillSwitchStateEnum.ON, False, None, True),
    ]
)
def test_permanet_mode_enable(modified_loader, state, permanent, initial_should_ks_be_enabled, should_ks_be_enabled):
    ks = DummyKillSwitch(state, permanent)
    _test_switch_permanent_mode(ks, ks.permanent_mode_enable, state, permanent, initial_should_ks_be_enabled, should_ks_be_enabled)


@pytest.mark.parametrize(
    "state, permanent, initial_should_ks_be_enabled, should_ks_be_enabled",
    [
        (KillSwitchStateEnum.ON, True, True, False),
    ]
)
def test_permanet_mode_disable(modified_loader, state, permanent, initial_should_ks_be_enabled, should_ks_be_enabled):
    ks = DummyKillSwitch(state, permanent)
    _test_switch_permanent_mode(ks, ks.permanent_mode_disable, state, permanent, initial_should_ks_be_enabled, should_ks_be_enabled)


def _test_switch_permanent_mode(ks, method, state, permanent, initial_should_ks_be_enabled, should_ks_be_enabled):
    method()
    assert ks.state == state
    assert ks.permanent_mode == (not permanent)
    assert ks.should_ks_be_enabled == should_ks_be_enabled


def test_get_priority(modified_loader):
    assert DummyKillSwitch._get_priority() is None


def test_get_validate(modified_loader):
    assert not DummyKillSwitch._validate()


def test_attempt_to_get_non_existing_backend():
    with pytest.raises(MissingKillSwitchBackendDetails):
        KillSwitch.get_from_factory("dummy-backend")
