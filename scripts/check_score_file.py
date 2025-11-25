"""Script to check the generated score files."""

import os
import re

def check_file(filepath):
    """Check if file exists and show its content."""
    print(f"\n{'='*60}")
    print(f"Checking: {filepath}")
    print(f"{'='*60}")
    
    if not os.path.exists(filepath):
        print("❌ File does not exist")
        return False
    
    print("✓ File exists")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\nFile size: {len(content)} bytes")
    print(f"\n--- Content ---")
    print(content)
    print(f"--- End Content ---\n")
    
    # Try to extract score
    score_match = re.search(r"\*\*Score:\*\*\s*(\d+)/10", content)
    if score_match:
        print(f"✓ Score found: {score_match.group(1)}/10")
    else:
        print("❌ Score not found in expected format")
        # Try alternative patterns
        alt_match = re.search(r"Score[:\s]*(\d+)", content, re.IGNORECASE)
        if alt_match:
            print(f"  Found score in alternative format: {alt_match.group(1)}")
    
    return True

if __name__ == "__main__":
    print("Checking Score Files")
    print("="*60)
    
    files_to_check = [
        "analises-concluidas/performance_score.md",
        "analises-concluidas/avaliacao_performance.md"
    ]
    
    for filepath in files_to_check:
        check_file(filepath)
    
    print(f"\n{'='*60}")
    print("Check complete")
    print(f"{'='*60}")
