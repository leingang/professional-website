from nikola.plugin_categories import ConfigPlugin
import logbook
from nikola.utils import get_logger, STDERR_HANDLER
import logging
import copy

_debug = False # for testing
_name = "coverimages"

handler = copy.copy(STDERR_HANDLER[0])
handler.level=logbook.INFO if not _debug else logbook.DEBUG
handler.filter = lambda r,h: r.channel == _name
LOGGER=get_logger(_name,STDERR_HANDLER)
logger=logbook.Logger(_name,logbook.DEBUG if _debug else logbook.WARNING)
handler.push_application()


import conf as config
import posixpath # for walking a unix-style directory tree
import micawber, micawber.exceptions # for extracting metadata from provided files

class AddCoverImages(ConfigPlugin):
    """Add site statistics to global context"""

    name = "coverimages"

    def set_site(self,site):
        site.scan_posts()
        self.category_cover_images = config.CATEGORY_COVER_IMAGES
        self.tag_cover_images = config.TAG_COVER_IMAGES
        self.category_hierarchy = site.category_hierarchy
        for node in self.category_hierarchy:
            category = node.category_name
            # LOGGER.debug("category: %s" % category)
            ancestor = category
            while(ancestor != ""):
                # LOGGER.debug("ancestor: %s" % ancestor)
                try:
                    self.category_cover_images[category] = self.category_cover_images[ancestor]
                    break
                except KeyError:
                    ancestor = posixpath.dirname(ancestor)
        # LOGGER.debug(self.category_cover_images)
        for post in site.posts:
            # LOGGER.debug("%s.category = %s" %(post.meta('slug'),post.meta('category')))
            if post.meta('coverimage') is "":
                try:
                    post.meta[post.default_lang]['coverimage'] = self.category_cover_images[post.meta('category')]
                except KeyError:
                    pass
            if post.meta('coverimage') is "":
                logger.debug("tags: %s" % post.tags)
                try:
                    tag=([tag for tag in post.tags if tag in self.tag_cover_images and tag not in config.HIDDEN_TAGS])[0]
                    post.meta[post.default_lang]['coverimage'] = self.tag_cover_images[tag]
                except IndexError: # no tag cover image
                    pass
            logger.debug("%s.coverimage = %s" %(post.meta('slug'),post.meta[post.default_lang]['coverimage']))
        site.GLOBAL_CONTEXT['category_cover_images'] = self.category_cover_images
        site.GLOBAL_CONTEXT['tag_cover_images'] = self.tag_cover_images
        self.set_coverimage_metadata(site)
        super(AddCoverImages,self).set_site(site)

    def set_coverimage_metadata(self,site):
        """walk the posts' coverimages and insert metadata."""
        image_metadata={}
        providers = micawber.bootstrap_basic()
        for post in site.posts:
            try:
                img = post.meta('coverimage')
                if img[:2]=="//":
                    raise ValueError("No protocol-relative URLs allowed.  Please add 'https:'")
                if img in image_metadata:
                    next
                key = img+"#metadata"
                if site.cache.get(key) is None:
                    try:
                        metadata = providers.request(img)
                        site.cache.set(key,metadata)
                        image_metadata[img]=metadata
                    except micawber.exceptions.ProviderNotFoundException:
                        LOGGER.warn("Post {} seems to have no cover image".format(post.meta('slug')))
                else:
                    image_metadata[img]=site.cache.get(key)
            except:
                raise
        # LOGGER.debug('image_metadata: %s' % (image_metadata))
        site.GLOBAL_CONTEXT['image_metadata'] = image_metadata
