#!/usr/bin/env python3
"""
Setup script for Python 3.11 environment with TensorFlow support.
Run this after installing Python 3.11.
"""

import sys
import subprocess
import os

def check_python_version():
    """Check if we're using Python 3.11."""
    version = sys.version_info
    print(f"Current Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor == 11:
        print("✅ Using Python 3.11 - Perfect for TensorFlow!")
        return True
    elif version.major == 3 and version.minor >= 12:
        print("⚠️  Using Python 3.12+ - TensorFlow may not be available")
        return False
    else:
        print("❌ Not using Python 3.11")
        return False

def create_venv():
    """Create a new virtual environment."""
    print("\nCreating new virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv311"], check=True)
        print("✅ Virtual environment created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_requirements():
    """Install all requirements."""
    print("\nInstalling requirements...")
    try:
        # Activate virtual environment and install
        if os.name == 'nt':  # Windows
            activate_script = "venv311\\Scripts\\activate.bat"
            pip_cmd = "venv311\\Scripts\\pip"
        else:  # Unix/Linux
            activate_script = "venv311/bin/activate"
            pip_cmd = "venv311/bin/pip"
        
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def main():
    """Main setup function."""
    print("=" * 60)
    print("Chess Application - Python 3.11 Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        print("\nPlease install Python 3.11 and run this script again.")
        print("Download from: https://www.python.org/downloads/release/python-3118/")
        return
    
    # Create virtual environment
    if not create_venv():
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    print("\n" + "=" * 60)
    print("✅ Setup completed successfully!")
    print("\nTo activate your environment:")
    if os.name == 'nt':  # Windows
        print("  venv311\\Scripts\\activate.bat")
    else:  # Unix/Linux
        print("  source venv311/bin/activate")
    print("\nTo test your installation:")
    print("  python test_imports.py")

if __name__ == "__main__":
    main() 