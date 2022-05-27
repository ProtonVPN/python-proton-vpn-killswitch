from enum import IntEnum
from unittest.mock import patch

import pytest
from proton.vpn.connection import states
from proton.vpn.killswitch.interface import KillSwitch
from proton.vpn.killswitch.interface.enums import KillSwitchStateEnum
from proton.vpn.killswitch.interface.exceptions import \
    MissingKillSwitchBackendDetails


class RandomEnum(IntEnum):
    RANDOM = 1


class DummyKillSwitch(KillSwitch):
    def __init__(self, *args, **kwargs):
        self.reset_call_flags()
        super().__init__(*args, **kwargs)

    def _disable(self, **kwargs):
        self.disable_was_called = True

    def _enable(self, **kwargs):
        self.enable_was_called = True

    def _update(self, **kwargs):
        self.update_was_called = True

    def reset_call_flags(self):
        self.disable_was_called = False
        self.enable_was_called = False
        self.update_was_called = False


class NotImplementedEnable(KillSwitch):
    def _disable(self, **kwargs):
        pass

    def _update(self, **kwargs):
        pass


class NotImplementedDisable(KillSwitch):
    def _enable(self, **kwargs):
        pass

    def _update(self, **kwargs):
        pass


class NotImplementedUpdate(KillSwitch):
    def _enable(self, **kwargs):
        pass

    def _disable(self, **kwargs):
        pass


@pytest.fixture
def modified_loader():
    with patch("proton.vpn.killswitch.interface.killswitch.Loader") as dummy_loader:
        dummy_loader.get.return_value = DummyKillSwitch
        yield dummy_loader


def test_not_implemented_enable(modified_loader):
    with pytest.raises(NotImplementedError):
        NotImplementedEnable()._enable()


def test_not_implemented_disable(modified_loader):
    with pytest.raises(NotImplementedError):
        NotImplementedDisable()._disable()


def test_not_implemented_update(modified_loader):
    with pytest.raises(NotImplementedError):
        NotImplementedUpdate()._update()


def test_get_from_factory(modified_loader):
    ks = KillSwitch.get_from_factory()()
    assert ks.state == KillSwitchStateEnum.OFF


def test_get_from_factory_raises_exception_when_called_with_invalid_state(modified_loader):
    with pytest.raises(TypeError):
        KillSwitch.get_from_factory()(RandomEnum.RANDOM)


@pytest.mark.parametrize(
    "state, should_ks_be_enabled, should_ks_be_disabled",
    [
        (KillSwitchStateEnum.ON_NON_PERMANENT, False, False),
        (KillSwitchStateEnum.ON_PERMANENT, True,  False),
        (KillSwitchStateEnum.OFF, False, True),
    ]
)
def test_init_with_expected_args(modified_loader, state, should_ks_be_enabled, should_ks_be_disabled):
    ks = DummyKillSwitch(state)
    assert ks.state == state
    assert ks.enable_was_called == should_ks_be_enabled
    assert ks.disable_was_called == should_ks_be_disabled


def test_turn_on_permanently_enables_the_kill_switch_instantly():
    ks = DummyKillSwitch()
    ks.reset_call_flags()
    ks.turn_on_permanently()
    assert ks.enable_was_called
    assert not ks.disable_was_called
    assert not ks.update_was_called


def test_turn_on_not_permanently_does_not_enable_the_kill_switch_instantly():
    ks = DummyKillSwitch()
    ks.reset_call_flags()
    ks.turn_on_non_permanently()
    assert not ks.enable_was_called
    assert not ks.disable_was_called
    assert not ks.update_was_called


def test_off_disables_the_kill_switch():
    ks = DummyKillSwitch()
    ks.reset_call_flags()
    ks.turn_off()
    assert ks.disable_was_called
    assert not ks.enable_was_called
    assert not ks.update_was_called


@pytest.mark.parametrize(
    "state, connection_status, should_ks_be_enabled, should_ks_be_disabled, should_ks_be_updated",
    [
        (KillSwitchStateEnum.OFF, states.Disconnected(), False, False, False),
        (KillSwitchStateEnum.ON_NON_PERMANENT, states.Disconnected(), False, True, False),
        (KillSwitchStateEnum.ON_PERMANENT, states.Disconnected(), False, False, False),
    ]
)
def test_expected_connection_status_updates_on_disconnected(
    modified_loader, state, connection_status, should_ks_be_enabled, should_ks_be_disabled, should_ks_be_updated
):
    _test_on_connection_status_update(
        state, connection_status, should_ks_be_enabled, should_ks_be_disabled, should_ks_be_updated
    )


@pytest.mark.parametrize(
    "state, connection_status, should_ks_be_enabled, should_ks_be_disabled, should_ks_be_updated",
    [
        (KillSwitchStateEnum.OFF, states.Connecting(), False, False, False),
        (KillSwitchStateEnum.ON_NON_PERMANENT, states.Connecting(), True, False, False),
        (KillSwitchStateEnum.ON_PERMANENT, states.Connecting(), False, False, True),

    ]
)
def test_expected_connection_status_updates_on_connecting(
        modified_loader, state, connection_status, should_ks_be_enabled, should_ks_be_disabled, should_ks_be_updated
):
    _test_on_connection_status_update(
        state, connection_status, should_ks_be_enabled, should_ks_be_disabled, should_ks_be_updated
    )


def _test_on_connection_status_update(
    state, connection_status, should_ks_be_enabled, should_ks_be_disabled, should_ks_be_updated
):
    ks = DummyKillSwitch(state)
    ks.reset_call_flags()
    ks.connection_status_update(connection_status)
    assert ks.state == state
    assert ks.enable_was_called == should_ks_be_enabled
    assert ks.disable_was_called == should_ks_be_disabled
    assert ks.update_was_called == should_ks_be_updated


def test_get_priority(modified_loader):
    assert DummyKillSwitch._get_priority() is None


def test_get_validate(modified_loader):
    assert not DummyKillSwitch._validate()


def test_attempt_to_get_non_existing_backend():
    with pytest.raises(MissingKillSwitchBackendDetails):
        KillSwitch.get_from_factory("dummy-backend")
