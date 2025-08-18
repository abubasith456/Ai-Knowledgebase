#!/usr/bin/env python3
"""
Script to downgrade ChromaDB to a stable version without telemetry issues.
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🔧 Downgrading ChromaDB to version 0.4.22...")
    print("=" * 50)
    
    # Check current ChromaDB version
    print("📋 Checking current ChromaDB version...")
    success, stdout, stderr = run_command("pip show chromadb")
    if success:
        print(f"Current version info:\n{stdout}")
    else:
        print("Could not get current version info")
    
    print("\n🔄 Uninstalling current ChromaDB version...")
    success, stdout, stderr = run_command("pip uninstall chromadb -y")
    if success:
        print("✅ ChromaDB uninstalled successfully")
    else:
        print(f"⚠️  Uninstall warning: {stderr}")
    
    print("\n📦 Installing ChromaDB version 0.4.22...")
    success, stdout, stderr = run_command("pip install chromadb==0.4.22")
    if success:
        print("✅ ChromaDB 0.4.22 installed successfully")
    else:
        print(f"❌ Installation failed: {stderr}")
        return False
    
    print("\n🔍 Verifying installation...")
    success, stdout, stderr = run_command("pip show chromadb")
    if success:
        print(f"New version info:\n{stdout}")
        if "0.4.22" in stdout:
            print("✅ ChromaDB 0.4.22 verified successfully")
        else:
            print("⚠️  Version verification failed")
            return False
    else:
        print("❌ Could not verify installation")
        return False
    
    print("\n🎉 ChromaDB downgrade completed successfully!")
    print("=" * 50)
    print("You can now run your application without telemetry errors.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)