"""
Pytest fixtures for Mycorrhizae protocol tests.
"""

import pytest

pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def mdp_encoder():
    """MDP v1 encoder fixture."""
    from mycorrhizae.protocols.mdp_v1 import MDPv1Encoder
    from mycorrhizae.protocols.mdp_types import MDPEndpoint

    return MDPv1Encoder(src=MDPEndpoint.SIDE_A, dst=MDPEndpoint.GATEWAY)


@pytest.fixture
def mdp_decoder():
    """MDP v1 decoder fixture."""
    from mycorrhizae.protocols.mdp_v1 import MDPv1Decoder

    return MDPv1Decoder(validate_crc=True)


@pytest.fixture
def mmp_encoder():
    """MMP v1 encoder fixture."""
    from mycorrhizae.protocols.mmp_v1 import MMPv1Encoder
    from mycorrhizae.protocols.mmp_types import MMPDeviceType

    return MMPv1Encoder(device_id=0x1234, device_type=MMPDeviceType.MYCOBRAIN)


@pytest.fixture
def mmp_decoder():
    """MMP v1 decoder fixture."""
    from mycorrhizae.protocols.mmp_v1 import MMPv1Decoder

    return MMPv1Decoder(validate_trailer=True)


@pytest.fixture
def device_gateway():
    """DeviceGateway without broker (for unit tests)."""
    from mycorrhizae.gateway.device_gateway import DeviceGateway

    return DeviceGateway(broker=None)
