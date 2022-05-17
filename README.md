# ProtonVPN kill Switch

The `proton-vpn-killswitch` component defines the [VPN kill switch](https://protonvpn.com/secure-vpn/kill-switch) 
interface.

Other components, like `proton-vpn-killswitch-network-manager` provide concrete implementations for this interface.

## Development

Even though our CI pipelines always test and build releases using Linux distribution packages,
you can use pip to setup your development environment as follows:

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

You might also need to set up our internal package registry.
[Here](https://gitlab.protontech.ch/help/user/packages/pypi_repository/index.md#authenticate-to-access-packages-within-a-group)
you have the documentation on how to do that.

### Tests

You can run the tests with:

```shell
pytest
```
