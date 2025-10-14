# 02 - System Architecture

**Purpose:** High-level system architecture and design patterns

---

## 📚 Documents in This Section

### [TECHNICAL_DOCS.md](TECHNICAL_DOCS.md)
**Technical documentation and architecture notes**

---

## 🏗️ CODA System Architecture

### Core Philosophy
**"Transactions are the source of truth"** - All budget decisions flow from real spending data.

### Data Flow
```
Transaction Entry (Smart Form)
    ↓
Auto-Categorization (AI Service)
    ↓
Transaction Database (Source of Truth)
    ↓
Budget Projections (Data Analysis)
    ↓
Dashboard Views (User Interface)
```

### Technology Stack
- **Backend:** Django 4.x
- **Database:** PostgreSQL (Heroku)
- **Frontend:** jQuery 3.6.0, Bootstrap
- **Deployment:** Heroku
- **AI/ML:** Custom prediction service (84% accuracy)

### Key Design Patterns
- **Service Layer:** Business logic separated from views
- **Repository Pattern:** Data access through services
- **Event Sourcing:** Transactions as immutable events
- **4-Doc Standard:** Every feature documented consistently

---

**For detailed technical implementation, see app-specific IMPLEMENTATION.md files.**

**Last Updated:** October 13, 2025

