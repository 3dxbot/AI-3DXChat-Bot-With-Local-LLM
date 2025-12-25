"""
Chat UI Module.

This module provides the UIChatMixin class, which implements a ChatGPT-style
chat interface with message bubbles and history.
"""

import tkinter as tk
import customtkinter as ctk
from .ui_styles import UIStyles
import asyncio
from typing import Optional

class UIChatMixin:
    """Mixin class for the Chat interface."""

    def _initialize_chat_vars(self):
        self.chat_messages = [] # List of (author, message, is_bot)
        self.chat_input_var = tk.StringVar()

    def _populate_chat_view(self):
        """Build the Chat page content."""
        if not hasattr(self, 'chat_input_var'):
            self._initialize_chat_vars()

        # Clear existing
        for widget in self.chat_frame.winfo_children():
            widget.destroy()

        # Page container
        self.chat_frame.columnconfigure(0, weight=1)
        self.chat_frame.rowconfigure(1, weight=1)

        # 1. Header with Tools
        header = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        header.columnconfigure(0, weight=1)

        self.chat_title_label = ctk.CTkLabel(header, text="Chat Room", 
                      font=(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_DISPLAY, "bold"), 
                      text_color=UIStyles.TEXT_PRIMARY)
        self.chat_title_label.grid(row=0, column=0, sticky="w")

        # Active character indicator (Small)
        self.chat_active_char_label = ctk.CTkLabel(header, text="", 
                                                   font=UIStyles.FONT_SMALL, 
                                                   text_color=UIStyles.PRIMARY_COLOR)
        self.chat_active_char_label.grid(row=1, column=0, sticky="w")

        if not hasattr(self, 'chat_messages'):
            self._initialize_chat_vars()

        UIStyles.create_secondary_button(header, text="Clear History", 
                                        command=self.clear_chat_history_ui, 
                                        width=120, height=28).grid(row=0, column=1, rowspan=2, sticky="e")
        
        # Subscribe to character changes
        if hasattr(self, 'status_manager'):
            self.status_manager.add_callback('active_character', self._on_chat_active_char_change)
            # Initial update
            curr_char = self.status_manager.get_active_character()
            if curr_char:
                self._on_chat_active_char_change(curr_char, None)

        # 2. Chat History Area
        # We use a non-scrollable character_frame at the top level, but THIS card is scrollable for messages
        chat_card = UIStyles.create_card_frame(self.chat_frame)
        chat_card.grid(row=1, column=0, sticky="nsew", padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_MD)
        chat_card.columnconfigure(0, weight=1)
        chat_card.rowconfigure(0, weight=1)

        self.chat_scroll_frame = ctk.CTkScrollableFrame(chat_card, fg_color="transparent")
        self.chat_scroll_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # 3. Input Area
        input_panel = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        input_panel.grid(row=2, column=0, sticky="ew", padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_MD, UIStyles.SPACE_2XL))
        input_panel.columnconfigure(0, weight=1)

        self.chat_entry = UIStyles.create_input_field(input_panel, textvariable=self.chat_input_var, 
                                                       placeholder_text="Type your message here...")
        self.chat_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.chat_entry.bind("<Return>", lambda e: self.on_send_chat())

        UIStyles.create_button(input_panel, text="Send", command=self.on_send_chat, width=100, height=36).grid(row=0, column=1, sticky="e")

        # Load existing messages
        self._refresh_chat_display()

        # Show greeting if starting fresh
        if not self.chat_messages:
            self._display_character_greeting()

    def _display_character_greeting(self):
        """Show the greeting from the current active character."""
        if not hasattr(self, 'chat_messages'):
            self._initialize_chat_vars()
            
        active_name = getattr(self.bot, 'active_character_name', None)
        if active_name and hasattr(self.bot, 'character_greeting') and self.bot.character_greeting:
            # Check if greeting is already the last message to avoid duplicates on re-activations
            if not self.chat_messages or self.chat_messages[-1][1] != self.bot.character_greeting:
                self._add_message(active_name, self.bot.character_greeting, is_bot=True)

    def _add_message(self, author, message, is_bot=False, msg_id=None):
        """Add a message to the internal list and update display if initialized."""
        self.chat_messages.append((author, message, is_bot, msg_id))
        
        # Only render if UI is initialized
        if hasattr(self, 'chat_scroll_frame') and self.chat_scroll_frame:
            self._render_message(author, message, is_bot)
            # Auto-scroll
            self.root.after(100, lambda: self.chat_scroll_frame._parent_canvas.yview_moveto(1.0))

    def _render_message(self, author, message, is_bot=False):
        """Create a message bubble in the scroll frame if initialized."""
        if not hasattr(self, 'chat_scroll_frame') or not self.chat_scroll_frame:
            return

        # Bubble alignment
        align = "w" if is_bot else "e"
        padx_outer = (20, 100) if is_bot else (100, 20)
        
        # Outer container for bubble
        bubble_row = ctk.CTkFrame(self.chat_scroll_frame, fg_color="transparent")
        bubble_row.pack(fill="x", pady=10)
        
        # The bubble itself
        bg_color = UIStyles.CHAT_BOT_BUBBLE if is_bot else UIStyles.CHAT_USER_BUBBLE
        # Expert UI: Rounded corners, subtle border, deeper shadow (simulated)
        bubble = ctk.CTkFrame(
            bubble_row, 
            fg_color=bg_color, 
            corner_radius=20,
            border_width=1,
            border_color="#475569" # Subtle Slate-600 border
        )
        bubble.pack(side="left" if is_bot else "right", padx=padx_outer, pady=2)
        
        # Author label - Bold and slightly larger for better readability
        author_color = "#fbcfe8" if is_bot else "#c7d2fe"
        author_label = ctk.CTkLabel(
            bubble, 
            text=author, 
            font=UIStyles.FONT_SMALL_BOLD, 
            text_color=author_color
        )
        author_label.pack(anchor="w", padx=15, pady=(10, 0))
        
        # Message text - Standardized wraplength and better line spacing
        text_color = UIStyles.TEXT_PRIMARY
        msg_label = ctk.CTkLabel(
            bubble, 
            text=message, 
            font=UIStyles.FONT_NORMAL, 
            text_color=text_color, 
            wraplength=380, 
            justify="left"
        )
        msg_label.pack(anchor="w", padx=15, pady=(2, 12))

    def _refresh_chat_display(self):
        """Clear and re-render all messages."""
        for widget in self.chat_scroll_frame.winfo_children():
            widget.destroy()
        for author, msg, is_bot, mid in self.chat_messages:
            self._render_message(author, msg, is_bot)

    def on_send_chat(self):
        """Handle sending a message from the UI."""
        message = self.chat_input_var.get().strip()
        if not message:
            return

        self.chat_input_var.set("")
        self._add_message("You", message, is_bot=False)

        # Forward to bot logic
        if self.bot and self.bot.loop:
            asyncio.run_coroutine_threadsafe(self._async_chat_request(message), self.bot.loop)
        else:
            self._add_message("System", "Error: Bot loop is not running. Please click 'Start' first.", is_bot=True)

    async def _async_chat_request(self, message):
        """Send message to Roxy and capture response."""
        active_name = getattr(self.bot, 'active_character_name', "Roxy")
        
        # Add thinking indicator
        thinking_id = "thinking_" + str(len(self.chat_messages))
        self.root.after(0, lambda: self._add_message(active_name, "...", is_bot=True, msg_id=thinking_id))
        
        try:
            if hasattr(self.bot, 'get_chat_response'):
                response = await self.bot.get_chat_response(message)
                
                # Remove thinking indicator and add real response
                def update_ui():
                    # Find and remove the indicator
                    for author, msg, is_bot, mid in list(self.chat_messages):
                        if mid == thinking_id:
                            self.chat_messages.remove((author, msg, is_bot, mid))
                    self._refresh_chat_display()
                    
                    if response:
                        active_name = getattr(self.bot, 'active_character_name', "Roxy")
                        self._add_message(active_name, response, is_bot=True)
                    else:
                        self._add_message("System", "Error: Failed to get response.", is_bot=True)

                self.root.after(0, update_ui)
        except Exception as e:
            self.bot.log(f"Error in UI chat: {e}", internal=True)
            self.root.after(0, lambda: self._add_message("System", f"Error: {str(e)}", is_bot=True))

    def clear_chat_history_ui(self):
        """Reset the chat history."""
        if tk.messagebox.askyesno("Clear History", "Are you sure you want to clear the chat history?"):
            self.chat_messages = []
            self._refresh_chat_display()
            # Also clear bot memory/browser
            if hasattr(self.bot, 'clear_chat_history'):
                self.bot.clear_chat_history()
            self._display_character_greeting()

    def _on_chat_active_char_change(self, new_char: Optional[str], old_char: Optional[str]):
        """Callback for active character change."""
        if hasattr(self, 'chat_active_char_label') and self.chat_active_char_label:
            text = f"Speaking with: {new_char}" if new_char else "No active profile"
            self.chat_active_char_label.configure(text=text)
