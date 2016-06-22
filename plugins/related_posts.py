from nikola.plugin_categories import ConfigPlugin
import logbook
from nikola.utils import STDERR_HANDLER
import logging
import copy

_debug = True # for testing
_name = "related_posts"

handler = copy.copy(STDERR_HANDLER[0])
handler.level=logbook.INFO if not _debug else logbook.DEBUG
handler.filter = lambda r,h: r.channel == _name
logger=logbook.Logger(_name,logbook.DEBUG if _debug else logbook.WARNING)
handler.push_application()

class RelatedPosts(ConfigPlugin):
    """insert related posts into each post's metadata"""
    name = _name

    def set_site(self,site):
        site.scan_posts()
        logger.debug("Hello")
        super(RelatedPosts,self).set_site(site)
