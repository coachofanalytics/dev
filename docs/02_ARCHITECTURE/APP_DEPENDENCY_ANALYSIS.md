# Django App Dependency Analysis
**Date:** January 2025  
**Branch:** `26.01_CODA_DEV_CM`  
**Purpose:** Identify dependent vs independent apps for incremental isolation

## Executive Summary

This document analyzes all Django applications in the CODA project to:
1. Identify which apps are **core** (must keep for basic functionality)
2. Identify which apps are **dependent** (depend on other apps)
3. Identify which apps are **independent** (can run standalone)
4. Create a dependency graph showing relationships
5. Propose which apps to keep temporarily to maintain current behavior

---

## 1. All Apps Inventory

### 1.1 Django Core Apps (Always Required)
- `django.contrib.admin`
- `django.contrib.auth`
- `django.contrib.contenttypes`
- `django.contrib.sessions`
- `django.contrib.messages`
- `django.contrib.staticfiles`
- `django.contrib.humanize`
- `django.contrib.sites`

### 1.2 Third-Party Apps
- `crispy_forms`
- `storages`
- `django_countries`
- `mathfilters`
- `mptt`
- `django_filters`
- `allauth`
- `allauth.account`
- `allauth.socialaccount`
- `allauth.socialaccount.providers.google`
- `allauth.socialaccount.providers.facebook`

### 1.3 Custom CODA Apps
*(To be analyzed from INSTALLED_APPS)*

---

## 2. Dependency Analysis Methodology

For each custom app, we will analyze:
- **Direct imports**: What other apps does it import from?
- **Model dependencies**: ForeignKey/ManyToMany relationships
- **Service dependencies**: Does it call services from other apps?
- **Template dependencies**: Does it extend templates from other apps?
- **URL dependencies**: Does it reference URLs from other apps?

---

## 3. App Categories

### 3.1 Core Apps (Must Keep)
*Apps required for basic system functionality*

### 3.2 Dependent Apps
*Apps that depend on other apps*

### 3.3 Independent Apps
*Apps that can run standalone*

### 3.4 Supporting Apps
*Apps that provide shared functionality*

---

## 4. Dependency Matrix

*(To be filled in during analysis)*

---

## 5. Recommendations

### 5.1 Apps to Keep Temporarily
*Apps needed to maintain current behavior while decoupling*

### 5.2 Apps Safe to Remove
*Apps that can be removed without breaking core functionality*

### 5.3 Decoupling Priority
*Order in which to decouple apps*

---

## Next Steps

1. ✅ Read full INSTALLED_APPS from `26.01_CODA_DEV_CM`
2. ⏳ Analyze each app's imports and dependencies
3. ⏳ Create dependency graph
4. ⏳ Categorize apps
5. ⏳ Propose temporary keep list
6. ⏳ Create incremental decoupling plan

