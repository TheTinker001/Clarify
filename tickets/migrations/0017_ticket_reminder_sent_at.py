from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0016_merge_20260303_1236"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="reminder_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
