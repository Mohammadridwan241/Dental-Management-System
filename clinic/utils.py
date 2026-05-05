from io import BytesIO
from pathlib import Path

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _register_prescription_fonts():
    font_candidates = [
        ("Nirmala", Path("C:/Windows/Fonts/Nirmala.ttf")),
        ("NirmalaBold", Path("C:/Windows/Fonts/NirmalaB.ttf")),
    ]
    registered = {}
    for font_name, font_path in font_candidates:
        if font_path.exists():
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
            registered[font_name] = font_name
    return {
        "regular": registered.get("Nirmala", "Helvetica"),
        "bold": registered.get("NirmalaBold", registered.get("Nirmala", "Helvetica-Bold")),
    }


def _doctor_block_text(doctor, bangla=False):
    if bangla:
        return [
            doctor.display_name_bn,
            doctor.display_degrees_bn,
            doctor.display_specialization_bn,
            doctor.display_training_bn,
            doctor.display_designation_bn,
            doctor.display_hospital_bn,
        ]
    return [
        doctor.display_name,
        doctor.degrees,
        doctor.specialization,
        doctor.training_details,
        doctor.designation,
        doctor.hospital_name,
    ]


def render_prescription_pdf(prescription):
    fonts = _register_prescription_fonts()
    regular_font = fonts["regular"]
    bold_font = fonts["bold"]

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PrescriptionTitle",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=14,
        leading=16,
        alignment=1,
        textColor=colors.HexColor("#3347a8"),
    )
    small_style = ParagraphStyle(
        "PrescriptionSmall",
        parent=styles["BodyText"],
        fontName=regular_font,
        fontSize=9,
        leading=11,
        textColor=colors.black,
    )
    small_bold = ParagraphStyle(
        "PrescriptionSmallBold",
        parent=small_style,
        fontName=bold_font,
    )
    rx_style = ParagraphStyle(
        "PrescriptionRx",
        parent=small_style,
        fontName=bold_font,
        fontSize=18,
        leading=20,
    )

    doctor = prescription.doctor
    patient = prescription.patient
    story = []

    left_lines = [line for line in _doctor_block_text(doctor, bangla=True) if line]
    right_lines = [line for line in _doctor_block_text(doctor, bangla=False) if line]
    if doctor.bmdc_no:
        right_lines.append(f"BMDC No: {doctor.bmdc_no}")

    left_paragraph = Paragraph(
        "<br/>".join(
            [f"<b>{left_lines[0]}</b>"] + left_lines[1:] if left_lines else ["&nbsp;"]
        ),
        ParagraphStyle(
            "DoctorLeft",
            parent=small_style,
            fontName=bold_font if regular_font == "Helvetica" else regular_font,
            fontSize=10,
            leading=13,
        ),
    )
    right_paragraph = Paragraph(
        "<br/>".join(
            [f"<b>{right_lines[0]}</b>"] + right_lines[1:] if right_lines else ["&nbsp;"]
        ),
        ParagraphStyle(
            "DoctorRight",
            parent=small_style,
            fontName=regular_font,
            fontSize=10,
            leading=12,
            alignment=1,
        ),
    )

    header_table = Table([[left_paragraph, right_paragraph]], colWidths=[92 * mm, 88 * mm])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ]
        )
    )
    story.append(Paragraph("Dr SHAFIQUE'S DENTAL CARE", title_style))
    story.append(Spacer(1, 6))
    story.append(header_table)
    story.append(Spacer(1, 4))

    patient_row = Table(
        [[
            Paragraph(f"<b>Patient:</b> {patient.name}", small_style),
            Paragraph(f"<b>ID:</b> {prescription.patient_code or patient.patient_id}", small_style),
            Paragraph(f"<b>Age:</b> {patient.age}", small_style),
            Paragraph(f"<b>Date:</b> {prescription.date.strftime('%d/%m/%Y')}", small_style),
            Paragraph(f"<b>Phone:</b> {patient.phone_number}", small_style),
        ]],
        colWidths=[44 * mm, 35 * mm, 22 * mm, 34 * mm, 45 * mm],
    )
    patient_row.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ]
        )
    )
    story.append(patient_row)
    story.append(Spacer(1, 6))

    left_notes = [
        Paragraph("<b>Chief Complaint</b>", small_bold),
        Paragraph(prescription.chief_complaint or "-", small_style),
        Spacer(1, 8),
        Paragraph("<b>Diagnosis</b>", small_bold),
        Paragraph(prescription.diagnosis or "-", small_style),
    ]
    left_notes_table = Table([[item] for item in left_notes], colWidths=[52 * mm])
    left_notes_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    rx_rows = [[Paragraph("Rx", rx_style), "", "", ""]]
    rx_rows.append(
        [
            Paragraph("<b>Medicine</b>", small_bold),
            Paragraph("<b>Dose</b>", small_bold),
            Paragraph("<b>Duration</b>", small_bold),
            Paragraph("<b>Instruction</b>", small_bold),
        ]
    )
    for index, item in enumerate(prescription.prescription_medicines.select_related("medicine"), start=1):
        rx_rows.append(
            [
                Paragraph(f"{index}. {item.medicine}", small_style),
                Paragraph(item.display_dose or "-", small_style),
                Paragraph(item.display_duration or "-", small_style),
                Paragraph(item.display_instruction or "-", small_style),
            ]
        )

    rx_table = Table(rx_rows, colWidths=[62 * mm, 26 * mm, 24 * mm, 34 * mm])
    rx_table.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (3, 0)),
                ("LINEBELOW", (0, 1), (-1, 1), 0.6, colors.HexColor("#94a3b8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    body_table = Table([[left_notes_table, rx_table]], colWidths=[54 * mm, 126 * mm])
    body_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEAFTER", (0, 0), (0, 0), 1, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(body_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Advice</b>", small_bold))
    story.append(Spacer(1, 2))
    story.append(Paragraph(prescription.advice or "-", small_style))
    story.append(Spacer(1, 16))

    signature_parts = []
    if doctor.signature_image and Path(doctor.signature_image.path).exists():
        signature_parts.append(Image(doctor.signature_image.path, width=28 * mm, height=14 * mm))
    signature_parts.append(Paragraph("<b>Signature</b>", small_bold))
    signature_parts.append(Paragraph(doctor.display_name, small_style))
    if doctor.hospital_name:
        signature_parts.append(Paragraph(doctor.hospital_name, small_style))
    if doctor.visiting_hours:
        signature_parts.append(Paragraph(f"Visiting Hours: {doctor.visiting_hours}", small_style))
    signature_parts.append(Paragraph(f"Contact: {doctor.phone_number}", small_style))

    right_footer = Table([[part] for part in signature_parts], colWidths=[60 * mm])
    right_footer.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    footer_left_lines = [line for line in [doctor.chamber_info, doctor.address] if line]
    footer_left = Paragraph("<br/>".join(footer_left_lines or ["&nbsp;"]), small_style)
    footer_table = Table([[footer_left, right_footer]], colWidths=[120 * mm, 60 * mm])
    footer_table.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, 0), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(footer_table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="prescription-{prescription.pk}.pdf"'
    return response
