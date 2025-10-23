"""
Portfolio Views
Handles all portfolio and presentation views
"""

from django.shortcuts import render, redirect
from django.http import Http404
from .services import ProjectRegistry
from ai_services.presentation_service import PresentationService


def portfolio_hub(request):
    """
    Main portfolio gallery - shows all projects (CODA branded)
    URL: /portfolio/
    """
    projects = ProjectRegistry.get_all_projects()
    
    # Debug: Log what we got
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Portfolio hub: Found {len(projects)} projects")
    for p in projects:
        logger.info(f"  Project: {p.get('name', 'NO NAME')} - Slug: {p.get('slug', 'NO SLUG')}")
    
    context = {
        'title': 'CODA Portfolio - Professional Projects',
        'projects': projects,
        'presentation_mode': 'branded',
        'show_branding': True,
        'is_portfolio_hub': True,
    }
    
    return render(request, 'portfolio/hub/gallery.html', context)


def interview_hub(request):
    """
    Interview portfolio hub - shows all projects (white-label, no CODA branding)
    URL: /interview/
    """
    projects = ProjectRegistry.get_all_projects()
    
    context = {
        'title': 'Technical Portfolio - Professional Projects',
        'projects': projects,
        'presentation_mode': 'interview',
        'show_branding': False,
        'is_interview_hub': True,
    }
    
    return render(request, 'portfolio/hub/interview_gallery.html', context)


def project_landing(request, project_slug):
    """
    Project landing page - shows available presentation modes
    URL: /portfolio/{project_slug}/
    """
    try:
        service = ProjectRegistry.get_service(project_slug)
    except ValueError:
        raise Http404("Project not found")
    
    # Get presentation mode from URL (branded by default)
    presentation_mode = 'interview' if 'interview' in request.path else 'branded'
    
    # Get base context (use 'demo' as default audience type)
    context = service.get_context('demo', presentation_mode)
    context.update({
        'title': f"{service.project_name} - Presentations",
        'available_audiences': ['investor', 'technical', 'recruiter', 'demo'],
        'is_project_landing': True,
        'project_slug': project_slug,
    })
    
    return render(request, 'portfolio/project_landing.html', context)


def project_presentation(request, project_slug, audience_type):
    """
    Specific project presentation for an audience
    URL: /portfolio/{project_slug}/{audience}/
    """
    try:
        service = ProjectRegistry.get_service(project_slug)
    except ValueError:
        raise Http404("Project not found")
    
    # Determine presentation mode from URL
    presentation_mode = 'interview' if 'interview' in request.path else 'branded'
    
    # Get context for this audience
    context = service.get_context(audience_type, presentation_mode)
    context.update({
        'title': f"{service.project_name} - {audience_type.title()} Presentation",
    })
    
    # Map to template
    template_mapping = {
        'investor': f'portfolio/{project_slug}/investor.html',
        'technical': f'portfolio/{project_slug}/technical.html',
        'recruiter': f'portfolio/{project_slug}/recruiter.html',
        'demo': f'portfolio/{project_slug}/demo.html',
    }
    
    template = template_mapping.get(audience_type, 'portfolio/shared/base_presentation.html')
    
    return render(request, template, context)


def presentation_guide(request):
    """
    Master presentation guide with talking points
    URL: /portfolio/guide/
    """
    projects = ProjectRegistry.get_all_projects()
    
    context = {
        'title': 'Presentation Guide - Master Talking Points',
        'projects': projects,
        'presentation_modes': [
            {
                'mode': 'investor',
                'title': 'Investor Presentation',
                'description': 'Focus on ROI, cost savings, market opportunity',
                'audience': 'VCs, Angel Investors, Business Stakeholders',
                'duration': '15-20 minutes',
            },
            {
                'mode': 'technical',
                'title': 'Technical Interview Presentation',
                'description': 'Showcase AI/ML skills, architecture, problem-solving',
                'audience': 'Hiring Managers, Technical Interviewers, CTOs',
                'duration': '20-30 minutes',
            },
            {
                'mode': 'recruiter',
                'title': 'Recruiter/HR Presentation',
                'description': 'Highlight achievements, impact, leadership',
                'audience': 'Recruiters, HR Managers, Department Heads',
                'duration': '10-15 minutes',
            },
        ],
    }
    
    return render(request, 'portfolio/guide/master_guide.html', context)


# Legacy Presentation Views (copied from original apps)
def legacy_ai_diaspora_presentation(request, presentation_mode='investor'):
    """
    Legacy AI Diaspora presentation - exact copy from ai_services
    URL: /portfolio/legacy/ai-diaspora/{mode}/
    """
    # Use the original presentation service
    presentation_service = PresentationService()
    context = presentation_service.get_presentation_context(presentation_mode)
    
    # Map presentation modes to templates
    template_mapping = {
        'investor': 'portfolio/legacy-ai-diaspora/investor_presentation_dashboard.html',
        'banking': 'portfolio/legacy-ai-diaspora/banking_presentation_dashboard.html',
        'hybrid': 'portfolio/legacy-ai-diaspora/hybrid_presentation_dashboard.html',
        'standard': 'portfolio/legacy-ai-diaspora/presentation_dashboard.html',
    }
    
    template = template_mapping.get(presentation_mode, 'portfolio/legacy-ai-diaspora/presentation_dashboard.html')
    
    return render(request, template, context)


def legacy_finance_presentation(request):
    """
    Legacy Finance presentation - exact copy from finance app
    URL: /portfolio/legacy/finance/
    """
    return render(request, 'portfolio/legacy-finance/loan_system_presentation.html')
