# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller Spec File for ChatBot Application.

This file configures PyInstaller to build a standalone executable for the ChatBot application.
It specifies which files to include, exclude, and how to package the application.

Generated with: pyi-makespec main.py
Modified for: Windows executable with icon, no console window.
"""

# Analysis: Analyze the main script and its dependencies
a = Analysis(
    ['main.py'],              # Main script to analyze
    pathex=[],                # Additional paths to search for imports
    binaries=[],              # Additional binary files to include
    datas=[],                 # Additional data files to include (format: ('source', 'destination'))
    hiddenimports=[],         # Modules that PyInstaller might not detect automatically
    hookspath=[],             # Paths to search for PyInstaller hooks
    hooksconfig={},           # Configuration for hooks
    runtime_hooks=[],         # Runtime hooks to execute
    excludes=[],              # Modules to exclude from the bundle
    noarchive=False,          # Whether to create a single-file archive
    optimize=0,               # Optimization level (0=none, 1=asserts, 2=docstrings)
)

# PYZ: Create a compressed archive of pure Python modules
pyz = PYZ(a.pure)

# EXE: Create the final executable
exe = EXE(
    pyz,                           # Compressed Python code
    a.scripts,                     # Scripts to include
    a.binaries,                    # Binary files
    a.datas,                       # Data files
    [],                            # Additional files
    name='main',                   # Executable name
    debug=False,                   # Include debug information
    bootloader_ignore_signals=False, # Handle signals in bootloader
    strip=False,                   # Strip symbols from binaries
    upx=True,                      # Use UPX compression
    upx_exclude=[],                # Files to exclude from UPX compression
    runtime_tmpdir=None,           # Runtime temporary directory
    console=False,                 # Show console window (False = GUI only)
    disable_windowed_traceback=False, # Show traceback in windowed mode
    argv_emulation=False,          # Emulate command line arguments
    target_arch=None,              # Target architecture
    codesign_identity=None,        # Code signing identity (macOS)
    entitlements_file=None,        # Entitlements file (macOS)
    icon=['resources\\logo.ico'],  # Application icon
)
