#!/usr/bin/env python3
from pathlib import Path

# Creates the directory tree in the current working directory
ROOT = Path.cwd()

DIRS = [
    "00-admin",
    "01-source/chapters",
    "01-source/annex-I-technical-specification",
    "01-source/annex-II-organizations",
    "01-source/annex-III-codes",
    "01-source/annex-IV-individual-results",
    "02-manifest",
    "03-normalized/chapters",
    "03-normalized/annex-I-technical-specification",
    "03-normalized/annex-II-organizations",
    "03-normalized/annex-III-codes",
    "03-normalized/annex-IV-individual-results",
    "04-assets/chapters",
    "04-assets/annex-II-organizations",
    "04-assets/annex-III-codes",
    "04-assets/annex-IV-individual-results",
    "05-build",
    "06-master",
    "07-review",
    "08-archive/original-flat-directory",
    "09-tools/python",
    "09-tools/config",
]

FILES = [
    "00-admin/tecdoc-template.docx",
    "00-admin/editorial-rules.md",
    "00-admin/status-tracker.xlsx",
    "02-manifest/master-order.yaml",
    "02-manifest/files-inventory.csv",
    "02-manifest/files-inventory.json",
    "05-build/qa-report.md",
    "05-build/build.log",
]

def touch_if_missing(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()

def main() -> None:
    print(f"Creating NACIE TECDOC directory tree under: {ROOT}")

    for rel_dir in DIRS:
        full_dir = ROOT / rel_dir
        full_dir.mkdir(parents=True, exist_ok=True)
        print(f"[DIR ] {full_dir}")

    for rel_file in FILES:
        full_file = ROOT / rel_file
        touch_if_missing(full_file)
        print(f"[FILE] {full_file}")

    print("Done.")

if __name__ == "__main__":
    main()