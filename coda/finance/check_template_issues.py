#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Template Issue Checker
Checks templates for common issues after structure organization.
"""

import os
import re
import glob

def check_template_issues():
    """Check templates for common issues."""
    
    print("CHECKING TEMPLATE ISSUES")
    print("=" * 50)
    
    # Template directory
    template_dir = "/Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda/finance/templates/finance"
    
    # Issues found
    issues = []
    
    # Check critical templates
    critical_templates = [
        "budgets/unified_dashboard.html",
        "payments/smart_transaction_entry.html",
        "budgets/budget_category_edit.html",
        "budgets/budget_requests_list.html",
        "loans/loan_budget_dashboard.html"
    ]
    
    for template_path in critical_templates:
        full_path = os.path.join(template_dir, template_path)
        if os.path.exists(full_path):
            print("\nCHECKING: {}".format(template_path))
            print("-" * 40)
            
            with open(full_path, 'r') as f:
                content = f.read()
            
            # Check for URL references
            url_matches = re.findall(r'url\s+[\'"]([^\'"]+)[\'"]', content)
            if url_matches:
                print("URL REFERENCES FOUND:")
                for url in url_matches:
                    print("  - {}".format(url))
            
            # Check for form actions
            form_matches = re.findall(r'<form[^>]*action\s*=\s*[\'"]([^\'"]*)[\'"]', content)
            if form_matches:
                print("FORM ACTIONS FOUND:")
                for action in form_matches:
                    print("  - {}".format(action))
            
            # Check for JavaScript AJAX calls
            ajax_matches = re.findall(r'url\s*:\s*[\'"]([^\'"]+)[\'"]', content)
            if ajax_matches:
                print("AJAX URLS FOUND:")
                for url in ajax_matches:
                    print("  - {}".format(url))
            
            # Check for onclick handlers
            onclick_matches = re.findall(r'onclick\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            if onclick_matches:
                print("ONCLICK HANDLERS FOUND:")
                for handler in onclick_matches:
                    print("  - {}".format(handler))
            
            # Check for href links
            href_matches = re.findall(r'href\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            if href_matches:
                print("HREF LINKS FOUND:")
                for href in href_matches:
                    print("  - {}".format(href))
        else:
            print("WARNING: Template not found: {}".format(template_path))
            issues.append("Missing template: {}".format(template_path))
    
    # Check for common issues
    print("\nCHECKING FOR COMMON ISSUES")
    print("-" * 40)
    
    # Check all HTML files for potential issues
    html_files = []
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    
    for html_file in html_files:
        relative_path = os.path.relpath(html_file, template_dir)
        
        with open(html_file, 'r') as f:
            content = f.read()
        
        # Check for old view references
        old_view_refs = re.findall(r'views_[a-z_]+', content)
        if old_view_refs:
            print("OLD VIEW REFERENCES in {}:".format(relative_path))
            for ref in old_view_refs:
                print("  - {}".format(ref))
                issues.append("Old view reference in {}: {}".format(relative_path, ref))
        
        # Check for missing URL names
        url_refs = re.findall(r'url\s+[\'"]([^\'"]+)[\'"]', content)
        for url_ref in url_refs:
            if ':' not in url_ref:
                print("POTENTIAL ISSUE in {}: URL without namespace: {}".format(relative_path, url_ref))
                issues.append("URL without namespace in {}: {}".format(relative_path, url_ref))
    
    # Summary
    print("\nSUMMARY")
    print("-" * 40)
    print("Templates checked: {}".format(len(html_files)))
    print("Issues found: {}".format(len(issues)))
    
    if issues:
        print("\nISSUES TO FIX:")
        for issue in issues:
            print("  - {}".format(issue))
    else:
        print("\nNo issues found!")
    
    return issues

if __name__ == '__main__':
    issues = check_template_issues()
    
    if issues:
        print("\nWARNING: {} issues found that need attention.".format(len(issues)))
        exit(1)
    else:
        print("\nSUCCESS: No template issues found!")
        exit(0)
