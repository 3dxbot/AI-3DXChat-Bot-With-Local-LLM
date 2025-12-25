"""
UI Styles Module.

This module defines the premium design system for the ChatBot application,
including color palette, typography, spacing, shadows, and styled component
factory methods.

Classes:
    UIStyles: Central design system configuration and component factories.
"""

import customtkinter as ctk


class UIStyles:
    """
    Premium design system configuration and component factories.
    
    Provides a sophisticated, professional design system with:
    - Rich dark color palette with gradients
    - Professional typography scale
    - Consistent spacing system
    - Elevation through shadows
    - Factory methods for styled components
    """

    # ==========================================
    # COLOR PALETTE
    # ==========================================
    
    # Backgrounds - Rich, layered darks
    APP_BG = "#0a0e1a"           # Deep navy-black base
    HEADER_BG = "#111827"         # Elevated header/sidebar
    SURFACE_COLOR = "#1a1f2e"     # Cards and elevated surfaces
    CARD_BG = "#1e293b"           # Interactive cards
    CONTROL_PANEL_BG = "#1a1f2e"  # Control panels
    
    # Primary Accents - Indigo to Purple gradient system
    PRIMARY_COLOR = "#6366f1"     # Indigo-500
    PRIMARY_HOVER = "#8b5cf6"     # Purple-500 (for gradients)
    HOVER_COLOR = "#2563eb"       # Blue-600 (interactive states)
    
    # Secondary & Neutral
    SECONDARY_COLOR = "#64748b"   # Slate-500
    DISABLED_COLOR = "#475569"    # Slate-600
    
    # Borders & Dividers
    BORDER_COLOR = "#334155"      # Slate-700
    DIVIDER_COLOR = "#1e293b"     # Subtle divider
    
    # Text Hierarchy
    TEXT_PRIMARY = "#f1f5f9"      # Slate-100 (high contrast)
    TEXT_SECONDARY = "#94a3b8"    # Slate-400 (muted)
    TEXT_TERTIARY = "#64748b"     # Slate-500 (dimmer)
    
    # Semantic Colors
    SUCCESS_COLOR = "#10b981"     # Emerald-500
    WARNING_COLOR = "#f59e0b"     # Amber-500
    ERROR_COLOR = "#ef4444"       # Red-500
    
    # ==========================================
    # TYPOGRAPHY
    # ==========================================
    
    # Font Families
    FONT_FAMILY = "Inter"         # Primary UI font
    FONT_FAMILY_MONO = "JetBrains Mono"  # Logs and code
    FONT_FAMILY_FALLBACK = "Segoe UI"    # System fallback
    
    # Type Scale (size, weight, letter-spacing)
    FONT_SIZE_DISPLAY = 22
    FONT_WEIGHT_DISPLAY = "bold"
    
    FONT_SIZE_H1 = 18
    FONT_WEIGHT_H1 = "bold"
    
    FONT_SIZE_H2 = 16
    FONT_WEIGHT_H2 = "bold"
    
    FONT_SIZE_H3 = 14
    FONT_WEIGHT_H3 = "bold"
    
    FONT_SIZE_NORMAL = 13
    FONT_SIZE_SMALL = 12
    FONT_SIZE_TINY = 11
    FONT_SIZE_TITLE = FONT_SIZE_H2  # Alias for backward compatibility
    
    # Composed font tuples for common use
    FONT_DISPLAY = (FONT_FAMILY, FONT_SIZE_DISPLAY, FONT_WEIGHT_DISPLAY)
    FONT_H1 = (FONT_FAMILY, FONT_SIZE_H1, FONT_WEIGHT_H1)
    FONT_H2 = (FONT_FAMILY, FONT_SIZE_H2, FONT_WEIGHT_H2)
    FONT_H3 = (FONT_FAMILY, FONT_SIZE_H3, FONT_WEIGHT_H3)
    FONT_TITLE = FONT_H2
    FONT_BUTTON = (FONT_FAMILY, FONT_SIZE_NORMAL, "bold")
    FONT_NORMAL = (FONT_FAMILY, FONT_SIZE_NORMAL)
    FONT_SMALL = (FONT_FAMILY, FONT_SIZE_SMALL)
    FONT_MONO = (FONT_FAMILY_MONO, FONT_SIZE_SMALL)
    
    # ==========================================
    # SPACING SCALE (4px base)
    # ==========================================
    
    SPACE_XS = 2
    SPACE_SM = 4
    SPACE_MD = 8
    SPACE_LG = 12
    SPACE_XL = 16
    SPACE_2XL = 20
    SPACE_3XL = 24
    SPACE_4XL = 32
    SPACE_5XL = 48
    
    # ==========================================
    # BORDER RADIUS
    # ==========================================
    
    RADIUS_SM = 4
    RADIUS_MD = 6
    RADIUS_LG = 10
    RADIUS_XL = 14
    RADIUS_PILL = 999  # For pill-shaped elements
    
    # ==========================================
    # COMPONENT STYLES
    # ==========================================
    
    @staticmethod
    def configure_styles():
        """
        Configure global CustomTkinter appearance settings.
        """
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
    
    @staticmethod
    def apply_to_root(root):
        """
        Apply base styles to root window.
        
        Args:
            root: The root Tk window.
        """
        root.configure(fg_color=UIStyles.APP_BG)
    
    @staticmethod
    def create_button(parent, text, command, fg_color=None, hover_color=None, 
                     width=120, height=36, **kwargs):
        """
        Create a premium styled primary button with gradient-ready colors.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Button command
            fg_color: Button background color (default: PRIMARY_COLOR)
            hover_color: Hover state color (default: PRIMARY_HOVER)
            width: Button width
            height: Button height
            **kwargs: Additional CTkButton arguments
            
        Returns:
            CTkButton: Styled button instance
        """
        if fg_color is None:
            fg_color = UIStyles.PRIMARY_COLOR
        if hover_color is None:
            hover_color = UIStyles.PRIMARY_HOVER
        
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color=fg_color,
            hover_color=hover_color,
            width=width,
            height=height,
            corner_radius=UIStyles.RADIUS_MD,
            text_color=UIStyles.TEXT_PRIMARY,
            text_color_disabled=UIStyles.TEXT_SECONDARY,
            font=UIStyles.FONT_BUTTON,
            border_width=0,
            **kwargs
        )
    
    @staticmethod
    def create_secondary_button(parent, text, command, width=120, height=36, **kwargs):
        """
        Create a secondary/neutral button with subtle styling.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Button command
            width: Button width
            height: Button height
            **kwargs: Additional CTkButton arguments
            
        Returns:
            CTkButton: Styled secondary button
        """
        border_width = kwargs.pop('border_width', 1)
        fg_color = kwargs.pop('fg_color', UIStyles.SECONDARY_COLOR)
        hover_color = kwargs.pop('hover_color', UIStyles.DISABLED_COLOR)
        
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color=fg_color,
            hover_color=hover_color,
            width=width,
            height=height,
            corner_radius=UIStyles.RADIUS_MD,
            text_color=UIStyles.TEXT_PRIMARY,
            text_color_disabled=UIStyles.TEXT_SECONDARY,
            font=UIStyles.FONT_BUTTON,
            border_width=border_width,
            border_color=UIStyles.BORDER_COLOR,
            **kwargs
        )
    
    @staticmethod
    def create_card_frame(parent, **kwargs):
        """
        Create an elevated card frame with premium styling.
        
        Args:
            parent: Parent widget
            **kwargs: Additional CTkFrame arguments
            
        Returns:
            CTkFrame: Styled card frame
        """
        return ctk.CTkFrame(
            parent,
            fg_color=UIStyles.SURFACE_COLOR,
            corner_radius=UIStyles.RADIUS_LG,
            border_width=1,
            border_color=UIStyles.BORDER_COLOR,
            **kwargs
        )
    
    @staticmethod
    def create_input_field(parent, **kwargs):
        """
        Create a premium styled input field.
        
        Args:
            parent: Parent widget
            **kwargs: Additional CTkEntry arguments
            
        Returns:
            CTkEntry: Styled input field
        """
        return ctk.CTkEntry(
            parent,
            height=36,
            corner_radius=UIStyles.RADIUS_MD,
            border_width=1,
            border_color=UIStyles.BORDER_COLOR,
            fg_color=UIStyles.CARD_BG,
            text_color=UIStyles.TEXT_PRIMARY,
            font=UIStyles.FONT_NORMAL,
            **kwargs
        )
    
    @staticmethod
    def create_section_header(parent, text, **kwargs):
        """
        Create a styled section header label.
        
        Args:
            parent: Parent widget
            text: Header text
            **kwargs: Additional CTkLabel arguments
            
        Returns:
            CTkLabel: Styled section header
        """
        font = kwargs.pop('font', UIStyles.FONT_TITLE)
        return ctk.CTkLabel(
            parent,
            text=text,
            font=font,
            text_color=UIStyles.TEXT_PRIMARY,
            anchor="w",
            **kwargs
        )