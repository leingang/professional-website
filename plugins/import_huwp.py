"""Import the static HTML dump of my old HU WP site"""

# This block copied from import_wordpress.py
from __future__ import unicode_literals, print_function
import os
import re
import sys
import datetime
import glob
import io
import json
import requests
import logbook
from lxml import etree
from collections import defaultdict

try:
    from urlparse import urlparse
    from urllib import unquote
except ImportError:
    from urllib.parse import urlparse, unquote  # NOQA

try:
    import phpserialize
except ImportError:
    phpserialize = None  # NOQA

from nikola.plugin_categories import Command
from nikola import utils
from nikola.utils import req_missing, unicode_str
from nikola.plugins.basic_import import ImportMixin, links
from nikola.nikola import DEFAULT_TRANSLATIONS_PATTERN
from nikola.plugins.command.init import SAMPLE_CONF, prepare_config, format_default_translations_config

LOGGER = utils.get_logger('import_huwp', utils.STDERR_HANDLER)

class CommandImportHuwp(Command, ImportMixin):
    """Import the static HTML dump of my old HU WP site"""

    name = "import_huwp"
    needs_config = False
    doc_usage = "[options] source_directory"
    doc_purpose = "Import the static HTML dump of my old HU WP site"
    cmd_options = ImportMixin.cmd_options + [
        # {
        #     'name': 'exclude_drafts',
        #     'long': 'no-drafts',
        #     'short': 'd',
        #     'default': False,
        #     'type': bool,
        #     'help': "Don't import drafts",
        # },
        {
            'name' : 'import_technorati_tags',
            'long' : 'import-technorati-tags',
            'default' : True,
            'type' : bool,
            'help' : "Scrape files for Technorati tags and import as tags"
        },
        {
            'name' : 'strip_technorati',
            'long' : 'strip-technorati',
            'default' : True,
            'type' : bool,
            'help' : "Strip out HTML from Technorati"
        },
        {
            'name': 'one_file',
            'long': 'one-file',
            'default': True,
            'type': bool,
            'help': "Save imported posts in the more modern one-file format.",
        },
        {
            'name' : 'debug',
            'long' : 'debug',
            'default' : False,
            'type' : bool,
            'help' : 'print debugging messages'
        },
        {
            'name' : 'prefix',
            'long' : 'prefix',
            'type' : str,
            'default' : 'huwp',
            'help' : 'path between <output-folder>/posts/ and imported posts'
        }
    ]
    all_tags = set([])

    def _read_options(self,options={},args=[]):
        """Read command-line options."""
        self.source_directory = args.pop(0) if args else "old-sources/huwp"
        self.import_technorati_tags = options['import_technorati_tags']
        self.onefile = options['one_file']
        self.debug=options['debug']
        self.prefix=options['prefix']
        if args and ('output_folder' not in args or
                     options['output_folder'] == 'new_site'):
            options['output_folder'] = args.pop(0)
        else:
            options['output_folder'] = ''
        self.output_folder=options['output_folder']
        self.import_into_existing_site = False
        self.url_map = {}
        self.timezone = None
        self.import_technorati_tags = options['import_technorati_tags']

        if self.debug:
            for handler in LOGGER.handlers:
                handler.level=logbook.DEBUG

        return True

    def _execute(self, options={}, args=[]):
        """Import the static HTML dump of my old HU WP site"""
        if not args:
            print(self.help())
            return False
        # for debugging
        # print("options: %s" % options)
        # print("args: %s" % args)

        if not self._read_options(options, args):
            return False

        channel = self.get_channel(self.source_directory)
        self.import_posts(channel)

    def get_channel(self,source_directory):
        """Get the list of posts to import"""
        channel=[]
        channel.extend(glob.glob(os.path.join(source_directory,"index.php","*.html")))
        LOGGER.debug(channel)
        return channel

    def import_posts(self,channel):
        """Import a list of posts"""
        for post_file in channel:
            self.import_post(post_file)
        return True

    def _sanitize_category(self,cat):
        return cat.lower()

    @classmethod
    def _sanitize_tag(cls,tag):
        tag=tag.lower().strip()
        replacements={'del.icio.us' : 'delicious'}
        try:
            if replacements[tag]:
                tag=replacements[tag]
        except KeyError:
            pass
        return tag

    @classmethod
    def _adjust_category(cls,cat,slug):
        """ map old categories to new ones"""
        old_to_new = {
            "uncategorized" : "miscellaneous",
            "wordpress" : "computing/wordpress",
            "books" : "computing/php", # there's only one book review in this dump
            "php" : "computing/php",
            "courses" : "education/teaching",
            "latex" : "computing/tex",
            "math s-1ab" : "education/teaching/calculus",
            "math 1a, spring 2008" : "education/teaching/calculus-1",
            "math 21a, spring 2008" : "education/teaching/calculus-3",
            "math 20" : "education/teaching/math-20",
            "teacher training" : "education/teaching",
            "pop culture" : "leisure",
            "web" : "computing/web"
        }
        slug_to_cat ={
            "hooray-for-boston" : "computing/web",
            "what-the-heck-is-a-preceptor" : "education/teaching",
            "new-toys-department-i-nikon-coolpix-l10-on-clearance" : "miscellaneous",
            "a-funny-thing-happened-on-the-way-to-work" : "miscellaneous",
            "configuring-tex4ht-to-link-to-pdf" : "computing/tex",
            "ruminations-on-new-technologies-for-teaching" : "education/talks",
            "tuesday-reading-list-and-ditl" : "education/talks",
            "day-in-the-life-teaching-fellow-orientation-today" : "education/talks",
            "upcoming-msri-conference-on-teaching-teachers" : "education/talks",
            "ibl-courses-in-geometry-and-probability-for-high-school-teachers" : "education/talks",
            "upcoming-bok-center-talk-2" : "education/talks",
            "upcoming-tums-ii-talk" : "education/talks",
            "bok-center-recap" : "education/talks",
            "lesson-planning-talk" : "education/talks",
            "inside-higher-ed-advanced-yes-placement-no" : "education",
            "upcoming-bok-center-talk" : "education/talks",
            "the-freshman-experience" : "education",
            "game-theory-nfl-style" : "math",
            "can-you-own-an-integer" : "math",
            "habemus-presidentam" : "education/academia",
            "happy-spring-term" : "education/teaching",
            "hows-your-penmanship"  : "education",
            "harvard-studies-ways-to-promote-teaching" : "education/academia",
            "monday-reading-list" : "miscellaneous",
            "web-pedagogy-seminar-google-earth-continues-to-rock" : "education/talks",
            "to-friend-or-not-to-friend" : "education/teaching",
            "accepted" : "education/talks"
        }
        if slug in slug_to_cat.keys():
            return slug_to_cat[slug]
        try:
            return old_to_new[cat]
        except KeyError:
            return cat


    @staticmethod
    def _strip_xpath(tree,xpath):
        for elt in tree.xpath(xpath):
            elt.getparent().remove(elt)

    @staticmethod
    def _scrape_date(tree):
        for h1 in tree.xpath('//h1[@class="storydate"]'):
            datestr = h1.text
            (m,d,y) = datestr.split('.')
            date = datetime.date(2000+int(y),int(m),int(d))
            LOGGER.debug("date: {}".format(date))
        for byline in tree.xpath('(//a[@rel="category tag"])[last()]/following-sibling::node()'):
            match=re.search("at ((\d+):(\d+) (am|pm))",byline)
            time = datetime.datetime.strptime(match.group(1),"%I:%M %p").timetz()
            LOGGER.debug("time: {}".format(time))
        date = datetime.datetime.combine(date,time)
        LOGGER.debug("date: {}".format(date))
        return date

    @staticmethod
    def _scrape_title_and_slug(tree):
        for a in tree.xpath('//h2[@class="storytitle"]/a'):
            title = a.text
            slug,ext = os.path.splitext(os.path.basename(a.attrib['href']))
        LOGGER.debug("title: {}".format(title))
        LOGGER.debug("slug: {}".format(slug))
        return title,slug

    def _scrape_tags(self,tree):
        tags=set([])
        for tag in tree.xpath('//a[@rel="tag"]/text()'):
            LOGGER.debug("tag: {}".format(tag))
            tags.add(self._sanitize_tag(tag))
        for img in tree.xpath('//img[starts-with(@src,"http://www.texify.com/img")]'):
            tags.add('mathjax')
        LOGGER.debug("tags: {}".format(tags))
        return tags

    def _scrape_categories(self,tree):
        categories=[]
        for cat in tree.xpath('//a[@rel="category tag"]/text()'):
            categories.append(self._sanitize_tag(cat))
        if categories is None:
            categories.append("uncategorized")
        LOGGER.debug("catgeories: {}".format(categories))
        return categories

    def _scrape_content(self,tree):
        content=tree.find('.//div[@class="post"]/')

        # strip out some stuff
        technorati_xpath = '//a[starts-with(@href,"http://technorati.com/tag")]/parent::p'
        for xpath in [
            '//h1[@class="storydate"]',
            '//a[@rel="category tag"]/parent::node()',
            '//p[@class="feedback"]',
            '//a[@href="http://www.flock.com/blogged-with-flock"]/parent::node()',
            '//h2[@class="storytitle"]',
            technorati_xpath + '/preceding-sibling::p[1]',
            technorati_xpath + '/following-sibling::p[1]',
            technorati_xpath
        ]:
            self._strip_xpath(content,xpath)

        # resolve links to other posts
        for a in tree.xpath('//a[starts-with(@href,"http://www.math.harvard.edu/~leingang/")]'):
            url=a.attrib['href']
            LOGGER.debug("url to fix: %s", url)
            newurl=re.sub("http://www.math.harvard.edu/~leingang/\d{4}/\d{2}/\d{2}/(.*)/","/posts/\\1/",url)
            LOGGER.debug("newurl %s", newurl)
            a.attrib['href'] = newurl

        # resolve local img urls
        # could be os.path'ified, but works for now
        for img in tree.xpath('//img[starts-with(@src,".")]'):
            img.attrib['src'] = '/images/' + os.path.basename(img.attrib['src'])


        for a in  tree.xpath('//a[starts-with(@href,".")]'):
            # regexp match on file name
            href= a.attrib['href']
            basename = os.path.basename(href)
            replacements={
                "../2005/09/13/LessonPlanning/index.html":"http://www.slideshare.net/leingang/making-lesson-plans"
            }
            try:
                a.attrib['href'] = replacements[href]
            except KeyError:
                if (href != "../2005/09/13/LessonPlanning/index.html"):
                    if re.search('\.(jpg|png|gif)$',basename):
                        prefix='images'
                    else:
                        prefix='files'
                    a.attrib['href'] = '/{}/{}'.format(prefix,basename)

        # rewrite texify links as MathJax
        for img in tree.xpath('//img[starts-with(@src,"http://www.texify.com/img")]'):
            tex = img.attrib['alt']
            try:
                if img.attrib['align'] == 'middle':
                    text = '\\[' + tex + '\\]'
                else:
                    text = '\\(' + tex + '\\)'
            except KeyError:
                text = '\\(' + tex + '\\)'
            newtext = text + img.tail if img.tail else text
            parent = img.getparent()
            if parent is not None:
                previous = img.getprevious()
                if previous is not None:
                    previous.tail = (previous.tail or '') + newtext
                else:
                    parent.text = (parent.text or '') + newtext
                parent.remove(img)

        # serialize everything below <div class="post">
        content_lines=[]
        for elt in content.xpath('//div[@class="post"]/*'):
            content_lines.append(etree.tostring(elt,pretty_print=True))
        # LOGGER.debug("content: {}".format(b''.join(content_lines)))
        return b''.join(content_lines)
        # content.attrib['class'] = 'imported_huwp_post'
        # return etree.tostring(content,pretty_print=True)



    def import_post(self,post_file_name):
        """Import a single post"""
        LOGGER.debug("importing {}".format(post_file_name))
        post_file_handle=open(post_file_name,'r+')
        post=etree.HTML(post_file_handle.read())
        date=self._scrape_date(post)
        title,slug = self._scrape_title_and_slug(post)
        tags=self._scrape_tags(post)
        tags.add('harvard')
        categories=self._scrape_categories(post)
        category=self._adjust_category(categories[0],slug)
        tags = tags.union(categories)

        alert=b"""
            <div class="alert alert-warning alert-dismissible" role="alert">
                <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                <strong>Warning: Cobwebs ahead</strong>
                This post is imported from an old WordPress blog I maintained
                when I was <a class="alert-link" href="link://slug/what-the-heck-is-a-preceptor">Preceptor in Mathematics</a>
                at <a class="alert-link" href="http://math.harvard.edu/">Harvard University</a>.
                Some links are dead, references are dated, and comments were deleted.
            </div>"""
        content=alert + self._scrape_content(post)

        meta={
            'title' : title,
            'date' : date.isoformat(),
            'slug' : slug,
            'category' : category,
            'tags' : ','.join(tags),
            'categories' : ','.join(categories)
        }
        LOGGER.debug("meta: {}".format(meta))

        out_content_filename = slug + ".html"
        out_path = os.path.join(self.output_folder,"posts",self.prefix,out_content_filename)

        plugin_info = self.site.plugin_manager.getPluginByName('html', 'PageCompiler')
        rewrite_html=False # otherwise error
        if self.onefile:
            LOGGER.debug("Writing '{}' to {} ".format(title,out_path))
            self.write_post(
                out_path,
                content,
                meta,
                plugin_info.plugin_object,
                rewrite_html)
        else:
            raise NotImplementedError("two file writing not implemented yet!")
