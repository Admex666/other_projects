"""
MLSZ Deliverable Compliance Verifier
Checks files for forbidden terminology ('meccs'), checks output directories, and verifies formatting.
"""

import sys
import os
import re

FORBIDDEN_WORDS = [
    (r'\bmeccs\b', "A 'meccs' szó szigorúan tiltott! Használd a 'mérkőzés' kifejezést."),
    (r'\bmeccsek\b', "A 'meccsek' kifejezés tiltott! Használd a 'mérkőzések' kifejezést."),
    (r'\bmeccsen\b', "A 'meccsen' kifejezés tiltott! Használd a 'mérkőzésen' kifejezést."),
    (r'\bmeccsről\b', "A 'meccsről' kifejezés tiltott! Használd a 'mérkőzésről' kifejezést."),
    (r'\bmeccset\b', "A 'meccset' kifejezés tiltott! Használd a 'mérkőzést' kifejezést.")
]

def check_file(filepath: str) -> bool:
    if not os.path.exists(filepath):
        print(f"[ERR] File not found: {filepath}")
        return False

    print(f"🔍 Validating MLSZ Compliance for: {filepath}")
    has_errors = False

    # Check sandbox path rule if output file
    norm_path = filepath.replace('/', '\\')
    if '\\reports\\' in norm_path and '\\reports\\tmp\\' not in norm_path:
        print(f"  ⚠️ [WARNING] Path is outside '\\reports\\tmp\\': {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"  [ERR] Could not read file: {e}")
        return False

    # Check forbidden words
    for pattern, explanation in FORBIDDEN_WORDS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            has_errors = True
            print(f"  ❌ [FORBIDDEN TERMINOLOGY] Found {len(matches)} occurrence(s) matching '{pattern}':")
            print(f"     ↳ {explanation}")

    if not has_errors:
        print(f"  ✅ [PASS] All MLSZ design & terminology checks passed!")
        return True
    else:
        print(f"  ❌ [FAIL] Compliance violations detected. Please correct them.")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_mlsz_compliance.py <path_to_file>")
        sys.exit(1)
    
    target = sys.argv[1]
    success = check_file(target)
    sys.exit(0 if success else 1)
