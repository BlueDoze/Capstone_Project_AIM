#!/usr/bin/env python3
"""
Aggregates professor information from individual course folders into a consolidated file.

Usage:
    python3 src/scrapers/d2l/aggregate_professors.py

Output:
    data/professors_consolidated.json
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def find_professor_files(data_dir: Path) -> List[Path]:
    """Find all professor_info.json files in course_* subdirectories."""
    pattern = "course_*/professor_info.json"
    return sorted(data_dir.glob(pattern))


def load_professor_data(file_path: Path) -> Dict[str, Any]:
    """Load and parse a professor_info.json file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def aggregate_professors(data_dir: Path) -> Dict[str, Any]:
    """Aggregate all professor information from course folders."""
    professor_files = find_professor_files(data_dir)

    if not professor_files:
        print("⚠️  No professor_info.json files found in course folders", file=sys.stderr)
        return {
            "aggregated_at": datetime.now().isoformat(),
            "total_courses": 0,
            "total_professors_found": 0,
            "courses": []
        }

    courses = []
    professors_found = 0

    for file_path in professor_files:
        try:
            print(f"   Reading: {file_path.parent.name}/professor_info.json")
            data = load_professor_data(file_path)

            # Create clean course entry
            course_entry = {
                "course_id": data.get("course_id"),
                "professor": {
                    "name": data.get("name"),
                    "email": data.get("email"),
                    "office": data.get("office"),
                    "office_hours": data.get("office_hours")
                },
                "extraction_method": data.get("extraction_method"),
                "extracted_at": data.get("extracted_at"),
                "source_url": data.get("source_url")
            }

            courses.append(course_entry)

            # Count if professor name was found
            if data.get("name"):
                professors_found += 1
                print(f"      ✓ Professor: {data.get('name')}")
            else:
                print(f"      ⚠️  Professor name not found")

        except FileNotFoundError:
            print(f"   ⚠️  File not found: {file_path}", file=sys.stderr)
            continue
        except json.JSONDecodeError as e:
            print(f"   ⚠️  Invalid JSON in {file_path}: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"   ⚠️  Error reading {file_path}: {e}", file=sys.stderr)
            continue

    return {
        "aggregated_at": datetime.now().isoformat(),
        "total_courses": len(courses),
        "total_professors_found": professors_found,
        "courses": courses
    }


def main():
    """Main entry point for the aggregator script."""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    data_dir = project_root / "data"
    output_file = data_dir / "professors_consolidated.json"

    print("\n" + "=" * 70)
    print("PROFESSOR INFO AGGREGATOR")
    print("=" * 70)
    print(f"\n📂 Scanning: {data_dir}\n")

    # Aggregate data
    result = aggregate_professors(data_dir)

    # Write output
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n{'=' * 70}")
        print("✅ AGGREGATION COMPLETE")
        print("=" * 70)
        print(f"📊 Total courses: {result['total_courses']}")
        print(f"👨‍🏫 Professors found: {result['total_professors_found']}")
        print(f"📄 Output file: {output_file}")
        print("=" * 70 + "\n")

        return 0

    except PermissionError:
        print(f"\n❌ ERROR: Permission denied writing to {output_file}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: Failed to write output file: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
