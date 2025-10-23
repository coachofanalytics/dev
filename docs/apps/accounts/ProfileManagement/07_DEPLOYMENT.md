# Profile Management - Deployment

**Feature:** User Profiles & Settings  
**Status:** Deployed ✅  
**Last Updated:** October 22, 2025

---

## 📋 DEPLOYMENT CHECKLIST

- [x] UserProfile model migrated
- [x] Profile views functional
- [x] Templates tested
- [x] File upload configured (resumes)
- [x] Tests passing

---

## ⚙️ CONFIGURATION

### Media Files (Resume Storage)
```bash
heroku config:set MEDIA_ROOT="/app/media" --app codamakutano
heroku config:set MEDIA_URL="/media/" --app codamakutano
```

---

## 🚀 DEPLOYMENT PROCEDURE

```bash
# Push code
git push heroku main --app codamakutano

# Run migrations
heroku run "cd coda && python manage.py migrate accounts" --app codamakutano

# Test profile viewing
curl -I https://codamakutano.herokuapp.com/accounts/profile/testuser/
```

---

## ✅ VERIFICATION

- Profile page loads
- Edit profile works
- Changes save correctly
- Resume upload functional

---

**Status:** ✅ Deployed and stable


