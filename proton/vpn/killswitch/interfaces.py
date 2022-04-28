
class VPNServer:
    """
    A VPN server is needed to be able to get the neccessary data about the server.

    Usage:

    .. code-block::

        from proton.vpn.killswitch.interfaces import VPNServer

        class MyVPNServer(VPNServer):

            @property
            def server_ip(self):
                return "187.135.1.53"
    """

    @property
    def server_ip(self) -> "str":
        """
        :return: server ip to connect to
        :rtype: str
        """
        raise NotImplementedError


class Settings:
    """Optional.

    If you would like to pass some specific settings for KillSwitch
    configuration then you should derive from this class and override its methods.

    Usage:

    .. code-block::

        from proton.vpn.killswitch.interfaces import Settings

        class KillSwitchSettings(Settings):
            @property
            def split_tunneling_ipv4_ips(self):
                return ["182.24.1.3", "89.1.32.1"]

            @property
            def split_tunneling_ipv6_ips(self):
                return ["182.24.1.3", "89.1.32.1"]

            @property
            def block_ipv6(self):
                return False

    Note: Not all fields are mandatory to override, only those that are actually needed, ie:

    .. code-block::

        from proton.vpn.killswitch.interfaces import Settings

        class VPNSettings(Settings):

            @property
            def block_ipv6(self):
                return True

    Passing only this is perfectly fine, because rest of the methods will be
    inherited from base class which have default values.
    """

    @property
    def split_tunneling_ipv4_ips(self) -> "List[str]":
        """Optional.

        :return: a list with IPv4 IPs to exclude from VPN tunnel
        :rtype: List[str]
        """
        return []

    @property
    def split_tunneling_ipv6_ips(self) -> "List[str]":
        """Optional.

        :return: a list with IPv6 IPs to exclude from VPN tunnel
        :rtype: List[str]
        """
        return []

    @property
    def block_ipv6(self) -> "bool":
        """Optional.

        :return: if ipv6 traffic should be blocked to prevent leaks
        :rtype: bool
        """
        return True
