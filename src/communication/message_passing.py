"""
Message Passing Implementation
Reliable message passing dengan retry dan acknowledgment
"""

import asyncio
import logging
import json
import time
from typing import Dict, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
import aiohttp

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Tipe pesan dalam sistem"""
    REQUEST = "request"
    RESPONSE = "response"
    HEARTBEAT = "heartbeat"
    ELECTION = "election"
    LOCK = "lock"
    QUEUE = "queue"
    CACHE = "cache"


@dataclass
class Message:
    """Struktur pesan"""
    message_id: str
    message_type: MessageType
    sender_id: str
    receiver_id: str
    data: dict
    timestamp: float
    requires_ack: bool = True
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps({
            'message_id': self.message_id,
            'message_type': self.message_type.value,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'data': self.data,
            'timestamp': self.timestamp,
            'requires_ack': self.requires_ack
        })
    
    @classmethod
    def from_json(cls, json_str: str):
        """Create from JSON"""
        data = json.loads(json_str)
        return cls(
            message_id=data['message_id'],
            message_type=MessageType(data['message_type']),
            sender_id=data['sender_id'],
            receiver_id=data['receiver_id'],
            data=data['data'],
            timestamp=data['timestamp'],
            requires_ack=data.get('requires_ack', True)
        )


class MessagePasser:
    """
    Reliable Message Passing dengan retry mechanism
    Memastikan message delivery dengan acknowledgment
    """
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        
        # Message tracking
        self.sent_messages: Dict[str, Message] = {}
        self.received_messages: Dict[str, Message] = {}
        self.pending_acks: Dict[str, asyncio.Event] = {}
        
        # Callbacks
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # Configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        self.ack_timeout = 5.0
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.messages_failed = 0
        
        logger.info(f"MessagePasser initialized for node {node_id}")
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """
        Register message handler
        
        Args:
            message_type: Type of message to handle
            handler: Async function to handle message
        """
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for {message_type.value}")
    
    async def send_message(self, receiver_id: str, message_type: MessageType,
                          data: dict, requires_ack: bool = True) -> bool:
        """
        Send message to another node with retry
        
        Args:
            receiver_id: Target node ID
            message_type: Type of message
            data: Message data
            requires_ack: Whether to wait for acknowledgment
            
        Returns:
            True if successfully sent (and acked if required)
        """
        message_id = f"{self.node_id}:{time.time()}:{self.messages_sent}"
        
        message = Message(
            message_id=message_id,
            message_type=message_type,
            sender_id=self.node_id,
            receiver_id=receiver_id,
            data=data,
            timestamp=time.time(),
            requires_ack=requires_ack
        )
        
        self.sent_messages[message_id] = message
        self.messages_sent += 1
        
        if requires_ack:
            self.pending_acks[message_id] = asyncio.Event()
        
        # Try to send with retries
        for attempt in range(self.max_retries):
            try:
                success = await self._send_message_once(message)
                
                if success:
                    if requires_ack:
                        # Wait for acknowledgment
                        try:
                            await asyncio.wait_for(
                                self.pending_acks[message_id].wait(),
                                timeout=self.ack_timeout
                            )
                            logger.debug(f"Message {message_id} acknowledged")
                            return True
                        except asyncio.TimeoutError:
                            logger.warning(f"ACK timeout for message {message_id}, attempt {attempt + 1}")
                    else:
                        return True
                
            except Exception as e:
                logger.error(f"Error sending message (attempt {attempt + 1}): {e}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        # Failed after all retries
        self.messages_failed += 1
        logger.error(f"Failed to send message {message_id} after {self.max_retries} attempts")
        return False
    
    async def _send_message_once(self, message: Message) -> bool:
        """
        Send message once (internal)
        
        Args:
            message: Message to send
            
        Returns:
            True if sent successfully
        """
        # In real implementation, use actual network communication
        # For now, log it
        logger.debug(f"Sending {message.message_type.value} to {message.receiver_id}")
        
        # Simulate network send
        # In production, use aiohttp or similar
        return True
    
    async def receive_message(self, message: Message):
        """
        Receive and process message
        
        Args:
            message: Received message
        """
        message_id = message.message_id
        
        # Check for duplicate
        if message_id in self.received_messages:
            logger.debug(f"Duplicate message {message_id}, sending ACK again")
            if message.requires_ack:
                await self.send_ack(message)
            return
        
        self.received_messages[message_id] = message
        self.messages_received += 1
        
        logger.debug(f"Received {message.message_type.value} from {message.sender_id}")
        
        # Send acknowledgment if required
        if message.requires_ack:
            await self.send_ack(message)
        
        # Process message with registered handler
        if message.message_type in self.message_handlers:
            handler = self.message_handlers[message.message_type]
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Error handling message {message_id}: {e}")
    
    async def send_ack(self, original_message: Message):
        """
        Send acknowledgment for received message
        
        Args:
            original_message: Original message being acknowledged
        """
        ack_message = Message(
            message_id=f"ack:{original_message.message_id}",
            message_type=MessageType.RESPONSE,
            sender_id=self.node_id,
            receiver_id=original_message.sender_id,
            data={'ack': True, 'original_id': original_message.message_id},
            timestamp=time.time(),
            requires_ack=False
        )
        
        await self._send_message_once(ack_message)
    
    async def receive_ack(self, ack_message: Message):
        """
        Receive acknowledgment
        
        Args:
            ack_message: ACK message
        """
        original_id = ack_message.data.get('original_id')
        
        if original_id and original_id in self.pending_acks:
            self.pending_acks[original_id].set()
            logger.debug(f"Received ACK for message {original_id}")
    
    def get_stats(self) -> dict:
        """Get messaging statistics"""
        return {
            'node_id': self.node_id,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'messages_failed': self.messages_failed,
            'pending_acks': len(self.pending_acks),
            'success_rate': f"{(self.messages_sent - self.messages_failed) / max(self.messages_sent, 1) * 100:.2f}%"
        }
