"""
Chat Memory Management Module.

This module provides the ChatMemory class for managing short-term conversation memory
with automatic summarization to prevent context window overflow while maintaining
dialogue coherence.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatMessage:
    """Represents a single chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    summary_trigger: bool = False  # Whether this message triggered summarization


class ChatMemory:
    """
    Manages short-term conversation memory with automatic summarization.
    
    Features:
    - Maintains recent messages in working memory
    - Automatically summarizes old messages when limit exceeded
    - Provides context for LLM with summary + recent messages
    - Supports memory clearing and status tracking
    """
    
    def __init__(self, recent_limit: int = 12, summary_trigger_limit: int = 20):
        """
        Initialize ChatMemory.
        
        Args:
            recent_limit (int): Number of recent messages to keep in working memory.
            summary_trigger_limit (int): Number of messages before triggering summarization.
        """
        self.recent_limit = recent_limit
        self.summary_trigger_limit = summary_trigger_limit
        
        self.history: List[ChatMessage] = []
        self.summary = ""
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.total_messages = 0
        self.summaries_created = 0
        self.last_summary_time = None
        
    def add_message(self, role: str, content: str) -> None:
        """
        Add a new message to memory.
        
        Args:
            role (str): Message role ("user" or "assistant").
            content (str): Message content.
        """
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        
        self.history.append(message)
        self.total_messages += 1
        
        # Check if we need to trigger summarization
        if len(self.history) >= self.summary_trigger_limit:
            self._trigger_summarization()
    
    def _trigger_summarization(self) -> None:
        """Trigger summarization of old messages."""
        if not self.history:
            return
            
        # Calculate how many messages to summarize
        messages_to_summarize = len(self.history) - self.recent_limit
        
        if messages_to_summarize <= 0:
            return
            
        # Get old messages for summarization
        old_messages = self.history[:messages_to_summarize]
        remaining_messages = self.history[messages_to_summarize:]
        
        # Mark the trigger message
        if remaining_messages:
            remaining_messages[0].summary_trigger = True
        
        # Create summarization prompt
        conversation_text = self._format_messages_for_summarization(old_messages)
        summarization_prompt = self._create_summarization_prompt(conversation_text)
        
        # Log the summarization trigger
        self.logger.info(f"Triggering summarization for {len(old_messages)} messages")
        
        # Store the prompt for external processing
        self._pending_summarization = {
            'prompt': summarization_prompt,
            'old_messages_count': len(old_messages),
            'remaining_messages': remaining_messages
        }
        
        # Replace history with remaining messages
        self.history = remaining_messages
        
        # Update statistics
        self.summaries_created += 1
        self.last_summary_time = datetime.now()
    
    def _format_messages_for_summarization(self, messages: List[ChatMessage]) -> str:
        """Format messages for summarization prompt."""
        formatted = []
        for msg in messages:
            formatted.append(f"{msg.role}: {msg.content}")
        return "\n".join(formatted)
    
    def _create_summarization_prompt(self, conversation_text: str) -> str:
        """Create prompt for conversation summarization."""
        return f"""Summarize the key points of this conversation so far, keeping names and important facts. 
Be extremely concise (max 2-3 sentences). Focus on:

1. Main topics discussed
2. Important decisions or agreements
3. Key information exchanged
4. Current state of the conversation

Conversation:
{conversation_text}

Summary:"""
    
    def process_summarization_result(self, summary: str) -> None:
        """
        Process the result of summarization.
        
        Args:
            summary (str): Summarized text from LLM.
        """
        if not hasattr(self, '_pending_summarization'):
            self.logger.warning("No pending summarization to process")
            return
            
        # Clean up the summary
        cleaned_summary = self._clean_summary(summary)
        
        # Update the main summary
        if self.summary:
            self.summary = f"{self.summary}\n\n{cleaned_summary}"
        else:
            self.summary = cleaned_summary
        
        # Log the result
        self.logger.info(f"Summarization completed. New summary length: {len(self.summary)} chars")
        
        # Clean up
        delattr(self, '_pending_summarization')
    
    def _clean_summary(self, summary: str) -> str:
        """Clean and format the summary text."""
        # Remove common prefixes/suffixes
        summary = summary.strip()
        
        # Remove "Summary:" prefix if present
        if summary.startswith("Summary:"):
            summary = summary[8:].strip()
        
        # Limit length to prevent runaway growth
        if len(summary) > 1000:
            summary = summary[:997] + "..."
        
        return summary
    
    def get_context_for_llm(self) -> str:
        """
        Get context for LLM including summary and recent messages.
        
        Returns:
            str: Formatted context string.
        """
        context_parts = []
        
        # Add summary if available
        if self.summary:
            context_parts.append(f"Previous summary: {self.summary}")
        
        # Add recent messages
        recent_messages = self.history[-self.recent_limit:]
        if recent_messages:
            recent_text = "\n".join([
                f"{msg.role}: {msg.content}" 
                for msg in recent_messages
            ])
            context_parts.append(f"Recent conversation:\n{recent_text}")
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    def clear(self) -> None:
        """Clear all memory (summary and history)."""
        self.history = []
        self.summary = ""
        self.total_messages = 0
        self.summaries_created = 0
        self.last_summary_time = None
        
        if hasattr(self, '_pending_summarization'):
            delattr(self, '_pending_summarization')
        
        self.logger.info("Chat memory cleared")
    
    def get_status(self) -> Dict:
        """
        Get current memory status.
        
        Returns:
            Dict: Memory statistics and status.
        """
        return {
            'recent_messages_count': len(self.history),
            'summary_length': len(self.summary),
            'total_messages_processed': self.total_messages,
            'summaries_created': self.summaries_created,
            'last_summary_time': self.last_summary_time,
            'memory_usage_percentage': min(len(self.history) / self.summary_trigger_limit * 100, 100),
            'has_pending_summarization': hasattr(self, '_pending_summarization')
        }
    
    def get_pending_summarization(self) -> Optional[Dict]:
        """
        Get pending summarization data if any.
        
        Returns:
            Optional[Dict]: Pending summarization data or None.
        """
        return getattr(self, '_pending_summarization', None)
    
    def is_ready_for_summarization(self) -> bool:
        """Check if summarization is ready to be processed."""
        return hasattr(self, '_pending_summarization')
    
    def get_working_memory_size(self) -> int:
        """Get the current size of working memory."""
        return len(self.history)
    
    def get_summary_length(self) -> int:
        """Get the length of the current summary."""
        return len(self.summary)