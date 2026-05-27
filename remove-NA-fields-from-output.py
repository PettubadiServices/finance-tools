#!/usr/bin/env python3
import sys
import re

def main():
    lines = sys.stdin.read().splitlines()
    cleaned = []

    # Patterns to remove
    skip_patterns = [
        r"\bN/A\b",
        r"\bNone\b",
        r"\bnull\b",
        r"\bmissing\b",
        r"\bunknown\b",
    ]

    def should_skip(line):
        for pat in skip_patterns:
            if re.search(pat, line, flags=re.IGNORECASE):
                return True
        return False

    # First pass: remove unwanted lines (but keep headers)
    for line in lines:
        if should_skip(line):
            continue
        cleaned.append(line)

    # Second pass: collapse multiple blank lines
    final = []
    last_blank = False
    for line in cleaned:
        if line.strip() == "":
            if last_blank:
                continue
            last_blank = True
        else:
            last_blank = False
        final.append(line)

    # Print final cleaned output
    for line in final:
        print(line)

if __name__ == "__main__":
    main()
