# Generated by Django 2.2.16 on 2022-11-21 19:22

from django.db import migrations, models
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_auto_20221121_1922'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='user_not_author',
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.CheckConstraint(check=models.Q(_negated=True, user=django.db.models.expressions.F('author')), name='user_not_author'),
        ),
    ]