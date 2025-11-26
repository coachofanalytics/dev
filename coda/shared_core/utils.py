"""
Shared Core Utilities

Re-exports utility functions from main.utils and provides organization detection.
All apps should import utilities from shared_core.utils, not main.utils.

This provides:
- path_values: Extract values from path
- dates_functionality: Date utility functions
- generate_chatbot_response: Chatbot response generation
- today_date: Get today's date
- date_converter: Convert date strings
- Organization detection utilities (domain → Company mapping)
"""
import logging
from main.utils import (
    path_values,
    dates_functionality,
    generate_chatbot_response,
    today_date,
    date_converter,
    countdown_in_month,
)
from .models import Company

logger = logging.getLogger(__name__)

# Domain to company slug mapping for organization detection
ORGANIZATION_DOMAINS = {
    'codanalytics.net': 'coda',
    'www.codanalytics.net': 'coda',
    'codatrainingapp.herokuapp.com': 'coda',
    'diasporacounty48.org': 'dc48k',
    'www.diasporacounty48.org': 'dc48k',
    'biasharabridges.com': 'biashara',
    'www.biasharabridges.com': 'biashara',
}

# Logo filename mapping (static files)
LOGO_FILENAME_MAP = {
    'coda': 'coda_20251124_v1.jpg',
    'dc48k': 'dck20251124_v1.png',
    'biashara': 'bb_20251124_v1.png',
}


def detect_organization_from_request(request):
    """
    Detect organization from HTTP request domain
    
    Priority order:
    1. Exact website match in Company.website field
    2. Domain mapping dictionary lookup → Company by slug
    3. Partial domain matching
    4. Default to CODA company
    
    Args:
        request: Django HTTP request object
        
    Returns:
        Company instance or None
    """
    try:
        host = request.get_host().lower()
        host = host.split(':')[0]  # Remove port
        
        # Priority 1: Exact match with Company.website
        company = Company.objects.filter(website__iexact=host).first()
        if company:
            logger.debug(f"Organization detected via exact website match: {company.name} (host: {host})")
            return company
        
        # Try www variant
        if not host.startswith('www.'):
            company = Company.objects.filter(website__iexact=f'www.{host}').first()
            if company:
                logger.debug(f"Organization detected via www variant: {company.name} (host: {host})")
                return company
        
        # Priority 2: Domain mapping dictionary
        if host in ORGANIZATION_DOMAINS:
            company_slug = ORGANIZATION_DOMAINS[host]
            company = Company.objects.filter(slug__iexact=company_slug).first()
            if company:
                logger.debug(f"Organization detected via domain mapping: {company.name} (slug: {company_slug})")
                return company
        
        # Priority 3: Partial match (e.g., subdomain.biasharabridges.com)
        for domain_key, company_slug in ORGANIZATION_DOMAINS.items():
            domain_clean = domain_key.replace('www.', '')
            if domain_clean in host:
                company = Company.objects.filter(slug__iexact=company_slug).first()
                if company:
                    logger.debug(f"Organization detected via partial match: {company.name} (domain: {domain_key} in {host})")
                    return company
        
        # Priority 4: Default to CODA
        default_company = Company.objects.filter(slug__iexact='coda').first() or \
                         Company.objects.filter(name__icontains='CODA').first()
        
        if default_company:
            logger.debug(f"Organization defaulted to: {default_company.name} (host: {host})")
        else:
            logger.warning(f"No company found (default CODA not found). Host: {host}")
        
        return default_company
                
    except Exception as e:
        logger.error(f"Error detecting organization from request: {e}")
        try:
            return Company.objects.filter(slug__iexact='coda').first()
        except:
            return None


def get_company_logo_url(company):
    """
    Get logo URL for a company based on its slug
    
    Args:
        company: Company instance
        
    Returns:
        str: Static file path to logo
    """
    if not company:
        return f"/static/main/img/logos/{LOGO_FILENAME_MAP.get('coda', 'coda_20251124_v1.jpg')}"
    
    company_slug = company.slug.lower() if company.slug else 'coda'
    logo_filename = LOGO_FILENAME_MAP.get(company_slug, LOGO_FILENAME_MAP.get('coda', 'coda_20251124_v1.jpg'))
    return f"/static/main/img/logos/{logo_filename}"


def get_company_receipt_data(company):
    """
    Get receipt branding data from Company instance
    
    Args:
        company: Company instance
        
    Returns:
        dict: Receipt branding data
    """
    if not company:
        return {
            'company_name': 'CODA Analytics',
            'company_display_name': 'CODA ANALYTICS',
            'company_email': 'info@codanalytics.net',
            'company_website': 'www.codanalytics.net',
            'company_address': 'Nairobi, Kenya',
            'company_logo_url': get_company_logo_url(None),
        }
    
    return {
        'company_name': company.display_name or company.name or 'CODA Analytics',
        'company_display_name': company.display_name or company.name or 'CODA ANALYTICS',
        'company_email': company.receipt_email or (f"info@{company.website}" if company.website else 'info@codanalytics.net'),
        'company_website': company.website or 'www.codanalytics.net',
        'company_address': company.address or 'Nairobi, Kenya',
        'company_logo_url': get_company_logo_url(company),
        'company': company,
    }


__all__ = [
    'path_values',
    'dates_functionality',
    'generate_chatbot_response',
    'today_date',
    'date_converter',
    'countdown_in_month',
    'detect_organization_from_request',
    'get_company_logo_url',
    'get_company_receipt_data',
]

