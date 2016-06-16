from nikola.plugin_categories import ConfigPlugin
import logbook
from nikola import utils
LOGGER = utils.get_logger("tag_menu", utils.STDERR_HANDLER)

class TagMenu(ConfigPlugin):
    """Add top tags to global context"""

    name = "tag_menu"
    debug=False

    def set_site(self,site):
        site.scan_posts()
        if self.debug:
            for handler in LOGGER.handlers:
                handler.level=logbook.DEBUG
        self.set_top_tags(site)
        super(TagMenu,self).set_site(site)

    def set_top_tags(self,site):
        threshold = 2
        tag_counts = [(len(site.posts_per_tag[tag]),tag) for tag in site.posts_per_tag.keys()]
        # this should sort reverse numerical on count, then alpha on tag
        tag_counts.sort(key = lambda e: (-e[0],e[1]))
        LOGGER.debug('tag_counts: %s' % tag_counts)
        top_tags = [tag for count,tag in tag_counts if count > threshold]
        LOGGER.debug('top_tags: %s' % top_tags)
        site.GLOBAL_CONTEXT['top_tags'] = top_tags
