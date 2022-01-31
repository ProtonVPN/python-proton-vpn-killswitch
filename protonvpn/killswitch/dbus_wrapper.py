import dbus


class DbusWrapper:
    def __init__(self, bus):
        self.bus = bus

    def get_proxy_object_properties_interface(self, proxy_object):
        """Get org.freedesktop.DBus.Properties of proxy object.

        Args:
            proxy_object (dbus.proxies.ProxyObject)

        Returns:
            dbus.proxies.Interface: properties interface
        """
        return dbus.Interface(
            proxy_object,
            "org.freedesktop.DBus.Properties"
        )

    def get_proxy_object_interface(self, proxy_object, interface):
        """Get interface of proxy object.

        Args:
            proxy_object (dbus.proxies.ProxyObject)
            interface (string): interface name/path

        Returns:
            dbus.proxies.Interface: properties interface
        """
        
        return dbus.Interface(
            proxy_object,
            interface
        )

    def get_proxy_object(self, bus_name, object_path):
        """Get proxy object from bus name and object path.

        Args:
            bus_name (str): bus name (ie org.freedesktop.NetworkManager)
            object_path (str): path to object (ie /org/freedesktop/NetowrkManager)

        Returns:
            dbus.proxies.ProxyObject

        Usage:
            NetworkManager Proxy Object:
            - get_proxy_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetowrkManager")

            Login1 Proxy Object:
            - get_proxy_object("org.freedesktop.login1", "/org/freedesktop/login1")
        """
        
        return self.bus.get_object(
            bus_name, object_path
        )
