#!/usr/bin/env python3
"""
Comprehensive production setup script for Doc KB backend.
Handles ChromaDB downgrade, data clearing, and configuration.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def clear_chromadb_data():
    """Clear ChromaDB data directory."""
    data_dir = Path("./data/chroma")
    if data_dir.exists():
        print(f"🧹 Clearing ChromaDB data at: {data_dir}")
        try:
            shutil.rmtree(data_dir)
            data_dir.mkdir(parents=True, exist_ok=True)
            print("✅ ChromaDB data cleared successfully")
            return True
        except Exception as e:
            print(f"❌ Error clearing data: {e}")
            return False
    else:
        print("📁 No existing ChromaDB data found")
        data_dir.mkdir(parents=True, exist_ok=True)
        return True

def setup_directories():
    """Setup required directories."""
    directories = ["data", "logs", "data/chroma"]
    for dir_name in directories:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    print("✅ Directories created")

def main():
    """Main setup process."""
    print("🚀 Setting up Doc KB Production Environment...")
    print("=" * 50)
    
    # Step 1: Setup directories
    setup_directories()
    
    # Step 2: Clear old ChromaDB data
    if not clear_chromadb_data():
        print("❌ Failed to clear ChromaDB data")
        return False
    
    # Step 3: Downgrade ChromaDB
    if not run_command("pip uninstall chromadb -y", "Uninstalling current ChromaDB"):
        return False
    
    if not run_command("pip install chromadb==0.4.15", "Installing ChromaDB 0.4.15"):
        return False
    
    # Step 4: Update imports
    if not run_command("python update_imports.py", "Updating ChromaDB imports"):
        return False
    
    # Step 5: Test the setup
    if not run_command("python test_production_client.py", "Testing production client"):
        return False
    
    print("\n🎉 Production setup completed successfully!")
    print("=" * 50)
    print("You can now run your application with:")
    print("  python production_start.py")
    print("  or")
    print("  uvicorn app.main:app --host 0.0.0.0 --port 8000")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)