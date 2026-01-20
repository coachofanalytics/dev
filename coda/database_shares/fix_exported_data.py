#!/usr/bin/env python3
"""
Fix None boolean values in exported JSON file

This script fixes the current exported file so you don't have to re-export.
"""

import gzip
import json
import sys
from pathlib import Path


def fix_boolean_none_values(data):
    """Fix None boolean values and wrong types in exported data"""
    fixed_count = 0

    # Boolean field defaults
    boolean_defaults = {
        "laptop_status": True,
        "is_active": True,
        "is_karen_country_club_member": False,
        "is_admin": False,
        "email_verified": False,
        "is_featured": True,
        "is_staff": False,
        "is_superuser": False,
    }

    boolean_fields = list(boolean_defaults.keys())

    for item in data:
        fields = item.get("fields", {})
        for field_name in boolean_fields:
            if field_name in fields:
                value = fields[field_name]
                # Fix None values
                if value is None or value == "None" or value == "null":
                    fields[field_name] = boolean_defaults.get(field_name, False)
                    fixed_count += 1
                # Fix wrong types (integers that aren't 0/1, strings, etc.)
                elif isinstance(value, int) and value not in [0, 1, True, False]:
                    fields[field_name] = False
                    fixed_count += 1
                elif isinstance(value, str):
                    # String representation of boolean
                    if value.lower() in ["true", "1", "yes"]:
                        fields[field_name] = True
                        fixed_count += 1
                    elif value.lower() in ["false", "0", "no", ""]:
                        fields[field_name] = False
                        fixed_count += 1
                    elif value.isdigit():
                        # String number - convert to boolean
                        fields[field_name] = bool(int(value))
                        fixed_count += 1

    return fixed_count


def apply_additional_fixes(data):
    """Apply additional fixes for system models and relationships"""
    target_user_ids = [74, 244, 36, 392, 495]
    fixed_count = 0

    # Remove user groups (auth.Group was removed)
    user_groups_fixed = 0
    for item in data:
        if item.get("model") == "accounts.customeruser":
            fields = item.get("fields", {})
            if "groups" in fields and fields["groups"]:
                fields["groups"] = []
                user_groups_fixed += 1
    if user_groups_fixed > 0:
        print(f"✅ Removed groups from {user_groups_fixed} users")
    fixed_count += user_groups_fixed

    # Fix Company.relation field
    company_fixed = 0
    for item in data:
        if item.get("model") == "main.company":
            fields = item.get("fields", {})
            if "relation" in fields:
                value = fields["relation"]
                if value is None or value == "None" or value == "null" or value == "":
                    fields["relation"] = 4  # Default
                    company_fixed += 1
    if company_fixed > 0:
        print(f"✅ Fixed {company_fixed} Company.relation fields")
        fixed_count += company_fixed

    # Fix Policy.employee references
    policy_fixed = 0
    for item in data:
        if item.get("model") == "management.policy":
            fields = item.get("fields", {})
            if "employee" in fields:
                emp_val = fields["employee"]
                if isinstance(emp_val, int) and emp_val not in target_user_ids:
                    fields["employee"] = target_user_ids[0]
                    policy_fixed += 1
                elif isinstance(emp_val, list) and len(emp_val) > 1:
                    if (
                        isinstance(emp_val[0], int)
                        and emp_val[0] not in target_user_ids
                    ):
                        fields["employee"] = target_user_ids[0]
                        policy_fixed += 1
    if policy_fixed > 0:
        print(f"✅ Fixed {policy_fixed} Policy.employee references")
        fixed_count += policy_fixed

    # Fix image2 references
    image2_fixed = 0
    for item in data:
        if item.get("model") == "accounts.userprofile":
            fields = item.get("fields", {})
            if "image2" in fields:
                img_val = fields["image2"]
                if img_val and img_val != 1 and img_val != "1":
                    fields["image2"] = 1
                    image2_fixed += 1
    if image2_fixed > 0:
        print(f"✅ Fixed {image2_fixed} image2 references")
        fixed_count += image2_fixed

    # Remove credential categories
    cred_cat_fixed = 0
    for item in data:
        if item.get("model") == "accounts.credential":
            fields = item.get("fields", {})
            if "category" in fields and fields["category"]:
                fields["category"] = []
                cred_cat_fixed += 1
    if cred_cat_fixed > 0:
        print(f"✅ Removed categories from {cred_cat_fixed} credentials")
        fixed_count += cred_cat_fixed

    # Fix task groupname references
    task_groupname_fixed = 0
    for item in data:
        if item.get("model") == "management.task":
            fields = item.get("fields", {})
            if "groupname" in fields:
                gname_val = fields["groupname"]
                if isinstance(gname_val, int) and gname_val != 1:
                    fields["groupname"] = 1
                    task_groupname_fixed += 1
                elif isinstance(gname_val, list) and len(gname_val) > 1:
                    gname_id = gname_val[1] if isinstance(gname_val[1], int) else None
                    if gname_id and gname_id != 1:
                        fields["groupname"] = 1
                        task_groupname_fixed += 1
            elif "groupname_id" in fields:
                if fields["groupname_id"] and fields["groupname_id"] != 1:
                    fields["groupname_id"] = 1
                    task_groupname_fixed += 1
    if task_groupname_fixed > 0:
        print(f"✅ Fixed {task_groupname_fixed} task groupname references")
        fixed_count += task_groupname_fixed

    return fixed_count


def fix_required_foreign_keys(data):
    """Fix None values and invalid foreign key references to non-exported users"""
    fixed_count = 0

    # Get target usernames and IDs (the 5 users we're exporting)
    target_usernames = ["coda_info", "eunice", "gndahiro", "ckarugu", "EDWINORWA"]
    target_user_ids = [74, 244, 36, 392, 495]

    # Get all exported users from the data
    exported_users = set()
    exported_user_ids = set()
    for item in data:
        if item.get("model") == "accounts.customeruser":
            fields = item.get("fields", {})
            username = fields.get("username")
            pk = item.get("pk")
            if username:
                exported_users.add(username)
            if pk:
                exported_user_ids.add(pk)

    # Common user foreign key field names
    user_fk_fields = [
        "requester",
        "created_by",
        "last_modified_by",
        "sender",
        "added_by",
        "approved_by",
        "rejected_by",
        "borrower",
        "user",
        "budget_lead",
        "current_approver",
        "assessor",
        "recorded_by",
        "purchased_by",
        "requested_by",
        "updated_by",
        "reporter",
        "author",
        "trainee_username",
        "client",
    ]

    for item in data:
        fields = item.get("fields", {})
        model = item.get("model", "")

        # Check ALL fields (not just hardcoded list) to catch all user references
        # BUT skip boolean fields - they're handled separately
        boolean_fields = [
            "is_active",
            "is_staff",
            "is_superuser",
            "is_admin",
            "email_verified",
            "is_featured",
            "laptop_status",
            "is_karen_country_club_member",
        ]

        for field_name, value in fields.items():
            # Skip boolean fields - they're handled in fix_boolean_none_values
            if field_name in boolean_fields:
                continue

            needs_fix = False
            replacement = None

            # Check if it's None/null (might be required)
            if value is None or value == "None" or value == "null":
                # Only fix if it's a known required field
                if field_name in [
                    "last_modified_by",
                    "requester",
                    "created_by",
                    "user",
                    "sender",
                ]:
                    needs_fix = True
                else:
                    continue  # Skip None values for optional fields

            # Check if it's a list (natural foreign key format) - could be user reference
            if isinstance(value, list) and len(value) > 0:
                # Handle different natural key formats:
                # 1. ['username'] - single username
                # 2. ['app.Model', 'pk'] - model and primary key
                # 3. ['app.Model', 'field', 'value'] - model, field, value
                if len(value) == 1 and isinstance(value[0], str):
                    # Single element - likely a username
                    username = value[0]
                    if username not in exported_users and username not in [
                        "accounts.customeruser",
                        "CustomerUser",
                    ]:
                        needs_fix = True
                elif len(value) >= 2 and isinstance(value[0], str):
                    # Check if it's a user model reference
                    if value[0] in ["accounts.customeruser", "CustomerUser"]:
                        username = value[1] if isinstance(value[1], str) else None
                        if username and username not in exported_users:
                            needs_fix = True
                    # For other models, we'd need to check against exported records
                    # For now, we'll focus on user references
                else:
                    # Check first element as potential username
                    username = value[0] if isinstance(value[0], str) else None
                    if (
                        username
                        and username not in exported_users
                        and username not in ["accounts.customeruser", "CustomerUser"]
                    ):
                        needs_fix = True

            # Check if it's an integer (direct foreign key)
            # BUT exclude boolean fields that might have 'user' in the name (like is_superuser)
            elif (
                isinstance(value, int)
                and field_name.endswith("_id")
                and field_name not in boolean_fields
            ):
                if value not in exported_user_ids:
                    needs_fix = True
            # Also check for user FK fields by name (but not boolean fields)
            elif (
                isinstance(value, int)
                and "user" in field_name.lower()
                and field_name not in boolean_fields
                and not field_name.endswith("_id")
            ):
                # This is tricky - could be a user FK or just a field with 'user' in the name
                # Only fix if it's a known user FK field
                known_user_fk_fields = [
                    "requester",
                    "created_by",
                    "last_modified_by",
                    "sender",
                    "added_by",
                    "approved_by",
                    "rejected_by",
                    "borrower",
                    "user",
                    "budget_lead",
                    "current_approver",
                    "assessor",
                    "recorded_by",
                    "purchased_by",
                    "requested_by",
                    "updated_by",
                    "reporter",
                    "author",
                    "trainee_username",
                    "client",
                    "empname",
                    "vendor_supplier",
                ]
                if (
                    field_name in known_user_fk_fields
                    and value not in exported_user_ids
                ):
                    needs_fix = True

            if needs_fix:
                # Try to find a replacement from other fields in the same record
                if "requester" in fields and fields["requester"]:
                    if (
                        isinstance(fields["requester"], list)
                        and len(fields["requester"]) > 0
                    ):
                        if fields["requester"][0] in exported_users:
                            replacement = fields["requester"]
                    elif (
                        isinstance(fields["requester"], int)
                        and fields["requester"] in exported_user_ids
                    ):
                        replacement = fields["requester"]

                if not replacement and "created_by" in fields and fields["created_by"]:
                    if (
                        isinstance(fields["created_by"], list)
                        and len(fields["created_by"]) > 0
                    ):
                        if fields["created_by"][0] in exported_users:
                            replacement = fields["created_by"]
                    elif (
                        isinstance(fields["created_by"], int)
                        and fields["created_by"] in exported_user_ids
                    ):
                        replacement = fields["created_by"]

                if not replacement and "user" in fields and fields["user"]:
                    if isinstance(fields["user"], list) and len(fields["user"]) > 0:
                        if fields["user"][0] in exported_users:
                            replacement = fields["user"]
                    elif (
                        isinstance(fields["user"], int)
                        and fields["user"] in exported_user_ids
                    ):
                        replacement = fields["user"]

                # Default to first target user
                if not replacement:
                    if isinstance(value, list):
                        replacement = [target_usernames[0]]
                    else:
                        replacement = target_user_ids[0]

                # Preserve the format (list vs int)
                if isinstance(value, list) and not isinstance(replacement, list):
                    replacement = (
                        [replacement] if isinstance(replacement, str) else replacement
                    )
                elif not isinstance(value, list) and isinstance(replacement, list):
                    replacement = (
                        replacement[0] if len(replacement) > 0 else target_user_ids[0]
                    )

                fields[field_name] = replacement
                fixed_count += 1

    return fixed_count


def main():
    input_file = Path("database_shares/limited_export.json")
    output_file = Path("database_shares/limited_export_fixed.json")

    # Check if compressed version exists
    if not input_file.exists():
        input_file = Path("database_shares/limited_export.json.gz")
        output_file = Path("database_shares/limited_export_fixed.json.gz")
        is_compressed = True
    else:
        is_compressed = False

    if not input_file.exists():
        print(f"❌ Error: {input_file} not found")
        print("\nAvailable files:")
        for f in Path("database_shares").glob("*.json*"):
            print(f"  {f}")
        sys.exit(1)

    print(f"📖 Reading {input_file}...")

    # Load data
    if is_compressed:
        with gzip.open(input_file, "rt") as f:
            data = json.load(f)
    else:
        with open(input_file) as f:
            data = json.load(f)

    print(f"✅ Loaded {len(data)} records")

    # Remove Django system models (created by migrations)
    print("\n🗑️  Removing Django system models...")
    system_models = ["contenttypes.contenttype", "auth.permission", "auth.group"]
    original_count = len(data)
    data = [item for item in data if item.get("model") not in system_models]
    removed = original_count - len(data)
    if removed > 0:
        print(f"✅ Removed {removed} Django system model records")

    # Remove accounts.UserGroups (depends on auth.Group)
    usergroups = [item for item in data if item.get("model") == "accounts.usergroups"]
    if usergroups:
        data = [item for item in data if item.get("model") != "accounts.usergroups"]
        print(f"✅ Removed {len(usergroups)} UserGroups records")

    # Fix boolean values
    print("\n🔧 Fixing None boolean values...")
    fixed_bools = fix_boolean_none_values(data)

    if fixed_bools > 0:
        print(f"✅ Fixed {fixed_bools} None boolean values")
    else:
        print("ℹ️  No None boolean values found")

    # Fix required foreign keys
    print("🔧 Fixing None required foreign keys...")
    fixed_fks = fix_required_foreign_keys(data)

    if fixed_fks > 0:
        print(f"✅ Fixed {fixed_fks} None required foreign keys")
    else:
        print("ℹ️  No None required foreign keys found")

    # Apply additional fixes
    print("\n🔧 Applying additional fixes...")
    additional_fixes = apply_additional_fixes(data)

    fixed_count = fixed_bools + fixed_fks + additional_fixes

    # Save fixed data
    print(f"💾 Saving to {output_file}...")

    if is_compressed:
        with gzip.open(output_file, "wt") as f:
            json.dump(data, f, indent=2)
    else:
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

    file_size = output_file.stat().st_size / (1024 * 1024)
    print(f"✅ Saved {len(data)} records to {output_file} ({file_size:.2f} MB)")
    print("")
    print("You can now load this file:")
    if is_compressed:
        print(f"  gunzip {output_file}")
        print(f"  python manage.py loaddata {output_file.with_suffix('')}")
    else:
        print(f"  python manage.py loaddata {output_file}")


if __name__ == "__main__":
    main()
