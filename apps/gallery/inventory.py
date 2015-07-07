import os
from datetime import datetime
from PIL import Image as PILImage
import exifread
from apps.gallery.models import Album, Image, ImagePlacementInAlbum
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


GALLERY_ROOT = '%s/gallery-holder' % settings.PROJECT_ROOT
THUMBNAIL_WIDTH = 125


def gather_albums_and_images(gallery_dir):
    '''
    Walk through gallery_dir, record each subdirectory as an Album,
    with each file in it as an Image in that Album.
    '''
    for counter, (subdir, dirs, image_files) in enumerate(os.walk(gallery_dir)):

        # Ignore root directory; we only want subdirectories.
        if subdir == gallery_dir:
            continue

        # Get or create the album corresponding to this dir.
        album_slug = subdir.split('/')[-1]
        album, album_created = Album.objects.get_or_create(slug=album_slug)
        container = album.container
        os.mkdir("%s/%s" % (subdir, "temp_image_resizing"))

        # Make picture objects for each file
        for filename in image_files:
            full_path = "%s/%s" % (subdir, filename)

            try:
                Image.objects.get(filename=filename)
                logger.info("We already have a file called %s" % filename)

                # We can do any update logic here.
                continue

            except Image.DoesNotExist:
                logger.info("%s is a new file.  Creating Image object." % filename)

                with open(full_path) as f:
                    exif_tags = exifread.process_file(
                        f,
                        details=False,
                        stop_tag='EXIF DateTimeOriginal')

                    picture_taken_tag = exif_tags.get('EXIF DateTimeOriginal', None)

                    if picture_taken_tag:
                        picture_taken_unicode = picture_taken_tag.values
                        picture_taken_datetime = datetime.strptime(picture_taken_unicode + 'UTC', '%Y:%m:%d %H:%M:%S%Z')
                        logger.info("Picture taken at %s" % picture_taken_unicode)

                    else:
                        # We didn't glean an EXIF tag for the datetime, so None.
                        picture_taken_datetime = None

                image = Image.objects.create(
                    filename=filename,
                    datetime_taken=picture_taken_datetime,
                )

                ImagePlacementInAlbum.objects.create(
                    image=image,
                    album=album,
                    order=counter,
                )
                # Create gallery size and thumb-size files.
                im = PILImage.open(full_path)

                show_filename = os.path.splitext(filename)[0] + "-show"
                show_full_path = "%s/temp_image_resizing/%s" % (subdir, show_filename)
                show = im.copy()
                height = im.size[1] / ((im.size[0] / 1600) or 1)
                show.thumbnail((1600, height), PILImage.ANTIALIAS)
                show.save(show_full_path, "JPEG")

                thumb_filename = os.path.splitext(filename)[0] + "-thumb"
                thumb_full_path = "%s/temp_image_resizing/%s" % (subdir, thumb_filename)
                thumb = im.copy()
                height = im.size[1] / ((im.size[0] / 1600) or 1)
                thumb.thumbnail((150, height), PILImage.ANTIALIAS)
                thumb.save(thumb_full_path, "JPEG")

                image.rack('full', full_path, container, im.format)
                image.rack('show', show_full_path, container, im.format)
                image.rack('thumb', thumb_full_path, container, im.format)

                logger.info("Finished gathering %s.  Removing temp files." % filename)
                os.remove(show_full_path)
                os.remove(thumb_full_path)

        os.rmdir("%s/%s" % (subdir, "temp_image_resizing"))


if __name__ == "__main__":
    gather_albums_and_images(GALLERY_ROOT)