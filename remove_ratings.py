#!/usr/bin/env python3
"""
Script to remove rating and safetyRating lines from app.py
"""

import re

def remove_ratings():
    # Read the file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove rating lines
    content = re.sub(r"^\s*'rating':\s*\d+\.\d+,\s*\n", "", content, flags=re.MULTILINE)
    
    # Remove safetyRating lines  
    content = re.sub(r"^\s*'safetyRating':\s*\d+\.\d+,\s*\n", "", content, flags=re.MULTILINE)
    
    # Write back to file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Removed all rating and safetyRating lines from app.py")

if __name__ == "__main__":
    remove_ratings()
