#!/usr/bin/env python3
from pathlib import Path
import shutil
import re
import sys

ROOT = Path.cwd()
SRC = ROOT / "docs"

DEST_ADMIN = ROOT / "00-admin"
DEST_CHAPTERS = ROOT / "01-source" / "chapters"
DEST_ANNEX_I = ROOT / "01-source" / "annex-I-technical-specification"
DEST_ANNEX_II = ROOT / "01-source" / "annex-II-organizations"
DEST_ANNEX_III = ROOT / "01-source" / "annex-III-codes"
DEST_ANNEX_IV = ROOT / "01-source" / "annex-IV-individual-results"
DEST_ARCHIVE = ROOT / "08-archive" / "original-flat-directory"

DOCX_EXT = ".docx"
PPTX_EXT = ".pptx"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)
    print(f"[COPY] {src.name} -> {dst}")


def normalize_spaces(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.lower()


def detect_structure_file(name: str) -> bool:
    return name.lower() == "00-structure-v01.docx"


def detect_status_pptx(name: str) -> bool:
    return name.lower().endswith(".pptx")


def map_chapter(filename: str):
    m = re.fullmatch(r"(0[1-9]|1[0-2])-(.+)-v(\d{2})\.docx", filename, re.IGNORECASE)
    if not m:
        return None

    num, title, ver = m.groups()
    title = normalize_spaces(title)
    new_name = f"{num}-{title}-v{ver}.docx"
    return DEST_CHAPTERS / new_name


def map_annex_i(filename: str):
    m = re.fullmatch(r"13-annexI-technical-specification-v(\d{2})\.docx", filename, re.IGNORECASE)
    if not m:
        return None
    ver = m.group(1)
    return DEST_ANNEX_I / f"13-annexI-technical-specification-v{ver}.docx"


def map_annex_ii(filename: str):
    m = re.fullmatch(
        r"14-annexII-description-of-organizations-(\d{2})-([A-Za-z0-9_-]+)-v(\d{2})\.docx",
        filename,
        re.IGNORECASE,
    )
    if not m:
        return None
    idx, org, ver = m.groups()
    org = normalize_spaces(org)
    return DEST_ANNEX_II / f"{idx}-{org.upper()}-v{ver}.docx"


def map_annex_iii(filename: str):
    m = re.fullmatch(
        r"15-annexIII-description-of-codes-(\d{2})-([A-Za-z0-9_.\- ]+)-v(\d{2})\.docx",
        filename,
        re.IGNORECASE,
    )
    if not m:
        return None
    idx, code, ver = m.groups()
    code = normalize_spaces(code)
    return DEST_ANNEX_III / f"{idx}-{code}-v{ver}.docx"


def map_annex_iv(filename: str):
    # Accept both "individual results" and "individual-results"
    m = re.fullmatch(
        r"16-annexIV-individual[- ]results-(\d{2})-([A-Za-z0-9_-]+)-v(\d{2})\.docx",
        filename,
        re.IGNORECASE,
    )
    if not m:
        return None
    idx, org, ver = m.groups()
    org = normalize_spaces(org)
    return DEST_ANNEX_IV / f"{idx}-{org.upper()}-v{ver}.docx"


def map_file(src: Path):
    name = src.name

    if detect_structure_file(name):
        return DEST_ADMIN / name

    if detect_status_pptx(name):
        # Keep this in admin with original name
        return DEST_ADMIN / name

    for mapper in (map_chapter, map_annex_i, map_annex_ii, map_annex_iii, map_annex_iv):
        dst = mapper(name)
        if dst is not None:
            return dst

    return None


def main() -> int:
    if not SRC.exists():
        print(f"ERROR: source directory does not exist: {SRC}", file=sys.stderr)
        return 1

    for d in [
        DEST_ADMIN,
        DEST_CHAPTERS,
        DEST_ANNEX_I,
        DEST_ANNEX_II,
        DEST_ANNEX_III,
        DEST_ANNEX_IV,
        DEST_ARCHIVE,
    ]:
        ensure_dir(d)

    unmatched = []
    copied = 0

    for src in sorted(SRC.iterdir()):
        if not src.is_file():
            continue

        dst = map_file(src)
        if dst is None:
            unmatched.append(src.name)
            continue

        if dst.exists():
            print(f"[SKIP] destination exists: {dst}")
            continue

        copy_file(src, dst)
        copied += 1

    # Optional: keep a snapshot of the original flat directory listing
    list_file = SRC / "list.txt"
    if list_file.exists():
        archive_copy = DEST_ARCHIVE / "list.txt"
        if not archive_copy.exists():
            copy_file(list_file, archive_copy)

    print()
    print(f"Copied {copied} files.")

    if unmatched:
        print("\nUnmatched files:")
        for name in unmatched:
            print(f"  - {name}")
        print("\nThese files were not copied because no mapping rule matched them.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())