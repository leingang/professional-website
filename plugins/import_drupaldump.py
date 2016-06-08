"""Import the static HTML dump of my old drupal site"""
# This block copied from import_wordpress.py
from __future__ import unicode_literals, print_function
import os
import re
import sys
import datetime
import glob
import io
import json
import logbook
import requests
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

LOGGER = utils.get_logger('import_drupaldump', utils.STDERR_HANDLER)

class CommandImportDrupalDump(Command, ImportMixin):
    """Import the static HTML dump of my old NYU Drupal site"""

    name = "import_drupaldump"
    needs_config = False
    doc_usage = "[options] source_directory"
    doc_purpose = "Import the static HTML dump of my old drupal site"
    # output_folder is in ImportMixin.cmd_options
    cmd_options = ImportMixin.cmd_options + [
        {
            'name' : 'import_tags',
            'long' : 'import-tags',
            'default' : True,
            'type' : bool,
            'help' : "Scrape files for tags and import as tags"
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
            'default' : 'drupal',
            'help' : 'path between <output-folder>/posts/ and imported posts'
        }
    ]
    all_tags = set([])

    def _read_options(self,options={},args=[]):
        """Read command-line options."""
        self.source_directory = args.pop(0) if args else "old-sources/drupal"
        self.import_tags = options['import_tags']
        self.onefile = options['one_file']
        self.debug=options['debug']
        self.prefix=options['prefix']
        if args and ('output_folder' not in args or
                     options['output_folder'] == 'new_site'):
            options['output_folder'] = args.pop(0)
        else:
            options['output_folder'] = ''
        self.output_folder=options['output_folder']

        if self.debug:
            for handler in LOGGER.handlers:
                handler.level=logbook.DEBUG

        return True


    def _execute(self, options={}, args=[]):
        """Import the static HTML dump of my old drupal site"""
        if not args:
            print(self.help())
            return False
        print("options: %s" % options)
        print("args: %s" % args)

        if not self._read_options(options, args):
            return False

        channel = self.get_channel(self.source_directory)
        self.import_posts(channel)

    def get_channel(self,source_directory):
        """Get the list of posts to import"""
        channel=[]
        channel.extend(glob.glob(os.path.join(source_directory,"content","*.html")))
        channel.extend(glob.glob(os.path.join(source_directory,"node","*.html")))
        # print(channel)
        return channel

    def import_posts(self,channel):
        """Import a list of posts"""
        for post_file in channel:
            self.import_post(post_file)
        return True

    def _sanitize_category(self,cat):
        return cat.lower()

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
            "are-we-still-here" : "math/science",
            "tooting-my-own-horn" : "education/teaching",
            "back-again" : "computing/blog",
        }
        if slug in slug_to_cat.keys():
            return slug_to_cat[slug]
        try:
            return old_to_new[cat]
        except KeyError:
            return cat

    def import_post(self,post_file_name):
        """Import a single post"""
        # print("Importing {}".format(post_file))
        post_file_handle = open(post_file_name,'r+')
        post = etree.HTML(post_file_handle.read())

        # date
        date_string = post.findtext('.//div[@class="date"]')
        LOGGER.debug("date_string: %s" % date_string)
        if date_string is None:
            LOGGER.warn("skipping {} since it seems to not be a post".format(post_file_name))
            return
        date = datetime.datetime.strptime(date_string, "%A, %B %d, %Y - %I:%M%p")
        LOGGER.debug("date: %s" % date)

        # title comes from an h1 element.
        # oddly, there are two <h1 class="bar"> elements, but only the second
        # has the real title.
        title=post.findtext('.//h1[@class="bar"][2]')
        LOGGER.debug("title: %s" % title)

        # slug comes from the file name
        post_file_basename = os.path.basename(post_file_name)
        slug, ext = os.path.splitext(post_file_basename)
        LOGGER.debug("slug: %s" % slug)

        # tags
        tags = set([])
        for tag_link in post.xpath('//a[@rel="tag" and starts-with(@href,"../category/tags")]'):
            tags.add(tag_link.text)
        LOGGER.debug("tags: %s" % tags)

        # category
        # right now we just choose the first category
        # demote the rest to tags?
        categories=[]
        for category in post.xpath('//a[@rel="tag" and starts-with(@href,"../category/categories")]/text()'):
            categories.append(self._sanitize_category(category))
        LOGGER.debug("categories: %s" % categories)
        if not categories:
            categories.append("uncategorized")
        category=categories.pop(0)
        category = self._adjust_category(category,slug)
        LOGGER.debug("category: %s" % category)

        # content!
        content_tree = post.xpath('//div[starts-with(@id,"node-")]').pop(0)
        # remove metadata and window dressing
        for xpath in [
            '//div[@class="author"]',
            '//div[@class="terms"]',
            '//div[@class="links"]',
            '//div[@class="date"]',
        ]:
            for elt in post.xpath(xpath):
                elt.getparent().remove(elt)
        # fix tag links
        # TODO: make this away of the PRETTY_URLS setting
        for a in content_tree.xpath('//a[starts-with(@href,"../category/tags/")]'):
            href=a.attrib['href']
            href_tail = href.split('/').pop(-1)
            tag,ext = os.path.splitext(href_tail)
            a.attrib['href'] = "/categories/{}/".format(tag)

        # fix one post that refers to another post
        for a in content_tree.xpath('//a[@href="back.html"]'):
            a.attrib['href'] = '/posts/back'


        content_lines=[]
        for elt in content_tree:
            content_lines.append(etree.tostring(elt,pretty_print=True))
        alert=b"""
            <div class="alert alert-warning alert-dismissible" role="alert">
                <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                <strong>Warning: Cobwebs ahead</strong>
                This post is imported from an old drupal site I maintained at the
                <a href="http://www.cims.nyu.edu/" class="alert-link">Courant Institute</a>.
                Some links are dead, references are dated, and comments were deleted.
            </div>"""
        content = alert + b''.join(content_lines)
        # LOGGER.debug("content %s" % content) # warning: very verbose!

        out_content_filename = slug + ".html"
        out_path = os.path.join(self.output_folder,"posts",self.prefix,out_content_filename)
        meta={
            'title' : title,
            'date' : date,
            'slug' : slug,
            'category' : category,
            'tags' : ','.join(tags)
        }
        plugin_info = self.site.plugin_manager.getPluginByName('html', 'PageCompiler')
        rewrite_html=True # why not?

        LOGGER.debug("Writing '{}' to {} ".format(title,out_path))
        if self.onefile:
            self.write_post(
                out_path,
                content,
                meta,
                plugin_info.plugin_object,
                rewrite_html)
        else:
            raise NotImplementedError("two file writing not implemented yet!")
