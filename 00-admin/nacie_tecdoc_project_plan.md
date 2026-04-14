# NACIE TECDOC Project Plan

## 1. Purpose

This project aims to create a reproducible and maintainable workflow for compiling the **IAEA TECDOC for CRP NACIE** from distributed Word contributions into a single editorial master document.

The workflow should support:

- consistent document structure
- compliance with the IAEA TECDOC template
- continuous numbering of figures, tables, and references
- traceable source inputs
- repeated updates from contributors
- partial automation of document organization, normalization, assembly, and quality checks

---

## 2. Project Goal

Build a reproducible workflow that converts distributed NACIE source contributions into a TECDOC master document with:

- controlled structure
- traceable inputs
- automated pre-processing
- reliable whole-document numbering of figures, tables, and references

---

## 3. Main Outputs

The project should deliver the following core outputs.

### 3.1 Organized source repository

A clean and scriptable repository containing:

- normalized directory structure
- normalized filenames
- preserved source contributions
- separation of source, generated, and editorial files

### 3.2 Editorial master document

A single TECDOC master Word document based on the IAEA template.

### 3.3 Automation scripts

A set of scripts supporting:

- directory creation
- source file import and renaming
- inventory generation
- document normalization
- master assembly
- QA and validation checks

### 3.4 Machine-readable project manifest

A manifest describing:

- merge order
- source metadata
- file completeness status
- placeholder detection

### 3.5 Reviewable reports

Reports identifying:

- missing contributions
- placeholder files
- formatting issues
- unresolved references or captions
- structural inconsistencies

---

## 4. Project Scope

### 4.1 In scope

- organizing source files into a stable project structure
- tracking versions of the working repository with Git
- building scripts for inventory, normalization, assembly, and QA
- generating an automatic draft master document
- preparing the master document for final Word-based editorial work

### 4.2 Out of scope

- full replacement of Word for final editorial formatting
- guaranteed perfect automatic repair of all cross-references
- guaranteed perfect automatic bibliography resolution from inconsistent partner inputs
- direct integration with NUCLEUS at this stage

---

## 5. Working Principles

### 5.1 Separate source, generated, and editorial material

Human-edited files and machine-generated files must remain clearly separated.

- **Source files**: original contributor documents
- **Generated files**: normalized content, extracted assets, build outputs
- **Editorial files**: reviewed master documents and release candidates

### 5.2 Keep source files separate during drafting

Contributors should continue working on separate files.

A single master file should be maintained only for editorial assembly, formatting, numbering, and submission preparation.

### 5.3 Normalize identities before assigning numbering

The workflow should avoid trusting local numbering inside source documents.

Instead:

- figures should receive stable internal IDs first
- tables should receive stable internal IDs first
- references should receive stable internal IDs first
- final numbering should be assigned only at assembly or finalization stage

### 5.4 Use automation to reduce risk, not to hide errors

Scripts should produce both output and warnings.

The system should help detect:

- placeholders
- missing captions
- missing sections
- unresolved references
- heading problems
- suspicious formatting

---

## 6. Repository Structure

The working repository is organized into the following top-level folders:

```text
00-admin/
01-source/
02-manifest/
03-normalized/
04-assets/
05-build/
06-master/
07-review/
08-archive/
09-tools/
```

### 6.1 `00-admin`

Administrative and control documents:

- TECDOC template
- structure document
- editorial rules
- status tracking

### 6.2 `01-source`

Human-edited source documents:

- chapters
- annex I
- annex II organization descriptions
- annex III code descriptions
- annex IV individual results

### 6.3 `02-manifest`

Machine-readable control files:

- merge order
- inventory CSV and JSON
- completeness information

### 6.4 `03-normalized`

Normalized intermediate representations generated from source files.

### 6.5 `04-assets`

Extracted figures and possibly structured table data.

### 6.6 `05-build`

Temporary build outputs:

- generated master drafts
- logs
- QA reports

### 6.7 `06-master`

Editorial master documents and release candidates.

### 6.8 `07-review`

Review packages and review-cycle outputs.

### 6.9 `08-archive`

Archived original layouts, legacy snapshots, and deprecated working material.

### 6.10 `09-tools`

Scripts, configuration files, and related tooling.

---

## 7. Project Phases

## Phase 0 — Project Definition and Conventions

### Goal

Freeze the working rules before further automation is developed.

### Tasks

- confirm directory structure
- confirm naming conventions
- define the boundary between source, generated, and editorial files
- define merge order of chapters and annexes
- define placeholder criteria
- define the limits of automation

### Deliverables

- `README.md`
- editorial rules document
- `02-manifest/master-order.yaml`

---

## Phase 1 — Source Organization

### Goal

Make the corpus stable and scriptable.

### Tasks

- create project directory structure
- import and rename files from the original flat directory
- separate source, admin, and archive material
- create a clean repository baseline

### Status

Largely completed.

### Deliverables

- populated `01-source/`
- populated `00-admin/`
- archived original file listing
- Git baseline commit

---

## Phase 2 — Inventory and Corpus Audit

### Goal

Understand exactly what material exists before attempting full assembly.

### Tasks

Create an inventory script that scans `01-source/` and records:

- file category
- item order
- file version
- file size
- placeholder probability
- likely completeness status

Also detect:

- missing expected items
- numbering gaps
- inconsistent naming
- suspiciously small files
- duplicates

### Deliverables

- `02-manifest/files-inventory.csv`
- `02-manifest/files-inventory.json`
- first completeness report

### Success Criterion

It is possible to identify:

- which contributions exist
- which are placeholders
- which expected items are missing or incomplete

---

## Phase 3 — Normalization Design

### Goal

Define the intermediate simplified representation used by the pipeline.

### Tasks

Specify the schema for normalized packages, including:

- headings
- paragraphs
- figures
- tables
- citations or reference markers
- warnings
- extracted assets

Decide:

- what information is preserved
- what numbering is removed
- how stable internal IDs are represented

### Deliverables

- normalization schema document
- sample normalized package for one chapter
- sample normalized package for one annex IV file

### Success Criterion

At least one representative source document can be transformed into a clean intermediate structure.

---

## Phase 4 — Prototype Normalization

### Goal

Demonstrate that source `.docx` files can be simplified consistently.

### Tasks

Test normalization on representative files:

- one chapter
- one annex II organization description
- one annex III code description
- one large annex IV contribution

Extract:

- ordered text blocks
- headings
- images
- tables
- candidate captions
- warnings

### Deliverables

- content under `03-normalized/`
- content under `04-assets/`
- parser warnings and logs

### Success Criterion

Representative files can be normalized without major loss of structure.

---

## Phase 5 — Master Assembly Prototype

### Goal

Assemble a first automatic draft from normalized inputs.

### Tasks

Build an assembler that:

- starts from the TECDOC template
- inserts content in manifest order
- writes standardized headings
- inserts figures and tables
- preserves annex ordering
- creates a draft master document

At this stage:

- do not over-engineer cross-reference repair
- focus on robust assembly

### Deliverables

- `05-build/master_auto.docx`
- assembly log
- first QA report

### Success Criterion

A readable master draft is produced with correct overall section order.

---

## Phase 6 — Numbering and Reference Strategy

### Goal

Handle whole-document numbering in a controlled way.

### Tasks

Define and implement strategy for:

- figure numbering
- table numbering
- bibliography/reference numbering
- in-text figure/table/reference markers

Recommended approach:

- use internal IDs during normalization
- assign final numbering at assembly or finalization stage
- let Word perform final field updates where practical

### Deliverables

- numbering strategy note
- prototype numbering logic
- bibliography merge approach

### Success Criterion

A repeatable workflow exists for producing continuous numbering across the master document.

---

## Phase 7 — QA and Editorial Controls

### Goal

Catch problems early and reduce manual cleanup.

### Tasks

Implement checks for:

- missing captions
- figures without references
- references without bibliography entries
- heading level jumps
- unresolved markers
- likely placeholders
- empty or near-empty sections

### Deliverables

- `05-build/qa-report.md`
- issue summary for editorial follow-up

### Success Criterion

The build produces both a master draft and a useful issue list.

---

## Phase 8 — Operational Workflow for Updates

### Goal

Make the system usable for repeated contributor updates.

### Tasks

Define the update workflow:

- contributor updates a source file
- source file is replaced in `01-source/`
- inventory is rerun
- normalization is rerun
- master is rebuilt
- QA is reviewed
- editorial master is updated

Define versioning rules:

- what is committed
- what is regenerated
- when milestone master files are frozen

### Deliverables

- workflow note
- Git usage rules
- release naming convention for editorial master files

### Success Criterion

New rounds of contributor updates can be processed without disrupting the workflow.

---

## Phase 9 — Final Editorial Production

### Goal

Produce the submission-quality TECDOC.

### Tasks

- final harmonization of wording and style
- final numbering verification
- final template formatting
- final TOC, list of figures, and list of tables update
- final review cycle
- freeze submission version

### Deliverables

- `06-master/NACIE-TECDOC-master-submission.docx`
- final QA checklist
- archive snapshot

---

## 8. Main Deliverables by Type

### 8.1 Governance and Project Definition

- `README.md`
- editorial rules
- merge-order manifest
- versioning rules

### 8.2 Source Management

- organized `01-source/`
- inventory CSV and JSON
- completeness tracking

### 8.3 Automation

- `create_tree.py`
- `copy_and_rename_from_docs.py`
- `inventory.py`
- `normalize_docx.py`
- `assemble_master.py`
- `qa_checks.py`

### 8.4 Outputs

- normalized packages
- extracted assets
- generated master drafts
- QA reports
- reviewed master milestones

---

## 9. Immediate Next Steps

The recommended next steps are:

1. write this plan into the repository as Markdown
2. create the inventory script
3. define the normalization schema
4. test normalization on a few representative files

---

## 10. Success Definition

The project is successful if it provides a reproducible workflow that converts distributed NACIE source contributions into a TECDOC master document with:

- controlled structure
- traceable source inputs
- automated support for preprocessing and assembly
- reliable whole-document numbering support
- manageable editorial review and update cycles

---

## 11. Project Decomposition

The work can be treated as two linked subprojects.

### 11.1 Editorial Production

Focus:

- TECDOC structure
- consistency
- numbering
- final Word output

### 11.2 Tooling and Automation

Focus:

- inventory
- normalization
- assembly
- QA

This separation helps prioritize tasks and keeps editorial and technical decisions clear.
