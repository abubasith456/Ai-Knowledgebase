#!/usr/bin/env python3
"""
Simple script to clear ChromaDB data without user input.
"""

import os
import shutil
from pathlib import Path

def clear_chromadb_data():
    """Clear all ChromaDB data to start fresh."""
    
    print("🧹 Clearing ChromaDB data for version compatibility...")
    print("=" * 50)
    
    # Get the data directory
    data_dir = Path(os.environ.get("CHROMA_DATA_DIR") or "./data/chroma")
    
    if data_dir.exists():
        print(f"📁 Found ChromaDB data at: {data_dir}")
        
        try:
            # Remove the entire data directory
            shutil.rmtree(data_dir)
            print("✅ ChromaDB data cleared successfully")
            
            # Recreate the directory
            data_dir.mkdir(parents=True, exist_ok=True)
            print("✅ Fresh data directory created")
            
            print("\n🎉 ChromaDB data cleared! You can now start fresh with version 0.4.22.")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing data: {e}")
            return False
    else:
        print(f"📁 No ChromaDB data found at: {data_dir}")
        print("✅ Ready to start fresh!")
        return True

if __name__ == "__main__":
    success = clear_chromadb_data()
    if success:
        print("\n🚀 You can now run your application with a clean ChromaDB setup!")
    else:
        print("\n❌ Failed to clear ChromaDB data")