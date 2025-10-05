"""
Application Workflow Services
Handles automated applicant-to-employee promotion logic
"""

from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

from .models import ApplicationWorkflow, WorkflowStatusLog, WorkflowCriteria, Rated
from accounts.models import UserProfile

User = get_user_model()
logger = logging.getLogger(__name__)


class WorkflowService:
    """
    Service class for managing application workflows
    Handles automated promotion logic and notifications
    """
    
    def __init__(self):
        self.logger = logger
    
    def create_workflow(self, applicant):
        """
        Create a new workflow for an applicant
        Called when applicant first applies
        """
        try:
            # Check if workflow already exists
            if hasattr(applicant, 'workflow'):
                return applicant.workflow
            
            # Create new workflow
            workflow = ApplicationWorkflow.objects.create(
                applicant=applicant,
                status=ApplicationWorkflow.WorkflowStatus.APPLIED
            )
            
            # Log the creation
            WorkflowStatusLog.objects.create(
                workflow=workflow,
                old_status='',
                new_status=ApplicationWorkflow.WorkflowStatus.APPLIED,
                notes="Workflow created"
            )
            
            self.logger.info(f"Created workflow for applicant {applicant.username}")
            return workflow
            
        except Exception as e:
            self.logger.error(f"Error creating workflow for {applicant.username}: {e}")
            return None
    
    def update_skills_score(self, applicant, score):
        """
        Update skills assessment score and check for promotion eligibility
        Called when applicant completes skills assessment
        """
        try:
            workflow = self.get_or_create_workflow(applicant)
            workflow.skills_assessment_score = score
            
            # Update status based on score
            if score >= workflow.min_skills_score:
                workflow.advance_status(
                    ApplicationWorkflow.WorkflowStatus.ASSESSMENT_COMPLETED,
                    notes=f"Skills assessment completed with score: {score}"
                )
                
                # Check if ready for promotion
                if workflow.is_eligible_for_promotion:
                    self._check_automatic_promotion(workflow)
            else:
                workflow.advance_status(
                    ApplicationWorkflow.WorkflowStatus.SKILLS_ASSESSMENT,
                    notes=f"Skills assessment failed with score: {score}. Retry required."
                )
            
            workflow.save()
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating skills score for {applicant.username}: {e}")
            return False
    
    def complete_interview(self, applicant, admin_user=None):
        """
        Mark interview as completed and check for promotion eligibility
        Called when interview process is finished
        """
        try:
            workflow = self.get_or_create_workflow(applicant)
            workflow.interview_completed = True
            
            workflow.advance_status(
                ApplicationWorkflow.WorkflowStatus.INTERVIEW_COMPLETED,
                admin_user,
                "Interview process completed"
            )
            
            # Check if ready for promotion
            if workflow.is_eligible_for_promotion:
                self._check_automatic_promotion(workflow)
            
            workflow.save()
            return True
            
        except Exception as e:
            self.logger.error(f"Error completing interview for {applicant.username}: {e}")
            return False
    
    def complete_documents(self, applicant):
        """
        Mark documents as completed and check for promotion eligibility
        Called when all required documents are submitted
        """
        try:
            workflow = self.get_or_create_workflow(applicant)
            workflow.documents_completed = True
            
            workflow.advance_status(
                ApplicationWorkflow.WorkflowStatus.UNDER_REVIEW,
                notes="All required documents submitted"
            )
            
            # Check if ready for promotion
            if workflow.is_eligible_for_promotion:
                self._check_automatic_promotion(workflow)
            
            workflow.save()
            return True
            
        except Exception as e:
            self.logger.error(f"Error completing documents for {applicant.username}: {e}")
            return False
    
    def admin_approve(self, applicant, admin_user, notes=""):
        """
        Admin approves application for promotion
        Can override automatic criteria
        """
        try:
            workflow = self.get_or_create_workflow(applicant)
            workflow.admin_approval = True
            
            workflow.advance_status(
                ApplicationWorkflow.WorkflowStatus.APPROVED,
                admin_user,
                f"Admin approval: {notes}"
            )
            
            # Promote to employee
            self._promote_to_employee(workflow, admin_user)
            
            workflow.save()
            return True
            
        except Exception as e:
            self.logger.error(f"Error approving application for {applicant.username}: {e}")
            return False
    
    def admin_reject(self, applicant, admin_user, notes=""):
        """
        Admin rejects application
        Can override even if criteria are met
        """
        try:
            workflow = self.get_or_create_workflow(applicant)
            
            workflow.advance_status(
                ApplicationWorkflow.WorkflowStatus.REJECTED,
                admin_user,
                f"Admin rejection: {notes}"
            )
            
            workflow.save()
            return True
            
        except Exception as e:
            self.logger.error(f"Error rejecting application for {applicant.username}: {e}")
            return False
    
    def _check_automatic_promotion(self, workflow):
        """
        Check if applicant meets criteria for automatic promotion
        Private method called internally
        """
        try:
            # Check promotion type
            if workflow.promotion_type == ApplicationWorkflow.PromotionType.AUTOMATIC:
                if workflow.is_eligible_for_promotion:
                    self._promote_to_employee(workflow)
                    return True
            
            elif workflow.promotion_type == ApplicationWorkflow.PromotionType.HYBRID:
                if workflow.is_eligible_for_promotion:
                    # Move to final review for admin approval
                    workflow.advance_status(
                        ApplicationWorkflow.WorkflowStatus.FINAL_REVIEW,
                        notes="Criteria met - awaiting admin approval"
                    )
                    self._send_admin_notification(workflow)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking automatic promotion: {e}")
            return False
    
    def _promote_to_employee(self, workflow, admin_user=None):
        """
        Promote applicant to employee (set is_staff=True)
        Private method called internally
        """
        try:
            with transaction.atomic():
                # Update workflow status
                workflow.advance_status(
                    ApplicationWorkflow.WorkflowStatus.EMPLOYEE,
                    admin_user,
                    "Promoted to employee"
                )
                
                # Set is_staff=True
                workflow.applicant.is_staff = True
                workflow.applicant.save()
                
                # Send notification
                self._send_promotion_notification(workflow)
                
                self.logger.info(f"Promoted {workflow.applicant.username} to employee")
                return True
                
        except Exception as e:
            self.logger.error(f"Error promoting to employee: {e}")
            return False
    
    def _send_admin_notification(self, workflow):
        """
        Send notification to admin about pending approval
        """
        try:
            # Get admin users
            admin_users = User.objects.filter(is_staff=True, is_active=True)
            
            subject = f"Application Ready for Review: {workflow.applicant.username}"
            message = f"""
            Application for {workflow.applicant.username} is ready for final review.
            
            Status: {workflow.get_status_display()}
            Skills Score: {workflow.skills_assessment_score}/{workflow.min_skills_score}
            Documents: {'✓' if workflow.documents_completed else '✗'}
            Interview: {'✓' if workflow.interview_completed else '✗'}
            
            Please review and approve/reject the application.
            """
            
            for admin in admin_users:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [admin.email],
                    fail_silently=True
                )
                
        except Exception as e:
            self.logger.error(f"Error sending admin notification: {e}")
    
    def _send_promotion_notification(self, workflow):
        """
        Send notification to applicant about promotion
        """
        try:
            subject = "Congratulations! You've been promoted to Employee"
            message = f"""
            Dear {workflow.applicant.first_name},
            
            Congratulations! You have successfully completed the application process and have been promoted to Employee status.
            
            Your new status: Employee
            Promotion date: {workflow.completed_date}
            
            You now have access to employee features and benefits.
            
            Best regards,
            CODA Team
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [workflow.applicant.email],
                fail_silently=True
            )
            
        except Exception as e:
            self.logger.error(f"Error sending promotion notification: {e}")
    
    def get_or_create_workflow(self, applicant):
        """
        Get existing workflow or create new one
        """
        try:
            if hasattr(applicant, 'workflow'):
                return applicant.workflow
            return self.create_workflow(applicant)
        except Exception as e:
            self.logger.error(f"Error getting/creating workflow: {e}")
            return None
    
    def get_workflow_status(self, applicant):
        """
        Get current workflow status for applicant
        """
        try:
            if hasattr(applicant, 'workflow'):
                return applicant.workflow.status
            return None
        except Exception as e:
            self.logger.error(f"Error getting workflow status: {e}")
            return None
    
    def get_eligible_for_promotion(self):
        """
        Get all applicants eligible for promotion
        """
        try:
            return ApplicationWorkflow.objects.filter(
                status=ApplicationWorkflow.WorkflowStatus.FINAL_REVIEW,
                documents_completed=True,
                skills_assessment_score__gte=models.F('min_skills_score'),
                interview_completed=True
            )
        except Exception as e:
            self.logger.error(f"Error getting eligible applicants: {e}")
            return ApplicationWorkflow.objects.none()


class WorkflowCriteriaService:
    """
    Service for managing workflow criteria
    """
    
    def __init__(self):
        self.logger = logger
    
    def get_default_criteria(self):
        """
        Get default criteria for workflow
        """
        return {
            'min_skills_score': 12,
            'min_interview_score': 8,
            'documents_required': True,
            'interview_required': True,
            'admin_approval_required': True
        }
    
    def update_criteria(self, criteria_data):
        """
        Update workflow criteria
        """
        try:
            for name, value in criteria_data.items():
                criteria, created = WorkflowCriteria.objects.get_or_create(
                    name=name,
                    defaults={'criteria_type': 'skills_score', 'min_value': value}
                )
                if not created:
                    criteria.min_value = value
                    criteria.save()
            
            return True
        except Exception as e:
            self.logger.error(f"Error updating criteria: {e}")
            return False


# Global service instances
workflow_service = WorkflowService()
criteria_service = WorkflowCriteriaService()



