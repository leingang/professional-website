from nikola.plugin_categories import ConfigPlugin
from nikola import utils
import conf as config
from string import capwords

import logbook
import logging
import copy

_debug = True # for testing
_name = "category_menu"

handler = copy.copy(utils.STDERR_HANDLER[0])
handler.level=logbook.INFO if not _debug else logbook.DEBUG
handler.filter = lambda r,h: r.channel == _name
logger=logbook.Logger(_name,logbook.DEBUG if _debug else logbook.WARNING)
handler.push_application()



class CategoryMenu(ConfigPlugin):
    """Add category menu to global context"""

    name = "category_menu"

    def set_site(self,site):
        site.scan_posts()
        # count posts in each category
        cat_count={}
        for cat,posts in site.posts_per_category.items():
            cat_count[cat] = len(posts)

        # this list of tuples has fields like so:
        # * "base name" of category
        # * "full name" of category (as a '/'-joined path)
        # * "path list" of category (list of branches)
        # * link to category index page
        # * count of posts in this category
        cat_hierarchy = [(node.name, node.category_name, node.category_path,
                            site.link("category", node.category_name),
                            cat_count[node.category_name])
                        for node in site.category_hierarchy]
        # dict for consolidating post count by top level category
        tlcats={}
        category_title={}
        for lang in site.config['NAVIGATION_LINKS'].values:
            for basename,fullname,pathlist,link,count in cat_hierarchy:
                # aggregate top level category counts
                tlname=pathlist[0]
                if (basename==tlname):
                    # top level
                    tlcats[tlname] = {'basename':basename,'link':link,'count':count}
                else:
                    tlfoo,tllink,tlcount = tlcats[tlname]
                    tlcats[tlname]['count'] += count
                # evaluate category titles
                try:
                    category_title[basename] = config.CATEGORY_TITLES[basename]
                except KeyError:
                    if basename.isupper():
                        category_title[basename] = basename
                    else:
                        category_title[basename] = capwords(basename)
                # populate CATEGORY_PAGES_TITLES
                # FIXME doesn't make its way to category page title.
                # I think it's a bug.  for now, we'll key on the basename AND the fullname,
                # in case the bug gets fixed.
                if basename not in config.CATEGORY_PAGES_TITLES[lang]:
                    site.config['CATEGORY_PAGES_TITLES'][lang][basename] = "Posts about %s" % category_title[basename]
                site.config['CATEGORY_PAGES_TITLES'][lang][fullname] = site.config['CATEGORY_PAGES_TITLES'][lang][basename]
        # decorated list for sorting
        tlcatlist=[
            (e['link'],e['count'],category_title[e['basename']]) for e in tlcats.values()
        ]
        tlcatlist.sort(key=lambda e: int(e[1]),reverse=True)
        logger.debug("tlcatlist: %s" % tlcatlist)
        site.GLOBAL_CONTEXT['category_menu'] = tlcatlist
        logger.debug("category_title: %s" % category_title)
        site.GLOBAL_CONTEXT['category_title'] = category_title
        logger.debug("CATEGORY_PAGES_TITLES: %s" % site.config['CATEGORY_PAGES_TITLES'])
        super(CategoryMenu,self).set_site(site)
