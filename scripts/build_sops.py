"""
build_sops.py — Main build script for the SOP platform.

Merges 3 tiers of data (CTP-wide, lab-specific, SOP-specific),
validates inputs, and generates HTML + DOCX output.

Usage:
    python scripts/build_sops.py                    # Build all approved SOPs
    python scripts/build_sops.py --all              # Build all SOPs (any status)
    python scripts/build_sops.py --sop example_lab/confocal_microscope_xyz
    python scripts/build_sops.py --drafts           # Include drafts in build
"""

import argparse
import os
import sys
import shutil

import yaml
import markdown as md_lib
from jinja2 import Environment, FileSystemLoader
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re

# Resolve project root (one level up from scripts/)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(ROOT, 'build')
HTML_DIR = os.path.join(BUILD_DIR, 'html')
DOCX_DIR = os.path.join(HTML_DIR, 'docx')
TEMPLATES_DIR = os.path.join(ROOT, 'templates')


def load_yaml(path):
    """Load a YAML file."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def load_text(path):
    """Load a text file."""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''


def discover_sops():
    """Find all SOP directories."""
    sops_dir = os.path.join(ROOT, 'sops')
    if not os.path.isdir(sops_dir):
        return []
    sops = []
    for lab_name in sorted(os.listdir(sops_dir)):
        lab_path = os.path.join(sops_dir, lab_name)
        if not os.path.isdir(lab_path) or lab_name.startswith('_'):
            continue
        for sop_name in sorted(os.listdir(lab_path)):
            sop_path = os.path.join(lab_path, sop_name)
            if os.path.isdir(sop_path) and not sop_name.startswith('_'):
                sops.append({
                    'lab': lab_name,
                    'sop': sop_name,
                    'path': os.path.join(lab_name, sop_name),
                })
    return sops


def merge_context(ctp_config, lab_info, sop_data, procedure_md):
    """Merge all 3 tiers into a single template context."""
    # Convert procedure markdown to HTML
    procedure_html = md_lib.markdown(
        procedure_md,
        extensions=['tables', 'fenced_code', 'nl2br']
    )

    return {
        'ctp': ctp_config,
        'lab': lab_info,
        'sop': sop_data,
        'procedure_html': procedure_html,
        'procedure_md': procedure_md,
    }


def build_html(context, sop_info, env):
    """Generate HTML for a single SOP."""
    template = env.get_template('sop_template.html.j2')
    html = template.render(**context)

    # Output path
    out_dir = os.path.join(HTML_DIR, sop_info['lab'], sop_info['sop'])
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'index.html')

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return out_path


def add_heading(doc, text, level=1):
    """Add a heading to a DOCX document."""
    heading = doc.add_heading(text, level=level)
    return heading


def add_paragraph(doc, text, bold=False, italic=False):
    """Add a paragraph to a DOCX document."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    return p


def add_checkbox_line(doc, label, checked=False):
    """Add a checkbox-style line to a DOCX document."""
    check = "\u2611" if checked else "\u2610"
    doc.add_paragraph(f"{check} {label}")


def build_docx(context, sop_info):
    """Generate DOCX for a single SOP."""
    doc = Document()
    sop = context['sop']
    lab = context['lab']
    ctp = context['ctp']

    # --- Title ---
    title_para = doc.add_heading(sop.get('title', 'Untitled SOP'), level=0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Metadata table
    table = doc.add_table(rows=5, cols=2)
    table.style = 'Table Grid'
    meta_fields = [
        ('SOP Number', sop.get('sop_number', '')),
        ('Version', sop.get('version', '')),
        ('Effective Date', sop.get('effective_date', '')),
        ('Author', sop.get('author', '')),
        ('Status', sop.get('status', '').upper()),
    ]
    for i, (label, value) in enumerate(meta_fields):
        table.rows[i].cells[0].text = label
        table.rows[i].cells[1].text = str(value)

    # --- Section 0: Scope ---
    add_heading(doc, 'SCOPE OF DOCUMENT', level=1)
    sop_type_map = {
        'specific_lab_procedure': 'Specific laboratory procedure or experiment',
        'generic_lab_procedure': 'Generic laboratory procedure',
        'specific_chemical': 'Specific chemical or class of chemicals',
    }
    sop_type_label = sop_type_map.get(sop.get('sop_type', ''), sop.get('sop_type', ''))
    add_checkbox_line(doc, sop_type_label, checked=True)
    add_paragraph(doc, sop.get('sop_type_description', ''))

    # --- Section 1: Emergency Shutdown ---
    add_heading(doc, '1. EMERGENCY SHUTDOWN PROCEDURE', level=1)
    add_paragraph(doc, sop.get('emergency_shutdown', 'Not specified.'))

    # --- Section 2: Emergency Contacts ---
    add_heading(doc, '2. EMERGENCY CONTACTS', level=1)
    contacts = ctp.get('emergency_contacts', {})
    add_paragraph(doc, f"Emergency Services: {contacts.get('emergency_services', '999')}", bold=True)

    ehs = contacts.get('ehs', {})
    add_paragraph(doc, f"EHS: {ehs.get('name', '')} — {ehs.get('phone', '')}")

    facilities = contacts.get('facilities', {})
    add_paragraph(doc, f"Facilities: {facilities.get('name', '')} — {facilities.get('email', '')} — {facilities.get('phone', '')}")

    add_paragraph(doc, f"Lab Supervisor: {lab.get('supervisor', {}).get('name', '')} — {lab.get('supervisor', {}).get('phone', '')}")
    add_paragraph(doc, f"Emergency Assembly Point: {lab.get('emergency_assembly_point', '')}")

    if lab.get('local_contacts'):
        add_paragraph(doc, "Local Contacts:", bold=True)
        for contact in lab['local_contacts']:
            add_paragraph(doc, f"  {contact.get('name', '')} ({contact.get('role', '')}) — {contact.get('phone', '')} / After hours: {contact.get('after_hours_phone', 'N/A')}")

    # --- Section 4: Description ---
    add_heading(doc, '4. PROCESS OR EXPERIMENT DESCRIPTION', level=1)
    add_paragraph(doc, sop.get('description', ''))
    add_paragraph(doc, f"Frequency: {sop.get('frequency', 'Not specified')}")
    add_paragraph(doc, f"Duration: {sop.get('duration', 'Not specified')}")

    # --- Section 5: Hazards ---
    add_heading(doc, '5. SAFETY LITERATURE REVIEW & HAZARD SUMMARY', level=1)

    add_paragraph(doc, "Hazardous Substances:", bold=True)
    for sub in sop.get('hazardous_substances', []):
        add_paragraph(doc, f"  • {sub.get('name', '')}: {sub.get('hazards', '')}")

    add_paragraph(doc, "Other Hazards:", bold=True)
    for hazard in sop.get('other_hazards', []):
        add_paragraph(doc, f"  • {hazard}")

    add_paragraph(doc, "Safety Guidelines:", bold=True)
    add_paragraph(doc, sop.get('safety_guidelines', ''))

    add_paragraph(doc, "References:", bold=True)
    for ref in sop.get('references', []):
        add_paragraph(doc, f"  • {ref}")

    ra = sop.get('risk_assessment', {})
    ra_status = "Yes" if ra.get('performed') else "No"
    add_paragraph(doc, f"Risk Assessment performed: {ra_status}")
    if ra.get('location'):
        add_paragraph(doc, f"RA Location: {ra['location']}")

    # --- Section 6: Storage ---
    add_heading(doc, '6. STORAGE REQUIREMENTS', level=1)
    add_paragraph(doc, sop.get('storage_requirements', 'Not specified.'))

    # --- Section 7: PPE / Operating Procedure ---
    add_heading(doc, '7. STEP-BY-STEP OPERATING PROCEDURE', level=1)

    # PPE subsection
    add_paragraph(doc, "PPE Required:", bold=True)
    ppe = sop.get('ppe', {})
    ppe_items = [
        ('street_clothing', 'Appropriate street clothing (long pants, closed-toed shoes)'),
        ('gloves', f"Gloves ({ppe.get('gloves_type', 'specify type')})"),
        ('safety_goggles', 'Safety goggles'),
        ('safety_glasses', 'Safety glasses'),
        ('face_shield', 'Face shield'),
        ('lab_coat', 'Lab coat'),
        ('flame_resistant_lab_coat', 'Flame-resistant lab coat'),
    ]
    for key, label in ppe_items:
        add_checkbox_line(doc, label, checked=ppe.get(key, False))
    if ppe.get('other'):
        add_checkbox_line(doc, f"Other: {ppe['other']}", checked=True)

    # Procedure steps from markdown (as plain text for DOCX)
    add_paragraph(doc, "")  # spacer
    procedure_text = context.get('procedure_md', '')
    if procedure_text:
        for line in procedure_text.strip().split('\n'):
            line = line.rstrip()
            if line.startswith('## '):
                add_heading(doc, line[3:], level=2)
            elif line.startswith('# '):
                add_heading(doc, line[2:], level=2)
            elif line.strip().startswith('|') and '---' in line:
                continue  # skip table separator lines
            elif line.strip().startswith('|'):
                # Simple table row
                cells = [c.strip() for c in line.split('|')[1:-1]]
                add_paragraph(doc, '  |  '.join(cells))
            elif line.strip():
                # Clean up markdown formatting for DOCX
                cleaned = line.replace('**', '').replace('> ', '')
                add_paragraph(doc, cleaned)

    # --- Section 8: Waste ---
    add_heading(doc, '8. WASTE DISPOSAL', level=1)
    add_paragraph(doc, sop.get('waste_disposal', 'Not specified.'))

    # --- Section 9: Emergency Procedures ---
    add_heading(doc, '9. EMERGENCY PROCEDURES', level=1)
    add_paragraph(doc, "Health-Threatening Emergencies:", bold=True)
    add_paragraph(doc, f"Call {contacts.get('emergency_services', '999')}")
    add_paragraph(doc, "Alert people in the vicinity and activate local alarm systems.")
    add_paragraph(doc, f"Evacuate to Emergency Assembly Point: {lab.get('emergency_assembly_point', '[See lab info]')}")
    add_paragraph(doc, "Remain nearby to advise emergency responders.")
    add_paragraph(doc, f"Once safe, call Public Safety: {contacts.get('public_safety', '')}")

    add_paragraph(doc, "")
    add_paragraph(doc, "Non-Health-Threatening Emergencies:", bold=True)
    add_paragraph(doc, f"For non-serious injuries, call {ehs.get('name', 'EHS')}: {ehs.get('phone', '')}")

    add_paragraph(doc, "")
    add_paragraph(doc, "Building Maintenance Emergencies:", bold=True)
    add_paragraph(doc, f"Call Facilities: {facilities.get('name', '')} — {facilities.get('phone', '')}")

    # --- Section 10: Training ---
    add_heading(doc, '10. TRAINING REQUIREMENTS', level=1)
    training = sop.get('training', {})

    add_paragraph(doc, "General Training:", bold=True)
    general = training.get('general', {})
    general_items = [
        ('safety_orientation', 'General Safety Orientation'),
        ('risk_assessment', 'Safety Risk Assessment Training'),
        ('lab_safety_induction', 'Laboratory Safety Induction'),
        ('bloodborne_pathogens', 'Blood borne pathogens'),
        ('xray_safety', 'Basic X-Ray Safety Training Course'),
        ('compressed_gas', 'Compressed Gases Safety Training'),
        ('biosafety_induction', 'Biosafety Induction Training'),
    ]
    for key, label in general_items:
        add_checkbox_line(doc, label, checked=general.get(key, False))
    if general.get('other'):
        add_checkbox_line(doc, f"Other: {general['other']}", checked=True)

    add_paragraph(doc, "")
    add_paragraph(doc, "Lab-Specific Training:", bold=True)
    lab_specific = training.get('lab_specific', {})
    lab_items = [
        ('review_sds', 'Review of SDS for chemicals involved'),
        ('review_sop', 'Review of this SOP'),
        ('hands_on_training', 'Hands-on training by Research Instrumentation Specialist'),
    ]
    for key, label in lab_items:
        add_checkbox_line(doc, label, checked=lab_specific.get(key, False))
    if lab_specific.get('other'):
        add_checkbox_line(doc, f"Other: {lab_specific['other']}", checked=True)

    add_paragraph(doc, f"Training records location: {training.get('records_location', 'Not specified')}")

    # --- Section 11: Prior Approvals ---
    add_heading(doc, '11. PRIOR APPROVALS', level=1)
    if sop.get('prior_approval_required'):
        add_checkbox_line(doc, 'Prior approval from the PI or lab supervisor is required for this procedure.', checked=True)
    else:
        add_paragraph(doc, 'No prior approval required.')

    # --- Section 12: Signatures ---
    add_heading(doc, '12. SIGNATURES', level=1)
    approvers = sop.get('approvers', [])
    if approvers:
        sig_table = doc.add_table(rows=len(approvers) + 1, cols=5)
        sig_table.style = 'Table Grid'
        headers = ['NAME', 'ROLE', 'EMAIL', 'DATE', 'SIGNATURE']
        for i, h in enumerate(headers):
            sig_table.rows[0].cells[i].text = h
        for i, approver in enumerate(approvers, 1):
            sig_table.rows[i].cells[0].text = approver.get('name', '')
            sig_table.rows[i].cells[1].text = approver.get('role', '')
            sig_table.rows[i].cells[2].text = approver.get('email', '')
            # Date and Signature left blank for manual completion

    # --- Change History ---
    doc.add_page_break()
    add_heading(doc, 'CHANGE HISTORY', level=1)
    history = sop.get('change_history', [])
    if history:
        hist_table = doc.add_table(rows=len(history) + 1, cols=4)
        hist_table.style = 'Table Grid'
        for i, h in enumerate(['Version', 'Date', 'Author', 'Description']):
            hist_table.rows[0].cells[i].text = h
        for i, entry in enumerate(history, 1):
            hist_table.rows[i].cells[0].text = str(entry.get('version', ''))
            hist_table.rows[i].cells[1].text = str(entry.get('date', ''))
            hist_table.rows[i].cells[2].text = str(entry.get('author', ''))
            hist_table.rows[i].cells[3].text = str(entry.get('description', ''))

    # --- Footer ---
    footer_text = ctp.get('branding', {}).get('footer_text', '')
    if footer_text:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(footer_text)
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(128, 128, 128)

    # Save
    out_dir = os.path.join(DOCX_DIR, sop_info['lab'])
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{sop.get('sop_number', sop_info['sop'])}_v{sop.get('version', '1.0')}.docx"
    out_path = os.path.join(out_dir, filename)
    doc.save(out_path)

    return out_path


def build_index(all_sops, env):
    """Generate the index page listing all SOPs by lab."""
    # Group SOPs by lab
    labs = {}
    for sop_info in all_sops:
        lab = sop_info['lab']
        if lab not in labs:
            # Try to load lab info
            lab_info_path = os.path.join(ROOT, 'labs', lab, 'lab_info.yaml')
            if os.path.exists(lab_info_path):
                labs[lab] = {
                    'info': load_yaml(lab_info_path),
                    'sops': []
                }
            else:
                labs[lab] = {
                    'info': {'lab_name': lab, 'lab_code': lab.upper()[:3]},
                    'sops': []
                }
        labs[lab]['sops'].append(sop_info)

    template = env.get_template('index.html.j2')
    html = template.render(labs=labs)

    out_path = os.path.join(HTML_DIR, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return out_path


def main():
    parser = argparse.ArgumentParser(description='Build SOP documents')
    parser.add_argument('--all', action='store_true', help='Build all SOPs regardless of status')
    parser.add_argument('--drafts', action='store_true', help='Include drafts in build')
    parser.add_argument('--sop', type=str, help='Build a specific SOP (lab/sop path)')
    parser.add_argument('--html-only', action='store_true', help='Only generate HTML')
    parser.add_argument('--docx-only', action='store_true', help='Only generate DOCX')
    args = parser.parse_args()

    # Load CTP global config
    ctp_config_path = os.path.join(ROOT, 'config', 'ctp_global.yaml')
    if not os.path.exists(ctp_config_path):
        print("ERROR: config/ctp_global.yaml not found!")
        sys.exit(1)
    ctp_config = load_yaml(ctp_config_path)

    # Set up Jinja2
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=False,
    )

    # Discover SOPs
    if args.sop:
        parts = args.sop.replace('\\', '/').split('/')
        if len(parts) != 2:
            print("ERROR: --sop must be in format lab_name/sop_name")
            sys.exit(1)
        sop_list = [{'lab': parts[0], 'sop': parts[1], 'path': args.sop}]
    else:
        sop_list = discover_sops()

    if not sop_list:
        print("No SOPs found to build.")
        sys.exit(0)

    # Prepare build directories
    os.makedirs(HTML_DIR, exist_ok=True)
    os.makedirs(DOCX_DIR, exist_ok=True)

    # Copy stylesheet
    css_src = os.path.join(TEMPLATES_DIR, 'style.css')
    if os.path.exists(css_src):
        css_dir = os.path.join(HTML_DIR, 'assets')
        os.makedirs(css_dir, exist_ok=True)
        shutil.copy2(css_src, os.path.join(css_dir, 'style.css'))

    built = []
    skipped = []

    for sop_info in sop_list:
        sop_yaml_path = os.path.join(ROOT, 'sops', sop_info['path'], 'sop.yaml')
        proc_path = os.path.join(ROOT, 'sops', sop_info['path'], 'procedure.md')

        if not os.path.exists(sop_yaml_path):
            print(f"  SKIP: {sop_info['path']} — sop.yaml not found")
            skipped.append(sop_info['path'])
            continue

        sop_data = load_yaml(sop_yaml_path)
        status = sop_data.get('status', 'draft')

        # Filter by status
        if not args.all:
            if status == 'archived':
                print(f"  SKIP: {sop_info['path']} — archived")
                skipped.append(sop_info['path'])
                continue
            if status == 'draft' and not args.drafts:
                print(f"  SKIP: {sop_info['path']} — draft (use --drafts to include)")
                skipped.append(sop_info['path'])
                continue

        # Load lab info
        lab_name = sop_data.get('lab', sop_info['lab'])
        lab_info_path = os.path.join(ROOT, 'labs', lab_name, 'lab_info.yaml')
        if os.path.exists(lab_info_path):
            lab_info = load_yaml(lab_info_path)
        else:
            print(f"  WARNING: Lab '{lab_name}' info not found, using defaults")
            lab_info = {'lab_name': lab_name}

        # Load procedure
        procedure_md = load_text(proc_path)

        # Merge context
        context = merge_context(ctp_config, lab_info, sop_data, procedure_md)

        # Build outputs
        outputs = []
        if not args.docx_only:
            html_path = build_html(context, sop_info, env)
            outputs.append(f"HTML: {html_path}")
        if not args.html_only:
            docx_path = build_docx(context, sop_info)
            outputs.append(f"DOCX: {docx_path}")

        for out in outputs:
            print(f"  BUILT: {out}")
        built.append(sop_info)

    # Build index page
    if built and not args.docx_only:
        # Reload SOP data for index
        index_sops = []
        for sop_info in built:
            sop_yaml_path = os.path.join(ROOT, 'sops', sop_info['path'], 'sop.yaml')
            sop_data = load_yaml(sop_yaml_path)
            sop_info['data'] = sop_data
            index_sops.append(sop_info)

        index_path = build_index(index_sops, env)
        print(f"  BUILT: Index: {index_path}")

    # Summary
    print()
    print(f"Build complete: {len(built)} built, {len(skipped)} skipped.")
    if built:
        print(f"  HTML output: {HTML_DIR}")
        print(f"  DOCX output: {DOCX_DIR}")


if __name__ == '__main__':
    main()
