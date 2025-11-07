from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("investing", "0015_remove_legacy_models"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="optionsposition",
            index=models.Index(
                fields=["managed_account", "-entry_date"],
                name="optionspos_managed_entry_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="suggestedposition",
            index=models.Index(
                fields=["review_status", "-ai_score"],
                name="suggested_rev_ai_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="suggestedposition",
            index=models.Index(
                fields=["symbol", "review_status"],
                name="suggested_symbol_review_idx",
            ),
        ),
    ]

