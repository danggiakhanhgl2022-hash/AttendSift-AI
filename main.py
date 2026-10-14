# -*- coding: utf-8 -*-
"""
ChamCongChatwork - Launcher
Entry point for the desktop application
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app.launcher import main

if __name__ == '__main__':
    sys.exit(main())
6