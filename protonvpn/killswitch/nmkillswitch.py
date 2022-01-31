from ipaddress import ip_network

import dbus
from dbus.mainloop.glib import DBusGMainLoop

from .exceptions import DeleteKillswitchError, KillswitchError, CreateBlockingKillswitchError, CreateRoutedKillswitchError, ActivateKillswitchError, DectivateKillswitchError, AvailableConnectivityCheckError, DisableConnectivityCheckError
from .constants import (KILLSWITCH_CONN_NAME, KILLSWITCH_INTERFACE_NAME,
                          ROUTED_CONN_NAME, ROUTED_INTERFACE_NAME,
                          IPv4_DUMMY_ADDRESS, IPv4_DUMMY_GATEWAY,
                          IPv6_DUMMY_ADDRESS, IPv6_DUMMY_GATEWAY, KILLSWITCH_DNS_PRIORITY_VALUE)
from .constants import (KillSwitchActionEnum, KillSwitchInterfaceTrackerEnum,
                      KillswitchStatusEnum)
from .dbus_network_manager_wrapper import NetworkManagerUnitWrapper
from .subprocess_wrapper import subprocess


class NMKillSwitch:
    # Additional loop needs to be create since SystemBus automatically
    # picks the default loop, which is intialized with the CLI.
    # Thus, to refrain SystemBus from using the default loop,
    # one extra loop is needed only to be passed, while it is never used.
    # https://dbus.freedesktop.org/doc/dbus-python/tutorial.html#setting-up-an-event-loop
    _dbus_loop = DBusGMainLoop()
    _bus = dbus.SystemBus(mainloop=_dbus_loop)

    """Manages killswitch connection/interfaces."""
    def __init__(
        self,
        nm_wrapper=NetworkManagerUnitWrapper,
        ks_conn_name=KILLSWITCH_CONN_NAME,
        ks_interface_name=KILLSWITCH_INTERFACE_NAME,
        routed_conn_name=ROUTED_CONN_NAME,
        routed_interface_name=ROUTED_INTERFACE_NAME,
        ipv4_dummy_addrs=IPv4_DUMMY_ADDRESS,
        ipv4_dummy_gateway=IPv4_DUMMY_GATEWAY,
        ipv6_dummy_addrs=IPv6_DUMMY_ADDRESS,
        ipv6_dummy_gateway=IPv6_DUMMY_GATEWAY,
    ):
        self._ks_conn_name = ks_conn_name
        self._ks_interface_name = ks_interface_name
        self._routed_conn_name = routed_conn_name
        self._routed_interface_name = routed_interface_name
        self._ipv4_dummy_addrs = ipv4_dummy_addrs
        self._ipv4_dummy_gateway = ipv4_dummy_gateway
        self._ipv6_dummy_addrs = ipv6_dummy_addrs
        self._ipv6_dummy_gateway = ipv6_dummy_gateway
        self._nm_wrapper = nm_wrapper(self._bus)
        self._interface_state_tracker = {
            self._ks_conn_name: {
                KillSwitchInterfaceTrackerEnum.EXISTS: False,
                KillSwitchInterfaceTrackerEnum.IS_RUNNING: False
            },
            self._routed_conn_name: {
                KillSwitchInterfaceTrackerEnum.EXISTS: False,
                KillSwitchInterfaceTrackerEnum.IS_RUNNING: False
            }
        }

        self._get_status_connectivity_check()

    def _manage(self, action, server_ip=None):
        """Manage killswitch.

        Args:
            action (string|int): either pre_connection or post_connection
            server_ip (string): server ip to be connected to
        """

        self._ensure_connectivity_check_is_disabled()
        self._update_connection_status()

        actions_dict = {
            KillSwitchActionEnum.PRE_CONNECTION: self._setup_pre_connection_ks,
            KillSwitchActionEnum.POST_CONNECTION: self._setup_post_connection_ks,
            KillSwitchActionEnum.SOFT: self._setup_soft_connection,
            KillSwitchActionEnum.DISABLE: self._disable_killswitch,

        }[action](server_ip)

    def is_active(self)-> bool:
        """ Return the status of killswitch : enabled or disabled.
        """
        if self._interface_state_tracker[self._ks_conn_name][KillSwitchInterfaceTrackerEnum.EXISTS]:
           if self._interface_state_tracker[self._ks_conn_name][KillSwitchInterfaceTrackerEnum.IS_RUNNING]:
               return True
        return False

    def enable(self, permanent=False) -> None:
        """ Enable killswitch : if permanent, need to disable/enable it again if VPN is down.
        """
        if permanent:
            self._ensure_connectivity_check_is_disabled()
            self._update_connection_status()

            try:
                self._delete_connection(self._routed_conn_name)
            except: # noqa
                pass

            if not self._interface_state_tracker[self._ks_conn_name][
                KillSwitchInterfaceTrackerEnum.EXISTS
            ]:
                self._create_killswitch_connection()
                return
            else:
                self._activate_connection(self._ks_conn_name)
        else:
            self._setup_soft_connection()

    def disable(self) -> None:
        """ Disable killswitch
        """
        self._ensure_connectivity_check_is_disabled()
        self._update_connection_status()
        self._disable_killswitch()

    def _setup_pre_connection_ks(self, server_ip, pre_attempts=0) -> None:
        """Assure Kill Switch is setup correctly before VPN Connection is
           established.

        Args:
            server_ip (list | string): ProtonVPN server IP
            pre_attempts (int): number of setup attempts
        """
        self._update_connection_status()

        if pre_attempts >= 5:
            raise KillswitchError(
                "Unable to setup pre-connection ks. "
                "Exceeded maximum attempts."
            )

        # happy path
        if (
            self._interface_state_tracker[self._ks_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
            and not self._interface_state_tracker[self._routed_conn_name][
                KillSwitchInterfaceTrackerEnum.EXISTS
            ]
        ):
            self._create_routed_connection(server_ip)
            self._deactivate_connection(self._ks_conn_name)
            return
        elif (
            not self._interface_state_tracker[self._ks_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
            and self._interface_state_tracker[self._routed_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
        ):
            return

        # check for routed ks and remove if present/running
        if (
            self._interface_state_tracker[self._routed_conn_name][
                KillSwitchInterfaceTrackerEnum.EXISTS
            ]
            and self._interface_state_tracker[self._routed_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
        ):
            self._delete_connection(self._routed_conn_name)

        # check if ks exists. Start it if it does
        # if not then create and start it
        if (
            self._interface_state_tracker[
                self._ks_conn_name
            ][KillSwitchInterfaceTrackerEnum.EXISTS]
        ):
            self._activate_connection(self._ks_conn_name)
        else:
            self._create_killswitch_connection()

        pre_attempts += 1
        self._setup_pre_connection_ks(server_ip, pre_attempts=pre_attempts)

    def _setup_post_connection_ks(
        self, _, post_attempts=0, activating_soft_connection=False
    ) -> None:
        """Assure Kill Switch is setup correctly after VPN has been connected

        Args:
            post_attempts (int): number of setup attempts
        """
        self._update_connection_status()

        if post_attempts >= 5:
            raise KillswitchError(
                "Unable to setup post-connection ks. "
                "Exceeded maximum attempts."
            )

        # happy path
        if (
            not self._interface_state_tracker[self._ks_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
            and self._interface_state_tracker[self._routed_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
        ):
            self._activate_connection(self._ks_conn_name)
            self._delete_connection(self._routed_conn_name)

            return
        elif (
            activating_soft_connection
            and (
                not self._interface_state_tracker[self._routed_conn_name][
                    KillSwitchInterfaceTrackerEnum.IS_RUNNING
                ] or not self._interface_state_tracker[self._routed_conn_name][
                    KillSwitchInterfaceTrackerEnum.EXISTS
                ]
            )
        ):
            self._activate_connection(self._ks_conn_name)
            return
        elif (
            self._interface_state_tracker[self._ks_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ] and (
                not self._interface_state_tracker[self._routed_conn_name][
                    KillSwitchInterfaceTrackerEnum.EXISTS
                ] or not self._interface_state_tracker[self._routed_conn_name][
                    KillSwitchInterfaceTrackerEnum.IS_RUNNING
                ]
            )
        ):
            return

        # check for ks and disable it if is running
        if (
            self._interface_state_tracker[self._ks_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
        ):
            self._deactivate_connection(self._ks_conn_name)

        # check if routed ks exists, if so then activate it
        # else raise exception
        if (
            self._interface_state_tracker[self._routed_conn_name][KillSwitchInterfaceTrackerEnum.EXISTS] # noqa
        ):
            self._activate_connection(self._routed_conn_name)
        else:
            raise Exception("Routed connection does not exist")

        post_attempts += 1
        self._setup_post_connection_ks(
            _, post_attempts=post_attempts,
            activating_soft_connection=activating_soft_connection
        )

    def _setup_soft_connection(self) -> None:
        """Setup Kill Switch for --on setting."""
        self._create_killswitch_connection()
        self._setup_post_connection_ks(None, activating_soft_connection=True)

    def _create_killswitch_connection(self):
        """Create killswitch connection/interface."""
        subprocess_command = [
            "nmcli", "c", "a", "type", "dummy",
            "ifname", self._ks_interface_name,
            "con-name", self._ks_conn_name,
            "ipv4.method", "manual",
            "ipv4.addresses", self._ipv4_dummy_addrs,
            "ipv4.gateway", self._ipv4_dummy_gateway,
            "ipv6.method", "manual",
            "ipv6.addresses", self._ipv6_dummy_addrs,
            "ipv6.gateway", self._ipv6_dummy_gateway,
            "ipv4.route-metric", "98",
            "ipv6.route-metric", "98",
            "ipv4.dns-priority", KILLSWITCH_DNS_PRIORITY_VALUE,
            "ipv6.dns-priority", KILLSWITCH_DNS_PRIORITY_VALUE,
            "ipv4.ignore-auto-dns", "yes",
            "ipv6.ignore-auto-dns", "yes",
            "ipv4.dns", "0.0.0.0",
            "ipv6.dns", "::1"
        ]
        self._update_connection_status()
        if not self._interface_state_tracker[self._ks_conn_name][
            KillSwitchInterfaceTrackerEnum.EXISTS
        ]:
            self._create_connection(
                self._ks_conn_name,
                "Unable to activate {}".format(self._ks_conn_name),
                subprocess_command, CreateBlockingKillswitchError
            )

    def _create_routed_connection(self, server_ip, try_route_addrs=False):
        """Create routed connection/interface.

        Args:
            server_ip (list(string)): the IP of the server to be connected
        """
        if isinstance(server_ip, list):
            server_ip = server_ip.pop()

        subnet_list = list(ip_network('0.0.0.0/0').address_exclude(
            ip_network(server_ip)
        ))

        route_data = [str(ipv4) for ipv4 in subnet_list]
        route_data_str = ",".join(route_data)

        subprocess_command = [
            "nmcli", "c", "a", "type", "dummy",
            "ifname", self._routed_interface_name,
            "con-name", self._routed_conn_name,
            "ipv4.method", "manual",
            "ipv4.addresses", self._ipv4_dummy_addrs,
            "ipv6.method", "manual",
            "ipv6.addresses", self._ipv6_dummy_addrs,
            "ipv6.gateway", self._ipv6_dummy_gateway,
            "ipv4.route-metric", "97",
            "ipv6.route-metric", "97",
            "ipv4.routes", route_data_str,
            "ipv4.dns-priority", KILLSWITCH_DNS_PRIORITY_VALUE,
            "ipv6.dns-priority", KILLSWITCH_DNS_PRIORITY_VALUE,
            "ipv4.ignore-auto-dns", "yes",
            "ipv6.ignore-auto-dns", "yes",
            "ipv4.dns", "0.0.0.0",
            "ipv6.dns", "::1"
        ]

        if try_route_addrs:
            subprocess_command = [
                "nmcli", "c", "a", "type", "dummy",
                "ifname", self._routed_interface_name,
                "con-name", self._routed_conn_name,
                "ipv4.method", "manual",
                "ipv4.addresses", route_data_str,
                "ipv6.method", "manual",
                "ipv6.addresses", self._ipv6_dummy_addrs,
                "ipv6.gateway", self._ipv6_dummy_gateway,
                "ipv4.route-metric", "97",
                "ipv6.route-metric", "97",
                "ipv4.dns-priority", KILLSWITCH_DNS_PRIORITY_VALUE,
                "ipv6.dns-priority", KILLSWITCH_DNS_PRIORITY_VALUE,
                "ipv4.ignore-auto-dns", "yes",
                "ipv6.ignore-auto-dns", "yes",
                "ipv4.dns", "0.0.0.0",
                "ipv6.dns", "::1"
            ]

        exception_msg = "Unable to activate {}".format(self._routed_conn_name)

        try:
            self._create_connection(
                self._routed_conn_name, exception_msg,
                subprocess_command, CreateRoutedKillswitchError
            )
        except CreateRoutedKillswitchError as e:
            if e.additional_context.returncode == 2 and not try_route_addrs:
                return self._create_routed_connection(server_ip, True)
            else:
                raise CreateRoutedKillswitchError(exception_msg)

    def _create_connection(
        self, conn_name, exception_msg,
        subprocess_command, exception
    ):
        self._update_connection_status()
        if not self._interface_state_tracker[conn_name][
            KillSwitchInterfaceTrackerEnum.EXISTS
        ]:
            self._run_subprocess(
                exception,
                exception_msg,
                subprocess_command
            )

    def _activate_connection(self, conn_name):
        """Activate a connection based on connection name.

        Args:
            conn_name (string): connection name (uid)
        """
        self._update_connection_status()
        conn_dict = self._nm_wrapper.search_for_connection( # noqa
            conn_name,
            return_device_path=True,
            return_settings_path=True
        )
        if (
            self._interface_state_tracker[conn_name][
                KillSwitchInterfaceTrackerEnum.EXISTS
            ]
        ) and (
            not self._interface_state_tracker[conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
        ) and conn_dict:
            device_path = str(conn_dict.get("device_path"))
            settings_path = str(conn_dict.get("settings_path"))

            try:
                active_conn = self._nm_wrapper._activate_connection(
                    settings_path, device_path
                )
            except dbus.exceptions.DBusException as e:
                raise ActivateKillswitchError(
                    "Unable to activate {}".format(conn_name)
                )
            else:
                if active_conn:
                    return
                raise ActivateKillswitchError(
                    "Unable to activate {}".format(conn_name)
                )

    def _deactivate_connection(self, conn_name):
        """Deactivate a connection based on connection name.

        Args:
            conn_name (string): connection name (uid)
        """
        self._update_connection_status()
        active_conn_dict = self._nm_wrapper.search_for_connection( # noqa
            conn_name, is_active=True,
            return_active_conn_path=True
        )
        if (
            self._interface_state_tracker[conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ] and active_conn_dict
        ):
            active_conn_path = str(active_conn_dict.get("active_conn_path"))
            try:
                self._nm_wrapper.disconnect_connection(
                    active_conn_path
                )
            except dbus.exceptions.DBusException as e:
                raise DectivateKillswitchError(
                    "Unable to deactivate {}".format(conn_name)
                )

    def _delete_connection(self, conn_name):
        """Delete a connection based on connection name.

        If it fails to delete the connection, it will attempt to deactivate it.

        Args:
            conn_name (string): connection name (uid)
        """
        subprocess_command = ""\
            "nmcli c delete {}".format(conn_name).split(" ")

        self._update_connection_status()
        if self._interface_state_tracker[conn_name][KillSwitchInterfaceTrackerEnum.EXISTS]: # noqa
            self._run_subprocess(
                DeleteKillswitchError,
                "Unable to delete {}".format(conn_name),
                subprocess_command
            )

    def _deactivate_all_connections(self):
        """Deactivate all connections."""
        self._deactivate_connection(self._ks_conn_name)
        self._deactivate_connection(self._routed_conn_name)

    def _disable_killswitch(self, _=None):
        """Disable killswitch by deleting all NM connections related to it."""
        self._delete_connection(self._ks_conn_name)
        self._delete_connection(self._routed_conn_name)

    def _update_connection_status(self):
        """Update connection/interface status."""
        all_conns = self._nm_wrapper.get_all_connections()
        active_conns = self._nm_wrapper.get_all_active_connections()
        self._interface_state_tracker[self._ks_conn_name][KillSwitchInterfaceTrackerEnum.EXISTS] = False # noqa
        self._interface_state_tracker[self._routed_conn_name][KillSwitchInterfaceTrackerEnum.EXISTS] = False  # noqa
        self._interface_state_tracker[self._ks_conn_name][KillSwitchInterfaceTrackerEnum.IS_RUNNING] = False # noqa
        self._interface_state_tracker[self._routed_conn_name][KillSwitchInterfaceTrackerEnum.IS_RUNNING] = False  # noqa

        for conn in all_conns:
            try:
                conn_name = str(self._nm_wrapper.get_settings_from_connection(
                    conn
                )["connection"]["id"])
            except dbus.exceptions.DBusException:
                conn_name = "None"

            if conn_name in self._interface_state_tracker:
                self._interface_state_tracker[conn_name][
                    KillSwitchInterfaceTrackerEnum.EXISTS
                ] = True

        for active_conn in active_conns:
            try:
                conn_name = str(self._nm_wrapper.get_active_connection_properties(
                    active_conn
                )["Id"])
            except dbus.exceptions.DBusException:
                conn_name = "None"

            if conn_name in self._interface_state_tracker:
                self._interface_state_tracker[conn_name][
                    KillSwitchInterfaceTrackerEnum.IS_RUNNING
                ] = True

    def _run_subprocess(self, exception, exception_msg, *args):
        """Run provided input via subprocess.

        Args:
            exception (exceptions.KillswitchError): exception based on action
            exception_msg (string): exception message
            *args (list): arguments to be passed to subprocess
        """
        subprocess_outpout = subprocess.run(
            *args, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )

        if (
            subprocess_outpout.returncode != 0
            and subprocess_outpout.returncode != 10
        ):
            raise exception(
                exception_msg,
                subprocess_outpout
            )

    def _ensure_connectivity_check_is_disabled(self):
        conn_check = self._connectivity_check()

        if len(conn_check) > 0:
            self._disable_connectivity_check(
                conn_check[0], conn_check[1]
            )

    def _connectivity_check(self):
        (
            is_conn_check_available,
            is_conn_check_enabled,
        ) = self._get_status_connectivity_check()

        if not is_conn_check_enabled:
            return tuple()

        if not is_conn_check_available:
            raise AvailableConnectivityCheckError(
                "Unable to change connectivity check for killswitch"
            )

        return is_conn_check_available, is_conn_check_enabled

    def _get_status_connectivity_check(self):
        """Check status of NM connectivity check."""
        nm_props = self._nm_wrapper.get_network_manager_properties()
        is_conn_check_available = nm_props["ConnectivityCheckAvailable"]
        is_conn_check_enabled = nm_props["ConnectivityCheckEnabled"]

        return is_conn_check_available, is_conn_check_enabled

    def _disable_connectivity_check(
        self, is_conn_check_available, is_conn_check_enabled
    ):
        """Disable NetworkManager connectivity check."""
        if is_conn_check_enabled:
            nm_methods = self._nm_wrapper.get_network_manager_properties_interface()
            nm_methods.Set(
                "org.freedesktop.NetworkManager",
                "ConnectivityCheckEnabled",
                False
            )
            nm_props = self._nm_wrapper.get_network_manager_properties()
            if nm_props["ConnectivityCheckEnabled"]:
                raise DisableConnectivityCheckError(
                    "Can not disable connectivity check for killswitch"
                )