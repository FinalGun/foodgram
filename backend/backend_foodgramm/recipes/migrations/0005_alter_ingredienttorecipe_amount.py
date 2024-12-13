# Generated by Django 3.2 on 2024-12-12 07:40

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_auto_20241212_1221'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredienttorecipe',
            name='amount',
            field=models.FloatField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Количество ингредиентов'),
        ),
    ]
