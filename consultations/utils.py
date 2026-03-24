from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.graphics.barcode import code128

import os
from django.conf import settings


def generate_application_pdf(application):

    # -------------------------------
    # File path
    # -------------------------------
    file_name = f"visa_application_{application.id}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)

    styles = getSampleStyleSheet()
    elements = []

    # -------------------------------
    # Document Title
    # -------------------------------
    elements.append(Paragraph(
        "<para align='center'><b>VISA APPLICATION FORM</b></para>",
        styles["Title"]
    ))
    elements.append(Spacer(1, 15))

    # -------------------------------
    # Application ID
    # -------------------------------
    barcode_value = f"VISA-2026-{application.id:05d}"
    elements.append(Paragraph(
        f"<para align='center'><b>Application ID: {barcode_value}</b></para>",
        styles["Heading3"]
    ))
    elements.append(Spacer(1, 20))

    # -------------------------------
    # Barcode Section
    # -------------------------------
    elements.append(Paragraph(
        "<para align='center'><b>APPLICATION ID</b></para>",
        styles["Heading3"]
    ))
    elements.append(Spacer(1, 10))

    barcode = code128.Code128(
        barcode_value,
        barHeight=30,
        barWidth=0.8
    )
    barcode.hAlign = "CENTER"
    elements.append(barcode)

    elements.append(Spacer(1, 8))

    # Barcode readable value
    elements.append(Paragraph(
        f"<para align='center'><b>{barcode_value}</b></para>",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 25))

    # -------------------------------
    # Table Style Function
    # -------------------------------
    def styled_table(data):
        table = Table(data, colWidths=[220, 300])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("ALIGN", (0,0), (-1,0), "CENTER"),

            ("GRID", (0,0), (-1,-1), 0.8, colors.grey),
            ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),

            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        return table

    # -------------------------------
    # Personal Information
    # -------------------------------
    elements.append(Paragraph("<b>PERSONAL INFORMATION</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))
    personal_data = [
        ["Field", "Information"],
        ["First Name", application.first_name],
        ["Last Name", application.last_name],
        ["Date of Birth", str(application.dob)],
        ["Gender", application.gender],
        ["Nationality", application.nationality],
        ["Marital Status", application.marital_status],
        ["Email", application.email],
        ["Phone", application.phone],
        ["Address", application.address],
    ]
    elements.append(styled_table(personal_data))
    elements.append(Spacer(1, 20))

    # -------------------------------
    # Passport Information
    # -------------------------------
    elements.append(Paragraph("<b>PASSPORT INFORMATION</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))
    passport_data = [
        ["Field", "Information"],
        ["Passport Number", application.passport_number],
        ["Issue Date", str(application.passport_issue)],
        ["Expiry Date", str(application.passport_expiry)],
        ["Passport Country", application.passport_country],
    ]
    elements.append(styled_table(passport_data))
    elements.append(Spacer(1, 20))

    # -------------------------------
    # Travel Details
    # -------------------------------
    elements.append(Paragraph("<b>TRAVEL DETAILS</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))
    travel_data = [
        ["Field", "Information"],
        ["Destination Country", application.destination_country],
        ["Visa Type", application.visa_type],
        ["Arrival Date", str(application.arrival_date)],
        ["Departure Date", str(application.departure_date)],
        ["Purpose", application.purpose],
    ]
    elements.append(styled_table(travel_data))
    elements.append(Spacer(1, 20))

    # -------------------------------
    # Employment Information
    # -------------------------------
    elements.append(Paragraph("<b>EMPLOYMENT INFORMATION</b>", styles["Heading2"]))
    elements.append(Spacer(1, 10))
    employment_data = [
        ["Field", "Information"],
        ["Occupation", application.occupation],
        ["Employer", application.employer],
        ["Employer Address", application.employer_address],
    ]
    elements.append(styled_table(employment_data))
    elements.append(Spacer(1, 30))

    # -------------------------------
    # Footer
    # -------------------------------
    elements.append(Paragraph(
        "<para align='center'><i>Generated by Visa Processing System</i></para>",
        styles["Normal"]
    ))

    # -------------------------------
    # Build PDF
    # -------------------------------
    pdf = SimpleDocTemplate(file_path, pagesize=letter)
    pdf.build(elements)

    return file_path


#new code for consultations
# utils.py

from .models import EligibilityRule, CitizenshipPath

def check_eligibility(applicant):
    try:
        rule = EligibilityRule.objects.get(country=applicant.country)
    except EligibilityRule.DoesNotExist:
        return {"status": "No rules defined for this country", "paths": []}

    if applicant.age < rule.min_age:
        return {"status": "Not Eligible: Age requirement not met", "paths": []}

    if applicant.years_in_country < rule.min_years_residence:
        return {"status": "Not Eligible: Not enough years of residence", "paths": []}

    if rule.requires_clean_record and applicant.has_criminal_record:
        return {"status": "Not Eligible: Criminal record issue", "paths": []}

    # Fetch paths for this country
    paths = CitizenshipPath.objects.filter(country=applicant.country)

    return {"status": "Eligible", "paths": paths}