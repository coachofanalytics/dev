# Permissions & Roles - Architecture

**Feature:** Role-Based Access Control  
**Status:** Basic Implementation  
**Last Updated:** October 22, 2025

---

## 📊 DATA MODELS

### Department Model
```python
class Department(models.Model):
    name = CharField(max_length=100)
    company = ForeignKey(Company, on_delete=models.CASCADE)
    is_active = BooleanField(default=True)
```

### UserGroups Model
```python
class UserGroups(Group):
    is_active = BooleanField(default=True)
    is_featured = BooleanField(default=True)
    users = ManyToManyField(CustomerUser, related_name="user_groups")
```

### Team_Members Model
```python
class Team_Members(models.Model):
    user = ForeignKey(CustomerUser, on_delete=models.CASCADE)
    team = ForeignKey(Team, on_delete=models.CASCADE)
    role = CharField(max_length=50)
```

---

**See:** 04_IMPLEMENTATION.md



