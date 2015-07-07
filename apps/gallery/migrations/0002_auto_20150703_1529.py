# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imageplacementinalbum',
            name='album',
            field=models.ForeignKey(related_name='placements', to='gallery.Album'),
            preserve_default=True,
        ),
    ]
