"""
Activity name normalization mappings for TaskHistory.

This module provides deterministic mappings from legacy/free-text activity names
to canonical ActivityType slugs. Used by the normalize_taskhistory_activities
management command to clean up historical data.

All mappings are case-insensitive and handle common variations.
"""

from typing import Optional


# Mapping of known messy/free-text names to canonical slugs
# Keys are lowercased, match against stripped/lowercased activity_name
TASKHISTORY_ACTIVITY_NAME_TO_SLUG = {
    # Daily Update Session variations
    "general meeting": "DAILY_UPDATE_SESSION",
    "update session": "DAILY_UPDATE_SESSION",
    "daily update": "DAILY_UPDATE_SESSION",
    "daily update meeting": "DAILY_UPDATE_SESSION",
    "daily update session": "DAILY_UPDATE_SESSION",
    "daily standup": "DAILY_UPDATE_SESSION",
    "standup": "DAILY_UPDATE_SESSION",
    
    # Self Training Session variations
    "one on one": "SELF_TRAINING_SESSION",
    "1-on-1": "SELF_TRAINING_SESSION",
    "one-on-one": "SELF_TRAINING_SESSION",
    "self learning": "SELF_TRAINING_SESSION",
    "self learning session": "SELF_TRAINING_SESSION",
    "self training": "SELF_TRAINING_SESSION",
    "self training session": "SELF_TRAINING_SESSION",
    "solo training": "SELF_TRAINING_SESSION",
    
    # Client Training Preparation Session variations
    "bi session": "CLIENT_TRAINING_PREP_SESSION",
    "bi training": "CLIENT_TRAINING_PREP_SESSION",
    "bi training session": "CLIENT_TRAINING_PREP_SESSION",
    "client training prep": "CLIENT_TRAINING_PREP_SESSION",
    "client training preparation": "CLIENT_TRAINING_PREP_SESSION",
    "training prep": "CLIENT_TRAINING_PREP_SESSION",
    
    # Client Training Session variations
    "client training": "CLIENT_TRAINING_SESSION",
    "client training session": "CLIENT_TRAINING_SESSION",
    
    # Internal Training Session variations
    "internal training": "INTERNAL_TRAINING_SESSION",
    "internal training session": "INTERNAL_TRAINING_SESSION",
    
    # Simulation Training Session variations
    "training simulation": "SIMULATION_TRAINING_SESSION",
    "training simulation session": "SIMULATION_TRAINING_SESSION",
    "simulation session": "SIMULATION_TRAINING_SESSION",
    
    # Client Job Support variations
    "job support": "CLIENT_JOB_SUPPORT",
    "job support session": "CLIENT_JOB_SUPPORT",
    "client support": "CLIENT_JOB_SUPPORT",
    "client job support": "CLIENT_JOB_SUPPORT",
    
    # Internal Technical Support variations
    "internal support": "INTERNAL_TECHNICAL_SUPPORT",
    "internal technical support": "INTERNAL_TECHNICAL_SUPPORT",
    "tech support": "INTERNAL_TECHNICAL_SUPPORT",
    
    # Developer Project Work variations
    "developer project work": "DEVELOPER_PROJECT_WORK",
    "dev project work": "DEVELOPER_PROJECT_WORK",
    "developer's project work": "DEVELOPER_PROJECT_WORK",
    "project work": "DEVELOPER_PROJECT_WORK",
    "dev work": "DEVELOPER_PROJECT_WORK",
    
    # General Project Work variations
    "general project work": "GENERAL_PROJECT_WORK",
    "non-dev project work": "GENERAL_PROJECT_WORK",
    
    # Employee DAF Review variations
    "employee daf review": "EMPLOYEE_DAF_REVIEW",
    "daf review": "EMPLOYEE_DAF_REVIEW",
    "work review": "EMPLOYEE_DAF_REVIEW",
    
    # Client Assignment Review variations
    "client assignment review": "CLIENT_ASSIGNMENT_REVIEW",
    "assignment review": "CLIENT_ASSIGNMENT_REVIEW",
    
    # Strategic Foresight Workshop variations
    "strategic foresight workshop": "STRATEGIC_FORESIGHT_WORKSHOP",
    "foresight workshop": "STRATEGIC_FORESIGHT_WORKSHOP",
    "board workshop": "STRATEGIC_FORESIGHT_WORKSHOP",
    
    # Annual Department Report Preparation variations
    "annual department report": "ANNUAL_DEPARTMENT_REPORT_PREP",
    "department report prep": "ANNUAL_DEPARTMENT_REPORT_PREP",
    "annual report prep": "ANNUAL_DEPARTMENT_REPORT_PREP",
    
    # Research & Development variations
    "research & development": "RESEARCH_DEVELOPMENT",
    "r&d": "RESEARCH_DEVELOPMENT",
    "research and development": "RESEARCH_DEVELOPMENT",
    "innovation work": "RESEARCH_DEVELOPMENT",
    
    # Team-Building / General Assembly variations
    "team building": "TEAM_BUILDING_EVENT",
    "team-building": "TEAM_BUILDING_EVENT",
    "general assembly": "TEAM_BUILDING_EVENT",
    "team event": "TEAM_BUILDING_EVENT",
    
    # Developer Recruitment variations
    "developer recruitment": "DEVELOPER_RECRUITMENT",
    "dev recruitment": "DEVELOPER_RECRUITMENT",
    "recruitment": "DEVELOPER_RECRUITMENT",
    
    # General Staff Recruitment variations
    "general staff recruitment": "GENERAL_STAFF_RECRUITMENT",
    "staff recruitment": "GENERAL_STAFF_RECRUITMENT",
    
    # Employee Development Meeting variations
    "employee development meeting": "EMPLOYEE_DEVELOPMENT_MEETING",
    "development meeting": "EMPLOYEE_DEVELOPMENT_MEETING",
    "1:1 meeting": "EMPLOYEE_DEVELOPMENT_MEETING",
    
    # Facilities & Office Maintenance variations
    "facilities maintenance": "FACILITIES_OFFICE_MAINTENANCE",
    "office maintenance": "FACILITIES_OFFICE_MAINTENANCE",
    "facilities & office maintenance": "FACILITIES_OFFICE_MAINTENANCE",
    "cleaning round": "FACILITIES_OFFICE_MAINTENANCE",
    
    # Cashflow Update & Reconciliation variations
    "cashflow update": "CASHFLOW_UPDATE_RECONCILIATION",
    "cashflow reconciliation": "CASHFLOW_UPDATE_RECONCILIATION",
    "cashflow update & reconciliation": "CASHFLOW_UPDATE_RECONCILIATION",
    
    # Budgeting & Forecasting Session variations
    "budgeting session": "BUDGETING_FORECASTING_SESSION",
    "forecasting session": "BUDGETING_FORECASTING_SESSION",
    "budgeting & forecasting": "BUDGETING_FORECASTING_SESSION",
    
    # Video Editing variations
    "video editing": "VIDEO_EDITING",
    "video edit": "VIDEO_EDITING",
    
    # Marketing Content Creation variations
    "marketing content creation": "MARKETING_CONTENT_CREATION",
    "content creation": "MARKETING_CONTENT_CREATION",
    "marketing content": "MARKETING_CONTENT_CREATION",
    
    # Social Media Content Publishing variations
    "social media content publishing": "SOCIAL_MEDIA_CONTENT_PUBLISHING",
    "social media publishing": "SOCIAL_MEDIA_CONTENT_PUBLISHING",
    "social media content work": "SOCIAL_MEDIA_CONTENT_PUBLISHING",
    "content publishing": "SOCIAL_MEDIA_CONTENT_PUBLISHING",
    
    # Social Media Monitoring & Engagement variations
    "social media monitoring": "SOCIAL_MEDIA_MONITORING_ENGAGEMENT",
    "social media engagement": "SOCIAL_MEDIA_MONITORING_ENGAGEMENT",
    "social media monitoring & engagement": "SOCIAL_MEDIA_MONITORING_ENGAGEMENT",
    
    # Agile Daily Standup variations
    "agile daily standup": "AGILE_DAILY_STANDUP",
    "daily standup": "AGILE_DAILY_STANDUP",
    
    # Agile Sprint Planning variations
    "agile sprint planning": "AGILE_SPRINT_PLANNING",
    "sprint planning": "AGILE_SPRINT_PLANNING",
    
    # Agile Sprint Review variations
    "agile sprint review": "AGILE_SPRINT_REVIEW",
    "sprint review": "AGILE_SPRINT_REVIEW",
    
    # Agile Retrospective variations
    "agile retrospective": "AGILE_RETROSPECTIVE",
    "retrospective": "AGILE_RETROSPECTIVE",
    "retro": "AGILE_RETROSPECTIVE",
    
    # Agile PBR Session variations
    "pbr session": "AGILE_PBR_SESSION",
    "product backlog refinement": "AGILE_PBR_SESSION",
    "backlog refinement": "AGILE_PBR_SESSION",
    "product backlog refinement session": "AGILE_PBR_SESSION",
    "sprint ceremony": "AGILE_PBR_SESSION",  # Legacy mapping
    
    # Requirements Walkthrough Video variations
    "requirements walkthrough video": "REQUIREMENTS_WALKTHROUGH_VIDEO",
    "requirements walkthrough": "REQUIREMENTS_WALKTHROUGH_VIDEO",
    "walkthrough video": "REQUIREMENTS_WALKTHROUGH_VIDEO",
    
    # App / Data Entry & Testing Support variations
    "app testing support": "APP_DATA_ENTRY_TESTING_SUPPORT",
    "data entry support": "APP_DATA_ENTRY_TESTING_SUPPORT",
    "testing support": "APP_DATA_ENTRY_TESTING_SUPPORT",
    "data entry & testing support": "APP_DATA_ENTRY_TESTING_SUPPORT",
}


def normalize_activity_name(raw_name: str) -> Optional[str]:
    """
    Return canonical slug if we know it, otherwise None.
    
    Args:
        raw_name: The raw activity name from TaskHistory (case-insensitive, trimmed)
        
    Returns:
        Canonical slug string if mapping exists, None otherwise
        
    Examples:
        >>> normalize_activity_name("General Meeting")
        'DAILY_UPDATE_SESSION'
        >>> normalize_activity_name("Something Weird")
        None
    """
    if not raw_name:
        return None
    
    # Normalize: strip whitespace and convert to lowercase
    key = raw_name.strip().lower()
    
    # Look up in mapping
    return TASKHISTORY_ACTIVITY_NAME_TO_SLUG.get(key)

