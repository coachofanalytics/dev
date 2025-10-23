# GoToMeeting Integration - Architecture

**Last Updated:** October 22, 2025  
**Purpose:** System design and technical architecture

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌───────────────┐      ┌──────────────┐      ┌─────────────┐
│  User/Form    │─────▶│    Views     │─────▶│ GoToMeeting │
│ (Date Range)  │      │ (OAuth/Fetch)│      │     API     │
└───────────────┘      └──────────────┘      └─────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  Database    │
                       │ (GotoMeetings│
                       │   model)     │
                       └──────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ Task System  │
                       │ (Link to     │
                       │  tasks)      │
                       └──────────────┘
```

---

## 📊 CURRENT DATA MODEL (Phase 1)

### GotoMeetings (Denormalized)
```python
class GotoMeetings(models.Model):
    meeting_topic = CharField(max_length=250)
    meeting_id = CharField(max_length=100)
    attendee_name = CharField(max_length=150)
    attendee_email = CharField(max_length=150)
    # ... other fields
```

**Issues:**
- ❌ One record per attendee (duplicates meeting info)
- ❌ CharField for dates (should be DateTimeField)
- ❌ No unique constraints

---

## 🎯 PROPOSED DATA MODEL (Phase 2)

### Meeting (Normalized)
```python
class Meeting(models.Model):
    meeting_id = CharField(max_length=100, unique=True)
    topic = CharField(max_length=500)
    start_time = DateTimeField(db_index=True)
    end_time = DateTimeField()
    duration_minutes = IntegerField()
    recording_url = URLField(blank=True)
    download_url = URLField(blank=True)
```

### MeetingAttendee
```python
class MeetingAttendee(models.Model):
    meeting = ForeignKey(Meeting, on_delete=CASCADE)
    user = ForeignKey(User, null=True)
    attendee_name = CharField(max_length=200)
    attendee_email = EmailField()
    duration_minutes = IntegerField()
    
    class Meta:
        unique_together = [('meeting', 'attendee_email')]
```

---

## 🔐 OAUTH ARCHITECTURE

### Current (Cache-Based):
```
User → OAuth Login → LogMeIn → Callback
                                   ↓
                            Exchange for Tokens
                                   ↓
                            Store in Django Cache
                            (Lost on restart!)
```

### Proposed (Database + Encryption):
```
User → OAuth Login → LogMeIn → Callback
                                   ↓
                            Exchange for Tokens
                                   ↓
                            Encrypt with Django Signer
                                   ↓
                            Store in OAuthToken Model
                            (Persists forever!)
```

---

## 🔧 TECHNOLOGY DECISIONS

### Decision 1: Sync vs Async
**Current:** Synchronous (blocks requests)  
**Proposed:** Celery (background tasks)  
**Reason:** Fetching 100 meetings takes 30+ seconds

### Decision 2: Token Storage
**Current:** Django cache  
**Proposed:** Database with encryption  
**Reason:** Tokens lost on cache clear/restart

### Decision 3: Duplicate Handling
**Current:** Creates duplicates every fetch  
**Proposed:** get_or_create with unique constraints  
**Reason:** Database filling with duplicates

---

**See:** 04_IMPLEMENTATION.md for current code, 02_REQUIREMENTS.md for improvement plan


