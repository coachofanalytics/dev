# Profile Management - Implementation

**Feature:** User Profiles & Settings  
**Status:** Phase 1 Complete  
**Last Updated:** October 22, 2025

---

## 📂 CODE LOCATIONS

### Models
**File:** `coda/accounts/models.py`
- `CustomerUser` (lines 37-185) - Profile core fields
- `UserProfile` (lines 186-247) - Extended profile

### Views  
**File:** `coda/accounts/views.py`
- `profile()` (lines ~300-330) - View profile
- `UserProfileUpdateView` (class-based) - Edit profile

### Forms
**File:** `coda/accounts/forms.py`
- Uses ModelForm with CustomerUser fields

### Templates
**File:** `coda/accounts/templates/accounts/profile.html`
**File:** `coda/accounts/templates/accounts/admin/user_update_form.html`

### URLs
```python
path("profile/<str:username>", views.profile, name="account-profile"),
path("profile/<int:pk>/update/", UserProfileUpdateView.as_view(), name="profile-update"),
```

---

## 🔑 KEY FUNCTIONS

### View Profile
```python
@login_required
def profile(request, username):
    """Display user profile"""
    user = get_object_or_404(CustomerUser, username=username)
    
    # Security: Users can only view own profile (or staff can view any)
    if user != request.user and not request.user.is_staff:
        messages.error(request, 'You can only view your own profile.')
        return redirect('accounts:account-profile', username=request.user.username)
    
    context = {
        'profile_user': user,
        'profile': user.profile,
        'completion': user.profile.completion_percentage,
    }
    return render(request, 'accounts/profile.html', context)
```

### Update Profile
```python
class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Edit profile information"""
    model = CustomerUser
    fields = [
        'first_name', 'last_name', 'phone',
        'address', 'city', 'state', 'zipcode', 'country', 'gender'
    ]
    template_name = 'accounts/admin/user_update_form.html'
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('accounts:account-profile', kwargs={'username': self.object.username})
```

---

## 📊 CHANGE HISTORY

| Date | Change | Files |
|------|--------|-------|
| Oct 22, 2025 | 7-doc structure | All docs |
| Earlier 2025 | UserProfile model added | models.py |
| Earlier 2025 | Profile views created | views.py |

---

**See:** 05_TESTING.md for test scenarios


