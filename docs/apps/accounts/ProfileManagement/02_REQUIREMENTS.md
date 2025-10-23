# Profile Management - Requirements

**Feature:** User Profiles & Settings  
**Status:** Phase 1 ✅, Phase 2 Planned  
**Last Updated:** October 22, 2025

---

## 📋 FUNCTIONAL REQUIREMENTS

### Phase 1: Basic Profile (IMPLEMENTED) ✅

#### FR1: View Own Profile
- FR1.1: System SHALL display user profile at `/accounts/profile/<username>`
- FR1.2: System SHALL show: name, email, phone, address, city, state, zip, country, gender
- FR1.3: System SHALL show category and department (if employee)
- FR1.4: System SHALL show resume link (if applicant)
- FR1.5: System SHALL show last login time
- FR1.6: System SHALL prevent users from viewing others' profiles (privacy)

#### FR2: Edit Profile
- FR2.1: System SHALL allow users to update own profile at `/accounts/profile/<id>/update/`
- FR2.2: System SHALL validate phone number format
- FR2.3: System SHALL validate email if changed (require re-verification)
- FR2.4: System SHALL support country selection dropdown
- FR2.5: System SHALL save changes to UserProfile model

#### FR3: Resume Management (Applicants)
- FR3.1: System SHALL allow applicants to upload/update resume
- FR3.2: System SHALL display current resume filename
- FR3.3: System SHALL allow resume download
- FR3.4: System SHALL accept PDF, DOC, DOCX formats
- FR3.5: System SHALL limit file size to 5MB

---

### Phase 2: Enhanced Profiles (NOT IMPLEMENTED) ⏳

#### FR4: Profile Pictures
- FR4.1: System SHALL allow profile picture upload
- FR4.2: System SHALL support JPG, PNG, GIF formats
- FR4.3: System SHALL crop/resize images to 200×200px
- FR4.4: System SHALL generate default avatar from initials if no upload
- FR4.5: System SHALL integrate Gravatar as fallback option
- FR4.6: System SHALL display picture on all user mentions

#### FR5: Notification Preferences
- FR5.1: System SHALL allow users to configure email notification preferences
- FR5.2: System SHALL support per-category notification settings
- FR5.3: System SHALL allow digest frequency selection (daily, weekly, never)
- FR5.4: System SHALL respect "do not disturb" hours
- FR5.5: System SHALL allow SMS notification opt-in

#### FR6: Privacy Settings
- FR6.1: System SHALL allow profile visibility control (public, colleagues, private)
- FR6.2: System SHALL support field-level privacy (hide phone, email, etc.)
- FR6.3: System SHALL allow search visibility toggle
- FR6.4: System SHALL allow activity visibility control

#### FR7: Custom Fields Per Category
- FR7.1: Employees SHALL have: job title, hire date, manager
- FR7.2: Clients SHALL have: company name, industry, account manager
- FR7.3: Applicants SHALL have: skills, experience, education
- FR7.4: Investors SHALL have: risk tolerance, investment goals

---

## 👥 USER STORIES

### Story 1: Update Contact Information
```
As a user
I want to update my phone number and address
So that CODA can reach me when needed

Acceptance Criteria:
- Can navigate to profile edit
- Phone and address fields editable
- Changes save immediately
- Confirmation message shown
- Changes reflected in profile view
```

### Story 2: Add Profile Picture (Phase 2)
```
As a user
I want to add my profile picture
So that my account looks professional

Acceptance Criteria:
- Can upload image (JPG, PNG)
- Image cropped to square
- Resized to 200x200px
- Picture shows on profile
- Picture shows in comments/posts
- Can delete and re-upload
```

### Story 3: Configure Notifications (Phase 2)
```
As a user receiving too many emails
I want to control which notifications I receive
So that I only get important updates

Acceptance Criteria:
- Notification settings page accessible
- Can toggle email notifications by type
- Can choose digest frequency
- Changes apply immediately
- Unsubscribe link in every email
```

---

## ⚙️ NON-FUNCTIONAL REQUIREMENTS

### Performance
- NFR1: Profile page loads in < 2 seconds
- NFR2: Profile update saves in < 1 second
- NFR3: Image upload/resize in < 3 seconds (Phase 2)

### Security
- NFR4: Users can only edit own profile
- NFR5: Admins can edit any profile
- NFR6: Profile data validated before save
- NFR7: File uploads scanned for malware (future)

### Usability
- NFR8: Mobile-responsive profile forms
- NFR9: Clear field labels and help text
- NFR10: Inline validation with helpful messages
- NFR11: Auto-save (future)

---

## 🎯 ACCEPTANCE CRITERIA

### Phase 1 - COMPLETE ✅
- [x] Users can view own profile
- [x] Users can edit contact information
- [x] Applicants can update resume
- [x] Employees show department
- [x] Country dropdown functional
- [x] Gender selection available
- [x] Changes save correctly
- [x] Validation prevents bad data

### Phase 2 - Profile Pictures
- [ ] Upload interface intuitive
- [ ] Images crop and resize automatically
- [ ] Default avatars generate from initials
- [ ] Pictures display everywhere (posts, comments, mentions)
- [ ] Can delete and replace
- [ ] Mobile upload works

### Phase 3 - Preferences & Privacy
- [ ] Notification settings comprehensive
- [ ] Privacy controls granular
- [ ] Changes apply immediately
- [ ] Export settings (backup)
- [ ] Import settings (restore)

---

**See:** 03_ARCHITECTURE.md for data model design


