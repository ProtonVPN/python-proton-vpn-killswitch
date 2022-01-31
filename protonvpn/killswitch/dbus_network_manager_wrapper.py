from enum import Enum
from dbus import exceptions as dbus_excp
from .dbus_wrapper import DbusWrapper

class SystemBusNMInterfaceEnum(Enum):
    NETWORK_MANAGER = "org.freedesktop.NetworkManager"
    NM_CONNECTION_SETTINGS = "org.freedesktop.NetworkManager.Settings.Connection"
    NM_SETTINGS = "org.freedesktop.NetworkManager.Settings"
    NM_CONNECTION_ACTIVE = "org.freedesktop.NetworkManager.Connection.Active"
    NM_DEVICE = "org.freedesktop.NetworkManager.Device"

class SystemBusNMObjectPathEnum(Enum):
    NETWORK_MANAGER = "/org/freedesktop/NetworkManager"
    NM_SETTINGS = "/org/freedesktop/NetworkManager/Settings"

class NetworkManagerUnitWrapper:
    BUS_NAME = "org.freedesktop.NetworkManager"

    def __init__(self, bus):
        self.__dbus_wrapper = DbusWrapper(bus)

    def search_for_connection(
        self, conn_name, interface_name=None, is_active=False,
        return_settings_path=False, return_device_path=False,
        return_active_conn_path=False,
    ):
        """Search for specified connection.

        Args:
            conn_name (string): connection/interface conn_name
            interface_name (string): (optional) Interface name.
            is_active (bool): check for active conns
            return_settings_path (bool): return settings path
            return_device_path (bool): return device path
            return_active_conn_path (bool): return active connection
            path. This returns only if is_active is also True.
        Returns:
           Dict: with specified content. Connection ID is returned always.
           To extract contents of dict, use the following keys:
            - connection_id
            - settings_path
            - device_path
            - active_conn_path
        """

        if is_active:
            connection_list = self.get_all_active_connections()
        else:
            connection_list = self.get_all_connections()

        for iterated_connection in connection_list:
            if is_active:
                conn_props = self.get_active_connection_properties(
                    iterated_connection
                )
                iterated_connection = conn_props["Connection"]

            all_connection_properties = self.get_settings_from_connection(
                iterated_connection
            )

            connection_id = str(all_connection_properties["connection"]["id"])

            dev_name = None
            if "vpn" in all_connection_properties:
                dev_name = all_connection_properties["vpn"].get("data")
                if dev_name:
                    dev_name = dev_name.get("dev")

            if (
                (
                    conn_name == connection_id
                ) or (
                    conn_name.lower() in connection_id.lower()
                    and interface_name != None
                    and interface_name == dev_name
                )
            ):
                return_dict = {"connection_id": connection_id}
                if return_settings_path:
                    return_dict["settings_path"] = iterated_connection
                if return_device_path:
                    return_dict["device_path"] = self.get_connection_device_path( # noqa
                        iterated_connection
                    )
                if return_active_conn_path and is_active:
                    return_dict["active_conn_path"] = self.get_active_connection( # noqa
                        get_by_settings_path=iterated_connection
                    )

                return return_dict

        return {}

    def get_connection_device_path(self, connection_settings_path):
        """Get path to connection device.

        Args:
            connection_settings_path (string): connection settings path

        Returns:
            string | None: either path to device if found
            or None if device was not found not.
        """

        devices = self._get_all_devices()
        for device in devices:
            device_available_conns = self._get_available_connections_from_device(device)
            if len(device_available_conns) > 0:
                conn_settings_path = str(device_available_conns.pop())
                if connection_settings_path == conn_settings_path:
                    return device

        return None

    def activate_connection(
        self, connection_settings_path, device_path, specific_object=None
    ):
        """Activate existing connection.

        Args:
            connection_settings_path (string): The connection to activate.
                If "/" is given, a valid device path must be given, and
                NetworkManager picks the best connection to activate for the
                given device. VPN connections must alwayspass a valid
                connection path.
            device_path (string): The object path of device to be activated
                for physical connections. This parameter is ignored for VPN
                connections, because the specific_object (if provided)
                specifies the device to use.
            specific_object (string): The path of a connection-type-specific
                object this activation should use. This parameter is currently
                ignored for wired and mobile broadband connections, and the
                value of "/" should be used (ie, no specific object). For
                Wi-Fi connections, pass the object path of a specific AP from
                the card's scan list, or "/" to pick an AP automatically.
                For VPN connections, pass the object path of an
                ActiveConnection object that should serve as the "base"
                connection (to which the VPN connections lifetime
                will be tied), or pass "/" and NM will automatically use
                the current default device.

        Returns:
            string | None: either path to active connection
            if connection was successfully activated
            or None if not.
        """

        nm_interface = self._get_network_manager_interface()
        active_conn_path = nm_interface.ActivateConnection(
            connection_settings_path,
            device_path,
            specific_object if specific_object else "/"
        )

        return None if not active_conn_path else active_conn_path

    def disconnect_connection(self, connection_path):
        """Disconnect active connection.

        Args:
            connection_path (string): path to active connection
        """
        nm_interface = self._get_network_manager_interface()
        nm_interface.DeactivateConnection(connection_path)

    def delete_connection(self, connection_settings_path):
        """Disconnect active connection.

        Args:
            connection_path (string): path to active connection
        """

        connection_settings_interface = self._get_connection_settings_interface(
            connection_settings_path
        )
        connection_settings_interface.Delete()

    def check_active_vpn_connection(self, active_conn):
        """Check if active connection is VPN.

        Args:
            active_conn (string): active connection path

        Returns:
            [0]: bool
            [1]: None | dict with all connection settings
        """

        active_conn_all_settings = [False, None]

        if active_conn is None or len(active_conn) < 1:
            return active_conn_all_settings

        try:
            active_conn_props = self.get_active_connection_properties(active_conn)
        except dbus_excp.DBusException as e:
            raise
        else:
            if (
                active_conn_props["Type"] == "vpn"
            ) and (
                # NMActiveConnectionState
                # State 1 = a network connection is being prepared
                # State 2 = there is a connection to the network
                active_conn_props["State"] == 2
            ):
                active_conn_all_settings[0] = True
                active_conn_all_settings[1] = self.get_settings_from_connection(
                    active_conn_props["Connection"]
                )
        return active_conn_all_settings


    def get_active_connection(
        self, get_by_id=None,
        get_by_settings_path=False, get_by_device_path=False
    ):
        """Get interface of active
        connection with default route(s) if no options
        were specified. Else returns active connection
        for the specified option.
        All options are mutually exclusive.

        Args:
            get_by_id (string): connection id
            get_by_settings_path (string): connection settings path
            get_by_device_path (string): connection device path

        Returns:
            string: active connection path
        """

        active_connections = self.get_all_active_connections()

        for active_conn in active_connections:
            try:
                active_conn_props = self.get_active_connection_properties(active_conn)
            except TypeError as e:
                return None
            except dbus_excp.DBusException as e:
                continue

            if get_by_id and str(active_conn_props["Id"]) == get_by_id:
                return active_conn
            elif get_by_settings_path and str(active_conn_props["Connection"]) == get_by_settings_path: # noqa
                return active_conn
            elif get_by_device_path and str(active_conn_props["Devices"].pop()) == get_by_device_path: # noqa
                return active_conn
            elif (
                active_conn_props["Default"]
            ) or (
                active_conn_props["Default"] and active_conn_props["Default6"]
            ):
                return active_conn

        return None

    def _get_connection_settings_interface(self, connection_object):
        iface = self.__dbus_wrapper.get_proxy_object_interface(
            self.__get_proxy_object(connection_object),
            SystemBusNMInterfaceEnum.NM_CONNECTION_SETTINGS.value
        )
        return iface

    def get_active_connection_properties(self, active_conn):
        """Get active connection properties.

        Args:
            active_conn (string): active connection path

        Returns:
            dict: properties of an active connection
        """

        iface = self.__dbus_wrapper.get_proxy_object_properties_interface(
            self.__get_proxy_object(active_conn)
        )
        return iface.GetAll(
            SystemBusNMInterfaceEnum.NM_CONNECTION_ACTIVE.value
        )

    def get_settings_from_connection(self, connection_path):
        """Get all settings of a connection.

        Args:
            conn (string): connection path
            return_iface (bool): also return the interface

        Returns:
            dict | interface:
                dict: only properties are returned
                tuple: dict with properties is returned
                    and also the interface to the connection
        """

        iface = self._get_connection_settings_interface(connection_path)
        return iface.GetSettings()

    def get_all_connections(self):
        """Get all existing connections.

        Returns:
            list(string): yields path to all connections
        """

        iface = self.__dbus_wrapper.get_proxy_object_interface(
            self.__get_proxy_object(SystemBusNMObjectPathEnum.NM_SETTINGS.value),
            SystemBusNMInterfaceEnum.NM_SETTINGS.value
        )
        all_conns = iface.ListConnections()
        for conn in all_conns:
            yield conn

    def get_all_active_connections(self):
        """Get all active connections.

        Returns:
            list(string): yields path to active connections
        """

        iface = self.__dbus_wrapper.get_proxy_object_properties_interface(
            self.__get_proxy_object(SystemBusNMObjectPathEnum.NETWORK_MANAGER.value)
        )

        all_active_conns_list = iface.Get(
            SystemBusNMInterfaceEnum.NETWORK_MANAGER.value,
            "ActiveConnections"
        )
        for active_conn in all_active_conns_list:
            yield active_conn

    def get_network_manager_properties(self,):
        """Get all network manager properties.

        Returns:
            Dict: contains all network manager properties
        """

        nm_interface = self.__dbus_wrapper.get_proxy_object_properties_interface(
            self.get_network_manager_proxy_object()
        )

        nm_properties = nm_interface.GetAll(
            SystemBusNMInterfaceEnum.NETWORK_MANAGER.value
        )

        return nm_properties

    def get_network_manager_properties_interface(self):

        nm_interface = self.__dbus_wrapper.get_proxy_object_properties_interface(
            self.get_network_manager_proxy_object()
        )

        return nm_interface

    def connect_network_manager_object_to_signal(self, signal_name, method):
        """Connect a signal to network manager object.

        Args:
            signal_name (string): the name of the signal to listen to
            method (func): the method that received the signal
        """

        interface = self._get_network_manager_interface()
        interface.connect_to_signal(
            signal_name, method
        )

    def _get_network_manager_interface(self):
        """Get network manager interface.

        Returns:
            dbus.proxies.Interface: network manager interface
        """

        return self.__dbus_wrapper.get_proxy_object_interface(
            self.get_network_manager_proxy_object(),
            SystemBusNMInterfaceEnum.NETWORK_MANAGER.value
        )

    def get_network_manager_proxy_object(self):
        """Get /org/freedesktop/NetworkManager proxy object.

        Returns:
            dbus.proxies.ProxyObject: network manager proxy object
        """

        return self.__get_proxy_object(SystemBusNMObjectPathEnum.NETWORK_MANAGER.value)

    def _get_all_devices(self):

        nm_interface = self.__dbus_wrapper.get_proxy_object_properties_interface(
            self.get_network_manager_proxy_object()
        )
        nm_properties = nm_interface.GetAll(
            SystemBusNMInterfaceEnum.NETWORK_MANAGER.value
        )

        return nm_properties["AllDevices"]

    def _get_available_connections_from_device(self, device):

        device_props_interface = self.__dbus_wrapper.get_proxy_object_properties_interface(
            self.__get_proxy_object(device)
        )
        devices_props = device_props_interface.GetAll(
            SystemBusNMInterfaceEnum.NM_DEVICE.value
        )
        return devices_props.get("AvailableConnections", [])

    def __get_proxy_object(self, path_to_object):
        return self.__dbus_wrapper.get_proxy_object(
            self.BUS_NAME,
            path_to_object
        )
