# SOP Management Platform

**Core Technology Platforms — New York University Abu Dhabi**

A centralized system for creating, managing, and publishing Standard Operating Procedures (SOPs). Non-technical users edit simple YAML files, and the build system automatically generates professional HTML and DOCX documents.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create a new SOP
```bash
python scripts/new_sop.py
```
This will walk you through creating a new SOP and generate the template files for you.

### 3. Edit your SOP
Open the generated files and fill in the details:
- **`sop.yaml`** — SOP metadata, hazards, PPE, training (structured fields)
- **`procedure.md`** — Step-by-step procedure (write in plain text with Markdown)

### 4. Validate
```bash
python scripts/validate.py
```

### 5. Build
```bash
python scripts/build_sops.py --all
```
Output will be in `build/html/` (web pages) and `build/docx/` (Word documents).

---

## How It Works

SOPs are composed of three layers of information that are **merged at build time**:

| Layer | Location | Who Edits | Scope |
|-------|----------|-----------|-------|
| **CTP-Wide** | `config/ctp_global.yaml` | Administrators | All SOPs |
| **Lab-Specific** | `labs/<lab>/lab_info.yaml` | Lab Managers | All SOPs in that lab |
| **SOP-Specific** | `sops/<lab>/<sop>/sop.yaml` | SOP Authors | Individual SOP |

**Change once, update everywhere:** Editing `ctp_global.yaml` (e.g., updating an emergency contact) will automatically update every SOP the next time you build.

---

## Project Structure

```
SOP_template/
├── config/ctp_global.yaml          ← Shared institution info
├── labs/
│   ├── _lab_template.yaml          ← Copy this for new labs
│   └── example_lab/lab_info.yaml
├── sops/
│   ├── _sop_template.yaml          ← Copy this for new SOPs
│   ├── _procedure_template.md
│   └── example_lab/
│       └── confocal_microscope_xyz/
│           ├── sop.yaml
│           └── procedure.md
├── templates/                       ← HTML/DOCX templates (admin only)
├── schema/                          ← Validation schemas
├── scripts/                         ← Build tools
└── build/                           ← Generated output (gitignored)
```

---

## Common Tasks

### Add a new lab
1. Create folder: `labs/<lab_name>/`
2. Copy `labs/_lab_template.yaml` → `labs/<lab_name>/lab_info.yaml`
3. Edit the file with your lab's details

### Add a new SOP
Run the helper script:
```bash
python scripts/new_sop.py
```
Or manually:
1. Create folder: `sops/<lab_name>/<sop_name>/`
2. Copy `sops/_sop_template.yaml` → `sops/<lab>/<sop>/sop.yaml`
3. Copy `sops/_procedure_template.md` → `sops/<lab>/<sop>/procedure.md`
4. Edit both files

### Build commands
```bash
python scripts/build_sops.py              # Build approved SOPs only
python scripts/build_sops.py --all        # Build everything
python scripts/build_sops.py --drafts     # Include drafts
python scripts/build_sops.py --html-only  # HTML only
python scripts/build_sops.py --docx-only  # DOCX only
python scripts/build_sops.py --sop example_lab/confocal_microscope_xyz  # Single SOP
```

### Validate without building
```bash
python scripts/validate.py                # Validate everything
python scripts/validate.py --config       # Check CTP config only
python scripts/validate.py --lab example_lab
python scripts/validate.py --sop example_lab/confocal_microscope_xyz
```

---

## Editing YAML Files

YAML files use simple `key: value` pairs. Here's what you need to know:

- **Text fields**: Just type after the colon: `title: "My SOP Title"`
- **Multi-line text**: Use `|` then indent:
  ```yaml
  description: |
    This is a longer description
    that spans multiple lines.
  ```
- **Checklists**: Use `true` or `false`: `safety_goggles: true`
- **Lists**: Use `- ` prefix:
  ```yaml
  references:
    - "First reference"
    - "Second reference"
  ```
- **Comments**: Lines starting with `#` are notes for you, they're ignored by the system

---

## Deployment

### GitHub Pages (Automatic)

The included GitHub Actions workflow (`.github/workflows/build-deploy.yml`) automatically builds and deploys whenever changes are pushed to `main`.

### Manual Deployment

1. Run `python scripts/build_sops.py --all`
2. Upload the contents of `build/html/` to any web server
