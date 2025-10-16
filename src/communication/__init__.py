"""
Communication package - Message passing and failure detection
"""

from .message_passing import MessagePasser, Message, MessageType
from .failure_detector import FailureDetector, NodeStatus

__all__ = ['MessagePasser', 'Message', 'MessageType', 'FailureDetector', 'NodeStatus']
