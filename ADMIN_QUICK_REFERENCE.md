# Django Admin Quick Reference - Legal Immigration System

## Accessing the Admin Panel

1. Navigate to: `http://your-domain/admin/`
2. Log in with your superuser credentials
3. Find "Communities" section on the admin homepage

## Managing Consular Services

### Location
`Admin Home > Communities > Consular Services`

### Adding a New Service

Click the **"Add Consular Service"** button and complete:

| Field | Example | Notes |
|-------|---------|-------|
| Name | USCIS | Official name of the organization |
| Service Type | Government Agency | Choose from dropdown |
| Description | Official agency handling... | Detailed description (2-3 sentences) |
| Website | https://www.uscis.gov | Full URL with https:// |
| Phone | 1-800-375-5283 | Optional but recommended |
| Email | contact@agency.gov | Optional |
| Address | 123 Main St, City, State | Optional, multiple addresses supported |
| Country Coverage | USA | Single country or region coverage area |
| Services Offered | Green card applications, Visa processing, Citizenship | Comma-separated list |
| Is Featured | ☑ | Check to display prominently on main page |

### Editing a Service

1. Click on the service name in the list
2. Make changes
3. Click **"Save"** at the bottom

### Deleting a Service

1. Click checkbox next to service name
2. Select "Delete selected consular services" from Actions dropdown
3. Click "Go"
4. Confirm deletion

### Search Tips

- **Search box:** Type to find by name, description, or services offered
- **Filter by Type:** Use right sidebar to filter by service category
- **Filter by Feature Status:** Use right sidebar to show only featured services

---

## Managing Legal Resources

### Location
`Admin Home > Communities > Legal Immigration Resources`

### Adding a New Resource

Click the **"Add Legal Immigration Resource"** button and complete:

| Field | Example | Notes |
|-------|---------|-------|
| Title | Understanding Green Cards | Concise, searchable title |
| Category | Green Card & Permanent Residency | Choose from dropdown |
| Content | The United States green card... | Main resource content (can be lengthy) |
| External URL | https://www.uscis.gov/green-card | Link to source material (optional) |
| Related Service | USCIS | Link to a consular service if applicable |
| Keywords | green card, permanent, residency | Comma-separated, used for search |
| Is Critical | ☑ | Check if this is essential information |

### Categories

- **Visa Information** - Visa types, application processes
- **Green Card & Permanent Residency** - Green card paths and procedures
- **Citizenship & Naturalization** - Path to citizenship, N-400 form
- **Employment Authorization** - Work permits, EAD, SSN
- **Asylum & Refugee** - Asylum applications, refugee status
- **Deportation Defense** - Legal defenses, removal proceedings
- **Family Sponsorship** - Family-based immigration, I-130 forms
- **Legal Rights** - Constitutional and legal protections

### Editing a Resource

1. Click on the resource title in the list
2. Make changes to any field
3. Click **"Save"**

### Critical Resources

Resources marked as **"Is Critical"** will display with a warning banner and appear first in filtered results. Use for:
- Emergency contact information
- Time-sensitive deadlines
- Critical legal warnings
- Rights information

### Deleting a Resource

1. Click checkbox next to resource
2. Select "Delete selected legal immigration resources" from Actions dropdown
3. Click "Go"
4. Confirm deletion

---

## Quick Admin Tasks

### Create a Complete Service Entry

**Step 1:** Add the Consular Service
```
Name: U.S. Embassy - Mexico City
Type: Government Agency
Description: Official U.S. Embassy providing visa services and consular assistance
Website: https://mx.usembassy.gov
Phone: +52 (55) 5080-2000
Country Coverage: Mexico
Services: Visa interviews, passport services, emergency assistance
Is Featured: Yes
```

**Step 2:** Add Related Resources
```
Title: Visa Interview Preparation Guide
Category: Visa Information
Content: [Detailed guide about interview preparation]
Related Service: U.S. Embassy - Mexico City
Keywords: visa, interview, preparation, Mexico
Is Critical: No
```

**Step 3:** Verify on Frontend
- Visit `/community/legal-immigration/` to see featured service in Consular Services tab
- Visit `/community/consular-services/` to search for the service
- Visit `/community/legal-resources/` to find the related resource

---

## Common Admin Workflows

### Workflow 1: Add New Government Agency

1. Go to **Consular Services > Add**
2. Fill in all contact information
3. List all services it provides
4. Mark as Featured if prominent
5. Save
6. Add related resources for that agency

### Workflow 2: Add Important Legal Info

1. Go to **Legal Resources > Add**
2. Write comprehensive content
3. Mark as **Critical** if urgent
4. Link to relevant consular service
5. Add searchable keywords
6. Save

### Workflow 3: Update Existing Service

1. Go to **Consular Services**
2. Click service name
3. Update phone/website/services
4. Click **Save**
5. Verify changes on frontend (may need to refresh)

### Workflow 4: Create Resource Series

1. Add first resource with category X
2. In related services, pick a consular service
3. Add more resources for same service
4. Users can navigate between related resources

---

## Display Rules

### Featured Services
- Displayed in homepage cards
- Appear first in search results
- Have special highlighting on detail pages

### Critical Resources
- Show warning banner
- Appear first in filtered results
- Persistent visual indicators throughout

### Search & Filter
- **Services:** Searchable by name, description, services offered
- **Resources:** Searchable by title and keywords

---

## Bulk Editing

### Change Multiple Services to Featured

1. Go to **Consular Services**
2. Check boxes for multiple services
3. Select "Mark selected services as featured" (if available)
4. Click "Go"

### Delete Multiple Resources

1. Go to **Legal Resources**
2. Check boxes for resources to delete
3. From Actions dropdown, select "Delete selected..."
4. Click "Go"
5. Confirm

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Save and continue | Alt + S |
| Save and add another | Alt + A |
| Save and return to list | Ctrl + S |
| Delete | Alt + D |

*Note: Shortcuts may vary depending on browser*

---

## Helpful Tips

### ✓ Do's
- Keep descriptions under 3 sentences
- Use full URLs with https://
- Include area codes in phone numbers
- Comma-separate lists (services, keywords)
- Mark important/urgent info as critical
- Link resources to services when applicable

### ✗ Don'ts
- Don't use all CAPS
- Don't forget required fields (marked with *)
- Don't include outdated information
- Don't duplicate entries
- Don't mix unrelated categories
- Don't leave descriptions blank

---

## Monitoring

### View Change History
Click the **"History"** button (top right) on any detail page to see:
- Who made changes
- When they were made
- What changed

### Check Live Status
After saving:
1. Copy the URL from your admin panel
2. Visit the corresponding frontend page
3. Verify the information displays correctly
4. Test search/filter functions

---

## Contact & Support

- **Django Admin Help:** Built into admin panel (? icon)
- **System Admin:** Contact your project administrator
- **Bug Reports:** Submit via project issue tracker
