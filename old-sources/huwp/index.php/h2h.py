#!/opt/local/bin/python2.7

import datetime
import logging
from lxml import etree
import sys
import re

import codecs
import locale

# Wrap sys.stdout into a StreamWriter to allow writing unicode.
# See http://stackoverflow.com/a/4546129/297797
sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

infilename = sys.argv[1]
infile = open(infilename,'r+')
inhtml = etree.HTML(infile.read())

logging.basicConfig(level=logging.DEBUG)

def fix_tag(tag):
    tag=tag.lower().strip()
    return tag


def remove_xpath(tree,xpath):
    logging.debug("removing xpath: %s",xpath)
    for elt in tree.xpath(xpath):
        elt.getparent().remove(elt)
    return tree

def serialize_metadata(md):
    lines = []
    lines.append(u'<!--')
    for key in ['title','slug','date','tags','category','categories']:
        lines.append(u'.. %s: %s' % (key,md[key]))
    lines.append(u'-->')
    lines.append(u'')
    return u'\n'.join(lines)

metadata={}
metadata['_categories'] = []
metadata['_tags'] = []

# scrape story date
for h1 in inhtml.xpath('//h1[@class="storydate"]'):
    storydatestr = h1.text
    (m,d,y) = storydatestr.split('.')
    metadata['_date'] = datetime.date(2000+int(y),int(m),int(d))
    logging.debug("_date: %s",metadata['_date'])

# scrape story time and build date
for byline in inhtml.xpath('(//a[@rel="category tag"])[last()]/following-sibling::node()'):
    match=re.search("at ((\d+):(\d+) (am|pm))",byline)
    logging.debug("match: %s",match.group(1))
    metadata['_time'] = datetime.datetime.strptime(match.group(1),"%I:%M %p").timetz()
    logging.info("_time: %s",metadata['_time'])

# scrape slug and title
for file in inhtml.xpath('//h2[@class="storytitle"]/a/attribute::href'):
    metadata['slug'] = file.replace('.html','')
    metadata['title'] = file.getparent().text
    logging.debug('title: %s',metadata['title'])

# scrape categories
for category in inhtml.xpath('//a[@rel="category tag"]/text()'):
    metadata['_categories'].append(category)
logging.info("_categories: %s",metadata['_categories'])

# scrape tags
for tag in inhtml.xpath('//a[@rel="tag"]/text()'):
    metadata['_tags'].append(tag)
logging.info("_tags: %s",metadata['_tags'])


# munge date
metadata['date'] = datetime.datetime.combine(metadata['_date'],metadata['_time'])
# munge categories
metadata['_categories'] = map(fix_tag,metadata['_categories'])
metadata['category'] = metadata['_categories'][0]
metadata['categories'] = ",".join(metadata['_categories'])
# munge tags
metadata['_tags'].append('harvard')
metadata['_tags'] = map(fix_tag,metadata['_tags'])
# remove a tag that's similar to another
# see http://stackoverflow.com/a/4915964/297797 for idiom
try:
    metadata['_tags'].remove('del.icio.us')
except ValueError:
    pass # or scream: thing not in some_list!
except AttributeError:
    pass # call security, some_list not quacking like a list!
metadata['tags'] = ','.join(metadata['_tags'])

for img in inhtml.xpath('//img[starts-with(@src,"http://www.texify.com/img")]'):
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
    if not('mathjax' in metadata['tags']):
        metadata['tags'] += ",mathjax"


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
    remove_xpath(inhtml,xpath)

# resolve links to other posts
for a in inhtml.xpath('//a[starts-with(@href,"http://www.math.harvard.edu/~leingang/")]'):
    url=a.attrib['href']
    logging.debug("url to fix: %s", url)
    newurl=re.sub("http://www.math.harvard.edu/~leingang/\d{4}/\d{2}/\d{2}/(.*)/","/posts/\\1/",url)
    logging.debug("newurl %s", newurl)
    a.attrib['href'] = newurl

# resolve local img urls
for img in inhtml.xpath('//img[starts-with(@src,".")]'):
    path=img.attrib['src'].split('/')
    img.attrib['src'] = '/images/' + path[-1]


print(serialize_metadata(metadata))
print("""
<div class="alert alert-dismissible alert-warning"><button type="button" class="close" data-dismiss="alert">x</button>
    <h4>Cobwebs ahead</h4>
    <p>This post is from a now-defunct blog I wrote when I was Preceptor in Mathematics at Harvard University.  Links may be dead, references may be dated, and comments were deleted.</p>
</div>
""")
for elt in inhtml.xpath('//div[@class="post"]/*'):
    print(etree.tostring(elt,pretty_print=True))
    pass
