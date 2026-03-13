"""
new_sop.py — Interactive helper to scaffold a new SOP.

Usage:
    python scripts/new_sop.py
    python scripts/new_sop.py --lab example_lab --title "My New SOP" --author "Dr. Smith"
"""

import argparse
import os
import re
import shutil

# Resolve project root (one level up from scripts/)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def slugify(text):
    """Convert a title to a folder-safe name."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s-]+', '_', text)
    return text


def discover_labs():
    """Find all lab directories."""
    labs_dir = os.path.join(ROOT, 'labs')
    if not os.path.isdir(labs_dir):
        return []
    return [
        d for d in sorted(os.listdir(labs_dir))
        if os.path.isdir(os.path.join(labs_dir, d)) and not d.startswith('_')
    ]


def get_lab_code(lab_name):
    """Read the lab code from lab_info.yaml."""
    import yaml
    lab_info_path = os.path.join(ROOT, 'labs', lab_name, 'lab_info.yaml')
    if os.path.exists(lab_info_path):
        with open(lab_info_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('lab_code', lab_name.upper()[:3])
    return lab_name.upper()[:3]


def count_sops_in_lab(lab_name):
    """Count existing SOPs for SOP number generation."""
    sops_dir = os.path.join(ROOT, 'sops', lab_name)
    if not os.path.isdir(sops_dir):
        return 0
    return len([
        d for d in os.listdir(sops_dir)
        if os.path.isdir(os.path.join(sops_dir, d)) and not d.startswith('_')
    ])


def main():
    parser = argparse.ArgumentParser(description='Create a new SOP from template')
    parser.add_argument('--lab', type=str, help='Lab folder name')
    parser.add_argument('--title', type=str, help='SOP title')
    parser.add_argument('--author', type=str, help='Author name')
    args = parser.parse_args()

    # Discover labs
    labs = discover_labs()

    # Get lab name
    if args.lab:
        lab_name = args.lab
    else:
        if labs:
            print("Available labs:")
            for i, lab in enumerate(labs, 1):
                print(f"  {i}. {lab}")
            print()

        lab_input = input("Enter lab folder name (or number from list above): ").strip()
        if lab_input.isdigit() and 1 <= int(lab_input) <= len(labs):
            lab_name = labs[int(lab_input) - 1]
        else:
            lab_name = lab_input

    # Verify lab exists
    lab_dir = os.path.join(ROOT, 'labs', lab_name)
    if not os.path.isdir(lab_dir):
        print(f"\nWarning: Lab '{lab_name}' not found in labs/ directory.")
        create = input("Create a new lab from template? (y/n): ").strip().lower()
        if create == 'y':
            os.makedirs(lab_dir, exist_ok=True)
            template = os.path.join(ROOT, 'labs', '_lab_template.yaml')
            dest = os.path.join(lab_dir, 'lab_info.yaml')
            if os.path.exists(template):
                shutil.copy2(template, dest)
                print(f"  Created: {dest}")
                print(f"  -> Please edit this file with your lab's details.")
            else:
                print(f"  Warning: Lab template not found at {template}")
        else:
            print("Aborted.")
            return

    # Get SOP title
    if args.title:
        title = args.title
    else:
        title = input("SOP title: ").strip()

    if not title:
        print("Error: title is required.")
        return

    # Get author
    if args.author:
        author = args.author
    else:
        author = input("Author name: ").strip()

    # Create SOP directory
    sop_slug = slugify(title)
    sop_dir = os.path.join(ROOT, 'sops', lab_name, sop_slug)

    if os.path.isdir(sop_dir):
        print(f"\nError: SOP directory already exists: {sop_dir}")
        return

    os.makedirs(sop_dir, exist_ok=True)

    # Generate SOP number
    lab_code = get_lab_code(lab_name)
    sop_count = count_sops_in_lab(lab_name) + 1
    sop_number = f"{lab_code}-SOP-{sop_count:03d}"

    # Read and customize the SOP template
    sop_template = os.path.join(ROOT, 'sops', '_sop_template.yaml')
    if os.path.exists(sop_template):
        with open(sop_template, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace placeholder values
        from datetime import date
        today = date.today().isoformat()

        content = content.replace(
            '[SOP Title — e.g., Operation of Confocal Microscope XYZ]', title
        )
        content = content.replace('[LAB_CODE]-SOP-[NUMBER]', sop_number)
        content = content.replace('[Author Name]', author, 1)  # first occurrence
        content = content.replace('[lab_folder_name]', lab_name)
        content = content.replace('YYYY-MM-DD', today, 1)  # first occurrence

        sop_yaml = os.path.join(sop_dir, 'sop.yaml')
        with open(sop_yaml, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        print(f"  Warning: SOP template not found at {sop_template}")

    # Copy procedure template
    proc_template = os.path.join(ROOT, 'sops', '_procedure_template.md')
    proc_dest = os.path.join(sop_dir, 'procedure.md')
    if os.path.exists(proc_template):
        shutil.copy2(proc_template, proc_dest)
    else:
        # Create a minimal procedure file
        with open(proc_dest, 'w', encoding='utf-8') as f:
            f.write("# Operating Procedure\n\n## Steps\n\n1. [First step]\n")

    # Print summary
    print()
    print(f"  SOP created successfully!")
    print(f"  SOP Number: {sop_number}")
    print()
    print(f"  Files created:")
    print(f"    {os.path.join(sop_dir, 'sop.yaml')}")
    print(f"    {os.path.join(sop_dir, 'procedure.md')}")
    print()
    print(f"  Next steps:")
    print(f"    1. Edit sop.yaml — fill in the SOP details")
    print(f"    2. Edit procedure.md — write your step-by-step procedure")
    print(f"    3. Run: python scripts/validate.py --sop {lab_name}/{sop_slug}")
    print(f"    4. Run: python scripts/build_sops.py")


if __name__ == '__main__':
    main()
