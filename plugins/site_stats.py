from nikola.plugin_categories import ConfigPlugin
import logbook
from nikola import utils
LOGGER = utils.get_logger("site_stats", utils.STDERR_HANDLER)


class SiteStats(ConfigPlugin):
    """Add site statistics to global context"""

    name = "site_stats"
    debug = False

    def set_site(self, site):
        site.scan_posts()
        if self.debug:
            for handler in LOGGER.handlers:
                handler.level = logbook.DEBUG
        self.set_post_count(site)
        self.set_category_count(site)
        self.set_tag_count(site)
        super(SiteStats, self).set_site(site)

    def set_post_count(self, site):
        post_count = len(site.posts)
        LOGGER.debug('post_count: %s' % post_count)
        site.GLOBAL_CONTEXT['post_count'] = post_count

    def set_tag_count(self, site):
        tag_count = len(site.posts_per_tag)
        LOGGER.debug('tag_count: %s' % tag_count)
        site.GLOBAL_CONTEXT['tag_count'] = tag_count

    def set_category_count(self, site):
        category_count = len(site.posts_per_category)
        LOGGER.debug('category_count: %s' % category_count)
        site.GLOBAL_CONTEXT['category_count'] = category_count

    def set_top_tags(self, site):
        threshold = 2
        tag_counts = [(len(site.posts_per_tag[tag]), tag)
                      for tag in site.posts_per_tag.keys()]
        # this should sort reverse numerical on count, then alpha on tag
        tag_counts.sort(key=lambda e: (-e[0], e[1]))
        LOGGER.debug('tag_counts: %s' % tag_counts)
        top_tags = [tag for count, tag in tag_counts if count > threshold]
        LOGGER.debug('top_tags: %s' % top_tags)
        site.GLOBAL_CONTEXT['top_tags'] = top_tags
