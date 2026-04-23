#!/usr/bin/env python3
from __future__ import annotations

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
TXT_PATH = MANIFEST_ROOT / "nacie_tecdoc_files_inventory.txt"
JSON_PATH = MANIFEST_ROOT / "nacie_tecdoc_files_inventory.json"

# Files smaller than or equal to this threshold are suspicious and may be
# placeholders, especially if combined with version v00.
PLACEHOLDER_SIZE_THRESHOLD = 20_000  # bytes

# In the current corpus, many placeholder Word documents had this exact size.
KNOWN_PLACEHOLDER_DOCX_SIZE = 13_325


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class InventoryRow:
    """
    One row of inventory information for a single file found under 01-source.

    Fields are designed to be easy to export both to fixed-width text and JSON
    and to support later QA checks and manifest generation.
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
    """
    parts = path.parts

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
    """
    _ = category
    _ = section

    pattern_with_item = (
        r"^(?P<item>\d{2})-(?P<short>.+)-v(?P<ver>\d{2})"
        r"\.(docx|pptx|md|txt|xlsx|pdf)$"
    )

    pattern_without_item = (
        r"^(?P<short>.+)-v(?P<ver>\d{2})"
        r"\.(docx|pptx|md|txt|xlsx|pdf)$"
    )

    for pattern in (pattern_with_item, pattern_without_item):
        match = re.fullmatch(pattern, filename, re.IGNORECASE)
        if not match:
            continue

        groups = match.groupdict()
        item_no = int(groups["item"]) if groups.get("item") else None
        short_name = groups.get("short")
        version = groups.get("ver")
        return item_no, short_name, version

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
    """
    reasons: list[str] = []

    if size_bytes == 0:
        reasons.append("empty file")

    if size_bytes <= PLACEHOLDER_SIZE_THRESHOLD:
        reasons.append(f"small file <= {PLACEHOLDER_SIZE_THRESHOLD} bytes")

    if version == "00":
        reasons.append("version v00")

    filename_lower = path.name.lower()
    if filename_lower.endswith(".docx") and size_bytes == KNOWN_PLACEHOLDER_DOCX_SIZE:
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
    """
    rows: list[InventoryRow] = []

    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(f"Source directory not found: {SOURCE_ROOT}")

    for path in sorted(SOURCE_ROOT.rglob("*")):
        if not path.is_file():
            continue

        rel_path = path.relative_to(SOURCE_ROOT)
        category, section = classify_path(rel_path)
        item_no, short_name, version = parse_filename(category, section, path.name)

        size_bytes = path.stat().st_size
        size_kb = round(size_bytes / 1024.0, 1)

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
# Formatting helpers
# ---------------------------------------------------------------------------

def truncate(value: str, width: int) -> str:
    """
    Truncate a string to fit a fixed-width text column.
    """
    if len(value) <= width:
        return value

    if width <= 3:
        return value[:width]

    return value[: width - 3] + "..."


def format_item_no(item_no: Optional[int]) -> str:
    """
    Format the item number for fixed-width output.
    """
    if item_no is None:
        return ""
    return f"{item_no:02d}"


def generic_status(row: InventoryRow) -> str:
    """
    Return a short generic status label for the full inventory table.
    """
    return "placeholder" if row.placeholder_likely else "normal"


def rows_for_section(rows: list[InventoryRow], section: str) -> list[InventoryRow]:
    """
    Filter rows for one section and sort them by item number then path.
    """
    return sorted(
        [row for row in rows if row.section == section],
        key=lambda row: ((row.item_no or 9999), row.rel_path),
    )


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_text_report(rows: list[InventoryRow], path: Path) -> None:
    """
    Write the inventory rows to a fixed-width plain text report.

    The report is intended for easy reading in a text editor or terminal and
    starts with compact summaries before the full listing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    section_w = 29
    item_w = 4
    version_w = 7
    size_w = 8
    status_w = 22
    short_name_w = 30

    chapter_rows = rows_for_section(rows, "chapters")
    annex1_rows = rows_for_section(rows, "annex-I-technical-specification")
    annex2_rows = rows_for_section(rows, "annex-II-organizations")
    annex3_rows = rows_for_section(rows, "annex-III-codes")
    annex4_rows = rows_for_section(rows, "annex-IV-individual-results")

    with path.open("w", encoding="utf-8") as handle:
        # -------------------------------------------------------------------
        # Compact section summaries
        # -------------------------------------------------------------------
        handle.write("SECTION SUMMARY\n")
        handle.write("---------------\n")

        def write_section_summary(label: str, section_rows: list[InventoryRow]) -> None:
            total = len(section_rows)
            placeholders = sum(1 for row in section_rows if row.placeholder_likely)
            present = total - placeholders
            handle.write(
                f"- {label}: total={total}, present={present}, placeholders={placeholders}\n"
            )

        write_section_summary("chapters", chapter_rows)
        write_section_summary("annex-I-technical-specification", annex1_rows)
        write_section_summary("annex-II-organizations", annex2_rows)
        write_section_summary("annex-III-codes", annex3_rows)
        write_section_summary("annex-IV-individual-results", annex4_rows)

        handle.write("\n")

        # -------------------------------------------------------------------
        # Full inventory table
        # -------------------------------------------------------------------
        handle.write("FULL FILE INVENTORY\n")
        handle.write("-------------------\n")

        header = (
            f"{'SECTION':<{section_w}}  "
            f"{'ITEM':>{item_w}}  "
            f"{'VERSION':<{version_w}}  "
            f"{'SIZE_KB':>{size_w}}  "
            f"{'STATUS':<{status_w}}  "
            f"{'SHORT_NAME':<{short_name_w}}  "
            f"REL_PATH"
        )

        separator = (
            f"{'-' * section_w}  "
            f"{'-' * item_w}  "
            f"{'-' * version_w}  "
            f"{'-' * size_w}  "
            f"{'-' * status_w}  "
            f"{'-' * short_name_w}  "
            f"{'-' * 40}"
        )

        handle.write(header + "\n")
        handle.write(separator + "\n")

        for row in rows:
            status = generic_status(row)

            handle.write(
                f"{truncate(row.section, section_w):<{section_w}}  "
                f"{format_item_no(row.item_no):>{item_w}}  "
                f"{truncate(row.version or '', version_w):<{version_w}}  "
                f"{row.size_kb:>{size_w}.1f}  "
                f"{status:<{status_w}}  "
                f"{truncate(row.short_name or '', short_name_w):<{short_name_w}}  "
                f"{row.rel_path}\n"
            )

        handle.write("\n")

        # -------------------------------------------------------------------
        # Minimal notes
        # -------------------------------------------------------------------
        handle.write("ANNEX NOTES\n")
        handle.write("-----------\n")
        handle.write("- No special annex notes.\n")

        handle.write("\n")

        handle.write("WARNINGS / MANUAL CHECKS\n")
        handle.write("------------------------\n")

        warning_lines: list[str] = []

        # Only report unusual cases here:
        # placeholder flagged, but version is not v00.
        suspicious_non_v00 = [
            row for row in rows
            if row.placeholder_likely and row.version not in {None, "00"}
        ]

        for row in suspicious_non_v00:
            warning_lines.append(
                f"Check manually: {row.rel_path} is v{row.version or '-'} "
                f"but was flagged as placeholder ({row.placeholder_reason})."
            )

        if warning_lines:
            for line in warning_lines:
                handle.write(f"- {line}\n")
        else:
            handle.write("- No unusual manual checks.\n")


def write_json(rows: list[InventoryRow], path: Path) -> None:
    """
    Write the inventory rows to JSON.
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
    print(f"TXT : {TXT_PATH}")
    print(f"JSON: {JSON_PATH}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Run the full inventory generation workflow.
    """
    rows = build_inventory()
    write_text_report(rows, TXT_PATH)
    write_json(rows, JSON_PATH)
    print_summary(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())