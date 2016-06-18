from nikola.plugin_categories import ConfigPlugin
import logbook
from nikola import utils
LOGGER = utils.get_logger("coverimages", utils.STDERR_HANDLER)

import conf as config
import posixpath # for walking a unix-style directory tree

class AddCoverImages(ConfigPlugin):
    """Add site statistics to global context"""

    name = "coverimages"
    debug=True

    def set_site(self,site):
        site.scan_posts()
        if self.debug:
            for handler in LOGGER.handlers:
                handler.level=logbook.DEBUG
        self.category_cover_images = config.CATEGORY_COVER_IMAGES
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
            # LOGGER.debug("%s.coverimage = %s" %(post.meta('slug'),post.meta[post.default_lang]['coverimage']))
        site.GLOBAL_CONTEXT['category_cover_images'] = self.category_cover_images
        site.GLOBAL_CONTEXT['tag_cover_images'] = config.TAG_COVER_IMAGES
        super(AddCoverImages,self).set_site(site)
