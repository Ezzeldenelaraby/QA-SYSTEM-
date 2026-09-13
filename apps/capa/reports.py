from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generate_8d_pdf(capa):
    """Generate a formal 8D Problem Solving Report PDF for automotive / industrial compliance."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1A365D'),
        alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4A5568'),
        alignment=TA_CENTER
    )
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.white
    )
    label_style = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#2D3748')
    )
    val_style = ParagraphStyle(
        'CellValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1A202C')
    )

    elements = []

    # Title Block
    elements.append(Paragraph("8D PROBLEM SOLVING REPORT", title_style))
    elements.append(Paragraph("IATF 16949 & ISO 9001:2015 Quality Management System Standard", subtitle_style))
    elements.append(Spacer(1, 12))

    # Meta Table
    meta_data = [
        [
            Paragraph("<b>CAPA Number:</b>", label_style), Paragraph(capa.capa_number, val_style),
            Paragraph("<b>Status:</b>", label_style), Paragraph(capa.get_status_display(), val_style)
        ],
        [
            Paragraph("<b>Title:</b>", label_style), Paragraph(capa.title, val_style),
            Paragraph("<b>Source:</b>", label_style), Paragraph(capa.get_source_display(), val_style)
        ],
        [
            Paragraph("<b>Start Date:</b>", label_style), Paragraph(str(capa.start_date), val_style),
            Paragraph("<b>Target Due Date:</b>", label_style), Paragraph(str(capa.due_date), val_style)
        ],
        [
            Paragraph("<b>Responsible Champion:</b>", label_style), Paragraph(capa.responsible_person.full_name, val_style),
            Paragraph("<b>Related NCR:</b>", label_style), Paragraph(capa.related_ncr.ncr_number if capa.related_ncr else "N/A", val_style)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[110, 160, 110, 160])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 14))

    # 8D Disciplines Table Builder
    def make_discipline_box(d_code, d_title, content_text):
        hdr_table = Table([[Paragraph(f"<b>{d_code} - {d_title}</b>", section_header_style)]], colWidths=[540])
        hdr_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1A365D')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
        ]))

        body_text = content_text if content_text else "Not applicable or pending analysis."
        body_table = Table([[Paragraph(body_text.replace('\n', '<br/>'), val_style)]], colWidths=[540])
        body_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E0')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFFFF')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        return [hdr_table, body_table, Spacer(1, 10)]

    # D1: Team
    d1_content = f"Champion / Lead: {capa.responsible_person.full_name} ({capa.responsible_person.get_role_display()})<br/>"
    if capa.related_ncr and capa.related_ncr.reported_by:
        d1_content += f"Reporter: {capa.related_ncr.reported_by.full_name}<br/>"
    if capa.verified_by:
        d1_content += f"Verification Authority: {capa.verified_by.full_name} ({capa.verified_by.get_role_display()})"
    elements.extend(make_discipline_box("D1", "Establish the Team", d1_content))

    # D2: Problem Description
    elements.extend(make_discipline_box("D2", "Describe the Problem", capa.description))

    # D3: Containment Actions
    containment = "Containment measures implemented and quarantine protocol active."
    if capa.related_ncr:
        containment = f"Immediate Correction: {capa.related_ncr.immediate_correction or 'N/A'}<br/>Containment Action: {capa.related_ncr.containment_action or 'N/A'}"
    elements.extend(make_discipline_box("D3", "Interim Containment Actions", containment))

    # D4: Root Cause Analysis
    elements.extend(make_discipline_box("D4", "Root Cause Analysis (RCA / 5-Whys)", capa.root_cause))

    # D5: Permanent Corrective Actions (PCA)
    elements.extend(make_discipline_box("D5", "Permanent Corrective Actions", capa.corrective_action))

    # D6: Implement & Validate PCA
    d6_content = f"Verification Method: {capa.verification_method}<br/>Evidence: {capa.evidence or 'Documentation verified.'}"
    elements.extend(make_discipline_box("D6", "Implement and Validate Corrective Actions", d6_content))

    # D7: Prevent Recurrence
    elements.extend(make_discipline_box("D7", "Prevent Recurrence (Systemic Prevention)", capa.preventive_action))

    # D8: Closure & Team Recognition
    d8_content = f"Effectiveness Result: {capa.effectiveness_result or 'Pending operational monitoring.'}<br/>"
    if capa.verified_by:
        d8_content += f"Formal QA Sign-off: {capa.verified_by.full_name} | Completion Date: {capa.completion_date or 'N/A'}"
    else:
        d8_content += "Formal QA Sign-off: Pending final effectiveness verification."
    elements.extend(make_discipline_box("D8", "Recognize Team & Sign-Off Closure", d8_content))

    # Signatures Block
    elements.append(Spacer(1, 10))
    sig_data = [
        [
            Paragraph("<b>Responsible Lead Signature:</b><br/><br/>___________________________", label_style),
            Paragraph("<b>QA Manager Sign-off:</b><br/><br/>___________________________", label_style),
            Paragraph("<b>Date of Final Sign-off:</b><br/><br/>" + (str(capa.completion_date) if capa.completion_date else "____ / ____ / ________"), label_style)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[180, 180, 180])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(t_sig)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
