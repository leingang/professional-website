from nikola.plugin_categories import ConfigPlugin
import logbook
from nikola import utils
LOGGER = utils.get_logger("recent_posts", utils.STDERR_HANDLER)


class SiteStats(ConfigPlugin):
    """Add site statistics to global context"""

    name = "recent_posts"
    debug = False

    def set_site(self, site):
        site.scan_posts()
        if self.debug:
            for handler in LOGGER.handlers:
                handler.level = logbook.DEBUG
        self.recent_posts = site.posts[:3]
        site.GLOBAL_CONTEXT['recent_posts'] = self.recent_posts
        super(SiteStats, self).set_site(site)
