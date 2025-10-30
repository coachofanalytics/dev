# BIASHARA BRIDGES LLC
## USER REGISTRATION & ACCOUNTS SYSTEM
### FUNCTIONAL REQUIREMENTS DOCUMENT (FRD)

**Document Version:** 1.0  
**Date:** October 28, 2025  
**Status:** Draft  
**Prepared For:** Biashara Bridges LLC Portal Development

---

## TABLE OF CONTENTS

1. [Document Purpose](#document-purpose)
2. [System Overview](#system-overview)
3. [User Registration Requirements](#user-registration-requirements)
4. [Authentication Requirements](#authentication-requirements)
5. [Profile Management Requirements](#profile-management-requirements)
6. [User Categories Requirements](#user-categories-requirements)
7. [Permissions & Roles Requirements](#permissions--roles-requirements)
8. [Security & Audit Requirements](#security--audit-requirements)
9. [Integration & API Requirements](#integration--api-requirements)
10. [Non-Functional Requirements](#non-functional-requirements)
11. [User Stories](#user-stories)
12. [Acceptance Criteria](#acceptance-criteria)
13. [Dependencies](#dependencies)
14. [Out of Scope](#out-of-scope)

---

## DOCUMENT PURPOSE

This Functional Requirements Document (FRD) specifies the detailed functional requirements for the Biashara Bridges LLC User Registration and Accounts System. It translates the business requirements (BRD) into specific, testable system requirements.

**Relationship to BRD:**
- BRD defines **WHY** we need the system (business needs, ROI)
- FRD defines **WHAT** the system must do (specific requirements)

**Audience:**
- Development Team
- QA/Testing Team
- Project Managers
- System Architects
- Stakeholders

---

## SYSTEM OVERVIEW

### System Purpose
The User Registration and Accounts System provides secure user onboarding, authentication, and profile management for all Biashara Bridges LLC users across four distinct categories: Employees, Clients, Applicants, and Investors.

### Key Capabilities
- **User Registration** with email verification
- **Multi-factor Authentication** (Phase 2)
- **Profile Management** for all user types
- **Role-Based Access Control** (RBAC)
- **Security Monitoring** and audit logging
- **API Access** for integrations (Phase 3)

### System Architecture
- **Platform:** Web-based (Django framework)
- **Database:** PostgreSQL
- **Frontend:** Responsive web (mobile-first)
- **Hosting:** Cloud infrastructure (AWS/Heroku)
- **Email:** Transactional email service (SendGrid/AWS SES)

---

## USER REGISTRATION REQUIREMENTS

### FR1: User Registration Form

**Priority:** HIGH  
**Status:** Phase 1  
**Dependencies:** None

#### FR1.1: Registration Page Access
- **Requirement:** System SHALL provide registration form at `/accounts/join/`
- **Input:** Browser HTTP GET request
- **Output:** HTML registration form
- **Validation:** Page accessible without authentication
- **Performance:** Page load < 2 seconds

#### FR1.2: Required Registration Fields
- **Requirement:** System SHALL collect the following required fields:
  - Username (unique, 3-150 characters, alphanumeric + underscore)
  - First Name (1-150 characters)
  - Last Name (1-150 characters)
  - Email (valid email format, unique in system)
  - Password (minimum 8 characters)
  - Password Confirmation (must match password)
  - User Category (dropdown: Employee, Client, Applicant, Investor)
- **Validation:** All fields must be provided before submission
- **Error Handling:** Display field-specific error messages

#### FR1.3: Optional Registration Fields
- **Requirement:** System MAY collect optional fields:
  - Phone Number (international format)
  - Company Name (for Clients)
  - Resume (for Applicants - PDF/DOC/DOCX, max 5MB)
- **Behavior:** Allow submission without optional fields
- **UX:** Indicate which fields are optional

#### FR1.4: Username Uniqueness Validation
- **Requirement:** System SHALL verify username is not already taken
- **Validation Timing:** On form submission (server-side), optionally real-time (client-side)
- **Error Message:** "This username is already taken. Please choose another."
- **Suggested Action:** Provide alternative username suggestions

#### FR1.5: Email Uniqueness Validation
- **Requirement:** System SHALL verify email is not already registered
- **Validation:** Check against User.email field in database
- **Error Message:** "An account with this email already exists. Please login or use a different email."
- **Security:** Don't reveal existing emails to prevent enumeration attacks

#### FR1.6: Password Strength Enforcement
- **Requirement:** System SHALL enforce password complexity rules:
  - Minimum 8 characters
  - Must contain at least one letter (a-z or A-Z)
  - Must contain at least one number (0-9)
  - Cannot be commonly used password (e.g., "password123")
  - Cannot be too similar to username or email
- **Validation:** Use Django password validators
- **UX:** Show password strength meter (Phase 2)
- **Error Messages:** Specific guidance on what's missing

#### FR1.7: Form Validation & Error Handling
- **Requirement:** System SHALL provide clear, actionable error messages
- **Validation Types:**
  - Client-side (JavaScript) for immediate feedback
  - Server-side (Django) for security
- **Error Display:** Highlight invalid fields in red with icon and message
- **Error Summary:** Display list of all errors at top of form
- **Accessibility:** Errors must be screen-reader accessible

#### FR1.8: Resume Upload (Applicants Only)
- **Requirement:** System SHALL display file upload field when "Applicant" category selected
- **Accepted Formats:** PDF, DOC, DOCX
- **Size Limit:** 5MB maximum
- **Validation:** File type and size checked before upload
- **Storage:** Files stored in `media/resumes/doc/` directory
- **Security:** Sanitize filename, prevent directory traversal
- **Error Handling:** Display helpful messages for unsupported formats or oversized files

#### FR1.9: CSRF Protection
- **Requirement:** System SHALL include CSRF token in registration form
- **Implementation:** Django {% csrf_token %} template tag
- **Validation:** Verify token on form submission
- **Security:** Reject requests without valid CSRF token

---

### FR2: Email Verification

**Priority:** HIGH  
**Status:** Phase 1  
**Dependencies:** Email service (SendGrid/AWS SES)

#### FR2.1: Verification Token Generation
- **Requirement:** System SHALL generate unique verification token upon registration
- **Token Format:** UUID4 (cryptographically random)
- **Token Storage:** Store in UserProfile.verification_token field
- **Token Expiry:** 24 hours from generation
- **Security:** Token must be unguessable

#### FR2.2: Verification Email Sending
- **Requirement:** System SHALL send verification email within 60 seconds of registration
- **Email Content:**
  - Subject: "Verify your email for Biashara Bridges"
  - Greeting with user's first name
  - Clear explanation of why verification is needed
  - Prominent verification button/link
  - Link format: `https://biasharabridges.com/accounts/verify-email/{token}/`
  - Alternative: Plain text link for email clients that don't support HTML
  - Footer with company contact information
- **Sender:** noreply@biasharabridges.com
- **Deliverability:** Configure SPF, DKIM, DMARC records
- **Logging:** Log email sent success/failure

#### FR2.3: Email Verification Notice Page
- **Requirement:** System SHALL redirect to verification notice page after registration
- **Page Content:**
  - Success message: "Registration successful!"
  - Instructions: "We've sent a verification email to {email}"
  - What to do: "Click the link in the email to verify your account"
  - What if not received: "Check spam folder" + "Resend email" button
  - Expected wait time: "Email should arrive within 1-2 minutes"
- **Page URL:** `/accounts/verification-notice/`

#### FR2.4: Email Verification Processing
- **Requirement:** System SHALL verify token when user clicks email link
- **Process:**
  1. Extract token from URL
  2. Look up user by token
  3. Check token not expired (< 24 hours old)
  4. If valid: Set user.email_verified = True
  5. If invalid: Display error message with resend option
- **Success:** Redirect to login page with success message
- **Failure:** Display appropriate error message (expired, invalid, already verified)

#### FR2.5: Prevent Unverified Login
- **Requirement:** System SHALL block login attempts for unverified emails
- **Check:** During login, verify user.email_verified = True
- **Error Message:** "Please verify your email before logging in. Check your inbox for the verification link."
- **Action:** Provide "Resend verification email" button

#### FR2.6: Resend Verification Email
- **Requirement:** System SHALL allow users to request new verification email
- **UI:** "Resend Verification Email" button on verification notice page
- **Process:**
  1. User enters email address
  2. System generates new token
  3. System sends new verification email
  4. Display confirmation message
- **Rate Limiting:** Max 3 resend requests per hour per email
- **Security:** Don't reveal if email exists in system

---

### FR3: Category Selection

**Priority:** HIGH  
**Status:** Phase 1  
**Dependencies:** User Categories system

#### FR3.1: Category Dropdown Display
- **Requirement:** System SHALL display category selection dropdown on registration form
- **Options:**
  - Employee
  - Client
  - Applicant
  - Investor
- **Default:** None selected (user must choose)
- **Validation:** Category selection is required
- **UX:** Clear labels with descriptions

#### FR3.2: Category-Specific Fields
- **Requirement:** System SHALL show/hide fields based on category selection
- **Dynamic Behavior:**
  - Applicant selected → Show resume upload field
  - Client selected → Show company name field
  - Employee selected → Show department field (future)
- **Implementation:** JavaScript to toggle field visibility
- **Fallback:** Server-side rendering works without JavaScript

#### FR3.3: Category Descriptions
- **Requirement:** System SHALL provide help text for each category
- **Content:**
  - **Employee:** "Biashara Bridges staff members and administrators"
  - **Client:** "Customers and partners of Biashara Bridges"
  - **Applicant:** "Job seekers applying for positions"
  - **Investor:** "Investment clients and portfolio holders"
- **UX:** Tooltips or info icons next to options

#### FR3.4: Sub-Category Support (Phase 2)
- **Requirement:** System MAY support sub-categories in Phase 2
- **Examples:**
  - Employee → Department Manager, Staff, Admin
  - Client → Premium, Standard, Trial
  - Investor → Accredited, Non-Accredited
- **Implementation:** Cascading dropdown after primary category

---

### FR4: Post-Registration Processing

**Priority:** HIGH  
**Status:** Phase 1  
**Dependencies:** Database, email service

#### FR4.1: User Record Creation
- **Requirement:** System SHALL create User record in database upon valid form submission
- **Process:**
  1. Validate all form data
  2. Hash password using PBKDF2 (SHA256, 260,000 iterations)
  3. Create User object with provided data
  4. Set email_verified = False
  5. Set is_active = True
  6. Set date_joined = current timestamp
  7. Save to database
- **Transaction:** Use database transaction (rollback on failure)
- **Logging:** Log successful registration with user ID and timestamp

#### FR4.2: UserProfile Creation
- **Requirement:** System SHALL create UserProfile record linked to User
- **Fields:**
  - user (ForeignKey to User)
  - category (selected category)
  - phone (if provided)
  - verification_token (generated UUID)
  - token_created_at (current timestamp)
  - Additional fields as needed per category
- **Process:** Create immediately after User creation in same transaction

#### FR4.3: Resume File Handling (Applicants)
- **Requirement:** System SHALL store uploaded resume file for applicants
- **Process:**
  1. Validate file type and size
  2. Sanitize filename (remove special characters)
  3. Generate unique filename (username_resume_timestamp.pdf)
  4. Save to media/resumes/doc/ directory
  5. Store file path in UserProfile.resume field
- **Security:** Scan files for malware (Phase 2)
- **Backup:** Files backed up with database backups

#### FR4.4: Welcome Email Trigger
- **Requirement:** System SHALL trigger verification email send after user creation
- **Implementation:** Call email sending function after commit
- **Async:** Use task queue (Celery) for email sending (don't block registration)
- **Retry Logic:** Retry failed emails up to 3 times

#### FR4.5: Registration Event Logging
- **Requirement:** System SHALL log registration event for audit purposes
- **Log Fields:**
  - User ID
  - Username
  - Email
  - Category
  - Registration timestamp
  - IP address
  - User agent (browser/device)
  - Success/failure status
- **Storage:** Application log file + database audit table
- **Retention:** 12 months

---

## AUTHENTICATION REQUIREMENTS

### FR5: Login with Username/Email + Password

**Priority:** HIGH  
**Status:** Phase 1  
**Dependencies:** User registration complete

#### FR5.1: Login Form Display
- **Requirement:** System SHALL provide login form at `/accounts/login/`
- **Fields:**
  - Username or Email (single field accepts both)
  - Password (masked input)
  - Remember Me (checkbox)
- **Additional:**
  - "Forgot Password?" link
  - "Don't have an account? Sign up" link
- **Accessibility:** Proper labels, keyboard navigation

#### FR5.2: Username OR Email Login
- **Requirement:** System SHALL accept either username or email in login field
- **Process:**
  1. User enters identifier (username or email)
  2. System checks if input contains '@' symbol
  3. If contains '@': Look up user by email
  4. If not: Look up user by username
  5. Proceed with password verification
- **Error:** Generic "Invalid credentials" message (don't reveal which field was wrong)

#### FR5.3: Password Verification
- **Requirement:** System SHALL verify password against stored hash
- **Process:**
  1. Retrieve user record
  2. Hash provided password with stored salt
  3. Compare with stored password hash
  4. Use constant-time comparison to prevent timing attacks
- **Security:** Never log or store plain-text passwords

#### FR5.4: Email Verification Check
- **Requirement:** System SHALL block login if email not verified
- **Check:** user.email_verified = True
- **Error Message:** "Your email address has not been verified. Please check your inbox or request a new verification email."
- **Action:** Provide link to resend verification email

#### FR5.5: Session Creation
- **Requirement:** System SHALL create session upon successful login
- **Process:**
  1. Generate session ID (cryptographically random)
  2. Store session data in database/cache
  3. Set session cookie in browser
  4. Set cookie attributes: HttpOnly, Secure, SameSite=Lax
- **Session Data:** User ID, username, login timestamp, category

#### FR5.6: Remember Me Functionality
- **Requirement:** System SHALL extend session duration if "Remember Me" checked
- **Duration:**
  - Remember Me checked: 30 days
  - Remember Me unchecked: Browser session (closes with browser)
- **Implementation:** Set cookie max_age parameter
- **Security:** Use secure, HttpOnly cookies

#### FR5.7: Dashboard Redirect
- **Requirement:** System SHALL redirect to appropriate dashboard based on user category
- **Routing:**
  - Employee → `/dashboard/employee/`
  - Client → `/dashboard/client/`
  - Applicant → `/dashboard/applicant/`
  - Investor → `/dashboard/investor/`
- **Fallback:** If category not set, redirect to `/dashboard/` (generic)

#### FR5.8: Login Attempt Logging
- **Requirement:** System SHALL log all login attempts
- **Log Fields:**
  - User ID (if identified)
  - Username/email attempted
  - IP address
  - User agent
  - Timestamp
  - Success/failure status
  - Failure reason (if applicable)
- **Retention:** 90 days

#### FR5.9: Failed Login Rate Limiting
- **Requirement:** System SHALL limit failed login attempts to prevent brute force
- **Limits:**
  - Per user: 5 failed attempts per 15 minutes
  - Per IP: 20 failed attempts per hour
- **Response:** "Too many failed login attempts. Please try again in X minutes."
- **Lockout:** Temporary account lockout after 10 failed attempts (30 minute cooldown)
- **Notification:** Email user about suspicious login attempts

---

### FR6: Logout

**Priority:** HIGH  
**Status:** Phase 1  
**Dependencies:** Active session

#### FR6.1: Logout Function
- **Requirement:** System SHALL provide logout capability at `/accounts/logout/`
- **Trigger:** User clicks "Logout" button/link
- **Method:** HTTP POST (prevent CSRF attacks)

#### FR6.2: Session Termination
- **Requirement:** System SHALL terminate user session on logout
- **Process:**
  1. Delete session record from database/cache
  2. Clear session cookie in browser
  3. Invalidate any active "Remember Me" tokens
- **Security:** Ensure complete session cleanup

#### FR6.3: Logout Confirmation
- **Requirement:** System SHALL display logout confirmation
- **Redirect:** Redirect to home page or login page
- **Message:** "You have been successfully logged out"

#### FR6.4: Logout Event Logging
- **Requirement:** System SHALL log logout events
- **Log Fields:**
  - User ID
  - Logout timestamp
  - Session duration
  - IP address
- **Purpose:** Audit trail, security monitoring

---

### FR7: Password Reset

**Priority:** HIGH  
**Status:** Phase 1  
**Dependencies:** Email service

#### FR7.1: Password Reset Request
- **Requirement:** System SHALL provide password reset request form at `/accounts/password-reset/`
- **Input:** Email address
- **Validation:** Email format validation (don't reveal if email exists)
- **Process:**
  1. User enters email
  2. If email exists: Generate reset token, send email
  3. If email doesn't exist: Show same success message (security)
  4. Display: "If an account exists with that email, you will receive password reset instructions"

#### FR7.2: Reset Token Generation
- **Requirement:** System SHALL generate secure password reset token
- **Token:** UUID4 or equivalent (cryptographically random)
- **Storage:** Store token in database with user ID and creation timestamp
- **Expiry:** 1 hour from generation
- **Single-use:** Token invalidated after successful password reset

#### FR7.3: Reset Email Sending
- **Requirement:** System SHALL send password reset email
- **Content:**
  - Subject: "Password reset request for Biashara Bridges"
  - Explanation that password reset was requested
  - Reset link: `https://biasharabridges.com/accounts/password-reset-confirm/{token}/`
  - Expiry notice: "This link expires in 1 hour"
  - Security note: "If you didn't request this, please ignore"
  - Contact support if suspicious
- **Delivery:** Within 60 seconds

#### FR7.4: Password Reset Confirmation Page
- **Requirement:** System SHALL provide password reset form at `/accounts/password-reset-confirm/{token}/`
- **Validation:**
  1. Verify token exists and not expired
  2. If invalid/expired: Display error with option to request new link
  3. If valid: Display password reset form
- **Form Fields:**
  - New Password
  - Confirm New Password
- **Validation:** Same password complexity rules as registration

#### FR7.5: Password Update
- **Requirement:** System SHALL update user password upon valid submission
- **Process:**
  1. Validate new password meets complexity requirements
  2. Hash new password
  3. Update user.password field
  4. Invalidate reset token
  5. Invalidate all existing sessions (force re-login)
  6. Send confirmation email
- **Success:** Redirect to login with success message

#### FR7.6: Password Reset Confirmation Email
- **Requirement:** System SHALL send confirmation email after successful password reset
- **Content:**
  - Confirmation that password was changed
  - Timestamp of change
  - Security advice if not authorized
  - Contact support link
- **Purpose:** Security notification

---

### FR8: Session Management

**Priority:** HIGH  
**Status:** Phase 1  
**Dependencies:** None

#### FR8.1: Session Timeout
- **Requirement:** System SHALL timeout sessions after 30 minutes of inactivity
- **Implementation:** Django session middleware with 30-minute expiry
- **Behavior:** Any user action extends session by 30 minutes
- **Expired Session:** Redirect to login with message "Your session has expired. Please login again."

#### FR8.2: Session Extension on Activity
- **Requirement:** System SHALL extend session on user activity
- **Activity Definition:** Any authenticated page load or API call
- **Implementation:** Update session last_activity timestamp
- **Performance:** Efficient session update (don't slow down requests)

#### FR8.3: Multiple Concurrent Sessions (Optional)
- **Requirement:** System MAY allow multiple concurrent sessions per user
- **Use Case:** User logged in on desktop and mobile simultaneously
- **Implementation:** Each device gets unique session ID
- **Limit:** Maximum 5 concurrent sessions per user
- **Management:** User can view and revoke active sessions in settings (Phase 2)

#### FR8.4: Session Cleanup
- **Requirement:** System SHALL clean up expired sessions daily
- **Implementation:** Django clearsessions management command
- **Schedule:** Run daily at 2 AM via cron job
- **Purpose:** Database cleanup, security

---

## PROFILE MANAGEMENT REQUIREMENTS

### FR9: View User Profile

**Priority:** MEDIUM  
**Status:** Phase 1  
**Dependencies:** Authentication

#### FR9.1: Profile Page Display
- **Requirement:** System SHALL display user profile at `/accounts/profile/{username}/`
- **Displayed Fields:**
  - Username
  - Full Name (First + Last)
  - Email address
  - Phone number (if provided)
  - Category
  - Address, City, State, Zip, Country (if provided)
  - Gender (if provided)
  - Department (if Employee)
  - Company (if Client)
  - Resume link (if Applicant)
  - Last login date/time
- **Privacy:** Users can only view own profile (Phase 1)

#### FR9.2: Profile Privacy
- **Requirement:** System SHALL enforce profile viewing permissions
- **Rule:** Only profile owner can view profile in Phase 1
- **Exception:** Admins can view any profile
- **Error:** 403 Forbidden if user tries to view another's profile
- **Future:** Configurable privacy settings (Phase 2)

---

### FR10: Edit User Profile

**Priority:** MEDIUM  
**Status:** Phase 1  
**Dependencies:** Authentication, Profile viewing

#### FR10.1: Profile Edit Form
- **Requirement:** System SHALL provide profile edit form at `/accounts/profile/{id}/update/`
- **Editable Fields:**
  - First Name, Last Name
  - Phone number
  - Address, City, State, Zip Code, Country
  - Gender
  - Bio (optional text field)
- **Non-Editable:**
  - Username (cannot be changed)
  - Email (requires verification if changed - Phase 2)
  - Category (only admin can change)
  - Date joined

#### FR10.2: Phone Number Validation
- **Requirement:** System SHALL validate phone number format
- **Format:** International format with country code (e.g., +1-555-123-4567)
- **Validation:** Accept multiple formats, standardize on save
- **Error Message:** "Please enter a valid phone number"

#### FR10.3: Country Selection
- **Requirement:** System SHALL provide country dropdown with all countries
- **Implementation:** ISO 3166 country codes
- **Default:** No pre-selection
- **UX:** Searchable dropdown (Select2 or similar)

#### FR10.4: Profile Update Processing
- **Requirement:** System SHALL save profile changes
- **Process:**
  1. Validate all fields
  2. Update UserProfile record
  3. Update User record if name changed
  4. Display success message
  5. Redirect back to profile view
- **Validation:** Server-side validation required

#### FR10.5: Profile Update Confirmation
- **Requirement:** System SHALL confirm successful profile update
- **Message:** "Your profile has been updated successfully"
- **UX:** Display at top of profile page
- **Logging:** Log profile update in audit log

---

### FR11: Resume Management (Applicants)

**Priority:** MEDIUM  
**Status:** Phase 1  
**Dependencies:** Profile management

#### FR11.1: Resume Upload/Update
- **Requirement:** System SHALL allow applicants to upload/update resume
- **Location:** Profile edit form (only for Applicants)
- **Behavior:** New upload replaces old resume
- **Confirmation:** "Are you sure you want to replace your current resume?"

#### FR11.2: Resume Display
- **Requirement:** System SHALL display current resume filename on profile
- **Format:** "Current Resume: resume_johndoe_2025.pdf"
- **Action:** Link to download resume
- **Icon:** PDF/DOC icon based on file type

#### FR11.3: Resume Download
- **Requirement:** System SHALL allow resume download
- **URL:** `/accounts/resume/download/{user_id}/`
- **Authorization:** User can download own resume, admins can download any
- **Response:** File download with correct content-type header
- **Security:** Prevent unauthorized access via direct URL

#### FR11.4: Resume File Validation
- **Requirement:** System SHALL validate resume file on upload
- **Checks:**
  - File type: PDF, DOC, DOCX only
  - File size: Maximum 5MB
  - File not corrupted
  - Filename not malicious
- **Error Messages:** Specific errors for each validation failure

---

## USER CATEGORIES REQUIREMENTS

### FR12: Category Assignment

**Priority:** HIGH  
**Status:** Phase 1  
**Dependencies:** User registration

#### FR12.1: Primary Category Storage
- **Requirement:** System SHALL store user's primary category in UserProfile.category field
- **Values:** 1=Employee, 2=Client, 3=Applicant, 4=Investor
- **Data Type:** IntegerField with choices
- **Required:** Every user must have a category

#### FR12.2: Multi-Category Support (Phase 2)
- **Requirement:** System SHALL support multiple categories per user in Phase 2
- **Implementation:** Many-to-many relationship (User ↔ Category)
- **Example:** User can be both Employee AND Investor
- **Primary:** One category designated as primary for dashboard routing

#### FR12.3: Category Validation
- **Requirement:** System SHALL validate category values
- **Rule:** Must be one of the 4 defined categories
- **Default:** No default (must be explicitly set)

---

### FR13: Category-Based Features

**Priority:** HIGH  
**Status:** Phase 1  
**Dependencies:** Category assignment

#### FR13.1: Dashboard Routing
- **Requirement:** System SHALL route users to category-specific dashboards
- **Implementation:** Middleware or login redirect based on user.profile.category
- **URLs:**
  - Category 1 (Employee) → `/dashboard/employee/`
  - Category 2 (Client) → `/dashboard/client/`
  - Category 3 (Applicant) → `/dashboard/applicant/`
  - Category 4 (Investor) → `/dashboard/investor/`

#### FR13.2: Feature Access Control
- **Requirement:** System SHALL show/hide features based on user category
- **Implementation:** Template tags and view decorators
- **Examples:**
  - Finance module: Only Employee and Investor
  - Job applications: Only Applicant and Employee (HR)
  - Client portal: Only Client
- **Enforcement:** Both frontend (UX) and backend (security)

#### FR13.3: UI Customization
- **Requirement:** System SHALL customize UI based on category
- **Customizations:**
  - Navigation menu items
  - Dashboard widgets
  - Available actions
  - Color scheme (optional)
- **Implementation:** Template inheritance with category-specific overrides

---

### FR14: Category Transitions

**Priority:** MEDIUM  
**Status:** Phase 2  
**Dependencies:** Category system, admin interface

#### FR14.1: Admin-Initiated Category Change
- **Requirement:** System SHALL allow administrators to change user categories
- **Authorization:** Only is_staff=True users
- **Interface:** Django admin or custom admin panel
- **Validation:** Confirm category change with admin

#### FR14.2: Data Preservation on Category Change
- **Requirement:** System SHALL preserve user data when category changes
- **Behavior:**
  - Keep all profile data
  - Update category field
  - Adjust permissions
  - Maintain history
- **Example:** Applicant hired → becomes Employee (keep resume, add employee fields)

#### FR14.3: Category History Tracking
- **Requirement:** System SHALL track category change history
- **Storage:** CategoryHistory model with user, old_category, new_category, changed_by, changed_at
- **Purpose:** Audit trail, lifecycle analysis
- **Retention:** Permanent

---

## PERMISSIONS & ROLES REQUIREMENTS

### FR15: Department-Based Permissions

**Priority:** MEDIUM  
**Status:** Phase 1  
**Dependencies:** User categories (Employee)

#### FR15.1: Department Assignment
- **Requirement:** System SHALL support department assignment for Employees
- **Implementation:** UserProfile.department field (ForeignKey to Department model)
- **Departments:** IT, Finance, HR, Operations, Management, etc.
- **Optional:** Not all Employees have department (e.g., contractors)

#### FR15.2: Department-Based Data Filtering
- **Requirement:** System SHALL filter data based on user's department
- **Example:** Finance department sees financial data, HR sees employee records
- **Implementation:** QuerySet filters in views
- **Override:** Admins can see all departments

---

### FR16: Staff and Admin Flags

**Priority:** HIGH  
**Status:** Phase 1  
**Dependencies:** User model

#### FR16.1: is_staff Flag
- **Requirement:** System SHALL use is_staff flag to differentiate employees from non-employees
- **Behavior:** is_staff=True grants access to internal systems
- **Default:** False (set True for Employee category users who need internal access)
- **Usage:** @staff_member_required decorator for views

#### FR16.2: is_superuser (Admin) Flag
- **Requirement:** System SHALL use is_superuser flag for administrators
- **Behavior:** is_superuser=True grants full system access and Django admin
- **Permissions:** Can do anything (create users, change any data, access all features)
- **Assignment:** Only via command line or by other superusers
- **Security:** Minimal number of superusers (2-3 max)

#### FR16.3: Permission Checks
- **Requirement:** System SHALL check permissions before allowing actions
- **Implementation:** Django permission system
- **Decorator:** @permission_required('app.permission_name')
- **Template:** {% if perms.app.permission_name %}
- **Error:** 403 Forbidden for unauthorized access

---

### FR17: Custom Roles (Phase 2)

**Priority:** MEDIUM  
**Status:** Phase 2 (Planned)  
**Dependencies:** Permission system

#### FR17.1: Role Creation
- **Requirement:** System SHALL allow creation of custom roles
- **Interface:** Admin interface for role management
- **Role Definition:** Name, description, list of permissions
- **Examples:** "Department Manager", "Client Services Rep", "Portfolio Manager"

#### FR17.2: Role Assignment
- **Requirement:** System SHALL allow assigning roles to users
- **Implementation:** Many-to-many relationship (User ↔ Role)
- **Multiple Roles:** User can have multiple roles
- **Permission Calculation:** Union of all role permissions

#### FR17.3: Role Hierarchy (Phase 3)
- **Requirement:** System MAY support role inheritance/hierarchy
- **Example:** "Senior Manager" inherits all "Manager" permissions + additional
- **Complexity:** Phase 3 feature

---

## SECURITY & AUDIT REQUIREMENTS

### FR18: Login History Tracking

**Priority:** HIGH  
**Status:** Phase 1  
**Dependencies:** Authentication system

#### FR18.1: Login Attempt Logging
- **Requirement:** System SHALL log all login attempts (successful and failed)
- **Data Captured:**
  - User ID (if successful)
  - Username/email attempted
  - IP address
  - User agent (browser, OS, device)
  - Timestamp
  - Success/failure status
  - Failure reason (invalid credentials, unverified email, etc.)
- **Storage:** LoginHistory model in database
- **Retention:** 90 days

#### FR18.2: User Login History View
- **Requirement:** System SHALL allow users to view their own login history
- **Location:** Profile settings → Security → Login History
- **Display:**
  - Table of recent logins (last 20)
  - Columns: Date/Time, IP Address, Device/Browser, Location (if available)
  - Highlight suspicious logins (different country, new device)
- **Action:** "Report suspicious activity" button

---

### FR19: Comprehensive Audit Logging (Phase 2)

**Priority:** HIGH  
**Status:** Phase 2 (Planned)  
**Dependencies:** Application infrastructure

#### FR19.1: User Action Logging
- **Requirement:** System SHALL log all significant user actions
- **Actions Logged:**
  - CRUD operations (Create, Read, Update, Delete)
  - Permission changes
  - Role assignments
  - Sensitive data access
  - Settings changes
- **Data Captured:**
  - User ID
  - Action type
  - Object type and ID
  - Before/after values (for updates)
  - Timestamp
  - IP address
  - Request URL

#### FR19.2: Audit Log Retention
- **Requirement:** System SHALL retain audit logs for 12 months minimum
- **Storage:** Dedicated audit database or table
- **Archival:** Older logs archived to cold storage
- **Purpose:** Compliance, security investigation, debugging

#### FR19.3: Audit Log Search
- **Requirement:** System SHALL provide audit log search capability (admin only)
- **Filters:**
  - User
  - Date range
  - Action type
  - Object type
- **Export:** Export search results to CSV

---

### FR20: AI Anomaly Detection (Phase 2)

**Priority:** MEDIUM  
**Status:** Phase 2 (Planned)  
**Dependencies:** ML infrastructure, comprehensive logging

#### FR20.1: Impossible Travel Detection
- **Requirement:** System SHALL detect impossible travel scenarios
- **Logic:** Login from Location A, then Location B within impossibly short time
- **Example:** Login from New York at 1pm, then London at 1:15pm (impossible)
- **Response:** Block login, require additional verification (2FA or email confirmation)
- **Alert:** Email user about suspicious login attempt

#### FR20.2: Unusual Behavior Detection
- **Requirement:** System SHALL detect unusual login patterns
- **Patterns:**
  - Login at unusual time (user normally logs in 9am-5pm, now logging in at 3am)
  - Login from unusual location (user normally in USA, now in China)
  - New device type (user normally on iPhone, now on Android)
  - Unusual IP address range
- **Risk Score:** Calculate 0-100 risk score
- **Response:** Risk score > 70 → Require 2FA or email confirmation

#### FR20.3: Account Compromise Indicators
- **Requirement:** System SHALL detect indicators of compromised accounts
- **Indicators:**
  - Multiple failed logins followed by success (password guessing)
  - Rapid changes to account settings
  - Mass data export
  - Privilege escalation attempts
  - Access to unusual resources
- **Response:** Lock account, alert administrators, email user

---

## INTEGRATION & API REQUIREMENTS

### FR21: OAuth 2.0 Integration (Phase 2)

**Priority:** HIGH  
**Status:** Phase 2 (Planned)  
**Dependencies:** OAuth provider accounts (Google, GitHub, Microsoft)

#### FR21.1: Google OAuth
- **Requirement:** System SHALL integrate Google OAuth 2.0 for authentication
- **Flow:**
  1. User clicks "Login with Google" button
  2. Redirect to Google authorization page
  3. User authorizes Biashara Bridges
  4. Google redirects back with authorization code
  5. System exchanges code for access token
  6. System retrieves user profile from Google
  7. System creates/updates user account
  8. System logs user in
- **Profile Import:**
  - Email (already verified)
  - First name, last name
  - Profile picture
- **Account Linking:** If email exists, link Google account to existing user

#### FR21.2: GitHub OAuth
- **Requirement:** System SHALL integrate GitHub OAuth for authentication
- **Purpose:** Developer-focused login option
- **Profile Import:**
  - Email (if public)
  - Name
  - Username (suggest as Biashara Bridges username)
  - Profile picture

#### FR21.3: Microsoft OAuth
- **Requirement:** System SHALL integrate Microsoft OAuth for enterprise users
- **Purpose:** Enterprise compatibility, preparation for SSO
- **Profile Import:**
  - Email
  - Name
  - Company (if available)
  - Department (if available)

---

### FR22: RESTful API (Phase 3)

**Priority:** MEDIUM  
**Status:** Phase 3 (Planned)  
**Dependencies:** API framework (Django REST Framework)

#### FR22.1: User Management API
- **Requirement:** System SHALL provide RESTful API for user management
- **Endpoints:**
  - `GET /api/users/` - List users (admin only)
  - `GET /api/users/{id}/` - Get user details
  - `POST /api/users/` - Create user (admin only)
  - `PATCH /api/users/{id}/` - Update user
  - `DELETE /api/users/{id}/` - Delete user (admin only)
- **Authentication:** Token-based (JWT)
- **Authorization:** Role-based access control

#### FR22.2: Authentication API
- **Requirement:** System SHALL provide API for authentication
- **Endpoints:**
  - `POST /api/auth/login/` - Login (returns JWT token)
  - `POST /api/auth/logout/` - Logout
  - `POST /api/auth/refresh/` - Refresh token
  - `POST /api/auth/verify/` - Verify token validity
- **Security:** Rate limiting, HTTPS required

#### FR22.3: API Documentation
- **Requirement:** System SHALL provide interactive API documentation
- **Implementation:** Swagger/OpenAPI specification
- **URL:** `/api/docs/`
- **Content:** All endpoints, request/response examples, authentication guide

---

### FR23: Webhooks (Phase 3)

**Priority:** LOW  
**Status:** Phase 3 (Planned)  
**Dependencies:** API infrastructure

#### FR23.1: Event Webhooks
- **Requirement:** System SHALL support webhook notifications for events
- **Events:**
  - `user.created` - New user registered
  - `user.updated` - User profile updated
  - `user.deleted` - User account deleted
  - `user.login` - User logged in
  - `user.email_verified` - User verified email
- **Configuration:** Admin can configure webhook URLs
- **Payload:** JSON with event details
- **Security:** HMAC signature for verification
- **Retry:** Retry failed deliveries up to 3 times

---

## NON-FUNCTIONAL REQUIREMENTS

### NFR1: Performance

**Priority:** HIGH  
**Status:** Phase 1  

#### NFR1.1: Page Load Times
- Registration form: < 2 seconds
- Login page: < 1 second
- Profile page: < 2 seconds
- Dashboard: < 3 seconds

#### NFR1.2: Transaction Times
- Form submission: < 3 seconds
- Login authentication: < 1 second
- Password verification: < 50ms
- Session validation: < 100ms

#### NFR1.3: Concurrency
- Support 100 concurrent registrations
- Support 500 concurrent logins
- Support 1,000 concurrent active sessions

#### NFR1.4: Scalability
- Architecture must support 10,000+ users
- Database queries optimized with indexes
- Caching for frequently accessed data
- CDN for static assets

---

### NFR2: Security

**Priority:** CRITICAL  
**Status:** Phase 1  

#### NFR2.1: Authentication Security
- All auth pages HTTPS only (redirect HTTP to HTTPS)
- Session cookies: HttpOnly, Secure, SameSite=Lax
- Passwords never sent/stored in plain text
- Password hashing: PBKDF2-SHA256 with 260,000 iterations
- CSRF protection on all forms
- XSS prevention (escape all user input)
- SQL injection prevention (use Django ORM, parameterized queries)

#### NFR2.2: Access Control
- Users can only access own data (except admins)
- Authorization checks on every request
- Permission checks before any data modification
- Failed authorization returns 403 Forbidden

#### NFR2.3: Rate Limiting
- Registration: 10 per hour per IP
- Login: 5 failed attempts per 15 minutes per user
- Password reset: 3 requests per hour per email
- API calls: 100 per minute per user (Phase 3)

#### NFR2.4: Token Security
- All tokens cryptographically random (UUID4 or equivalent)
- Email verification tokens expire after 24 hours
- Password reset tokens expire after 1 hour
- Session tokens expire after 30 minutes inactivity
- Single-use tokens (invalidated after use)

---

### NFR3: Usability

**Priority:** HIGH  
**Status:** Phase 1  

#### NFR3.1: Mobile Responsiveness
- All pages must be mobile-responsive
- Touch-friendly buttons (min 44×44px)
- Mobile-first design approach
- Test on iOS Safari, Android Chrome
- Forms work well on mobile (proper input types, no zoom)

#### NFR3.2: User Guidance
- Clear, actionable error messages (not technical jargon)
- Help text for complex fields
- Progress indicators for multi-step processes
- Confirmation messages for important actions
- Tooltips for additional information

#### NFR3.3: Accessibility (WCAG 2.1 AA)
- Proper semantic HTML
- ARIA labels where needed
- Keyboard navigation support
- Screen reader compatible
- Color contrast ratios meet standards (4.5:1 for text)
- Form validation accessible

#### NFR3.4: Browser Compatibility
- Support latest 2 versions of Chrome, Firefox, Safari, Edge
- Graceful degradation for older browsers
- JavaScript not required for critical functions (progressive enhancement)

---

### NFR4: Reliability

**Priority:** HIGH  
**Status:** Phase 1  

#### NFR4.1: Uptime
- Target: 99.9% uptime (< 9 hours downtime per year)
- Monitoring: 24/7 uptime monitoring
- Alerts: Immediate alerts on downtime

#### NFR4.2: Email Deliverability
- Target: > 95% email delivery rate
- Monitoring: Track delivery success/failure
- Retry: Failed emails retried up to 3 times
- Fallback: Manual resend option if email fails

#### NFR4.3: Data Integrity
- Database transactions for atomic operations
- Rollback on failure
- Regular database backups (daily)
- Backup retention: 30 days
- Backup testing: Monthly restore tests

#### NFR4.4: Error Handling
- Graceful error handling (no stack traces to users)
- Friendly error pages (404, 500, 403)
- Errors logged for debugging
- Critical errors alert administrators

---

### NFR5: Maintainability

**Priority:** MEDIUM  
**Status:** Phase 1  

#### NFR5.1: Code Quality
- Clean, readable code
- Proper documentation (docstrings)
- Follow PEP 8 style guide (Python)
- Code comments for complex logic
- DRY principle (Don't Repeat Yourself)

#### NFR5.2: Testing
- Unit tests for models, services
- Integration tests for views, forms
- Test coverage: > 80%
- Automated testing in CI/CD pipeline

#### NFR5.3: Logging
- Comprehensive application logging
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Structured logs (JSON format preferred)
- Log rotation to prevent disk fill
- Centralized logging (e.g., ELK stack)

---

### NFR6: Compliance

**Priority:** HIGH  
**Status:** Phase 1  

#### NFR6.1: GDPR Compliance
- User consent tracked
- Data minimization (collect only what's needed)
- Right to access (user can download data)
- Right to deletion (user can delete account)
- Data retention policies
- Privacy policy visible and clear

#### NFR6.2: Data Privacy
- Personal data encrypted in transit (HTTPS)
- Sensitive data encrypted at rest
- Access logs for sensitive data
- Data anonymization for analytics
- Third-party data sharing disclosed

---

## USER STORIES

### Story 1: New Employee Registration
```
As a new Biashara Bridges employee
I want to register for an account
So that I can access internal systems

Acceptance Criteria:
- I can navigate to the registration page
- I can fill in my details (name, email, password)
- I select "Employee" category
- I submit the form
- I receive a verification email within 1 minute
- I can click the link to verify my email
- My account is activated
- I can log in and see the employee dashboard
```

### Story 2: Client Registration
```
As a potential client
I want to quickly register for an account
So that I can access Biashara Bridges services

Acceptance Criteria:
- Registration form is simple and fast (< 3 minutes)
- Clear explanation of email verification
- Professional, trustworthy appearance
- Verification email arrives promptly
- Easy one-click verification
- Immediate access to client portal after verification
```

### Story 3: Job Applicant with Resume
```
As a job applicant
I want to register and upload my resume
So that I can apply for positions

Acceptance Criteria:
- I select "Applicant" category
- Resume upload field appears
- I can upload my PDF resume (< 5MB)
- Resume is stored securely
- I receive verification email
- After verification, I can access application system
- I can see my uploaded resume in my profile
```

### Story 4: Investor Registration with 2FA (Phase 2)
```
As an investor
I want to register with maximum security
So that my financial data is protected

Acceptance Criteria:
- I register and verify email
- System prompts me to set up 2FA (required for investors)
- I scan QR code with Google Authenticator
- I receive backup codes
- On next login, I must enter 6-digit code
- My account is secure with 2FA
- I can access portfolio management
```

### Story 5: Password Reset
```
As a user who forgot my password
I want to reset my password
So that I can access my account again

Acceptance Criteria:
- I can click "Forgot Password" on login page
- I enter my email address
- I receive password reset email within 1 minute
- I click the link in the email
- I can enter a new password
- I submit and receive confirmation
- I can log in with new password
- All my previous sessions are logged out
```

### Story 6: Profile Update
```
As a registered user
I want to update my contact information
So that Biashara Bridges has my current details

Acceptance Criteria:
- I can navigate to my profile
- I can click "Edit Profile"
- I can update phone, address, city, etc.
- Changes are validated
- Changes are saved
- I see confirmation message
- Updated information is visible on my profile
```

---

## ACCEPTANCE CRITERIA

### Phase 1 - Foundation (MUST HAVE) ✅

#### Registration System:
- [x] Registration form accessible at /accounts/join/
- [x] All required fields collected and validated
- [x] Username uniqueness enforced
- [x] Email uniqueness enforced
- [x] Password complexity enforced (8+ chars, mixed)
- [x] Category selection works for all 4 categories
- [x] Resume upload works for Applicants (PDF/DOC/DOCX, < 5MB)
- [x] CSRF protection enabled
- [x] Email verification token generated and sent within 60 seconds
- [x] Verification link works and activates account
- [x] Unverified users cannot login
- [x] Resend verification email works
- [x] Registration completion rate > 95%
- [x] Mobile-responsive design

#### Authentication:
- [x] Login with username OR email works
- [x] Password verified correctly (hashed, secure)
- [x] Email verification checked on login
- [x] Remember Me functionality works (30 days)
- [x] Appropriate dashboard redirect based on category
- [x] Login history logged
- [x] Failed login rate limiting works (5 per 15 min)
- [x] Password reset request works
- [x] Password reset email sent within 60 seconds
- [x] Password reset token validates and expires (1 hour)
- [x] Password update works
- [x] Logout works and clears session
- [x] Session timeout after 30 minutes inactivity

#### Profile Management:
- [x] Users can view own profile
- [x] Users can edit contact information
- [x] Phone validation works
- [x] Country dropdown works
- [x] Profile updates save correctly
- [x] Applicants can update resume
- [x] Resume download works
- [x] Profile privacy enforced (users see only own profile)

#### Security:
- [x] All auth pages HTTPS only
- [x] Passwords hashed with PBKDF2 (260K iterations)
- [x] Session cookies secure (HttpOnly, Secure, SameSite)
- [x] CSRF protection on all forms
- [x] SQL injection prevention (ORM)
- [x] XSS prevention (template escaping)
- [x] Zero security incidents during testing

#### Performance:
- [x] Registration form loads < 2 seconds
- [x] Login processes < 1 second
- [x] Profile page loads < 2 seconds
- [x] Supports 100 concurrent registrations (load test)

#### Usability:
- [x] Mobile-responsive all pages
- [x] Clear error messages
- [x] Keyboard navigation works
- [x] Works on iOS Safari and Android Chrome

---

### Phase 2 - Enhanced Security (SHOULD HAVE) ⏳

#### Two-Factor Authentication:
- [ ] Users can enable 2FA in settings
- [ ] QR code displayed for authenticator app
- [ ] 6-digit TOTP code validated on login
- [ ] Backup codes generated (10 per user)
- [ ] 2FA required for all investors
- [ ] 2FA recovery process works

#### OAuth / Social Login:
- [ ] Google login button on login/register pages
- [ ] Google OAuth flow works
- [ ] Profile auto-filled from Google
- [ ] Email already verified via Google
- [ ] GitHub login works
- [ ] Microsoft login works (enterprise)
- [ ] Password reset requests reduced by 60%

#### AI Fraud Detection:
- [ ] Duplicate user detection works (fuzzy matching)
- [ ] Disposable email detection works
- [ ] Bot behavior identification works
- [ ] Risk score calculated (0-100)
- [ ] High-risk logins challenged (2FA or email confirmation)
- [ ] Fraud detection accuracy > 90%

#### Enhanced Audit:
- [ ] All user actions logged
- [ ] Permission changes logged
- [ ] Logs retained 12 months
- [ ] Audit log search works (admin)

---

### Phase 3 - Enterprise Features (NICE TO HAVE) 🔮

#### Single Sign-On:
- [ ] SAML 2.0 integration complete
- [ ] Works with Okta
- [ ] Works with Azure AD
- [ ] SSO logout handling works
- [ ] Fallback to password if SSO unavailable

#### Biometric Authentication:
- [ ] WebAuthn support implemented
- [ ] FaceID/TouchID works on iOS
- [ ] Fingerprint works on Android
- [ ] Hardware security key support

#### APIs:
- [ ] RESTful API functional
- [ ] JWT authentication works
- [ ] API documentation available (Swagger)
- [ ] Webhooks deliver events
- [ ] Rate limiting works (100 per min)

---

## DEPENDENCIES

### External Dependencies

#### Phase 1:
- **Django Framework:** 4.x or higher
- **PostgreSQL:** 13 or higher
- **Email Service:** SendGrid or AWS SES
- **Cloud Hosting:** AWS, Heroku, or equivalent
- **SSL Certificate:** Let's Encrypt or commercial
- **CDN:** CloudFlare or AWS CloudFront (optional but recommended)

#### Phase 2:
- **django-otp:** For 2FA TOTP
- **django-allauth:** For OAuth integration
- **OAuth Credentials:** Google, GitHub, Microsoft developer accounts
- **ML Framework:** Scikit-learn or TensorFlow Lite (for fraud detection)

#### Phase 3:
- **python-saml:** For SSO
- **Django REST Framework:** For API
- **Celery:** For async tasks
- **Redis:** For caching and task queue
- **WebAuthn Library:** For biometric

### Internal Dependencies

- User Registration DEPENDS ON: None (foundational)
- Authentication DEPENDS ON: User Registration complete
- Profile Management DEPENDS ON: Authentication working
- User Categories DEPENDS ON: User Registration
- Permissions & Roles DEPENDS ON: User Categories
- Security & Audit DEPENDS ON: Authentication
- APIs DEPENDS ON: All Phase 1 and 2 features complete

---

## OUT OF SCOPE

The following features are **explicitly out of scope** for the current phases:

### Not Included in Any Phase:

1. **Social Features**
   - User-to-user messaging
   - Social networking features
   - User followers/friends
   - Activity feeds

2. **Advanced Analytics**
   - Predictive analytics dashboard
   - User behavior heatmaps
   - A/B testing platform
   - Custom reporting builder

3. **Mobile Native Apps**
   - iOS native app
   - Android native app
   - Mobile push notifications
   - (Mobile web works, native apps out of scope)

4. **Third-Party Integrations** (Beyond OAuth)
   - CRM integrations (Salesforce, HubSpot)
   - Accounting software integrations
   - Marketing automation platforms
   - (APIs in Phase 3 enable these but integration itself out of scope)

5. **Advanced AI Features**
   - Natural language processing
   - Computer vision for photo verification
   - Voice authentication
   - AI chatbot (Phase 3 has basic chatbot only)

6. **Internationalization**
   - Multi-language support (English only)
   - Currency localization
   - Date/time format localization
   - (May be added in future phases)

### Deferred to Future Phases (Post Phase 3):

7. **Blockchain Authentication**
8. **Zero-Knowledge Proofs**
9. **Quantum-Resistant Encryption**
10. **Custom Hardware Tokens**

---

## APPENDICES

### Appendix A: API Endpoints Reference (Phase 3)

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| POST | /api/auth/register/ | Register new user | No |
| POST | /api/auth/login/ | Login (get JWT) | No |
| POST | /api/auth/logout/ | Logout | Yes |
| POST | /api/auth/refresh/ | Refresh JWT | Yes |
| GET | /api/users/ | List users | Admin only |
| GET | /api/users/{id}/ | Get user details | Yes (own or admin) |
| PATCH | /api/users/{id}/ | Update user | Yes (own or admin) |
| DELETE | /api/users/{id}/ | Delete user | Admin only |
| POST | /api/users/{id}/change-password/ | Change password | Yes (own) |
| GET | /api/categories/ | List categories | Yes |

### Appendix B: Database Models Summary

**User (Django built-in + extensions):**
- id, username, email, password, first_name, last_name
- is_staff, is_superuser, is_active
- email_verified (custom field)
- date_joined, last_login

**UserProfile:**
- user (FK to User)
- category (1=Employee, 2=Client, 3=Applicant, 4=Investor)
- phone, address, city, state, zip, country
- gender, date_of_birth
- department (FK to Department, for Employees)
- resume (FileField, for Applicants)
- verification_token, token_created_at
- last_login_ip, last_login_device

**LoginHistory:**
- user (FK to User)
- timestamp, ip_address, user_agent
- success (Boolean)
- failure_reason (nullable)

**Department:**
- name, description
- manager (FK to User)

**CategoryHistory (Phase 2):**
- user (FK to User)
- old_category, new_category
- changed_by (FK to User)
- changed_at

**AuditLog (Phase 2):**
- user (FK to User)
- action (create/read/update/delete)
- model, object_id
- changes (JSON field)
- timestamp, ip_address

---

## GLOSSARY

- **2FA:** Two-Factor Authentication
- **BRD:** Business Requirements Document
- **CSRF:** Cross-Site Request Forgery
- **FRD:** Functional Requirements Document
- **GDPR:** General Data Protection Regulation
- **JWT:** JSON Web Token
- **OAuth:** Open Authorization (standard for delegated authentication)
- **PBKDF2:** Password-Based Key Derivation Function 2
- **RBAC:** Role-Based Access Control
- **SAML:** Security Assertion Markup Language
- **SSO:** Single Sign-On
- **TOTP:** Time-based One-Time Password
- **UUID:** Universally Unique Identifier
- **WCAG:** Web Content Accessibility Guidelines
- **XSS:** Cross-Site Scripting

---

**END OF FUNCTIONAL REQUIREMENTS DOCUMENT**

**Next Steps:**
1. Review and approve this FRD
2. Development team creates technical design document
3. Sprint planning based on Phase 1 requirements
4. Begin development (Week 1)

**Document Prepared By:** Development Team  
**Date:** October 28, 2025  
**Related Document:** Registration_System_BRD.md (Business Requirements)  
**Approval Required:** Project Stakeholders, Development Lead

---

*This document is a living document and will be updated as requirements evolve through each phase of development.*

