#!/usr/bin/env python3
"""Build the full formatted B.Tech Project Report DOCX (Part 1: setup + front matter)."""
import docx
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC_DOCX = "/Users/himanshu/Downloads/Annexure 6_Project report format - guidelines_SKP.docx"
OUT_PATH = "/Users/himanshu/Downloads/LLM_Code_Reviewer_Final_Report.docx"

# ============ LOW-LEVEL HELPERS ============

def set_run(run, size=12, bold=False, italic=False, name="Times New Roman"):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts')
        rpr.append(rfonts)
    rfonts.set(qn('w:ascii'), name)
    rfonts.set(qn('w:hAnsi'), name)
    rfonts.set(qn('w:cs'), name)

def para(text="", size=12, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         space_after=12, space_before=0, indent_first=0.25, line_spacing=1.5,
         name="Times New Roman", caps=False, left_indent=0.0):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing = line_spacing
    pf.left_indent = Inches(left_indent)
    if indent_first > 0:
        pf.first_line_indent = Inches(indent_first)
    disp = text.upper() if caps else text
    run = p.add_run(disp)
    set_run(run, size=size, bold=bold, italic=italic, name=name)
    return p

def heading_chapter(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(24)
    pf.space_after = Pt(18)
    pf.line_spacing = 1.0
    run = p.add_run(text.upper())
    set_run(run, size=18, bold=True, name="Times New Roman")
    return p

def heading_section(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = Pt(12)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.0
    run = p.add_run(text.upper())
    set_run(run, size=12, bold=True, name="Times New Roman")
    return p

def heading_sub(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = Pt(10)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.0
    run = p.add_run(text)
    set_run(run, size=12, bold=True, name="Times New Roman")
    return p

def bullet(text, indent=0.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.left_indent = Inches(indent)
    pf.first_line_indent = Inches(-0.25)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.5
    run = p.add_run("\u2022  " + text)
    set_run(run, size=12, name="Times New Roman")
    return p

def table(headers, rows, caption=None):
    if caption:
        para(caption, size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT,
             space_after=6, space_before=6, indent_first=0.0)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        set_run(run, size=11, bold=True, name="Times New Roman")
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(val))
            set_run(run, size=11, name="Times New Roman")
    para("", size=6, space_after=6, indent_first=0.0)
    return t

def mermaid_block(title, code):
    para(title, size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
         space_after=6, space_before=10, indent_first=0.0)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_after = Pt(12)
    pf.line_spacing = 1.0
    run = p.add_run(code)
    set_run(run, size=9, bold=False, name="Consolas")
    pPr = p._element.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:fill'), 'F2F2F2')
    pPr.append(shd)

def page_break():
    doc.add_page_break()

# ============ DOCUMENT SETUP ============
doc = Document(SRC_DOCX)

# Clear all existing content
for elem in list(doc.element.body):
    if elem.tag in (qn('w:p'), qn('w:tbl')):
        doc.element.body.remove(elem)

# Page setup: A4, margins
for section in doc.sections:
    section.page_width = Inches(8.27)   # A4 width
    section.page_height = Inches(11.69) # A4 height
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.25)
    section.right_margin = Inches(1.0)
    # Different first page not needed for cover (we handle manually)

# Footer on all sections
for section in doc.sections:
    footer = section.footer
    footer.is_linked_to_previous = False
    for p in list(footer.paragraphs):
        p.text = ""
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("MITSOC, Department of Computer Engineering 2026")
    set_run(run, size=10, bold=False, name="Times New Roman")

print("Part 1 framework loaded. Saving skeleton...")
doc.save(OUT_PATH)
print("Saved:", OUT_PATH)