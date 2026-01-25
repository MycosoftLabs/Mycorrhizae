"""
Mycorrhizae Protocol - Data Protocol for Nature

A pub/sub messaging protocol for routing biological sensor data
through the Mycosoft ecosystem (MINDEX, MAS, NatureOS, MycoBrain).
"""

__version__ = "1.0.0"

from .message import MycorrhizaeMessage, MessageType, SourceType
from .protocol import MycorrhizaeProtocol
from .channels import Channel, ChannelType, ChannelManager

__all__ = [
    "MycorrhizaeMessage",
    "MessageType",
    "SourceType",
    "MycorrhizaeProtocol",
    "Channel",
    "ChannelType",
    "ChannelManager",
]
