#!/usr/bin/env python3
"""
Test script for DOCX event parser
Usage: python test_docx_parser.py documents/parse_doc.docx
"""
import sys
from main import parse_docx_event
import json

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_docx_parser.py <path_to_docx>")
        sys.exit(1)

    docx_path = sys.argv[1]
    print(f"Parsing DOCX file: {docx_path}")
    print("-" * 50)

    result = parse_docx_event(docx_path)

    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print("Successfully parsed event:")
        print(json.dumps(result, indent=2))

        print("\n" + "=" * 50)
        print("To add this event to your database:")
        print(f"1. Open data/campus_events.json")
        print(f"2. Add this event to the 'events' array")
        print(f"3. Assign it a unique ID (e.g., 'evt006')")
