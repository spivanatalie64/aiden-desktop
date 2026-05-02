#!/usr/bin/env python3
"""AIDEN Desktop – Main entry point.

All frontends import from this package to ensure the common modules
are on the path.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
