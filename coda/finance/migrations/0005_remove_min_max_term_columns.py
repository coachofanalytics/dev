from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0004_add_employee_bonus_fields'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE finance_loanproduct
                DROP COLUMN IF EXISTS min_term_months;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                ALTER TABLE finance_loanproduct
                DROP COLUMN IF EXISTS max_term_months;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]


