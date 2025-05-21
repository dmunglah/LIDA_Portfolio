#!/usr/bin/env python3

"""
Author: David Munglah
Date: 2025-04-09
Description:
This script searches recursively through a DeepLabCut project's 'labeled-data' directory 
to find all CSV files matching the pattern 'CollectedData_*.csv' and outputs their absolute 
paths to a text file.

Mac Usage:
    python find_collected_data_files.py /full/path/to/your/DLC_project collected_data_paths.txt
"""

import sys
from pathlib import Path

def find_collected_data_files(root_dir, output_file):
    root_path = Path(root_dir).resolve()
    labeled_data_path = root_path / "labeled-data"

    if not labeled_data_path.exists():
        print(f"Error: {labeled_data_path} not found.")
        sys.exit(1)

    csv_files = sorted(labeled_data_path.rglob("CollectedData_*.csv"))

    if not csv_files:
        print("No matching files found.")
    else:
        print(f"Found {len(csv_files)} file(s). Writing to {output_file}.")

    with open(output_file, "w", encoding="utf-8") as f:
        for file in csv_files:
            f.write(str(file.resolve()) + "\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python find_collected_data_files.py <project_root_path> <output_txt_file>")
        sys.exit(1)

    project_root = sys.argv[1]
    output_txt = sys.argv[2]
    find_collected_data_files(project_root, output_txt)
