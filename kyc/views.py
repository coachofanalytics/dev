"""
KYC Views
Document upload, listing, and verification views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from .models import KYCDocument
from .forms import KYCDocumentUploadForm, KYCDocumentVerificationForm
from .services import DocumentService, VerificationService


@login_required
def upload_document(request):
    """Upload a KYC document."""
    # Check if user is already fully verified
    verification_status = DocumentService.check_user_verification_status(request.user)
    if verification_status.get('is_fully_verified'):
        messages.info(request, 'Your KYC is already fully verified. No additional documents needed.')
        return redirect('kyc:my_documents')
    
    if request.method == 'POST':
        form = KYCDocumentUploadForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                document = DocumentService.upload_document(
                    user=request.user,
                    document_type=form.cleaned_data['document_type'],
                    document_file=request.FILES['document_file'],
                    document_number=form.cleaned_data.get('document_number', ''),
                    issue_date=form.cleaned_data.get('issue_date'),
                    expiry_date=form.cleaned_data.get('expiry_date'),
                    issuing_authority=form.cleaned_data.get('issuing_authority', ''),
                )

                if document.status == 'rejected':
                    messages.error(
                        request,
                        'Document upload failed: File did not pass security scan. '
                        'Please ensure the file is not corrupted or infected.'
                    )
                else:
                    messages.success(
                        request,
                        f'{document.get_document_type_display()} uploaded successfully! '
                        'It will be reviewed by our team shortly.'
                    )

                return redirect('kyc:my_documents')

            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error uploading document: {str(e)}')

    else:
        form = KYCDocumentUploadForm()

    return render(request, 'kyc/upload.html', {
        'form': form,
        'page_title': 'Upload KYC Document',
    })


@login_required
def my_documents(request):
    """List user's KYC documents."""
    documents = DocumentService.get_user_documents(request.user)
    verification_status = DocumentService.check_user_verification_status(request.user)
    verification_level = VerificationService.get_user_verification_level(request.user)

    return render(request, 'kyc/my_documents.html', {
        'documents': documents,
        'verification_status': verification_status,
        'verification_level': verification_level,
        'page_title': 'My KYC Documents',
    })


@login_required
def document_detail(request, document_id):
    """View details of a specific document."""
    document = get_object_or_404(
        KYCDocument,
        id=document_id,
        user=request.user
    )

    return render(request, 'kyc/document_detail.html', {
        'document': document,
        'page_title': f'{document.get_document_type_display()} Details',
    })


@login_required
def delete_document(request, document_id):
    """Delete a KYC document."""
    document = get_object_or_404(
        KYCDocument,
        id=document_id,
        user=request.user
    )

    if request.method == 'POST':
        try:
            DocumentService.delete_document(document, request.user)
            messages.success(request, 'Document deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting document: {str(e)}')

    return redirect('kyc:my_documents')


def is_staff(user):
    """Check if user is staff."""
    return user.is_staff


@user_passes_test(is_staff)
def staff_review_list(request):
    """Staff view: List documents pending review."""
    status_filter = request.GET.get('status', '')
    document_type_filter = request.GET.get('document_type', '')

    documents = DocumentService.get_pending_documents()

    if status_filter:
        documents = documents.filter(status=status_filter)

    if document_type_filter:
        documents = documents.filter(document_type=document_type_filter)

    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'kyc/staff_review_list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'document_type_filter': document_type_filter,
        'page_title': 'KYC Document Review',
    })


@user_passes_test(is_staff)
def staff_review_document(request, document_id):
    """Staff view: Review and verify a document."""
    document = get_object_or_404(KYCDocument, id=document_id)

    if request.method == 'POST':
        form = KYCDocumentVerificationForm(request.POST, instance=document)

        if form.is_valid():
            action = form.cleaned_data['action']
            notes = form.cleaned_data.get('verification_notes', '')

            try:
                if action == 'approve':
                    VerificationService.approve_document(
                        document,
                        request.user,
                        notes
                    )
                    messages.success(
                        request,
                        f'Document approved for {document.user.username}'
                    )

                elif action == 'reject':
                    VerificationService.reject_document(
                        document,
                        request.user,
                        notes
                    )
                    messages.warning(
                        request,
                        f'Document rejected for {document.user.username}'
                    )

                elif action == 'under_review':
                    VerificationService.mark_under_review(
                        document,
                        request.user
                    )
                    messages.info(
                        request,
                        f'Document marked as under review'
                    )

                return redirect('kyc:staff_review_list')

            except Exception as e:
                messages.error(request, f'Error processing document: {str(e)}')

    else:
        form = KYCDocumentVerificationForm()

    # Get user's other documents for context
    user_documents = DocumentService.get_user_documents(document.user)
    verification_level = VerificationService.get_user_verification_level(document.user)

    return render(request, 'kyc/staff_review_document.html', {
        'document': document,
        'form': form,
        'user_documents': user_documents,
        'verification_level': verification_level,
        'page_title': f'Review Document - {document.user.username}',
    })


@login_required
def verification_status(request):
    """Show user's verification status and level."""
    verification_status = DocumentService.check_user_verification_status(request.user)
    verification_level = VerificationService.get_user_verification_level(request.user)

    return render(request, 'kyc/verification_status.html', {
        'verification_status': verification_status,
        'verification_level': verification_level,
        'page_title': 'Verification Status',
    })
