# Integrations & API - Deployment

**Feature:** External Integrations & APIs  
**Status:** Not Deployed (Phase 2-3)  
**Last Updated:** October 22, 2025

---

## 📋 FUTURE DEPLOYMENT

### Phase 2: OAuth Configuration
```bash
# Google OAuth
heroku config:set GOOGLE_OAUTH_CLIENT_ID="xxx" --app codamakutano
heroku config:set GOOGLE_OAUTH_CLIENT_SECRET="xxx" --app codamakutano

# GitHub OAuth
heroku config:set GITHUB_OAUTH_CLIENT_ID="xxx" --app codamakutano
heroku config:set GITHUB_OAUTH_CLIENT_SECRET="xxx" --app codamakutano

# API Settings
heroku config:set API_RATE_LIMIT="1000/hour" --app codamakutano
```

### Phase 3: SSO Configuration
```bash
# SAML Settings
heroku config:set SAML_ENTITY_ID="https://codatrainingapp.herokuapp.com" --app codatrainingapp
heroku config:set SAML_ACS_URL="https://codatrainingapp.herokuapp.com/accounts/saml/acs/" --app codatrainingapp
```

---

**Status:** Planned for Phase 2-3



