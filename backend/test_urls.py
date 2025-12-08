#!/usr/bin/env python3
"""
Test script to verify image URL generation in different environments.
"""

import os
import sys

# Add the app directory to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_production_mode():
    """Test URL generation in production mode."""
    # Set environment for testing
    os.environ['ENVIRONMENT'] = 'production'
    os.environ['BACKEND_URL'] = 'https://adorona.onrender.com'
    
    # Force reload of config module to pick up new environment
    import importlib
    if 'app.config' in sys.modules:
        importlib.reload(sys.modules['app.config'])
    if 'app.utils.file_utils' in sys.modules:
        importlib.reload(sys.modules['app.utils.file_utils'])
    
    from app.utils.file_utils import get_file_url
    
    # Test cases
    test_paths = [
        "uploads/products/vendor123/product456/image.jpg",
        "products/vendor123/product456/image.jpg", 
        "./uploads/products/vendor123/product456/image.jpg"
    ]
    
    print("Testing URL generation in production mode:")
    print("=" * 50)
    
    for path in test_paths:
        url = get_file_url(path)
        print(f"Input:  {path}")
        print(f"Output: {url}")
        print("-" * 30)

def test_development_mode():
    """Test URL generation in development mode."""
    # Set environment for testing
    os.environ['ENVIRONMENT'] = 'development'
    
    # Force reload of config module to pick up new environment
    import importlib
    if 'app.config' in sys.modules:
        importlib.reload(sys.modules['app.config'])
    if 'app.utils.file_utils' in sys.modules:
        importlib.reload(sys.modules['app.utils.file_utils'])
    
    from app.utils.file_utils import get_file_url
    
    # Test cases
    test_paths = [
        "uploads/products/vendor123/product456/image.jpg",
        "products/vendor123/product456/image.jpg", 
        "./uploads/products/vendor123/product456/image.jpg"
    ]
    
    print("\nTesting URL generation in development mode:")
    print("=" * 50)
    
    for path in test_paths:
        url = get_file_url(path)
        print(f"Input:  {path}")
        print(f"Output: {url}")
        print("-" * 30)

if __name__ == "__main__":
    try:
        test_production_mode()
        test_development_mode()
    except Exception as e:
        print(f"Error running test: {e}")
        import traceback
        traceback.print_exc()