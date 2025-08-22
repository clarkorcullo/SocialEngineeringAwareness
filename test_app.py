#!/usr/bin/env python3
"""
Simple test script to verify app initialization
"""

import os
import sys

# Set environment variables for testing
os.environ['FLASK_ENV'] = 'production'
os.environ['RENDER'] = 'true'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'

try:
    # Import the app
    from app import app, logger
    
    print("✅ App imported successfully")
    
    # Test app context
    with app.app_context():
        print("✅ App context works")
        
        # Test basic configuration
        print(f"✅ Debug mode: {app.config.get('DEBUG')}")
        print(f"✅ Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        
    print("✅ All tests passed - app is ready for deployment")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
