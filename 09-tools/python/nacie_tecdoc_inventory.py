#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Resolve the repository root from the script location, not from the shell's
# current working directory.
#
# Script location:
#   ./ACT/ACT-26-03-NACIE-TECDOC/09-tools/python/nacie_tecdoc_inventory.py
#
# Project root:
#   ./ACT/ACT-26-03-NACIE-TECDOC
SCRIPT_PATH = Path(__file__).resolve()
ROOT = SCRIPT_PATH.parents[2]

# Source documents organized by section.
SOURCE_ROOT = ROOT / "01-source"

# Output location for generated inventory files.
MANIFEST_ROOT = ROOT / "02-manifest"

# Inventory output files.
CSV_PATH = MANIFEST_ROOT / "files-inventory.csv"
JSON_PATH = MANIFEST_ROOT / "files-inventory.json"

# Files smaller than or equal to this threshold are suspicious and may be
# placeholders, especially if combined with version v00.
PLACEHOLDER_SIZE_THRESHOLD = 20_000  # bytes

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class InventoryRow:
    """
    One row of inventory information for a single file found under 01-source.

    Fields are designed to be easy to export both to CSV and JSON and to
    support later QA checks and manifest generation.
    """
    rel_path: str
    category: str
    section: str
    item_no: Optional[int]
    short_name: Optional[str]
    version: Optional[str]
    extension: str
    size_bytes: int
    size_kb: float
    placeholder_likely: bool
    placeholder_reason: str
    exists: bool


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def classify_path(path: Path) -> tuple[str, str]:
    """
    Classify a file based on its path relative to 01-source.

    Parameters
    ----------
    path : Path
        Path relative to SOURCE_ROOT, for example:
        'chapters/01-chapter01-v01.docx'

    Returns
    -------
    tuple[str, str]
        (category, section), where:
        - category is a broad class such as 'chapter' or 'annex'
        - section is the exact top-level source subsection
    """
    parts = path.parts

    # We expect at least:
    #   top-level folder / filename
    if len(parts) < 2:
        return "unknown", "unknown"

    top = parts[0]

    if top == "chapters":
        return "chapter", "chapters"
    if top == "annex-I-technical-specification":
        return "annex", "annex-I-technical-specification"
    if top == "annex-II-organizations":
        return "annex", "annex-II-organizations"
    if top == "annex-III-codes":
        return "annex", "annex-III-codes"
    if top == "annex-IV-individual-results":
        return "annex", "annex-IV-individual-results"

    # Fallback for unexpected directory names.
    return "unknown", top


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------

def parse_filename(
    category: str,
    section: str,
    filename: str,
) -> tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Extract structured information from a normalized filename.

    Parameters
    ----------
    category : str
        High-level classification such as 'chapter' or 'annex'.
        Currently not used directly in parsing logic, but kept as an argument
        because future section-specific parsing rules may depend on it.

    section : str
        Exact subsection such as 'chapters' or 'annex-III-codes'.
        Currently not used directly in parsing logic, but retained for future
        extension and readability.

    filename : str
        File name only, for example:
        '03-chapter03-v01.docx'
        '11-KIT-v01.docx'
        '21-sam-moose-scm-v01.docx'

    Returns
    -------
    tuple[Optional[int], Optional[str], Optional[str]]
        (item_no, short_name, version)

        - item_no: leading numeric item index if present
        - short_name: the descriptive middle part
        - version: two-digit version string without the leading 'v'
    """
    # Pattern 1:
    #   NN-short-name-vNN.ext
    #
    # Examples:
    #   03-chapter03-v01.docx
    #   11-KIT-v01.docx
    #   21-sam-moose-scm-v01.docx
    pattern_with_item = (
        r"^(?P<item>\d{2})-(?P<short>.+)-v(?P<ver>\d{2})"
        r"\.(docx|pptx|md|txt|xlsx)$"
    )

    # Pattern 2:
    #   short-name-vNN.ext
    #
    # This is a fallback for files without a leading numeric index.
    pattern_without_item = (
        r"^(?P<short>.+)-v(?P<ver>\d{2})"
        r"\.(docx|pptx|md|txt|xlsx)$"
    )

    patterns = [pattern_with_item, pattern_without_item]

    for pattern in patterns:
        match = re.fullmatch(pattern, filename, re.IGNORECASE)
        if not match:
            continue

        groups = match.groupdict()
        item_no = int(groups["item"]) if groups.get("item") else None
        short_name = groups.get("short")
        version = groups.get("ver")
        return item_no, short_name, version

    # Could not parse expected fields from the file name.
    return None, None, None


# ---------------------------------------------------------------------------
# Placeholder detection
# ---------------------------------------------------------------------------

def detect_placeholder(
    path: Path,
    size_bytes: int,
    version: Optional[str],
) -> tuple[bool, str]:
    """
    Determine whether a file is likely a placeholder or near-empty template.

    Heuristics used here are intentionally simple and conservative:
    - zero-byte file
    - very small file
    - version v00
    - exact size equal to a repeated placeholder DOCX size observed in the corpus

    Parameters
    ----------
    path : Path
        File path, used mainly for extension-based checks.

    size_bytes : int
        File size in bytes.

    version : Optional[str]
        Parsed version string, such as '00' or '01'.

    Returns
    -------
    tuple[bool, str]
        (placeholder_likely, reason)

        If placeholder_likely is True, reason contains a semicolon-separated
        explanation of which rules fired.
    """
    reasons: list[str] = []

    if size_bytes == 0:
        reasons.append("empty file")

    if size_bytes <= PLACEHOLDER_SIZE_THRESHOLD:
        reasons.append(f"small file <= {PLACEHOLDER_SIZE_THRESHOLD} bytes")

    if version == "00":
        reasons.append("version v00")

    # In your current corpus, many placeholder Word documents had the exact
    # same size. This is a useful strong signal.
    filename_lower = path.name.lower()
    if filename_lower.endswith(".docx") and size_bytes == 13_325:
        reasons.append("exact size matches common placeholder docx")

    if reasons:
        return True, "; ".join(reasons)

    return False, ""


# ---------------------------------------------------------------------------
# Inventory generation
# ---------------------------------------------------------------------------

def build_inventory() -> list[InventoryRow]:
    """
    Scan 01-source recursively and build the file inventory.

    Returns
    -------
    list[InventoryRow]
        One inventory row per file found in the source tree.

    Raises
    ------
    FileNotFoundError
        If SOURCE_ROOT does not exist.
    """
    rows: list[InventoryRow] = []

    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(f"Source directory not found: {SOURCE_ROOT}")

    # rglob("*") recursively scans all files and folders under 01-source.
    for path in sorted(SOURCE_ROOT.rglob("*")):
        if not path.is_file():
            continue

        # Path relative to 01-source is more useful than absolute paths in the
        # manifest, because it remains portable across machines.
        rel_path = path.relative_to(SOURCE_ROOT)

        # Determine broad document type and exact section.
        category, section = classify_path(rel_path)

        # Parse structured fields from the normalized file name.
        item_no, short_name, version = parse_filename(category, section, path.name)

        # Collect file statistics.
        size_bytes = path.stat().st_size
        size_kb = round(size_bytes / 1024.0, 1)

        # Detect whether this looks like a placeholder/incomplete input.
        placeholder_likely, placeholder_reason = detect_placeholder(
            path=path,
            size_bytes=size_bytes,
            version=version,
        )

        rows.append(
            InventoryRow(
                rel_path=str(rel_path),
                category=category,
                section=section,
                item_no=item_no,
                short_name=short_name,
                version=version,
                extension=path.suffix.lower(),
                size_bytes=size_bytes,
                size_kb=size_kb,
                placeholder_likely=placeholder_likely,
                placeholder_reason=placeholder_reason,
                exists=True,
            )
        )

    return rows


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_csv(rows: list[InventoryRow], path: Path) -> None:
    """
    Write the inventory rows to CSV.

    Parameters
    ----------
    rows : list[InventoryRow]
        Inventory rows to export.

    path : Path
        Output CSV path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "rel_path",
        "category",
        "section",
        "item_no",
        "short_name",
        "version",
        "extension",
        "size_bytes",
        "size_kb",
        "placeholder_likely",
        "placeholder_reason",
        "exists",
    ]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(asdict(row))


def write_json(rows: list[InventoryRow], path: Path) -> None:
    """
    Write the inventory rows to JSON.

    Parameters
    ----------
    rows : list[InventoryRow]
        Inventory rows to export.

    path : Path
        Output JSON path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "root": str(SOURCE_ROOT),
        "file_count": len(rows),
        "placeholder_count": sum(1 for row in rows if row.placeholder_likely),
        "files": [asdict(row) for row in rows],
    }

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_summary(rows: list[InventoryRow]) -> None:
    """
    Print a short console summary after inventory generation.

    Parameters
    ----------
    rows : list[InventoryRow]
        Inventory rows that were generated.
    """
    by_section: dict[str, int] = {}
    placeholder_by_section: dict[str, int] = {}

    for row in rows:
        by_section[row.section] = by_section.get(row.section, 0) + 1

        if row.placeholder_likely:
            placeholder_by_section[row.section] = (
                placeholder_by_section.get(row.section, 0) + 1
            )

    print(f"Inventory written for {len(rows)} files.")
    print()

    print("Files by section:")
    for section in sorted(by_section):
        print(f"  {section}: {by_section[section]}")

    print()
    print("Likely placeholders by section:")
    for section in sorted(by_section):
        count = placeholder_by_section.get(section, 0)
        print(f"  {section}: {count}")

    print()
    print(f"CSV : {CSV_PATH}")
    print(f"JSON: {JSON_PATH}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Run the full inventory generation workflow.

    Steps
    -----
    1. Scan source files
    2. Build structured inventory rows
    3. Write CSV output
    4. Write JSON output
    5. Print console summary

    Returns
    -------
    int
        Exit code suitable for command-line usage.
    """
    rows = build_inventory()
    write_csv(rows, CSV_PATH)
    write_json(rows, JSON_PATH)
    print_summary(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())