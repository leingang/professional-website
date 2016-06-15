from nikola.plugin_categories import ConfigPlugin
import logbook
from nikola import utils
LOGGER = utils.get_logger("archive_menu", utils.STDERR_HANDLER)

debug=False

if debug:
    for handler in LOGGER.handlers:
        handler.level=logbook.DEBUG

class ArchiveMenu(ConfigPlugin):
    """Add category menu to global context"""

    name = "archive_menu"

    def set_site(self,site):
        LOGGER.debug("hello")
        site.scan_posts()
        # TODO: respect the config value on archiving.
        # I just want the year
        site.GLOBAL_CONTEXT['posts_per_year'] = sorted(site.posts_per_year,reverse=True)
        super(ArchiveMenu,self).set_site(site)
        LOGGER.debug("goodby")
