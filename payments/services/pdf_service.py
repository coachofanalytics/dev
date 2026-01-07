"""
PDF Receipt Generation Service for Biashara Bridges

Generates professional PDF receipts and invoices for transactions and subscriptions.
Uses ReportLab for PDF generation with company branding.
"""

import io
import os
from datetime import datetime
from typing import Optional

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas

from payments.models import Transaction, Invoice


class PDFReceiptService:
    """Service for generating PDF receipts and invoices"""

    # Page settings
    PAGE_SIZE = letter
    MARGIN = 0.75 * inch

    # Colors (using brand colors from settings)
    PRIMARY_COLOR = colors.HexColor('#007bff')
    SECONDARY_COLOR = colors.HexColor('#6c757d')
    SUCCESS_COLOR = colors.HexColor('#28a745')
    DANGER_COLOR = colors.HexColor('#dc3545')
    WARNING_COLOR = colors.HexColor('#ffc107')

    @classmethod
    def generate_transaction_receipt(cls, transaction_id: str) -> io.BytesIO:
        """
        Generate PDF receipt for a transaction.

        Args:
            transaction_id: Transaction ID to generate receipt for

        Returns:
            BytesIO: PDF file buffer

        Raises:
            Transaction.DoesNotExist: If transaction not found
        """
        transaction = Transaction.objects.select_related('user', 'user__profile').get(
            transaction_id=transaction_id
        )

        # Create PDF buffer
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=cls.PAGE_SIZE,
            leftMargin=cls.MARGIN,
            rightMargin=cls.MARGIN,
            topMargin=cls.MARGIN,
            bottomMargin=cls.MARGIN
        )

        # Build content
        story = []

        # Add watermark for test mode
        if transaction.payment_gateway in ['manual'] or getattr(settings, 'DEBUG', False):
            cls._add_test_watermark(doc, buffer)

        # Header
        story.extend(cls._build_header())
        story.append(Spacer(1, 0.3 * inch))

        # Title
        story.append(Paragraph("TRANSACTION RECEIPT", cls._get_title_style()))
        story.append(Spacer(1, 0.2 * inch))

        # Transaction details
        story.extend(cls._build_transaction_details(transaction))
        story.append(Spacer(1, 0.3 * inch))

        # Footer
        story.extend(cls._build_footer())

        # Build PDF
        doc.build(story)

        # Reset buffer position
        buffer.seek(0)
        return buffer

    @classmethod
    def generate_invoice_pdf(cls, invoice_id: int) -> io.BytesIO:
        """
        Generate PDF for an invoice.

        Args:
            invoice_id: Invoice ID to generate PDF for

        Returns:
            BytesIO: PDF file buffer

        Raises:
            Invoice.DoesNotExist: If invoice not found
        """
        invoice = Invoice.objects.select_related(
            'user', 'user__profile', 'subscription'
        ).get(id=invoice_id)

        # Create PDF buffer
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=cls.PAGE_SIZE,
            leftMargin=cls.MARGIN,
            rightMargin=cls.MARGIN,
            topMargin=cls.MARGIN,
            bottomMargin=cls.MARGIN
        )

        # Build content
        story = []

        # Header
        story.extend(cls._build_header())
        story.append(Spacer(1, 0.3 * inch))

        # Title
        story.append(Paragraph("INVOICE", cls._get_title_style()))
        story.append(Spacer(1, 0.2 * inch))

        # Invoice details
        story.extend(cls._build_invoice_details(invoice))
        story.append(Spacer(1, 0.3 * inch))

        # Footer
        story.extend(cls._build_footer())

        # Build PDF
        doc.build(story)

        # Reset buffer position
        buffer.seek(0)
        return buffer

    @classmethod
    def _build_header(cls) -> list:
        """Build PDF header with company logo and info"""
        elements = []
        styles = getSampleStyleSheet()

        # Company name and info
        company_name = getattr(settings, 'PDF_COMPANY_NAME', 'Biashara Bridges')
        company_address = getattr(settings, 'PDF_COMPANY_ADDRESS', 'Nairobi, Kenya')
        company_email = getattr(settings, 'PDF_COMPANY_EMAIL', 'support@biasharabridges.com')
        company_phone = getattr(settings, 'PDF_COMPANY_PHONE', '+254-XXX-XXXX')

        # Company info table
        data = [
            [Paragraph(f"<b>{company_name}</b>", styles['Heading1'])],
            [Paragraph(company_address, styles['Normal'])],
            [Paragraph(f"Email: {company_email}", styles['Normal'])],
            [Paragraph(f"Phone: {company_phone}", styles['Normal'])],
        ]

        table = Table(data, colWidths=[6 * inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TEXTCOLOR', (0, 0), (0, 0), cls.PRIMARY_COLOR),
        ]))

        elements.append(table)

        # Horizontal line
        elements.append(Spacer(1, 0.1 * inch))
        line_table = Table([['']], colWidths=[6.5 * inch], rowHeights=[2])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 2, cls.PRIMARY_COLOR),
        ]))
        elements.append(line_table)

        return elements

    @classmethod
    def _build_transaction_details(cls, transaction: Transaction) -> list:
        """Build transaction details section"""
        elements = []
        styles = getSampleStyleSheet()

        # Transaction info section
        info_data = [
            ['Receipt Date:', datetime.now().strftime('%B %d, %Y %I:%M %p')],
            ['Transaction ID:', transaction.transaction_id],
            ['Transaction Date:', transaction.created_at.strftime('%B %d, %Y %I:%M %p')],
            ['Status:', transaction.get_status_display().upper()],
            ['Payment Method:', transaction.get_payment_gateway_display()],
        ]

        if transaction.gateway_transaction_id:
            info_data.append(['Gateway Transaction ID:', transaction.gateway_transaction_id])

        info_table = Table(info_data, colWidths=[2 * inch, 4.5 * inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Customer info
        elements.append(Paragraph("<b>Customer Information:</b>", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))

        customer_data = [
            ['Name:', f"{transaction.user.get_full_name() or transaction.user.username}"],
            ['Email:', transaction.user.email],
        ]

        customer_table = Table(customer_data, colWidths=[2 * inch, 4.5 * inch])
        customer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Transaction details
        elements.append(Paragraph("<b>Transaction Details:</b>", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))

        # Amount table with styled total
        amount_data = [
            ['Description', 'Amount'],
            [transaction.get_transaction_type_display(),
             cls._format_currency(transaction.amount, transaction.currency)],
            ['', ''],
            ['<b>Total Amount</b>',
             f'<b>{cls._format_currency(transaction.amount, transaction.currency)}</b>'],
        ]

        amount_table = Table(amount_data, colWidths=[4 * inch, 2.5 * inch])
        amount_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), cls.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Data rows
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 8),

            # Total row
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TOPPADDING', (0, -1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 10),

            # Grid
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ]))
        elements.append(amount_table)

        # Status indicator
        if transaction.status == 'completed':
            status_color = cls.SUCCESS_COLOR
            status_text = '✓ PAYMENT SUCCESSFUL'
        elif transaction.status == 'failed':
            status_color = cls.DANGER_COLOR
            status_text = '✗ PAYMENT FAILED'
        elif transaction.status == 'refunded':
            status_color = cls.WARNING_COLOR
            status_text = '↻ PAYMENT REFUNDED'
        else:
            status_color = cls.SECONDARY_COLOR
            status_text = f'○ {transaction.get_status_display().upper()}'

        elements.append(Spacer(1, 0.2 * inch))
        status_style = ParagraphStyle(
            'status',
            parent=styles['Normal'],
            fontSize=14,
            textColor=status_color,
            alignment=1,  # Center
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph(status_text, status_style))

        return elements

    @classmethod
    def _build_invoice_details(cls, invoice: Invoice) -> list:
        """Build invoice details section"""
        elements = []
        styles = getSampleStyleSheet()

        # Invoice info section
        info_data = [
            ['Invoice Date:', datetime.now().strftime('%B %d, %Y')],
            ['Invoice Number:', invoice.invoice_number],
            ['Due Date:', invoice.due_date.strftime('%B %d, %Y') if invoice.due_date else 'N/A'],
            ['Status:', invoice.get_status_display().upper()],
        ]

        if invoice.paid_date:
            info_data.append(['Paid Date:', invoice.paid_date.strftime('%B %d, %Y %I:%M %p')])

        info_table = Table(info_data, colWidths=[2 * inch, 4.5 * inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Customer info
        elements.append(Paragraph("<b>Bill To:</b>", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))

        customer_data = [
            ['Name:', f"{invoice.user.get_full_name() or invoice.user.username}"],
            ['Email:', invoice.user.email],
        ]

        customer_table = Table(customer_data, colWidths=[2 * inch, 4.5 * inch])
        customer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Invoice items
        elements.append(Paragraph("<b>Invoice Details:</b>", styles['Heading3']))
        elements.append(Spacer(1, 0.1 * inch))

        # Subscription description if available
        description = 'Subscription Payment'
        if invoice.subscription:
            description = f"{invoice.subscription.plan.name} Subscription"

        # Amount table
        amount_data = [
            ['Description', 'Amount'],
            [description, cls._format_currency(invoice.amount, invoice.currency)],
            ['', ''],
            ['<b>Total Amount Due</b>',
             f'<b>{cls._format_currency(invoice.amount, invoice.currency)}</b>'],
        ]

        amount_table = Table(amount_data, colWidths=[4 * inch, 2.5 * inch])
        amount_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), cls.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Data rows
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 8),

            # Total row
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TOPPADDING', (0, -1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 10),

            # Grid
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ]))
        elements.append(amount_table)

        # Status indicator
        if invoice.status == 'paid':
            status_color = cls.SUCCESS_COLOR
            status_text = '✓ PAID'
        elif invoice.status == 'cancelled':
            status_color = cls.DANGER_COLOR
            status_text = '✗ CANCELLED'
        elif invoice.status == 'refunded':
            status_color = cls.WARNING_COLOR
            status_text = '↻ REFUNDED'
        else:
            status_color = cls.WARNING_COLOR
            status_text = f'○ {invoice.get_status_display().upper()}'

        elements.append(Spacer(1, 0.2 * inch))
        status_style = ParagraphStyle(
            'status',
            parent=styles['Normal'],
            fontSize=14,
            textColor=status_color,
            alignment=1,  # Center
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph(status_text, status_style))

        return elements

    @classmethod
    def _build_footer(cls) -> list:
        """Build PDF footer with legal text and contact info"""
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Spacer(1, 0.3 * inch))

        # Horizontal line
        line_table = Table([['']], colWidths=[6.5 * inch], rowHeights=[1])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 1, cls.SECONDARY_COLOR),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 0.1 * inch))

        # Footer text
        footer_text = """
        <para align=center>
        <font size=8 color="#6c757d">
        This is an electronically generated receipt and does not require a signature.<br/>
        For questions, please contact us at {email} or {phone}.<br/>
        Thank you for your business!
        </font>
        </para>
        """.format(
            email=getattr(settings, 'PDF_COMPANY_EMAIL', 'support@biasharabridges.com'),
            phone=getattr(settings, 'PDF_COMPANY_PHONE', '+254-XXX-XXXX')
        )

        elements.append(Paragraph(footer_text, styles['Normal']))

        return elements

    @classmethod
    def _add_test_watermark(cls, doc, buffer):
        """Add TEST MODE watermark to PDF"""
        # Note: This is a placeholder - actual watermark would require
        # canvas manipulation before doc.build()
        pass

    @classmethod
    def _format_currency(cls, amount: float, currency: str = 'USD') -> str:
        """
        Format currency for display.

        Args:
            amount: Amount to format
            currency: Currency code (USD, KES, etc.)

        Returns:
            str: Formatted currency string
        """
        currency_symbols = {
            'USD': '$',
            'KES': 'KSh',
            'EUR': '€',
            'GBP': '£',
        }

        symbol = currency_symbols.get(currency.upper(), currency)

        # Format with comma separators and 2 decimal places
        formatted_amount = f"{amount:,.2f}"

        return f"{symbol} {formatted_amount}"

    @classmethod
    def _get_title_style(cls) -> ParagraphStyle:
        """Get paragraph style for titles"""
        styles = getSampleStyleSheet()
        return ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=cls.PRIMARY_COLOR,
            spaceAfter=12,
            alignment=1,  # Center
            fontName='Helvetica-Bold'
        )
