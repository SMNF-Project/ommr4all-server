# Generated by Django 2.2 on 2019-07-30 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0005_bookstyle'),
    ]

    operations = [
        migrations.CreateModel(
            name='GlobalPermissions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'permissions': [('add_book_style', 'Add book style'), ('delete_book_style', 'Delete book style'), ('edit_book_style', 'Edit book style'), ('change_default_model_for_book_style', 'Change default model for book style')],
            },
        ),
    ]
