#!/usr/bin/env python3
"""
Development script to run both frontend and backend simultaneously
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run both frontend and backend in development mode"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🚀 Starting HTTP Interceptor in development mode...")
    print("📁 Project root:", project_root)
    
    try:
        # Run the dev:full command which uses concurrently
        subprocess.run([
            "npm", "run", "dev:full"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running development servers: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down development servers...")
        sys.exit(0)

if __name__ == "__main__":
    main()
