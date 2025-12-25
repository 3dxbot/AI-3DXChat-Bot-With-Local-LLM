"""
UI Initialization Module.

This module provides the UIInitMixin class, which handles the initialization
and setup of the chatbot application's graphical user interface. It includes
methods for creating and configuring UI components, layouts, and responsive
design elements.

Classes:
    UIInitMixin: Mixin class for UI initialization and layout.
"""

import tkinter as tk
import customtkinter as ctk
import os
from .ui_styles import UIStyles


class UIInitMixin:
    """
    Mixin class for UI initialization and layout setup.

    This mixin provides methods to initialize and configure the main UI components
    including headers, footers, sidebars, and responsive layouts. It handles
    different view modes and adaptive UI behavior.

    Methods:
        setup_root_config: Configure root window settings.
        setup_top_header: Setup top header with settings and language buttons.
        setup_main_header: Setup main header with control buttons.
        setup_main_container: Setup main content container.
        setup_logs_frame: Setup logs display frame.
        setup_sidebar_frame: Setup sidebar with nick lists.
        setup_footer_frame: Setup footer with manual input and settings.
        setup_ui: Setup the main UI layout.
        update_header_layout: Adaptive grid layout for header buttons.
        update_footer_layout: Adaptive layout for footer.
        on_resize: Handle window resize event.
        rebuild_ui: Rebuild the UI based on view mode.
        on_auto_lang_toggle: Handle auto language switch toggle.
    """

    def setup_root_config(self):
        """
        Configure root window settings.

        Sets up grid weights for responsive layout and initial window geometry
        based on the current view mode.
        """
        self.root.columnconfigure(0, weight=0)  # Sidebar
        self.root.columnconfigure(1, weight=1)  # Main area
        self.root.rowconfigure(0, weight=0)  # Ollama Status
        self.root.rowconfigure(1, weight=0)  # Main header
        self.root.rowconfigure(2, weight=1)  # Main content
        self.root.rowconfigure(3, weight=0)  # Footer

        # Set initial window size based on view mode
        if self.view_mode == 0:
            self.root.geometry("800x820")
        elif self.view_mode == 1:
            self.root.geometry("750x770")
        elif self.view_mode == 2:
            self.root.geometry("600x520")

    def setup_top_header(self):
        """
        Setup top header frame.

        Creates the top header (currently minimal).
        """
        self.top_header_frame = ctk.CTkFrame(self.root, fg_color=UIStyles.HEADER_BG, border_width=1, border_color=UIStyles.BORDER_COLOR)
        self.top_header_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.top_header_frame.columnconfigure(0, weight=1)
        self.top_header_frame.columnconfigure(1, weight=0)

        # Currently empty, can be expanded later

    def setup_main_header(self):
        """
        Setup main header frame with control buttons.

        Creates the main header containing start, pause, stop, clear chat,
        and close partnership buttons with initial layout configuration.
        """
        # Ollama Status Zone (added first, at the very top)
        if hasattr(self, 'ollama_ui'):
             self.ollama_status_frame = self.ollama_ui.create_dashboard_zone(self.root)
             self.ollama_status_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=UIStyles.SPACE_LG, pady=(UIStyles.SPACE_LG, UIStyles.SPACE_SM))
             
        self.header_frame = UIStyles.create_card_frame(self.root)
        self.header_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=UIStyles.SPACE_LG, pady=(UIStyles.SPACE_LG, 0))
        for i in range(5):
            self.header_frame.columnconfigure(i, weight=1)

        # Buttons - calm neutral colors
        btn_height = 36
        self.start_button = UIStyles.create_button(self.header_frame, text="Start", command=self.on_start_click, fg_color=UIStyles.SUCCESS_COLOR, hover_color="#059669", height=btn_height)
        self.pause_button = UIStyles.create_secondary_button(self.header_frame, text="Pause", command=self.on_pause_click, state=tk.DISABLED, height=btn_height)
        self.stop_button = UIStyles.create_secondary_button(self.header_frame, text="Stop", command=self.on_stop_click, state=tk.DISABLED, height=btn_height)
        self.clear_chat_button = UIStyles.create_secondary_button(self.header_frame, text="Clear Chat", command=self.on_clear_chat_click, state=tk.DISABLED, height=btn_height)
        self.close_partnership_button = UIStyles.create_secondary_button(self.header_frame, text="Close Partn", command=self.on_close_partnership_click, state=tk.DISABLED, height=btn_height)

        # Initial layout
        self.update_header_layout()

    def setup_main_container(self):
        """
        Setup main content container.

        Creates and configures the main container frame for fields and logs.

        Returns:
            ctk.CTkFrame: The configured main container frame.
        """
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=UIStyles.SPACE_LG, pady=(0, UIStyles.SPACE_SM))
        main_container.columnconfigure(0, weight=1)
        
        
        # Row configuration
        main_container.rowconfigure(0, weight=0)  # Nicks Header
        main_container.rowconfigure(1, weight=0)  # Nicks Content
        main_container.rowconfigure(2, weight=0)  # Logs Header
        main_container.rowconfigure(3, weight=1)  # Logs Content
        
        return main_container

    def setup_logs_frame(self, parent):
        """
        Setup logs display frame with collapsible header.

        Creates a header with a collapse button and a scrollable text area
        for displaying application logs.

        Args:
            parent: Parent widget to contain the logs frame.
        """
        # Header - always visible
        logs_header = ctk.CTkFrame(parent, fg_color="transparent")
        logs_header.grid(row=2, column=0, sticky='ew', padx=0, pady=(UIStyles.SPACE_MD, UIStyles.SPACE_XS))
        logs_header.columnconfigure(0, weight=1)
        
        UIStyles.create_section_header(logs_header, text="System Logs", font=UIStyles.FONT_H3).grid(row=0, column=0, sticky='w', padx=(15, 0))
        self.logs_collapse_btn = UIStyles.create_secondary_button(logs_header, text="▲", 
                                                                 command=self.toggle_logs_collapse, 
                                                                 width=30, height=24, border_width=0,
                                                                 fg_color="transparent", hover_color=UIStyles.HOVER_COLOR)
        self.logs_collapse_btn.grid(row=0, column=1, sticky='e')

        # Logs content - Togglable
        self.logs_content_frame = UIStyles.create_card_frame(parent)
        self.logs_content_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=0, pady=(0, UIStyles.SPACE_SM))
        self.logs_content_frame.columnconfigure(0, weight=1)
        self.logs_content_frame.rowconfigure(0, weight=1)

        # Terminal-style text area - white text with rounded container
        text_container = ctk.CTkFrame(self.logs_content_frame, fg_color="#0f172a", corner_radius=8)
        text_container.grid(row=0, column=0, sticky='nsew', padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_2XL)
        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(text_container, wrap=tk.WORD, bg="#0f172a", fg=UIStyles.TEXT_PRIMARY,
                                font=UIStyles.FONT_MONO, borderwidth=0, relief='flat',
                                selectbackground=UIStyles.PRIMARY_COLOR, highlightthickness=0)
        self.log_text.grid(row=0, column=0, sticky='nsew', padx=UIStyles.SPACE_MD, pady=UIStyles.SPACE_MD)
        self.log_text.configure(state=tk.DISABLED)

    def setup_sidebar_frame(self, parent):
        """Setup sidebar with nick lists and collapsible header."""
        # Header - always visible
        nicks_header = ctk.CTkFrame(parent, fg_color="transparent")
        nicks_header.grid(row=1, column=0, sticky='ew', padx=0, pady=(UIStyles.SPACE_MD, UIStyles.SPACE_XS))
        nicks_header.columnconfigure(0, weight=1)
        
        UIStyles.create_section_header(nicks_header, text="Nick Management", font=UIStyles.FONT_H3).grid(row=0, column=0, sticky='w', padx=(15, 0))
        self.nicks_collapse_btn = UIStyles.create_secondary_button(nicks_header, text="▼", 
                                                                  command=self.toggle_nicks_collapse, 
                                                                  width=30, height=24, border_width=0,
                                                                  fg_color="transparent", hover_color=UIStyles.HOVER_COLOR)
        self.nicks_collapse_btn.grid(row=0, column=1, sticky='e')

        # Nicks content - Collapsed by default
        self.nicks_content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.nicks_content_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=0, pady=(0, UIStyles.SPACE_SM))
        self.nicks_content_frame.grid_remove() # Hide initially
        for i in range(3):
            self.nicks_content_frame.columnconfigure(i, weight=1)

        def create_list_card(parent_frame, title, col, listbox_attr):
            card = UIStyles.create_card_frame(parent_frame)
            card.grid(row=0, column=col, sticky="nsew", padx=5, pady=0)
            card.columnconfigure(0, weight=1)
            card.rowconfigure(1, weight=1)

            # Compact header
            ctk.CTkLabel(card, text=title, font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=UIStyles.SPACE_LG, pady=(UIStyles.SPACE_LG, UIStyles.SPACE_XS))
            
            # Larger listbox with rounded container and internal padding
            list_container = ctk.CTkFrame(card, fg_color="#0f172a", corner_radius=8)
            list_container.grid(row=1, column=0, sticky="nsew", padx=UIStyles.SPACE_LG, pady=(0, UIStyles.SPACE_XS))
            list_container.columnconfigure(0, weight=1)
            list_container.rowconfigure(0, weight=1)
            
            lb = tk.Listbox(list_container, height=5, bg="#0f172a", fg=UIStyles.TEXT_PRIMARY,
                            font=UIStyles.FONT_NORMAL, borderwidth=0, relief='flat', highlightthickness=0, 
                            selectbackground=UIStyles.PRIMARY_COLOR)
            lb.grid(row=0, column=0, sticky="nsew", padx=UIStyles.SPACE_MD, pady=UIStyles.SPACE_MD)
            setattr(self, listbox_attr, lb)
            return card

        # Suggested list (Found)
        suggested_card = create_list_card(self.nicks_content_frame, "Found", 0, "suggested_listbox")
        btn_frame = ctk.CTkFrame(suggested_card, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=UIStyles.SPACE_LG, pady=(0, UIStyles.SPACE_LG))
        UIStyles.create_secondary_button(btn_frame, text="Ignore", command=lambda: self.add_nick_from_suggested("ignore"), width=60, height=28).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        UIStyles.create_button(btn_frame, text="Track", command=lambda: self.add_nick_from_suggested("target"), width=60, height=28).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))

        # Ignore list
        ignore_card = create_list_card(self.nicks_content_frame, "Ignored", 1, "ignore_listbox")
        UIStyles.create_secondary_button(ignore_card, text="Remove", command=lambda: self.remove_nick(self.ignore_listbox, "ignore"), height=28).grid(row=2, column=0, sticky="ew", padx=UIStyles.SPACE_LG, pady=(0, UIStyles.SPACE_LG))

        # Target list
        target_card = create_list_card(self.nicks_content_frame, "Tracked", 2, "target_listbox")
        UIStyles.create_secondary_button(target_card, text="Remove", command=lambda: self.remove_nick(self.target_listbox, "target"), height=28).grid(row=2, column=0, sticky="ew", padx=UIStyles.SPACE_LG, pady=(0, UIStyles.SPACE_LG))

    def setup_footer_frame(self):
        """
        Setup footer with manual input and settings.

        Creates the footer containing manual message input, send button,
        and autonomous mode toggle.
        """
        self.footer_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.footer_frame.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.S), padx=UIStyles.SPACE_LG, pady=(0, 10))

        # Manual input container - always at the bottom
        self.input_container = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        self.input_container.pack(side='bottom', fill='x', pady=0)

        self.manual_input_entry = UIStyles.create_input_field(self.input_container, textvariable=self.manual_input_var)
        self.manual_input_entry.pack(side='left', fill='x', expand=True, padx=(0, 5), pady=0)
        self.manual_input_entry.bind('<Return>', lambda event: self.on_manual_send_click())

        self.send_button = UIStyles.create_button(self.input_container, text="Send", command=self.on_manual_send_click, height=36, width=100)
        self.send_button.pack(side='right', padx=0, pady=0)

    def setup_sidebar(self):
        """
        Setup left sidebar with navigation buttons and controls.
        """
        self.sidebar_frame = ctk.CTkFrame(self.root, width=180, fg_color=UIStyles.HEADER_BG, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=3, sticky=(tk.N, tk.S, tk.W), padx=0, pady=0)
        self.sidebar_frame.pack_propagate(False)

        # Brand/Logo Area
        brand_label = ctk.CTkLabel(self.sidebar_frame, text="CHATBOT", font=UIStyles.FONT_TITLE, text_color=UIStyles.PRIMARY_COLOR)
        brand_label.pack(pady=(20, 20), padx=20, anchor="w")

        # Zone 1: Navigation Menu
        nav_card = UIStyles.create_card_frame(self.sidebar_frame)
        nav_card.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Navigation Buttons with backgrounds
        self.dashboard_button = UIStyles.create_secondary_button(nav_card, text="Dashboard", command=self.switch_to_dashboard)
        self.dashboard_button.pack(fill=tk.X, padx=UIStyles.SPACE_MD, pady=(UIStyles.SPACE_MD, UIStyles.SPACE_XS))

        self.settings_button_sidebar = UIStyles.create_secondary_button(nav_card, text="Prompts", command=self.switch_to_settings)
        self.settings_button_sidebar.pack(fill=tk.X, padx=UIStyles.SPACE_MD, pady=UIStyles.SPACE_XS)

        self.hooker_mod_button_sidebar = UIStyles.create_secondary_button(nav_card, text="Hooker Mod", command=self.switch_to_hooker_mod)
        self.hooker_mod_button_sidebar.pack(fill=tk.X, padx=UIStyles.SPACE_MD, pady=UIStyles.SPACE_XS)

        self.game_sync_button_sidebar = UIStyles.create_secondary_button(nav_card, text="Game Sync", command=self.switch_to_game_sync)
        self.game_sync_button_sidebar.pack(fill=tk.X, padx=UIStyles.SPACE_MD, pady=UIStyles.SPACE_XS)

        self.character_button_sidebar = UIStyles.create_secondary_button(nav_card, text="Character", command=self.switch_to_character)
        self.character_button_sidebar.pack(fill=tk.X, padx=UIStyles.SPACE_MD, pady=UIStyles.SPACE_XS)

        self.ai_setup_button_sidebar = UIStyles.create_secondary_button(nav_card, text="AI Setup", command=self.switch_to_ai_setup)
        self.ai_setup_button_sidebar.pack(fill=tk.X, padx=UIStyles.SPACE_MD, pady=UIStyles.SPACE_XS)

        self.chat_button_sidebar = UIStyles.create_secondary_button(nav_card, text="Chat", command=self.switch_to_chat)
        self.chat_button_sidebar.pack(fill=tk.X, padx=UIStyles.SPACE_MD, pady=(UIStyles.SPACE_XS, UIStyles.SPACE_MD))

        # Zone 2: Toggle Switches
        switches_card = UIStyles.create_card_frame(self.sidebar_frame)
        switches_card.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Toggle Switches with larger, thicker font
        TOGGLE_FONT = UIStyles.FONT_H3

        # Translation Layer switch
        ctk.CTkLabel(switches_card, text="Translation", font=TOGGLE_FONT, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_MD, pady=(UIStyles.SPACE_MD, UIStyles.SPACE_XS))
        self.translation_layer_switch = ctk.CTkSwitch(
            switches_card, text="", variable=self.use_translation_var,
            command=self.on_translation_toggle,
            fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR, button_color="#FFFFFF"
        )
        self.translation_layer_switch.pack(anchor='w', padx=UIStyles.SPACE_MD, pady=(0, UIStyles.SPACE_SM))

        # Auto-mode switch
        ctk.CTkLabel(switches_card, text="Auto-mode", font=TOGGLE_FONT, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_MD, pady=(0, UIStyles.SPACE_XS))
        self.auto_mode_switch = ctk.CTkSwitch(
            switches_card, text="", variable=self.autonomous_var,
            command=self.on_autonomous_toggle,
            fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR, button_color="#FFFFFF"
        )
        self.auto_mode_switch.pack(anchor='w', padx=UIStyles.SPACE_MD, pady=(0, UIStyles.SPACE_SM))

        # Hooker Mod switch
        ctk.CTkLabel(switches_card, text="Hooker Mod", font=TOGGLE_FONT, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_MD, pady=(0, UIStyles.SPACE_XS))
        self.hooker_switch = ctk.CTkSwitch(
            switches_card, text="", variable=self.hooker_enabled_var,
            command=self.on_hooker_toggle,
            fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR, button_color="#FFFFFF"
        )
        self.hooker_switch.pack(anchor='w', padx=UIStyles.SPACE_MD, pady=(0, UIStyles.SPACE_SM))

        # Show Zones switch
        ctk.CTkLabel(switches_card, text="Show Zones", font=TOGGLE_FONT, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_MD, pady=(0, UIStyles.SPACE_XS))
        self.show_zones_switch = ctk.CTkSwitch(
            switches_card, text="", variable=self.show_zones_var,
            command=self.on_toggle_overlay,
            fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR, button_color="#FFFFFF"
        )
        self.show_zones_switch.pack(anchor='w', padx=UIStyles.SPACE_MD, pady=(0, UIStyles.SPACE_MD))

        # Zone 3: Language & Help
        settings_card = UIStyles.create_card_frame(self.sidebar_frame)
        settings_card.pack(fill=tk.X, padx=10, pady=(0, 10))

        ctk.CTkLabel(settings_card, text="Language", font=TOGGLE_FONT, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_MD, pady=(UIStyles.SPACE_MD, UIStyles.SPACE_XS))
        language_options = ["en", "ru", "fr", "es"]
        self.language_dropdown = ctk.CTkOptionMenu(
            settings_card, 
            values=language_options, 
            variable=self.hiwaifu_language_var, 
            command=self.on_language_selected,
            fg_color=UIStyles.SECONDARY_COLOR,
            button_color=UIStyles.PRIMARY_COLOR,
            button_hover_color=UIStyles.PRIMARY_HOVER,
            dropdown_fg_color=UIStyles.CARD_BG,
            dropdown_hover_color=UIStyles.HOVER_COLOR,
            text_color=UIStyles.TEXT_PRIMARY,
            font=UIStyles.FONT_NORMAL
        )
        self.language_dropdown.pack(anchor='w', fill=tk.X, padx=UIStyles.SPACE_MD, pady=(0, UIStyles.SPACE_SM))

        # Help button - using standard styling but will be highlighted when active
        self.help_button = UIStyles.create_secondary_button(settings_card, text="❓ Help", command=self.switch_to_help, height=32)
        self.help_button.pack(anchor='w', fill=tk.X, padx=UIStyles.SPACE_MD, pady=(0, UIStyles.SPACE_MD))
        
        # Highlight active page
        self.update_sidebar_active()

        # Set initial switch colors based on variables
        if self.use_translation_var.get():
            self.translation_layer_switch.configure(fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR)
        else:
            self.translation_layer_switch.configure(fg_color=UIStyles.DISABLED_COLOR, progress_color=UIStyles.DISABLED_COLOR)

        if self.show_zones_var.get():
            self.show_zones_switch.configure(fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR)
        else:
            self.show_zones_switch.configure(fg_color=UIStyles.DISABLED_COLOR, progress_color=UIStyles.DISABLED_COLOR)

        if self.autonomous_var.get():
            self.auto_mode_switch.configure(fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR)
        else:
            self.auto_mode_switch.configure(fg_color=UIStyles.DISABLED_COLOR, progress_color=UIStyles.DISABLED_COLOR)

        if self.hooker_enabled_var.get():
            self.hooker_switch.configure(fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR)
        else:
            self.hooker_switch.configure(fg_color=UIStyles.DISABLED_COLOR, progress_color=UIStyles.DISABLED_COLOR)

        # Set initial active
        self.update_sidebar_active()
        self.update_switch_colors()

    def switch_to_dashboard(self):
        """
        Switch to dashboard view.
        """
        self.current_view = 'dashboard'
        self.update_sidebar_active()
        self.show_dashboard_view()

    def switch_to_settings(self):
        """
        Switch to settings view.
        """
        self.current_view = 'settings'
        self.update_sidebar_active()
        self.show_settings_view()

    def switch_to_help(self):
        """
        Switch to help view.
        """
        self.current_view = 'help'
        self.update_sidebar_active()
        self.show_help_view()

    def switch_to_hooker_mod(self):
        """
        Switch to hooker mod view.
        """
        self.current_view = 'hooker_mod'
        self.update_sidebar_active()
        self.show_hooker_mod_view()

    def switch_to_game_sync(self):
        """
        Switch to game sync view.
        """
        self.current_view = 'game_sync'
        self.update_sidebar_active()
        self.show_game_sync_view()

    def switch_to_character(self):
        """
        Switch to character view.
        """
        self.current_view = 'character'
        self.update_sidebar_active()
        self.show_character_view()

    def switch_to_ai_setup(self):
        """
        Switch to AI setup view.
        """
        self.current_view = 'ai_setup'
        self.update_sidebar_active()
        self.show_ai_setup_view()

    def switch_to_chat(self):
        """
        Switch to chat view.
        """
        self.current_view = 'chat'
        self.update_sidebar_active()
        self.show_chat_view()

    def _hide_all_views(self):
        """
        Hide all view frames and show main UI.
        """
        # Hide all secondary views
        if hasattr(self, 'settings_frame'):
            self.settings_frame.grid_remove()
        if hasattr(self, 'hooker_mod_frame'):
            self.hooker_mod_frame.grid_remove()
        if hasattr(self, 'game_sync_frame'):
            self.game_sync_frame.grid_remove()
        if hasattr(self, 'help_frame'):
            self.help_frame.grid_remove()
        if hasattr(self, 'character_frame'):
            self.character_frame.grid_remove()
        if hasattr(self, 'ai_setup_frame'):
            self.ai_setup_frame.grid_remove()
        if hasattr(self, 'chat_frame'):
            self.chat_frame.grid_remove()

        # Hide main UI
        self.header_frame.grid_remove()
        self.main_container.grid_remove()
        if hasattr(self, 'footer_frame'):
            self.footer_frame.grid_remove()

    def show_help_view(self):
        """
        Show help view.
        """
        # Hide other views
        self._hide_all_views()

        # Show help
        if not hasattr(self, 'help_frame'):
            self.help_frame = ctk.CTkScrollableFrame(self.root, width=self.root.winfo_width() - 180,
                                                      height=self.root.winfo_height(), fg_color="transparent")
            self.help_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
            self._populate_help_content()
        else:
            self.help_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

    def _populate_help_content(self):
        # Page title
        ctk.CTkLabel(self.help_frame, text="Help & Instructions", 
                      font=(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_DISPLAY, "bold"), 
                      text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_LG))
        
        # Instructions card
        instructions_card = UIStyles.create_card_frame(self.help_frame)
        instructions_card.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG)
        
        ctk.CTkLabel(instructions_card, text="Getting Started",
                      font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        
        instructions_text = """1. Screen Area Setup:
   - Click the "Configure Zones" button in Game Sync.
   - Follow instructions to select areas: chat, input field, partnership, and poses.
   - This is necessary for the bot to work correctly.

2. Starting the Bot:
   - Click "Start" to launch the bot.
   - Press F2 to begin chat scanning.
   - The bot will automatically respond to tracked nicks.

3. Nick Management:
   - Ignored: Messages from these nicks are ignored.
   - Tracked: The bot responds to messages from these nicks.
   - New nicks appear in the "Found" list.

4. Autonomous Mode:
   - Enable "Auto-mode" for automatic pose/partnership scanning.
   - Set your preferred inactivity timeout.

5. Pose Management:
   - Unknown poses trigger a customizable message.
   - Users can provide descriptions that get saved.
   - Customize messages for different languages in Prompts.

6. Manual Sending:
   - Enter text in the bottom field and press "Send" or Enter."""
        
        ctk.CTkLabel(instructions_card, text=instructions_text, 
                      justify="left", anchor="w", 
                      font=UIStyles.FONT_NORMAL,
                      text_color=UIStyles.TEXT_SECONDARY).pack(anchor="w", padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))

        # Hotkeys card  
        hotkeys_card = UIStyles.create_card_frame(self.help_frame)
        hotkeys_card.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_LG))
        
        ctk.CTkLabel(hotkeys_card, text="Keyboard Shortcuts",
                      font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        
        hotkeys_text = """F2: Pause/Resume chat scanning
F3: Show/Hide window
F4: Clear chat history in HiWaifu
F5-F12: Send preset phrases (configured in Prompts)

Ctrl+E: Change HiWaifu language to English
Ctrl+R: Change language to Russian
Ctrl+F: Change language to French
Ctrl+S: Change language to Spanish"""
        
        ctk.CTkLabel(hotkeys_card, text=hotkeys_text,
                      justify="left", anchor="w",
                      font=UIStyles.FONT_NORMAL,
                      text_color=UIStyles.TEXT_SECONDARY).pack(anchor="w", padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))

    def _populate_character_view(self):
        """
        Populate the character view content.
        """
        # Page title
        ctk.CTkLabel(self.character_frame, text="Character Settings",
                      font=(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_DISPLAY, "bold"),
                      text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_LG))

        # Character settings card
        character_card = UIStyles.create_card_frame(self.character_frame)
        character_card.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG)

        ctk.CTkLabel(character_card, text="Character Configuration",
                      font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))

        character_text = """Configure your character's personality, appearance, and behavior settings here.

This section allows you to:
- Set character name and description
- Define personality traits
- Configure appearance preferences
- Set behavioral patterns

Note: This feature is under development."""
        ctk.CTkLabel(character_card, text=character_text,
                      justify="left", anchor="w",
                      font=UIStyles.FONT_NORMAL,
                      text_color=UIStyles.TEXT_SECONDARY).pack(anchor="w", padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))

    def _populate_ai_setup_view(self):
        """
        Populate the AI setup view content.
        """
        # Page title
        ctk.CTkLabel(self.ai_setup_frame, text="AI Setup",
                      font=(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_DISPLAY, "bold"),
                      text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_LG))

        # Create Ollama zones if Ollama UI is available
        if hasattr(self, 'ollama_ui'):
            self.ai_setup_zones = self.ollama_ui.create_ai_setup_zones(self.ai_setup_frame)
        else:
            # Fallback content
            ai_card = UIStyles.create_card_frame(self.ai_setup_frame)
            ai_card.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG)

            ctk.CTkLabel(ai_card, text="AI Configuration",
                          font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))

            ai_text = """Configure AI model settings and parameters here.

This section allows you to:
- Select AI model and provider
- Set temperature and other generation parameters
- Configure API endpoints
- Set up model-specific options

Note: This feature is under development."""
            ctk.CTkLabel(ai_card, text=ai_text,
                          justify="left", anchor="w",
                          font=UIStyles.FONT_NORMAL,
                          text_color=UIStyles.TEXT_SECONDARY).pack(anchor="w", padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))

    def _populate_chat_view(self):
        """
        Populate the chat view content.
        """
        # Page title
        ctk.CTkLabel(self.chat_frame, text="Chat Settings",
                      font=(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_DISPLAY, "bold"),
                      text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_LG))

        # Chat settings card
        chat_card = UIStyles.create_card_frame(self.chat_frame)
        chat_card.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG)

        ctk.CTkLabel(chat_card, text="Chat Configuration",
                      font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))

        chat_text = """Configure chat behavior and response settings here.

This section allows you to:
- Set response delay and timing
- Configure message filtering
- Set up auto-responses
- Define chat rules and boundaries

Note: This feature is under development."""
        ctk.CTkLabel(chat_card, text=chat_text,
                      justify="left", anchor="w",
                      font=UIStyles.FONT_NORMAL,
                      text_color=UIStyles.TEXT_SECONDARY).pack(anchor="w", padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))

    def show_hooker_mod_view(self):
        """
        Show hooker mod view.
        """
        # Update hooker var from bot
        if hasattr(self, 'bot') and self.bot:
            self.hooker_enabled_var.set(getattr(self.bot, 'hooker_mod_enabled', False))

        # Hide other views
        self._hide_all_views()

        # Show hooker mod
        if not hasattr(self, 'hooker_mod_frame'):
            self.hooker_mod_frame = ctk.CTkScrollableFrame(self.root, width=self.root.winfo_width() - 180,
                                                           height=self.root.winfo_height(), fg_color="transparent")
            self.hooker_mod_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
            self._populate_hooker_mod_view()
        else:
            self.hooker_mod_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

    def show_game_sync_view(self):
        """
        Show game sync view.
        """
        # Hide settings if shown
        if hasattr(self, 'settings_frame'):
            self.settings_frame.grid_remove()

        # Hide hooker mod frame if shown
        if hasattr(self, 'hooker_mod_frame'):
            self.hooker_mod_frame.grid_remove()

        # Hide help if shown
        if hasattr(self, 'help_frame'):
            self.help_frame.grid_remove()

        # Hide character, ai_setup, chat frames if shown
        if hasattr(self, 'character_frame'):
            self.character_frame.grid_remove()
        if hasattr(self, 'ai_setup_frame'):
            self.ai_setup_frame.grid_remove()
        if hasattr(self, 'chat_frame'):
            self.chat_frame.grid_remove()

        # Hide main UI
        self.header_frame.grid_remove()
        self.main_container.grid_remove()
        if hasattr(self, 'footer_frame'):
            self.footer_frame.grid_remove()

        # Show game sync
        if not hasattr(self, 'game_sync_frame'):
            self.game_sync_frame = ctk.CTkScrollableFrame(self.root, width=self.root.winfo_width() - 180,
                                                          height=self.root.winfo_height(), fg_color="transparent")
            self.game_sync_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
            self._populate_game_sync_view()
        else:
            self.game_sync_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

    def show_character_view(self):
        """
        Show character view.
        """
        # Hide other views
        self._hide_all_views()

        # Show character
        if not hasattr(self, 'character_frame'):
            self.character_frame = ctk.CTkScrollableFrame(self.root, width=self.root.winfo_width() - 180,
                                                          height=self.root.winfo_height(), fg_color="transparent")
            self.character_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
            self._populate_character_view()
        else:
            self.character_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

    def show_ai_setup_view(self):
        """
        Show AI setup view.
        """
        # Hide other views
        self._hide_all_views()

        # Show AI setup
        if not hasattr(self, 'ai_setup_frame'):
            self.ai_setup_frame = ctk.CTkScrollableFrame(self.root, width=self.root.winfo_width() - 180,
                                                         height=self.root.winfo_height(), fg_color="transparent")
            self.ai_setup_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
            self._populate_ai_setup_view()
        else:
            self.ai_setup_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

    def show_chat_view(self):
        """
        Show chat view.
        """
        # Hide other views
        self._hide_all_views()

        # Show chat
        if not hasattr(self, 'chat_frame'):
            self.chat_frame = ctk.CTkScrollableFrame(self.root, width=self.root.winfo_width() - 180,
                                                     height=self.root.winfo_height(), fg_color="transparent")
            self.chat_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
            self._populate_chat_view()
        else:
            self.chat_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

    def update_sidebar_active(self):
        """
        Update sidebar button colors based on current view.
        """
        # Reset all to neutral secondary style
        self.dashboard_button.configure(fg_color=UIStyles.SECONDARY_COLOR, hover_color=UIStyles.HOVER_COLOR, border_width=0)
        self.settings_button_sidebar.configure(fg_color=UIStyles.SECONDARY_COLOR, hover_color=UIStyles.HOVER_COLOR, border_width=0)
        self.hooker_mod_button_sidebar.configure(fg_color=UIStyles.SECONDARY_COLOR, hover_color=UIStyles.HOVER_COLOR, border_width=0)
        self.game_sync_button_sidebar.configure(fg_color=UIStyles.SECONDARY_COLOR, hover_color=UIStyles.HOVER_COLOR, border_width=0)
        self.character_button_sidebar.configure(fg_color=UIStyles.SECONDARY_COLOR, hover_color=UIStyles.HOVER_COLOR, border_width=0)
        self.ai_setup_button_sidebar.configure(fg_color=UIStyles.SECONDARY_COLOR, hover_color=UIStyles.HOVER_COLOR, border_width=0)
        self.chat_button_sidebar.configure(fg_color=UIStyles.SECONDARY_COLOR, hover_color=UIStyles.HOVER_COLOR, border_width=0)
        self.help_button.configure(fg_color=UIStyles.SECONDARY_COLOR, hover_color=UIStyles.HOVER_COLOR, border_width=0)

        # Highlight active button with primary color
        if self.current_view == 'dashboard':
            self.dashboard_button.configure(fg_color=UIStyles.PRIMARY_COLOR, hover_color=UIStyles.PRIMARY_HOVER)
        elif self.current_view == 'settings':
            self.settings_button_sidebar.configure(fg_color=UIStyles.PRIMARY_COLOR, hover_color=UIStyles.PRIMARY_HOVER)
        elif self.current_view == 'hooker_mod':
            self.hooker_mod_button_sidebar.configure(fg_color=UIStyles.PRIMARY_COLOR, hover_color=UIStyles.PRIMARY_HOVER)
        elif self.current_view == 'game_sync':
            self.game_sync_button_sidebar.configure(fg_color=UIStyles.PRIMARY_COLOR, hover_color=UIStyles.PRIMARY_HOVER)
        elif self.current_view == 'character':
            self.character_button_sidebar.configure(fg_color=UIStyles.PRIMARY_COLOR, hover_color=UIStyles.PRIMARY_HOVER)
        elif self.current_view == 'ai_setup':
            self.ai_setup_button_sidebar.configure(fg_color=UIStyles.PRIMARY_COLOR, hover_color=UIStyles.PRIMARY_HOVER)
        elif self.current_view == 'chat':
            self.chat_button_sidebar.configure(fg_color=UIStyles.PRIMARY_COLOR, hover_color=UIStyles.PRIMARY_HOVER)
        elif self.current_view == 'help':
            self.help_button.configure(fg_color=UIStyles.PRIMARY_COLOR, hover_color=UIStyles.PRIMARY_HOVER)

    def update_switch_colors(self):
        """
        Update sidebar switch colors based on their current state.
        """
        # Translation switch
        if self.use_translation_var.get():
            self.translation_layer_switch.configure(fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR)
        else:
            self.translation_layer_switch.configure(fg_color=UIStyles.DISABLED_COLOR, progress_color=UIStyles.DISABLED_COLOR)

        # Zones switch
        if self.show_zones_var.get():
            self.show_zones_switch.configure(fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR)
        else:
            self.show_zones_switch.configure(fg_color=UIStyles.DISABLED_COLOR, progress_color=UIStyles.DISABLED_COLOR)

        # Auto-mode switch
        if self.autonomous_var.get():
            self.auto_mode_switch.configure(fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR)
        else:
            self.auto_mode_switch.configure(fg_color=UIStyles.DISABLED_COLOR, progress_color=UIStyles.DISABLED_COLOR)

        # Hooker switch
        if self.hooker_enabled_var.get():
            self.hooker_switch.configure(fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR)
        else:
            self.hooker_switch.configure(fg_color=UIStyles.DISABLED_COLOR, progress_color=UIStyles.DISABLED_COLOR)

    def show_dashboard_view(self):
        """
        Show dashboard view (main UI components).
        """
        # Hide all secondary views
        self._hide_all_views()

        # Show main UI
        self.header_frame.grid()
        self.main_container.grid()
        if hasattr(self, 'footer_frame'):
            self.footer_frame.grid()
        
        # Ollama status is already created in setup_main_header, no need to duplicate

    def show_settings_view(self):
        """
        Show settings view.
        """
        # Hide other views
        self._hide_all_views()

        # Show settings
        if not hasattr(self, 'settings_frame'):
            self.settings_frame = ctk.CTkScrollableFrame(self.root, width=self.root.winfo_width() - 180,
                                                         height=self.root.winfo_height(), fg_color="transparent")
            self.settings_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
            self._populate_settings_tabs()
        else:
            self.settings_frame.grid(row=0, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

    def setup_ui(self):
        """
        Setup the main UI layout.

        Initializes all UI components including headers, containers, frames,
        and binds resize events. Performs initial rebuild for compact mode.
        """
        self.nicks_collapsed = True
        self.logs_collapsed = False
        self.setup_root_config()
        self.setup_sidebar()
        self.setup_main_header()

        # Bind resize event
        self.root.bind('<Configure>', self.on_resize)

        self.main_container = self.setup_main_container()
        # Setup Logs
        self.setup_logs_frame(self.main_container)
        
        self.setup_sidebar_frame(self.main_container)
        self.setup_footer_frame()
        self.update_footer_layout()

        # Initial rebuild to apply compact mode
        self.rebuild_ui()

    def update_header_layout(self):
        """
        Adaptive grid layout for header buttons based on window width.

        Dynamically rearranges the 5 control buttons (start, pause, stop,
        clear chat, close partnership) into different grid configurations
        based on available window width for optimal usability.
        """
        # First, forget all current positions
        for widget in self.header_frame.winfo_children():
            widget.grid_forget()

        width = self.root.winfo_width() - 180  # Subtract sidebar width
        buttons = [self.start_button, self.pause_button, self.stop_button, self.clear_chat_button, self.close_partnership_button]

        if width > 1200:
            # 1 row, 5 columns
            for i in range(5):
                self.header_frame.columnconfigure(i, weight=1)
            for i, btn in enumerate(buttons):
                btn.grid(row=0, column=i, padx=5, pady=5, sticky='ew')
        elif width > 800:
            # 2 rows: 3 in first, 2 in second
            for i in range(3):
                self.header_frame.columnconfigure(i, weight=1)
            for i in range(3):
                buttons[i].grid(row=0, column=i, padx=5, pady=5, sticky='ew')
            for i in range(2):
                buttons[i+3].grid(row=1, column=i, padx=5, pady=5, sticky='ew')
        elif width > 500:
            # 2 rows: 3, 2
            for i in range(3):
                self.header_frame.columnconfigure(i, weight=1)
            for i in range(3):
                buttons[i].grid(row=0, column=i, padx=5, pady=5, sticky='ew')
            for i in range(2):
                buttons[i+3].grid(row=1, column=i, padx=5, pady=5, sticky='ew')
        elif width > 300:
            # 3 rows, 2 columns: 2,2,1
            for i in range(2):
                self.header_frame.columnconfigure(i, weight=1)
            for i in range(2):
                buttons[i].grid(row=0, column=i, padx=5, pady=5, sticky='ew')
            for i in range(2):
                buttons[i+2].grid(row=1, column=i, padx=5, pady=5, sticky='ew')
            buttons[4].grid(row=2, column=0, padx=5, pady=5, sticky='ew')
        else:
            # 5 rows, 1 column
            self.header_frame.columnconfigure(0, weight=1)
            for i, btn in enumerate(buttons):
                btn.grid(row=i, column=0, padx=5, pady=5, sticky='ew')

    def update_footer_layout(self):
        """
        Adaptive layout for footer based on window width.

        Rearranges footer elements (input field, send button)
        based on available width for optimal mobile and desktop usability.
        """
        width = self.root.winfo_width() - 180  # Subtract sidebar width

        # Only update positions, don't forget and recreate widgets
        # Manual input always at top (using pack for consistency as requested)
        if width > 400:
            # Wide: send button next to input
            self.manual_input_entry.pack(side='left', fill='x', expand=True, padx=(0, 5), pady=0)
            self.send_button.pack(side='right', padx=0, pady=0)
        else:
            # Narrow: send button below input
            self.manual_input_entry.pack(side='top', fill='x', expand=True, padx=0, pady=(0, 5))
            self.send_button.pack(side='top', fill='x', padx=0, pady=0)

    def on_resize(self, event):
        """
        Handle window resize event.

        Updates header and footer layouts when the main window is resized.

        Args:
            event: Tkinter event object containing resize information.
        """
        if event.widget == self.root:
            self.update_header_layout()
            self.update_footer_layout()

    def rebuild_ui(self):
        """
        Rebuild the UI based on view mode.

        Since view_mode is always 0 (expanded), this just ensures the layout is correct.
        """
        # Set window size
        self.root.geometry("800x820")

        # Footer is already gridded in setup_ui
        self.footer_frame.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.S), padx=UIStyles.SPACE_LG, pady=(0, 10))

        # Update header layout
        self.update_header_layout()

    def on_auto_lang_toggle(self):
        """
        Handle auto language switch toggle.

        Updates the bot's auto language switching setting and logs the change.
        """
        enabled = self.auto_lang_var.get()
        if hasattr(self, 'bot') and self.bot:
            self.bot.auto_lang_switch = enabled
        self.log_message(f"Auto language switching {'enabled' if enabled else 'disabled'}", internal=True)

    def on_translation_toggle(self):
        """
        Handle translation layer toggle.

        Updates the bot's translation layer setting and logs the change.
        """
        enabled = self.use_translation_var.get()
        if hasattr(self, 'bot') and self.bot:
            self.bot.use_translation_layer = enabled
            self.bot._save_hotkey_settings()
        self.log_message(f"Translation layer {'enabled' if enabled else 'disabled'}", internal=True)

        # Update switch colors
        if enabled:
            self.translation_layer_switch.configure(fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR)
        else:
            self.translation_layer_switch.configure(fg_color=UIStyles.DISABLED_COLOR, progress_color=UIStyles.DISABLED_COLOR)

    def on_hooker_toggle(self):
        """
        Handle hooker mod toggle.

        Updates the bot's hooker mod setting and logs the change.
        """
        enabled = self.hooker_enabled_var.get()
        if hasattr(self, 'bot') and self.bot:
            self.bot.hooker_mod_enabled = enabled
            self.bot._save_hotkey_settings()
        self.log_message(f"Hooker Mod {'enabled' if enabled else 'disabled'}", internal=True)

        # Update switch colors
        if enabled:
            self.hooker_switch.configure(fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR)
        else:
            self.hooker_switch.configure(fg_color=UIStyles.DISABLED_COLOR, progress_color=UIStyles.DISABLED_COLOR)
    
    def _update_start_button_state(self):
        """
        Update Start button state based on Ollama status.
        
        The Start button should be enabled only when Ollama is Running.
        """
        if hasattr(self, 'ollama_ui') and hasattr(self, 'start_button'):
            if hasattr(self, 'status_manager'):
                ollama_status = self.status_manager.get_ollama_status()
                if ollama_status == "Running":
                    self.start_button.configure(state="normal", fg_color=UIStyles.SUCCESS_COLOR, hover_color="#059669")
                else:
                    self.start_button.configure(state="disabled", fg_color=UIStyles.DISABLED_COLOR, hover_color=UIStyles.DISABLED_COLOR)
            else:
                # Fallback: disable if no status manager available
                self.start_button.configure(state="disabled", fg_color=UIStyles.DISABLED_COLOR, hover_color=UIStyles.DISABLED_COLOR)