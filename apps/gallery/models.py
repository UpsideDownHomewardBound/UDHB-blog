from django.db import models

import pyrax
import urllib
import urlparse

pyrax.set_setting("identity_type", "rackspace")
pyrax.set_default_region('IAD')
pyrax.set_credentials('ckaye89', '89677988dd861a029ac2f914c35d02ad')


class Image(models.Model):
    name = models.CharField(max_length=200)
    filename = models.CharField(max_length=200)
    date = models.DateTimeField(blank=True, null=True)

    full_url = models.CharField(max_length=200)
    show_url = models.CharField(max_length=200)
    thumb_url = models.CharField(max_length=200)

    def rack(self, size, file_path, container, format):
        with open(file_path) as f:
            cdn_obj = container.store_object("%s-%s" % (self.filename, size), f)
            cdn_obj.change_content_type("image/%s" % format)
            encoded_name = urllib.quote(cdn_obj.name)
            setattr(self,
                    "%s_url" % size,
                    urlparse.urljoin(container.cdn_uri, encoded_name)
                    )
            self.save()


class Album(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    slug = models.SlugField()

    def __unicode__(self):
        return self.name

    @property
    def container(self):
        try:
            return self.container_obj
        except AttributeError:
            pyrax.cloudfiles.create_container(self.name)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.slug.replace('-', ' ').capitalize()

        # This is effectively a get-or-create flow.
        self.container_obj = pyrax.cloudfiles.create_container(self.slug)
        self.container_obj.make_public()
        return super(Album, self).save(*args, **kwargs)


class ImagePlacementInAlbum(models.Model):
    image = models.ForeignKey(Image)
    album = models.ForeignKey(Album)
    caption = models.CharField(max_length=200)
    order = models.IntegerField()

    class Meta:
        unique_together = ('image', 'album', 'order')