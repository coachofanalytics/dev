# IMPLEMENTATION GUIDE

**Document:** 6 of 7  
**Created:** November 5, 2025  
**Purpose:** Step-by-step implementation instructions

---

## 🚀 IMPLEMENTATION PHASES

### **Phase 1: Setup (Day 1)**

#### **1.1 Create Service Layer**
```bash
mkdir -p coda/main/services
touch coda/main/services/__init__.py
touch coda/main/services/team_service.py
```

#### **1.2 Create Management Commands Directory**
```bash
mkdir -p coda/main/management/commands
touch coda/main/management/__init__.py
touch coda/main/management/commands/__init__.py
```

---

### **Phase 2: Data Model (Day 2)**

#### **2.1 Create Migration**
```bash
cd coda
python manage.py makemigrations accounts --name add_team_assignment_fields
```

#### **2.2 Review Migration**
```python
# Review the generated migration file
# Ensure all fields are correct
```

#### **2.3 Run Migration (Dev)**
```bash
python manage.py migrate
python manage.py migrate --plan  # Verify
```

---

### **Phase 3: Service Implementation (Day 3)**

#### **3.1 Implement TeamService**
```python
# coda/main/services/team_service.py
# See Architecture Design document for full implementation
```

#### **3.2 Create Point Calculation Method**
```python
def calculate_total_points(user_profile):
    # Implementation from Architecture Design
    pass
```

---

### **Phase 4: View Updates (Day 4)**

#### **4.1 Update team() View**
```python
# Replace existing logic with service calls
# See Architecture Design for structure
```

#### **4.2 Remove Hardcoded Logic**
```python
# Find and replace all hardcoded usernames
# Replace with category-based queries
```

---

### **Phase 5: Management Commands (Day 5)**

#### **5.1 Create Assignment Commands**
```python
# management/commands/assign_bog_leadership.py
# management/commands/assign_elite_team.py
# management/commands/verify_team_members.py
```

#### **5.2 Create Point Calculation Command**
```python
# management/commands/recalculate_team_points.py
```

---

### **Phase 6: Testing (Day 6)**

#### **6.1 Write Tests**
```python
# tests/test_team_service.py
# tests/test_team_assignment.py
```

#### **6.2 Run Tests**
```bash
pytest tests/ -v
```

---

### **Phase 7: Deployment (Day 7-8)**

#### **7.1 Deploy to UAT**
```bash
# See Migration Plan document
```

#### **7.2 Deploy to Production**
```bash
# See Migration Plan document
```

---

## 📝 CODE EXAMPLES

### **Complete TeamService Implementation**

See `ARCHITECTURE_DESIGN.md` for full code.

---

## ✅ CHECKLIST

- [ ] Service layer created
- [ ] Data model updated
- [ ] Migrations run
- [ ] Views updated
- [ ] Management commands created
- [ ] Tests written
- [ ] Deployed to UAT
- [ ] Deployed to production

---

**Continue to Document 7: [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)**

