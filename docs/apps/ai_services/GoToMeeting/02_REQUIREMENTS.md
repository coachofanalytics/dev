# GoToMeeting Integration - Requirements

**Last Updated:** October 22, 2025  
**Status:** Phase 1 ✅ Working | Phase 2 📋 Planned | Phase 3 📋 Planned

---

## 🎯 PRIMARY OBJECTIVE

Automate meeting attendance tracking and recording management with minimal manual effort.

---

## 📋 PHASE 1: Basic Integration (COMPLETE ✅)

### REQ-001: OAuth Authentication
**Status:** ✅ Implemented

**Requirements:**
- ✅ OAuth2 flow with LogMeIn
- ✅ Token storage (cache-based)
- ✅ Auto-refresh on expiry
- ⚠️ **Issue:** Tokens lost on restart

---

### REQ-002: Fetch Meetings
**Status:** ✅ Implemented

**Requirements:**
- ✅ Fetch meetings by date range
- ✅ Retrieve attendee information
- ✅ Store in database
- ⚠️ **Issue:** Creates duplicates

---

### REQ-003: Download Recordings
**Status:** ✅ Implemented

**Requirements:**
- ✅ Download meeting recordings
- ✅ Upload to Google Drive
- ⚠️ **Issue:** Memory issues with large files

---

### REQ-004: Link to Tasks
**Status:** ✅ Implemented

**Requirements:**
- ✅ Match attendees to users
- ✅ Link meetings to tasks via `activity_mapping`
- ✅ Award task points for attendance (>3 min)
- ⚠️ **Issue:** Hardcoded mapping (11 meetings only)

---

## 📋 PHASE 2: Critical Fixes (PLANNED - Week 1)

### REQ-010: Normalized Data Model
**Priority:** 🔴 CRITICAL

**Requirements:**
- [ ] Create separate Meeting and MeetingAttendee models
- [ ] Use proper field types (DateTimeField, IntegerField)
- [ ] Add unique constraints
- [ ] Migrate existing data without loss

---

### REQ-011: Secure Token Storage
**Priority:** 🔴 CRITICAL

**Requirements:**
- [ ] Store tokens in database (not cache)
- [ ] Encrypt tokens at rest
- [ ] Persist across server restarts
- [ ] Support token rotation

---

### REQ-012: Duplicate Prevention
**Priority:** 🔴 CRITICAL

**Requirements:**
- [ ] Use get_or_create with unique constraints
- [ ] Check meeting_id + attendee_email uniqueness
- [ ] Prevent re-fetching same data
- [ ] Update existing records instead of creating new

---

### REQ-013: Proper Error Handling
**Priority:** 🔴 CRITICAL

**Requirements:**
- [ ] Replace bare `except:` with specific exceptions
- [ ] Log all errors properly
- [ ] User-friendly error messages
- [ ] Retry logic for transient failures

---

## 📋 PHASE 3: Performance (PLANNED - Week 2)

### REQ-020: Async Processing
**Priority:** 🟡 HIGH

**Requirements:**
- [ ] Use Celery for background meeting fetch
- [ ] Queue recording downloads
- [ ] Email notifications when complete
- [ ] Progress tracking UI

---

### REQ-021: Batch API Calls
**Priority:** 🟡 HIGH

**Requirements:**
- [ ] Fetch attendees in parallel (ThreadPoolExecutor)
- [ ] Reduce N+1 queries
- [ ] 10x faster for 100+ meetings

---

## 📋 PHASE 4: Features (PLANNED - Week 3)

### REQ-030: Automated Daily Sync
**Priority:** 🟢 MEDIUM

**Requirements:**
- [ ] Celery beat schedule (daily at 1 AM)
- [ ] Auto-fetch yesterday's meetings
- [ ] Email summary to admins

---

### REQ-031: Meeting Analytics
**Priority:** 🟢 MEDIUM

**Requirements:**
- [ ] Dashboard showing meeting stats
- [ ] Top attendees
- [ ] Meeting trends
- [ ] Department participation

---

## 📜 BUSINESS RULES

### BR-001: Task Point Award
- Attendance >3 minutes qualifies for points
- User matched by email (preferred) or name
- Points awarded per `activity_mapping` configuration

### BR-002: Activity Mapping
Current hardcoded mapping (11 meeting types):
- '708385093': "PBR sessions"
- '632884285': "BI Sessions"
- etc.

**Future:** Make configurable via admin interface

---

**See:** 03_ARCHITECTURE.md for design details


