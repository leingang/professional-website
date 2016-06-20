from nikola.plugin_categories import ConfigPlugin
import logbook
from nikola import utils
LOGGER = utils.get_logger("coverimages", utils.STDERR_HANDLER)

import conf as config
import posixpath # for walking a unix-style directory tree
import micawber, micawber.exceptions # for extracting metadata from provided files

class AddCoverImages(ConfigPlugin):
    """Add site statistics to global context"""

    name = "coverimages"
    debug=False

    def set_site(self,site):
        site.scan_posts()
        if self.debug:
            for handler in LOGGER.handlers:
                handler.level=logbook.DEBUG
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
                    # TODO: set coverimage by tag
                    pass
            # LOGGER.debug("%s.coverimage = %s" %(post.meta('slug'),post.meta[post.default_lang]['coverimage']))
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
