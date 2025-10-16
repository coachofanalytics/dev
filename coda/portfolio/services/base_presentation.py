"""
Base Presentation Service
Unified service architecture for all portfolio presentations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from django.conf import settings


class BasePresentationService(ABC):
    """
    Abstract base class for all presentation services
    Provides common functionality and enforces consistent interface
    """
    
    # Project metadata (override in subclasses)
    project_name = "Override in subclass"
    project_slug = "override-slug"
    project_tagline = "Override tagline"
    created_date = "2025"
    
    def get_context(self, audience_type: str, presentation_mode: str = 'branded') -> Dict[str, Any]:
        """
        Get complete presentation context
        
        Args:
            audience_type: investor|technical|recruiter|demo
            presentation_mode: branded|interview
        """
        context = {
            # Project info
            'project_name': self.project_name,
            'project_slug': self.project_slug,
            'project_tagline': self.project_tagline,
            'created_date': self.created_date,
            
            # Presentation settings
            'audience_type': audience_type,
            'presentation_mode': presentation_mode,
            'show_branding': presentation_mode == 'branded',
            
            # Branding
            'branding': self._get_branding(presentation_mode),
            
            # Content
            'technologies': self.get_technologies(),
            'key_metrics': self.get_key_metrics(),
            'subtitle': self._get_subtitle(audience_type),
        }
        
        # Add audience-specific context
        if audience_type == 'investor':
            context.update(self.get_investor_context())
        elif audience_type == 'technical':
            context.update(self.get_technical_context())
        elif audience_type == 'recruiter':
            context.update(self.get_recruiter_context())
        elif audience_type == 'demo':
            context.update(self.get_demo_context())
        
        return context
    
    def _get_branding(self, mode: str) -> Dict[str, Any]:
        """Get branding information based on mode"""
        if mode == 'branded':
            return {
                'company_name': 'CODA Analytics',
                'logo_url': '/static/images/coda-logo.png',
                'tagline': 'Data-Driven Solutions',
                'website': 'https://codanalytics.net',
                'contact': {
                    'email': 'info@coda.com',
                    'phone': '+254...',
                },
                'footer_text': '© 2025 CODA Analytics. All rights reserved.',
            }
        else:  # interview mode
            return {
                'developer_name': getattr(settings, 'DEVELOPER_NAME', 'Portfolio Developer'),
                'developer_title': getattr(settings, 'DEVELOPER_TITLE', 'Full-Stack AI/ML Engineer'),
                'logo_url': '/static/portfolio/images/portfolio-logo.png',
                'tagline': 'Professional Portfolio',
                'contact': {
                    'email': getattr(settings, 'DEVELOPER_EMAIL', 'your.email@example.com'),
                    'linkedin': getattr(settings, 'DEVELOPER_LINKEDIN', '#'),
                    'github': getattr(settings, 'DEVELOPER_GITHUB', '#'),
                },
                'footer_text': 'Portfolio Project - 2025',
            }
    
    def _get_subtitle(self, audience_type: str) -> str:
        """Get subtitle based on audience type"""
        subtitles = {
            'investor': 'Business Value & ROI Analysis',
            'technical': 'Technical Deep-Dive & Architecture',
            'recruiter': 'Achievements & Professional Impact',
            'demo': 'Interactive Demonstration',
        }
        return subtitles.get(audience_type, 'Professional Presentation')
    
    # Abstract methods - must be implemented by subclasses
    @abstractmethod
    def get_technologies(self) -> Dict[str, List[Dict[str, str]]]:
        """Return technology stack used in project"""
        pass
    
    @abstractmethod
    def get_key_metrics(self) -> Dict[str, str]:
        """Return key performance metrics"""
        pass
    
    @abstractmethod
    def get_investor_context(self) -> Dict[str, Any]:
        """Return investor-specific content"""
        pass
    
    @abstractmethod
    def get_technical_context(self) -> Dict[str, Any]:
        """Return technical-specific content"""
        pass
    
    def get_recruiter_context(self) -> Dict[str, Any]:
        """Return recruiter-specific content (optional override)"""
        return {
            'subtitle': 'Professional Achievements & Impact',
            'achievements': [],
            'skills': [],
        }
    
    def get_demo_context(self) -> Dict[str, Any]:
        """Return demo-specific content (optional override)"""
        return {
            'subtitle': 'Interactive Demonstration',
            'demo_url': '#',
        }


class ProjectRegistry:
    """Registry of all available portfolio projects"""
    
    _projects = {}
    
    @classmethod
    def register(cls, project_slug: str, service_class: type):
        """Register a presentation service"""
        cls._projects[project_slug] = service_class
    
    @classmethod
    def get_service(cls, project_slug: str) -> BasePresentationService:
        """Get presentation service for a project"""
        service_class = cls._projects.get(project_slug)
        if not service_class:
            raise ValueError(f"Project '{project_slug}' not found in registry")
        return service_class()
    
    @classmethod
    def get_all_projects(cls) -> List[Dict[str, Any]]:
        """Get list of all registered projects"""
        projects = []
        for slug, service_class in cls._projects.items():
            service = service_class()
            projects.append({
                'slug': service.project_slug,
                'name': service.project_name,
                'tagline': service.project_tagline,
                'created_date': service.created_date,
                'key_metrics': service.get_key_metrics(),
            })
        return sorted(projects, key=lambda x: x['created_date'], reverse=True)

