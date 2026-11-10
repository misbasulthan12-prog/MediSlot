import io
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_appointment_pdf(appointment_data):
    """
    appointment_data expected keys:
      token, patient_name, doctor_name, specialty, room_no, 
      date, time_slot, fee, status
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=15
    )
    token_style = ParagraphStyle(
        'TokenStyle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#0f172a'),
        alignment=1
    )

    story = []

    # Clinic Header
    story.append(Paragraph("🩺 MediSlot Health Clinic", title_style))
    story.append(Paragraph("Official Appointment Confirmation & Consultation Slip", subtitle_style))
    story.append(Spacer(1, 10))

    # Generate QR Code in-memory
    qr_content = f"MediSlot Verification | Token: {appointment_data['token']} | Patient: {appointment_data['patient_name']} | Doctor: {appointment_data['doctor_name']} | Slot: {appointment_data['date']} {appointment_data['time_slot']}"
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(qr_content)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    reportlab_qr = RLImage(qr_buffer, width=100, height=100)

    # Token Card Table
    token_card_data = [
        [
            Paragraph(f"<b>TOKEN NUMBER</b><br/><font size=24 color='#0284c7'><b>{appointment_data['token']}</b></font><br/><font size=9 color='#64748b'>Status: {appointment_data['status']}</font>", token_style),
            reportlab_qr
        ]
    ]
    token_table = Table(token_card_data, colWidths=[380, 140])
    token_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f9ff')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#0284c7')),
        ('ALIGN', (0,0), (0,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(token_table)
    story.append(Spacer(1, 20))

    # Details Table
    details = [
        [Paragraph("<b>Patient Name:</b>", styles['Normal']), Paragraph(str(appointment_data['patient_name']), styles['Normal'])],
        [Paragraph("<b>Consulting Doctor:</b>", styles['Normal']), Paragraph(str(appointment_data['doctor_name']), styles['Normal'])],
        [Paragraph("<b>Department / Specialty:</b>", styles['Normal']), Paragraph(str(appointment_data['specialty']), styles['Normal'])],
        [Paragraph("<b>Consultation Room:</b>", styles['Normal']), Paragraph(str(appointment_data['room_no']), styles['Normal'])],
        [Paragraph("<b>Appointment Date:</b>", styles['Normal']), Paragraph(str(appointment_data['date']), styles['Normal'])],
        [Paragraph("<b>Reserved Time Slot:</b>", styles['Normal']), Paragraph(str(appointment_data['time_slot']), styles['Normal'])],
        [Paragraph("<b>Consultation Fee:</b>", styles['Normal']), Paragraph(f"₹{appointment_data['fee']:.2f}", styles['Normal'])],
    ]

    t = Table(details, colWidths=[180, 340])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1e293b')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 25))

    # Instructions & Footer
    instructions = Paragraph(
        "<b>Important Instructions:</b><br/>"
        "1. Please arrive at least 10 minutes prior to your allocated time slot.<br/>"
        "2. Present this digital or printed slip with the QR token at the reception desk.<br/>"
        "3. Cancellations must be made at least 1 hour prior to your visit.",
        ParagraphStyle('Notes', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#475569'))
    )
    story.append(instructions)

    doc.build(story)
    buffer.seek(0)
    return buffer