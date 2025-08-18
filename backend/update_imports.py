#!/usr/bin/env python3
"""
Script to update all ChromaDB imports to use the production client.
"""

import os
import re
from pathlib import Path

def update_file_imports(file_path: str):
    """Update imports in a single file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace the import
        old_import = "from .chroma_client import get_chroma_client"
        new_import = "from production_chroma_client import get_chroma_client"
        
        if old_import in content:
            content = content.replace(old_import, new_import)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Updated: {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Update all Python files in the app directory."""
    app_dir = Path("app")
    
    if not app_dir.exists():
        print("❌ app directory not found")
        return
    
    files_to_update = [
        "app/main.py",
        "app/query.py", 
        "app/ingest.py"
    ]
    
    updated_count = 0
    for file_path in files_to_update:
        if Path(file_path).exists():
            if update_file_imports(file_path):
                updated_count += 1
    
    print(f"\n🎉 Updated {updated_count} files successfully!")

if __name__ == "__main__":
    main()