import json
import glob
import os
from pathlib import Path

def aggregate_announcements(data_dir=None, output_file=None):
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), '../../data/announcements')
    if output_file is None:
        output_file = os.path.join(data_dir, 'all_courses_announcements.json')

    pattern = os.path.join(data_dir, 'course_*_announcements.json')
    files = glob.glob(pattern)
    all_courses = []
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Only keep relevant fields
            course_summary = {
                'course_id': data.get('course_id'),
                'course_url': data.get('course_url'),
                'total_announcements': data.get('total_announcements'),
                'announcements': [
                    {
                        'index': a.get('index'),
                        'title': a.get('title'),
                        'date': a.get('date'),
                        'url': a.get('url'),
                        'content_length': a.get('content_length')
                    } for a in data.get('announcements', [])
                ]
            }
            all_courses.append(course_summary)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_courses, f, indent=2, ensure_ascii=False)
    print(f"Aggregated {len(files)} files into {output_file}")

if __name__ == "__main__":
    aggregate_announcements()
