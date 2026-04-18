# NACIE TECDOC Document Model and Normalization Rules

## 1. Purpose

This document defines the **document model**, **normalization rules**, and **assembly principles** for the NACIE TECDOC workflow.

Its purpose is to provide a stable specification for:

- source document disassembly
- intermediate structured representation
- master document assembly
- whole-document numbering of figures, tables, and references
- QA and consistency checks

This document is intended to be the source of truth for future scripts such as:

- `nacie_tecdoc_inventory.py`
- `nacie_tecdoc_create_skeleton.py`
- `nacie_tecdoc_normalize_docx.py`
- `nacie_tecdoc_assemble_master.py`
- `nacie_tecdoc_qa_checks.py`

## 2. Overall Workflow

The recommended workflow has four layers:

1. **Source documents**
   - Word files under `01-source/`
   - human-edited contributor inputs
   - official working source material

2. **Skeleton document**
   - template-derived empty TECDOC structure
   - heading hierarchy and page layout
   - no imported source content yet

3. **Normalized intermediate representation**
   - machine-readable description of each source document
   - extracted images
   - extracted tables
   - warnings and unresolved items

4. **Assembled master**
   - populated TECDOC master document
   - globally numbered figures, tables, and references
   - final editorial polishing done in Word

## 3. Core Design Principle

The system must preserve **identity**, not **source numbering**.

This applies to:

- figures
- tables
- references

Source-local numbers such as:
- `Fig. 3`
- `Table 2`
- `[17]`

must not be treated as final numbering.

Instead, the normalization step must assign stable internal identifiers such as:

- `FIG:chapter03_001`
- `TAB:chapter03_001`
- `REF:huo2019`

Final numbering is assigned only during **full-document assembly**.

## 4. Directory-Level Responsibility

### 4.1 Source documents

Source `.docx` files are stored under:

- `01-source/chapters/`
- `01-source/annex-I-technical-specification/`
- `01-source/annex-II-organizations/`
- `01-source/annex-III-codes/`
- `01-source/annex-IV-individual-results/`

These files are considered the working source inputs.

### 4.2 Normalized outputs

Normalized outputs should be written under:

- `03-normalized/`
- `04-assets/`

### 4.3 Build outputs

Generated draft master documents and logs should be written under:

- `05-build/`

### 4.4 Editorial masters

Reviewed milestone Word documents should be stored under:

- `06-master/`

## 5. Normalized Package Structure

Each source document should be normalized into its own package.

Recommended structure:

```text
03-normalized/<doc-id>/
  content.yaml
  warnings.yaml

04-assets/<doc-id>/
  images/
  tables/
```

Example:

```text
03-normalized/chapter03/
  content.yaml
  warnings.yaml

04-assets/chapter03/
  images/
    fig_001.png
    fig_002.emf
  tables/
    table_001.yaml
```

The normalized package should be fully regenerable from the source `.docx`.

## 6. Required Metadata for Each Normalized Document

Each normalized document should contain metadata such as:

```yaml
document_id: chapter03
source_path: 01-source/chapters/03-chapter03-v01.docx
section: chapters
item_no: 3
version: "01"
title: "Chapter 3"
status: "present"
```

Minimum required fields:

- `document_id`
- `source_path`
- `section`
- `item_no` where applicable
- `version`
- `title`

Optional fields:

- `status`
- `source_hash`
- `generated_at`
- `normalizer_version`

## 7. Block Model

The normalized content must be represented as an ordered list of blocks.

Example:

```yaml
blocks:
  - type: heading
    level: 1
    text: "Benchmark description"

  - type: paragraph
    text: "The benchmark was defined in {REF:huo2019}."

  - type: figure
    id: FIG:chapter03_001
    image: images/fig_001.png
    caption: "Temperature distribution in the core."

  - type: paragraph
    text: "As shown in {FIG:chapter03_001}, the peak temperature..."

  - type: table
    id: TAB:chapter03_001
    caption: "Main input parameters."
    file: tables/table_001.yaml
```

The order of blocks in `content.yaml` must reflect the original source document order as closely as possible.

## 8. Supported Block Types

The following block types should be supported initially.

### 8.1 `heading`

```yaml
- type: heading
  level: 1
  text: "Benchmark description"
```

Required fields:
- `level`
- `text`

### 8.2 `paragraph`

```yaml
- type: paragraph
  text: "The calculation follows {REF:huo2019}."
```

Required fields:
- `text`

Paragraph text may include inline markers such as:
- `{REF:...}`
- `{FIG:...}`
- `{TAB:...}`
- later optionally `{EQ:...}`

### 8.3 `figure`

```yaml
- type: figure
  id: FIG:chapter03_001
  image: images/fig_001.png
  caption: "Temperature distribution in the core."
```

Required fields:
- `id`
- `image`
- `caption`

Optional fields:
- `source_caption_text`
- `image_format`
- `width_hint`
- `height_hint`

### 8.4 `table`

```yaml
- type: table
  id: TAB:chapter03_001
  caption: "Main input parameters."
  file: tables/table_001.yaml
```

Required fields:
- `id`
- `caption`
- `file`

Optional fields:
- `source_caption_text`
- `table_kind`

### 8.5 `equation`

Initial support may be minimal.

```yaml
- type: equation
  id: EQ:chapter03_001
  text: "Re = rho * u * D / mu"
```

### 8.6 `list`

```yaml
- type: list
  ordered: false
  items:
    - "item 1"
    - "item 2"
```

## 9. Figure Rules

### 9.1 Figure identity

Each figure must receive a stable internal ID.

Recommended pattern:

```text
FIG:<document_id>_<nnn>
```

Examples:
- `FIG:chapter03_001`
- `FIG:annexIV_01_ANL_002`

### 9.2 Figure numbering

Final visible numbering such as:
- `FIG. 1`
- `FIG. 2`

must **not** be stored in normalized content.

It must be assigned during final full-document assembly.

### 9.3 Figure references in text

In normalized text, references to figures should use markers such as:

```text
{FIG:chapter03_001}
```

The assembler later resolves these to final visible numbering.

## 10. Table Rules

### 10.1 Table identity

Each table must receive a stable internal ID.

Recommended pattern:

```text
TAB:<document_id>_<nnn>
```

Examples:
- `TAB:chapter03_001`
- `TAB:annexIII_14_001`

### 10.2 Table numbering

Final visible numbering such as:
- `Table 1`
- `Table 2`

must **not** be stored in normalized content.

It must be assigned only during final assembly.

### 10.3 Table references in text

In normalized text, references to tables should use markers such as:

```text
{TAB:chapter03_001}
```

The assembler later resolves these to final visible numbering.

## 11. Reference Rules

### 11.1 Reference identity

Each bibliographic entry must receive a stable internal ID.

Recommended pattern:

```text
REF:<key>
```

Examples:
- `REF:huo2019`
- `REF:iaea2024_sodium`
- `REF:subbotin1963`

### 11.2 References block

Each normalized document may contain a `references` section:

```yaml
references:
  - id: REF:huo2019
    raw_text: 'HUO, X., VIRGILI, N., KRIVENTSEV, V., "Technical Specifications for Neutronics Benchmark of CEFR Start-up Tests", ...'

  - id: REF:iaea2024_sodium
    raw_text: 'INTERNATIONAL ATOMIC ENERGY AGENCY, Sodium Coolant Handbook: Thermal-Hydraulic Correlations, IAEA, Vienna (2024).'
```

Required fields:
- `id`
- `raw_text`

Optional fields:
- `authors`
- `title`
- `year`
- `publisher`
- `doi`
- `url`
- `normalized_text`

### 11.3 In-text citation markers

Normalized paragraph text should use internal reference markers:

```text
The benchmark definition is given in {REF:huo2019}.
```

Source numbering such as `[7]` must not be preserved as final numbering.

### 11.4 Flat numbering of references

The final TECDOC must use one flat numbering across the whole document:

- `[1]`
- `[2]`
- `[3]`
- ...

These numbers must be assigned during assembly after global collection and deduplication of all references.

### 11.5 Reference deduplication

Two source documents may cite the same work using slightly different text.

Therefore, assembly must later support:
- exact match
- normalized-text match
- manual alias mapping if needed

A future mapping file may be introduced, for example:

```text
02-manifest/nacie_tecdoc_reference_aliases.yaml
```

## 12. Flat Numbering Rule for the Whole Document

The final TECDOC must have one flat numbering across the entire document for:

- figures
- tables
- references

This means:

- figures are numbered in document order across all chapters and annexes
- tables are numbered in document order across all chapters and annexes
- references are numbered in final bibliography order after deduplication

No section-local numbering is allowed unless explicitly required later by IAEA rules.

## 13. Placeholder Rule

Placeholder source files should normally be indicated by:

- version `v00`
- very small file size
- repeated placeholder docx size observed in the corpus

The normalizer should preserve placeholder documents as source metadata, but usually should not try to produce rich content from them.

A placeholder normalized package may contain:

```yaml
status: placeholder
blocks: []
references: []
```

and warnings such as:

```yaml
warnings:
  - "Source file appears to be a placeholder."
```

## 14. Warnings and QA

Each normalized package should include a `warnings.yaml` file for issues such as:

- figure without caption
- table without caption
- manual numbering detected
- unresolved citation
- suspicious heading structure
- unsupported object type
- equation could not be parsed
- placeholder source file

Warnings are not failures. They are editorial signals for later review.

## 15. What the Normalizer Must Preserve

The normalizer must preserve:

- source order
- semantic structure
- text content
- figures as extracted assets
- tables as structured data where possible
- captions
- citation identities

The normalizer should avoid preserving:

- source-local numbering as final numbering
- irrelevant layout artifacts
- copied Word formatting junk
- arbitrary local styles from contributor documents

## 16. What the Assembler Must Do

The assembler must:

1. read the skeleton TECDOC document
2. read normalized source packages
3. insert normalized content into the right sections
4. assign global flat numbering for:
   - figures
   - tables
   - references
5. resolve inline markers:
   - `{FIG:...}`
   - `{TAB:...}`
   - `{REF:...}`
6. generate the final bibliography
7. keep unresolved items visible for editorial review

## 17. First Implementation Scope

The first normalizer version does **not** need to solve everything.

Recommended first scope:

- headings
- paragraphs
- figures
- tables
- simple captions
- reference entries
- inline reference markers
- warnings

Later scope may add:

- equations
- lists
- footnotes
- advanced cross-reference repair
- bibliography metadata parsing
- equation numbering

## 18. Immediate Next Deliverables

The next practical deliverables should be:

1. `nacie_tecdoc_normalize_docx.py`
   - prototype normalizer for one source `.docx`

2. sample normalized packages for:
   - one chapter
   - one annex II organization file
   - one annex III code file
   - one annex IV individual-results file

3. later:
   - `nacie_tecdoc_assemble_master.py`

## 19. Summary Rule

The normalized representation must store:

- **figure identities**
- **table identities**
- **reference identities**
- **text containing internal markers**

The final TECDOC numbering must be assigned only at the **assembly stage**, not during normalization.
