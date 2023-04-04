from enum import IntEnum
from unittest.mock import patch, Mock

import pytest
from proton.vpn.killswitch.interface import KillSwitch
from proton.vpn.killswitch.interface.exceptions import \
    MissingKillSwitchBackendDetails


MOCK_KILLSWITCH_BACKEND = Mock()


def test_raises_exception_when_enable_is_not_implemented():
    with pytest.raises(NotImplementedError):
        KillSwitch().enable(Mock())


def test_raises_exception_when_disable_is_not_implemented():
    with pytest.raises(NotImplementedError):
        KillSwitch().disable()


def test_raises_exception_when_update_is_not_implemented():
    with pytest.raises(NotImplementedError):
        KillSwitch().update(Mock())


def test_raises_exception_when_enable_ipv6_leak_protection_is_not_implemented():
    with pytest.raises(NotImplementedError):
        KillSwitch().enable_ipv6_leak_protection()


def test_raises_exception_when_not_backend_can_be_found():
    with pytest.raises(MissingKillSwitchBackendDetails):
        KillSwitch.get(class_name="dummy-backend")


def test_raises_exception_when_disable_ipv6_leak_protection_is_not_implemented():
    with pytest.raises(NotImplementedError):
        KillSwitch().disable_ipv6_leak_protection()


@patch("proton.vpn.killswitch.interface.killswitch.Loader")
def test_get_backend_killswitch(mock_loader):
    mock_loader.get.return_value = MOCK_KILLSWITCH_BACKEND
    assert KillSwitch.get() == MOCK_KILLSWITCH_BACKEND


def test_get_priority_raises_exception_when_not_implemented():
    with pytest.raises(NotImplementedError):
        KillSwitch._get_priority() == None


def test_validate_raises_exception_when_not_implemented():
    with pytest.raises(NotImplementedError):
        KillSwitch._validate()

