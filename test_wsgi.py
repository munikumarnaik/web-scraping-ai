#!/usr/bin/env python
"""Test if WSGI application can be loaded"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

print("Testing WSGI application load...")
print(f"Python path: {sys.path}")
print(f"Working directory: {os.getcwd()}")

try:
    from config.wsgi import application
    print("✅ SUCCESS: WSGI application loaded successfully")
    print(f"Application type: {type(application)}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
