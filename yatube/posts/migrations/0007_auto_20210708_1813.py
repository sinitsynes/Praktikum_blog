# Generated by Django 2.2.6 on 2021-07-08 18:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_auto_20210706_1412'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ('-created',), 'verbose_name': 'Комментарий', 'verbose_name_plural': 'Комментарии'},
        ),
    ]
