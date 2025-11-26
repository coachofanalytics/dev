from django.db import migrations


class Migration(migrations.Migration):
    """
    Merge migration to reconcile parallel branches:
    - 0006_scholarship_trainingcourse
    - 0008_scholarship_amount
    """

    dependencies = [
        ("main", "0006_scholarship_trainingcourse"),
        ("main", "0008_scholarship_amount"),
    ]

    operations = [
        # No database operations are needed; this migration just
        # collapses the divergent branches in the migration graph.
    ]


