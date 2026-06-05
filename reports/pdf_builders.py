"""
PDF builders using ReportLab for report generation.
No system dependencies - pure Python PDF generation.
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# Define colors matching EvacuaLink design
EV_PRIMARY = colors.HexColor('#0f4c81')
EV_ACCENT = colors.HexColor('#1c7ed6')
EV_DANGER = colors.HexColor('#dc3545')
EV_SUCCESS = colors.HexColor('#198754')
EV_WARNING = colors.HexColor('#f59f00')
EV_LIGHT = colors.HexColor('#f3f6fb')
EV_BORDER = colors.HexColor('#e5eaf2')


def build_pdf(pdf_filename, report_title, prepared_by, report_type, table_data, summary_data=None):
    """
    Generic PDF builder function.

    Args:
        pdf_filename: Output filename
        report_title: Title of the report
        prepared_by: Name of person who prepared the report
        report_type: Type of report (for display)
        table_data: List of lists containing table data (first row is header)
        summary_data: Optional dictionary with summary statistics

    Returns:
        BytesIO object containing PDF data
    """
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=EV_PRIMARY,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )

    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        spaceAfter=3,
        fontName='Helvetica'
    )

    # Build story (page content)
    story = []

    # Header: EvacuaLink branding
    header_text = "EVACUALINK - Evacuation Management System"
    story.append(Paragraph(header_text, header_style))
    story.append(Spacer(1, 0.15*inch))

    # Title
    story.append(Paragraph(report_title, title_style))

    # Report info
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    info_text = f"<b>Report Type:</b> {report_type} | <b>Generated:</b> {now} | <b>Prepared by:</b> {prepared_by}"
    story.append(Paragraph(info_text, ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=12,
        alignment=TA_CENTER
    )))

    # Main data table
    if table_data and len(table_data) > 0:
        col_widths = [1.2*inch] * len(table_data[0])
        # Adjust column widths to fit page
        total_width = 7.5*inch  # Letter width minus margins
        col_width = total_width / len(table_data[0])
        col_widths = [col_width] * len(table_data[0])

        table = Table(table_data, colWidths=col_widths)

        # Style the table
        table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), EV_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),

            # Data rows styling
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('GRID', (0, 0), (-1, -1), 0.5, EV_BORDER),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))

        story.append(table)
        story.append(Spacer(1, 0.3*inch))

    # Summary statistics
    if summary_data:
        story.append(Paragraph("<b>Summary Statistics</b>", ParagraphStyle(
            'SummaryHeader',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=EV_PRIMARY,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )))

        summary_items = []
        for key, value in summary_data.items():
            if isinstance(value, float):
                display_value = f"{value:.2f}"
            else:
                display_value = str(value)
            summary_items.append(f"• <b>{key}:</b> {display_value}")

        if summary_items:
            summary_text = "<br/>".join(summary_items)
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

    # Footer
    story.append(Spacer(1, 0.2*inch))
    footer_text = "© 2026 EvacuaLink - Evacuation Management & Disaster Information System | Barangay Alicante, EB Magalona, Negros Occidental"
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=0
    )))

    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer


def generate_occupancy_report_pdf(report_data):
    """
    Generate Occupancy Report PDF using ReportLab.

    Args:
        report_data: Dictionary with report data from utils.generate_occupancy_report()

    Returns:
        BytesIO object containing PDF data
    """
    # Build table data
    table_data = [
        ['Center Name', 'Capacity', 'Current', 'Available', 'Occupancy %', 'Status']
    ]

    for center in report_data.get('centers', []):
        table_data.append([
            center['name'],
            str(center['capacity']),
            str(center['occupancy']),
            str(center['available']),
            f"{center['occupancy_percentage']}%",
            center['status']
        ])

    # Build summary
    summary = report_data.get('summary', {})
    summary_data = {
        'Total Centers': summary.get('total_centers', 0),
        'Total Capacity': summary.get('total_capacity', 0),
        'Total Occupancy': summary.get('total_occupancy', 0),
        'Total Available': summary.get('total_available', 0),
        'Overall Occupancy %': f"{summary.get('occupancy_percentage', 0)}%",
        'Open Centers': summary.get('open_centers', 0),
        'Full Centers': summary.get('full_centers', 0),
        'Closed Centers': summary.get('closed_centers', 0),
    }

    return build_pdf(
        'occupancy_report.pdf',
        'Evacuation Center Occupancy Report',
        report_data.get('generated_by', 'System'),
        'Occupancy Report',
        table_data,
        summary_data
    )


def generate_family_reunification_report_pdf(report_data):
    """
    Generate Family Reunification Report PDF using ReportLab.

    Args:
        report_data: Dictionary with report data from utils.generate_family_reunification_report()

    Returns:
        BytesIO object containing PDF data
    """
    # Build table data
    table_data = [
        ['Family Code', 'Family Name', 'Total Members', 'Reunited', 'Missing', 'Checked In', 'Reunification %', 'Status']
    ]

    for family in report_data.get('families', []):
        table_data.append([
            family['code'],
            family['name'],
            str(family['total_members']),
            str(family['reunited_members']),
            str(family['missing_members']),
            str(family['checked_in_members']),
            f"{family['reunification_percentage']}%",
            family['status']
        ])

    # Build summary
    summary = report_data.get('summary', {})
    summary_data = {
        'Total Families': summary.get('total_families', 0),
        'Total Members': summary.get('total_members', 0),
        'Reunited Members': summary.get('total_reunited', 0),
        'Missing Members': summary.get('total_missing', 0),
        'Fully Reunified': summary.get('reunified_families', 0),
        'Partially Reunified': summary.get('partial_families', 0),
        'Pending': summary.get('pending_families', 0),
        'Overall Reunification %': f"{summary.get('overall_reunification_percentage', 0)}%",
    }

    return build_pdf(
        'family_reunification_report.pdf',
        'Family Reunification Status Report',
        report_data.get('generated_by', 'System'),
        'Family Reunification Report',
        table_data,
        summary_data
    )


def generate_special_needs_report_pdf(report_data):
    """
    Generate Special Needs Report PDF using ReportLab.

    Args:
        report_data: Dictionary with report data from utils.generate_special_needs_report()

    Returns:
        BytesIO object containing PDF data
    """
    # Build table data
    table_data = [
        ['Full Name', 'Age', 'Gender', 'Assigned Center', 'Special Needs Detail', 'Status']
    ]

    for evacuee in report_data.get('evacuees', []):
        description = evacuee.get('special_needs_description', '') or ''
        medical = evacuee.get('medical_condition', '') or ''
        detail = description or medical or 'N/A'
        if len(detail) > 30:
            detail = detail[:30] + '...'

        table_data.append([
            evacuee.get('full_name', 'N/A'),
            str(evacuee.get('age', 'N/A')),
            evacuee.get('gender', 'N/A'),
            evacuee.get('current_center', 'Not assigned'),
            detail,
            evacuee.get('status', 'N/A')
        ])

    # Build summary (keys match utils.generate_special_needs_report output)
    summary = report_data.get('summary', {})
    by_status = summary.get('by_status', {})
    summary_data = {
        'Total with Special Needs': summary.get('total_special_needs', 0),
        'Registered': by_status.get('registered', 0),
        'Checked In': by_status.get('checked_in', 0),
        'Reunited': by_status.get('reunited', 0),
        'Missing': by_status.get('missing', 0),
    }

    return build_pdf(
        'special_needs_report.pdf',
        'Special Needs Assessment Report',
        report_data.get('generated_by', 'System'),
        'Special Needs Report',
        table_data,
        summary_data
    )


def generate_incident_report_pdf(report_data):
    """
    Generate Incident Report PDF using ReportLab.

    Args:
        report_data: Dictionary with report data from utils.generate_incident_report()

    Returns:
        BytesIO object containing PDF data
    """
    # Build table data
    table_data = [
        ['Date/Time', 'Location', 'Title', 'Severity', 'Status', 'Description']
    ]

    for incident in report_data.get('incidents', []):
        # Truncate description for table
        desc = incident.get('description', '')
        description = desc[:40] + '...' if len(desc) > 40 else desc

        reported_at = incident.get('reported_at', '')
        if hasattr(reported_at, 'strftime'):
            reported_at = reported_at.strftime('%m/%d %H:%M')
        else:
            reported_at = str(reported_at)

        table_data.append([
            reported_at,
            incident.get('location', incident.get('evacuation_center', 'N/A')),
            incident.get('title', 'N/A'),
            incident.get('severity', 'N/A'),
            incident.get('status', 'N/A'),
            description
        ])

    # Build summary
    summary = report_data.get('summary', {})
    summary_data = {
        'Total Incidents': summary.get('total_incidents', 0),
        'Critical': summary.get('critical_incidents', 0),
        'High': summary.get('high_incidents', 0),
        'Medium': summary.get('medium_incidents', 0),
        'Low': summary.get('low_incidents', 0),
        'Open Incidents': summary.get('open_incidents', 0),
        'Resolved Incidents': summary.get('resolved_incidents', 0),
    }

    return build_pdf(
        'incident_report.pdf',
        'Emergency Incidents Report',
        report_data.get('generated_by', 'System'),
        'Incident Report',
        table_data,
        summary_data
    )
