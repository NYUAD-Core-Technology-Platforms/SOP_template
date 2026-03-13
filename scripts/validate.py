"""
validate.py — Validate SOP YAML files against schemas.

Usage:
    python scripts/validate.py                    # Validate everything
    python scripts/validate.py --sop example_lab/confocal_microscope_xyz
    python scripts/validate.py --lab example_lab
    python scripts/validate.py --config
"""

import argparse
import os
import sys

import yaml
from jsonschema import validate, ValidationError

# Resolve project root (one level up from scripts/)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_yaml(path):
    """Load a YAML file and return its contents."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_schema(name):
    """Load a schema from the schema/ directory."""
    path = os.path.join(ROOT, 'schema', name)
    return load_yaml(path)


def validate_file(data, schema, filepath):
    """Validate data against a schema. Returns list of error messages."""
    errors = []
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        field_path = ' -> '.join(str(p) for p in e.absolute_path) if e.absolute_path else '(root)'
        errors.append(f"  {filepath}: [{field_path}] {e.message}")
    return errors


def validate_config():
    """Validate the CTP global config."""
    schema = load_schema('ctp_global_schema.yaml')
    config_path = os.path.join(ROOT, 'config', 'ctp_global.yaml')

    if not os.path.exists(config_path):
        return [f"  Missing: {config_path}"]

    data = load_yaml(config_path)
    return validate_file(data, schema, config_path)


def validate_lab(lab_name):
    """Validate a single lab's info file."""
    schema = load_schema('lab_info_schema.yaml')
    lab_path = os.path.join(ROOT, 'labs', lab_name, 'lab_info.yaml')

    if not os.path.exists(lab_path):
        return [f"  Missing: {lab_path}"]

    data = load_yaml(lab_path)
    return validate_file(data, schema, lab_path)


def validate_sop(sop_path_relative):
    """Validate a single SOP's data file."""
    schema = load_schema('sop_schema.yaml')
    sop_yaml = os.path.join(ROOT, 'sops', sop_path_relative, 'sop.yaml')

    if not os.path.exists(sop_yaml):
        return [f"  Missing: {sop_yaml}"]

    data = load_yaml(sop_yaml)
    errors = validate_file(data, schema, sop_yaml)

    # Check that the referenced lab exists
    lab_ref = data.get('lab', '')
    lab_dir = os.path.join(ROOT, 'labs', lab_ref)
    if lab_ref and not os.path.isdir(lab_dir):
        errors.append(f"  {sop_yaml}: lab '{lab_ref}' not found in labs/ directory")

    # Check that procedure.md exists
    proc_path = os.path.join(ROOT, 'sops', sop_path_relative, 'procedure.md')
    if not os.path.exists(proc_path):
        errors.append(f"  Warning: No procedure.md found at {proc_path}")

    return errors


def discover_labs():
    """Find all lab directories (excluding templates starting with _)."""
    labs_dir = os.path.join(ROOT, 'labs')
    if not os.path.isdir(labs_dir):
        return []
    return [
        d for d in os.listdir(labs_dir)
        if os.path.isdir(os.path.join(labs_dir, d)) and not d.startswith('_')
    ]


def discover_sops():
    """Find all SOP directories (lab/sop paths relative to sops/)."""
    sops_dir = os.path.join(ROOT, 'sops')
    if not os.path.isdir(sops_dir):
        return []
    sops = []
    for lab_name in os.listdir(sops_dir):
        lab_path = os.path.join(sops_dir, lab_name)
        if not os.path.isdir(lab_path) or lab_name.startswith('_'):
            continue
        for sop_name in os.listdir(lab_path):
            sop_path = os.path.join(lab_path, sop_name)
            if os.path.isdir(sop_path) and not sop_name.startswith('_'):
                sops.append(os.path.join(lab_name, sop_name))
    return sops


def main():
    parser = argparse.ArgumentParser(description='Validate SOP YAML files')
    parser.add_argument('--config', action='store_true', help='Validate CTP global config only')
    parser.add_argument('--lab', type=str, help='Validate a specific lab (folder name)')
    parser.add_argument('--sop', type=str, help='Validate a specific SOP (lab/sop path)')
    args = parser.parse_args()

    all_errors = []
    validated = 0

    if args.config:
        print("Validating CTP global config...")
        errors = validate_config()
        all_errors.extend(errors)
        validated += 1

    elif args.lab:
        print(f"Validating lab: {args.lab}")
        errors = validate_lab(args.lab)
        all_errors.extend(errors)
        validated += 1

    elif args.sop:
        print(f"Validating SOP: {args.sop}")
        errors = validate_sop(args.sop)
        all_errors.extend(errors)
        validated += 1

    else:
        # Validate everything
        print("Validating CTP global config...")
        all_errors.extend(validate_config())
        validated += 1

        labs = discover_labs()
        print(f"Validating {len(labs)} lab(s)...")
        for lab in labs:
            all_errors.extend(validate_lab(lab))
            validated += 1

        sops = discover_sops()
        print(f"Validating {len(sops)} SOP(s)...")
        for sop in sops:
            all_errors.extend(validate_sop(sop))
            validated += 1

    # Report
    print()
    if all_errors:
        print(f"VALIDATION FAILED — {len(all_errors)} error(s) in {validated} file(s):")
        for err in all_errors:
            print(err)
        sys.exit(1)
    else:
        print(f"All {validated} file(s) passed validation.")
        sys.exit(0)


if __name__ == '__main__':
    main()
