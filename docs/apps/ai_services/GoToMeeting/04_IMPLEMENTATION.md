# GoToMeeting Integration - Implementation

**Last Updated:** October 22, 2025  
**Status:** ✅ Functional (needs refactoring)

---

## 📁 FILE STRUCTURE

```
coda/ai_services/
├── models.py                    # GotoMeetings model (lines 97-119)
├── views.py                     # OAuth & meeting functions (lines 214-637)
├── forms.py                     # MeetingForm (lines 98-108)
├── utils.py                     # Helper functions (download_recording, upload_to_google_drive)
├── urls.py                      # URL patterns
├── admin.py                     # Admin registration
│
└── templates/ai_services/
    ├── meetingForm.html         # Date range form
    ├── meetingList.html         # Meeting results
    └── download_upload_recordings.html  # Recording management
```

---

## 🗄️ KEY MODELS

### GotoMeetings (Current)
**File:** `coda/ai_services/models.py` (lines 97-119)  
**Table:** `getdata_gotomeetings`  
**Records:** ~500+ (with duplicates)

---

## 🎯 KEY FUNCTIONS

### get_access_token()
**File:** `coda/ai_services/views.py` (lines 303-315)  
**Purpose:** Retrieve valid OAuth token, refresh if needed

### getmeetingresponse(startDate, endDate)
**File:** `coda/ai_services/views.py` (lines 320-390)  
**Purpose:** Fetch meetings from API for date range

### save_meeting_data(meeting_data)
**File:** `coda/ai_services/views.py` (lines 393-491)  
**Purpose:** Persist meetings to database, link to tasks

### meetingFormView(request)
**File:** `coda/ai_services/views.py` (lines 494-546)  
**Purpose:** Main view for fetching/displaying meetings

### download_and_upload_recordings(request)
**File:** `coda/ai_services/views.py` (lines 551-637)  
**Purpose:** Download recordings and upload to Google Drive

---

## 🔌 API ENDPOINTS

### GoToMeeting API
```
GET https://api.getgo.com/G2M/rest/historicalMeetings?startDate={start}&endDate={end}
GET https://api.getgo.com/G2M/rest/meetings/{meeting_id}/attendees
```

### OAuth Endpoints
```
https://authentication.logmeininc.com/oauth/authorize
https://authentication.logmeininc.com/oauth/token
```

---

## ⚙️ CONFIGURATION

### Environment Variables
```bash
API_CLIENT_ID=your_client_id
API_CLIENT_SECRET=your_client_secret
```

### Redirect URI (Hardcoded)
```python
API_REDIRECT_URI = "https://www.codanalytics.net/management/oauth/callback/"
```

**⚠️ Issue:** Not environment-aware

---

## 🐛 KNOWN TECHNICAL DEBT

1. **Denormalized Data:** One record per attendee
2. **Cache-Only Tokens:** Lost on restart
3. **Bare Exceptions:** `except:` hides errors
4. **Synchronous Calls:** Blocks requests
5. **Hardcoded Mapping:** activity_mapping dict (11 meetings)
6. **No Pagination:** Fetches all meetings at once
7. **Memory Issues:** Loads entire videos into RAM

---

## 📊 CHANGE HISTORY

| Date | Change | Files | Dev |
|------|--------|-------|-----|
| Oct 22, 2025 | 7-doc migration | All docs | AI |
| Oct 22, 2025 | Comprehensive analysis | Analysis doc | AI |
| [Earlier] | Initial implementation | views.py, models.py | Original team |

---

**See:** 03_ARCHITECTURE.md for design, 06_MAINTENANCE.md for issues


