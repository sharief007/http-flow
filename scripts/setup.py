#!/usr/bin/env python3
"""
Setup script for the HTTP Interceptor project
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}: {e}")
        return False

def main():
    """Setup the project"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🚀 Setting up HTTP Interceptor project...")
    print("📁 Project root:", project_root)
    
    # Install Node.js dependencies
    if not run_command("npm install", "Installing Node.js dependencies"):
        sys.exit(1)
    
    # Install Python dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        sys.exit(1)
    
    # Optional: Install development dependencies
    if not run_command("pip install pytest pytest-asyncio pytest-cov flake8 black isort", "Installing Python dev dependencies"):
        print("⚠️  Warning: Could not install Python dev dependencies")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("  npm run dev:full     - Run both frontend and backend")
    print("  npm run dev          - Run only frontend")
    print("  npm run dev:backend  - Run only backend")
    print("  npm run test:all     - Run all tests")

if __name__ == "__main__":
    main()
