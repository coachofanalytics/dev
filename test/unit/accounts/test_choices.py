from accounts.choices import CategoryChoices, SubCategoryChoices


def test_category_choices_members():
    # Ensure the enum contains expected members
    names = [c.name for c in CategoryChoices]
    assert 'ORDINARY_MEMBER' in names
    assert 'ACTIVE_MEMBER' in names


def test_subcategory_choices_members():
    names = [c.name for c in SubCategoryChoices]
    assert 'NO_SELECTION' in names
    assert 'FULL_TIME' in names
