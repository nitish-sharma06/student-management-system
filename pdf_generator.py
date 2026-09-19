import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import config

def get_base_styles():
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'SchoolTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1E3A8A')
    )
    
    subtitle_style = ParagraphStyle(
        'SchoolSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#4B5563')
    )

    h2_style = ParagraphStyle(
        'DocHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1F2937')
    )

    body_bold = ParagraphStyle(
        'TableBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    return styles, title_style, subtitle_style, h2_style, body_style, body_bold

def generate_report_card_pdf(student, exam, grades):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles, title_style, subtitle_style, h2_style, body_style, body_bold = get_base_styles()
    story = []

    # School Header
    story.append(Paragraph(config.SCHOOL_NAME.upper(), title_style))
    story.append(Paragraph(f"{config.SCHOOL_TAGLINE} &bull; {config.SCHOOL_ADDRESS}", subtitle_style))
    story.append(Paragraph(f"Contact: {config.SCHOOL_CONTACT}", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1E3A8A'), spaceAfter=12))

    # Document Title
    story.append(Paragraph(f"OFFICIAL ACADEMIC REPORT CARD &mdash; {exam['name'].upper()}", h2_style))
    story.append(Spacer(1, 6))

    # Student Details Box
    student_meta = [
        [
            Paragraph("<b>Student Name:</b>", body_style),
            Paragraph(f"{student['first_name']} {student['last_name']}", body_bold),
            Paragraph("<b>Admission No:</b>", body_style),
            Paragraph(student['admission_no'], body_bold)
        ],
        [
            Paragraph("<b>Class & Section:</b>", body_style),
            Paragraph(f"{student['class_name']}", body_bold),
            Paragraph("<b>Roll Number:</b>", body_style),
            Paragraph(student['roll_no'], body_bold)
        ],
        [
            Paragraph("<b>Academic Term:</b>", body_style),
            Paragraph(f"{exam['term']} ({exam['academic_year']})", body_style),
            Paragraph("<b>Date of Issue:</b>", body_style),
            Paragraph(exam['end_date'], body_style)
        ]
    ]

    meta_table = Table(student_meta, colWidths=[1.4*inch, 2.3*inch, 1.3*inch, 2.0*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Marks Table
    marks_data = [
        [
            Paragraph("<b>Code</b>", body_bold),
            Paragraph("<b>Subject Title</b>", body_bold),
            Paragraph("<b>Max Marks</b>", body_bold),
            Paragraph("<b>Marks Obtained</b>", body_bold),
            Paragraph("<b>Percentage</b>", body_bold),
            Paragraph("<b>Grade</b>", body_bold),
            Paragraph("<b>Remarks</b>", body_bold)
        ]
    ]

    total_obtained = 0
    total_max = 0

    for g in grades:
        obt = float(g['marks_obtained'])
        mx = float(g['max_marks'])
        pct = (obt / mx) * 100 if mx > 0 else 0
        total_obtained += obt
        total_max += mx
        rem = g['remarks'] if 'remarks' in g.keys() and g['remarks'] else '-'

        marks_data.append([
            Paragraph(g['subject_code'], body_style),
            Paragraph(g['subject_name'], body_style),
            Paragraph(f"{mx:.0f}", body_style),
            Paragraph(f"{obt:.1f}", body_bold),
            Paragraph(f"{pct:.1f}%", body_style),
            Paragraph(f"<b>{g['grade_letter']}</b>", body_style),
            Paragraph(rem, body_style)
        ])

    overall_pct = (total_obtained / total_max) * 100 if total_max > 0 else 0
    
    # Grand Total Row
    marks_data.append([
        Paragraph("<b>TOTAL</b>", body_bold),
        Paragraph("<b>All Subjects Cumulative</b>", body_bold),
        Paragraph(f"<b>{total_max:.0f}</b>", body_bold),
        Paragraph(f"<b>{total_obtained:.1f}</b>", body_bold),
        Paragraph(f"<b>{overall_pct:.1f}%</b>", body_bold),
        Paragraph(f"<b>{'PASSED' if overall_pct >= 50 else 'FAILED'}</b>", body_bold),
        Paragraph("Overall Result", body_bold)
    ])

    marks_table = Table(
        marks_data,
        colWidths=[1.0*inch, 2.2*inch, 0.7*inch, 0.9*inch, 0.8*inch, 0.6*inch, 1.2*inch]
    )
    marks_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (2,0), (4,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F8FAFC')]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(marks_table)
    story.append(Spacer(1, 20))

    # Grading Scale Legend
    scale_text = "<b>Grading Scale:</b> A+ (90-100%), A (80-89%), B (70-79%), C (60-69%), D (50-59%), F (Below 50% - Fail)"
    story.append(Paragraph(scale_text, subtitle_style))
    story.append(Spacer(1, 40))

    # Signatures
    sig_data = [
        [
            Paragraph("____________________________<br/><b>Class Teacher</b>", subtitle_style),
            Paragraph("____________________________<br/><b>Exam Controller</b>", subtitle_style),
            Paragraph("____________________________<br/><b>Principal</b>", subtitle_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[2.3*inch, 2.3*inch, 2.3*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(KeepTogether(sig_table))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_fee_receipt_pdf(payment, invoice, student):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles, title_style, subtitle_style, h2_style, body_style, body_bold = get_base_styles()
    story = []

    # School Header
    story.append(Paragraph(config.SCHOOL_NAME.upper(), title_style))
    story.append(Paragraph(f"{config.SCHOOL_ADDRESS} &bull; Phone: {config.SCHOOL_CONTACT}", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#047857'), spaceAfter=12))

    story.append(Paragraph("OFFICIAL FEE PAYMENT RECEIPT", h2_style))
    story.append(Spacer(1, 6))

    txn_ref = payment['transaction_ref'] if 'transaction_ref' in payment.keys() and payment['transaction_ref'] else 'N/A'

    # Receipt & Student Details Box
    details_data = [
        [
            Paragraph("<b>Receipt Number:</b>", body_style),
            Paragraph(f"<font color='#047857'><b>{payment['receipt_no']}</b></font>", body_bold),
            Paragraph("<b>Payment Date:</b>", body_style),
            Paragraph(payment['payment_date'], body_bold)
        ],
        [
            Paragraph("<b>Invoice Ref:</b>", body_style),
            Paragraph(invoice['invoice_no'], body_style),
            Paragraph("<b>Payment Method:</b>", body_style),
            Paragraph(payment['payment_method'], body_style)
        ],
        [
            Paragraph("<b>Student Name:</b>", body_style),
            Paragraph(f"{student['first_name']} {student['last_name']}", body_bold),
            Paragraph("<b>Admission No:</b>", body_style),
            Paragraph(student['admission_no'], body_bold)
        ],
        [
            Paragraph("<b>Class / Grade:</b>", body_style),
            Paragraph(student['class_name'], body_style),
            Paragraph("<b>Transaction Ref:</b>", body_style),
            Paragraph(txn_ref, body_style)
        ]
    ]

    details_table = Table(details_data, colWidths=[1.5*inch, 2.2*inch, 1.5*inch, 2.0*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0FDF4')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#BBF7D0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DCFCE7')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 16))

    # Financial Breakdown Table
    balance = float(invoice['amount']) - float(invoice['paid_amount'])
    breakdown_data = [
        [
            Paragraph("<b>Description</b>", body_bold),
            Paragraph("<b>Fee Category</b>", body_bold),
            Paragraph("<b>Total Due</b>", body_bold),
            Paragraph("<b>Amount Paid</b>", body_bold),
            Paragraph("<b>Remaining Balance</b>", body_bold)
        ],
        [
            Paragraph(f"Tuition / Fee Payment for {student['first_name']} {student['last_name']}", body_style),
            Paragraph(invoice['fee_type_name'], body_style),
            Paragraph(f"${float(invoice['amount']):,.2f}", body_style),
            Paragraph(f"<font color='#047857'><b>${float(payment['amount_paid']):,.2f}</b></font>", body_bold),
            Paragraph(f"${balance:,.2f}", body_bold)
        ]
    ]

    breakdown_table = Table(breakdown_data, colWidths=[2.5*inch, 1.4*inch, 1.1*inch, 1.1*inch, 1.1*inch])
    breakdown_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#047857')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(breakdown_table)
    story.append(Spacer(1, 20))

    if 'notes' in payment.keys() and payment['notes']:
        story.append(Paragraph(f"<b>Notes:</b> {payment['notes']}", body_style))
        story.append(Spacer(1, 10))

    # Status confirmation
    status_label = "FULLY PAID" if invoice['status'] == 'Paid' else f"PARTIALLY PAID (Due: ${balance:,.2f})"
    story.append(Paragraph(f"<b>Current Invoice Status:</b> {status_label}", body_bold))
    story.append(Spacer(1, 40))

    # Cashier signature
    auth_data = [
        [
            Paragraph("<i>Thank you for your payment.</i><br/>This is an official computer-generated receipt.", subtitle_style),
            Paragraph("____________________________<br/><b>Authorized Accounts Officer</b>", subtitle_style)
        ]
    ]
    auth_table = Table(auth_data, colWidths=[4.2*inch, 3.0*inch])
    story.append(auth_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
