from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import MembershipRegistrationForm,ContactMessageForm

# View for member registration
def member_home(request):
    if request.method == 'POST':
        if 'register_submit' in request.POST:
            member_form = MembershipRegistrationForm(request.POST)
            if member_form.is_valid():
                member_form.save()
                messages.success(request, 'Membership registration successful! welcome back to DC48.')
                return redirect('member_home')
        elif 'contact_submit' in request.POST:
            contact_form = ContactMessageForm(request.POST)
            if contact_form.is_valid():
                contact_form.save()
                messages.success(request, 'Your message has been sent successfully!')
                return redirect('member_home')  
    else:
        member_form = MembershipRegistrationForm()
        contact_form = ContactMessageForm()
        context = {
            'form': member_form,
            'contact_form': contact_form
        }
        return render(request, 'member_home.html', context)    