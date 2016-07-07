from nikola.plugin_categories import ConfigPlugin
import logbook
from nikola.utils import STDERR_HANDLER
import logging
import copy

from nltk import word_tokenize
from nltk.stem.snowball import SnowballStemmer
from more_itertools import unique_everseen
import numpy
import math

_debug = False # for testing
_name = "related_posts"

handler = copy.copy(STDERR_HANDLER[0])
handler.level=logbook.INFO if not _debug else logbook.DEBUG
handler.filter = lambda r,h: r.channel == _name
logger=logbook.Logger(_name,logbook.DEBUG if _debug else logbook.WARNING)
handler.push_application()

class RelatedPosts(ConfigPlugin):
    """insert related posts into each post's metadata"""
    name = _name

    stemmer_map = {
        'en' : 'english',
        'da' : 'danish',
        'nl' : 'dutch',
        'de' : 'german',
        'fi' : 'finnish',
        'fr' : 'french',
        'hu' : 'hungarian',
        'it' : 'italian',
        'no' : 'norwegian',
        'pt' : 'portuguese',
        'ro' : 'romanian',
        'ru' : 'russian',
        'es' : 'spanish',
        'sv' : 'swedish'
    }
    allwords=[]
    _tf = None
    _idf = None
    _tfidf = None
    _dc = None
    num_related = 3

    def set_site(self,site):
        site.scan_posts()
        logger.debug("Hello")
        self.set_related(site)
        super(RelatedPosts,self).set_site(site)

    def set_related(self,site):
        """ set the top related posts for each post"""
        logger.debug("set_related: begin")
        self.set_term_count(site)
        # take the top scores by column index
        # see http://stackoverflow.com/a/23734295/297797
        indices = numpy.argpartition(self.dc,-self.num_related)[:,-self.num_related:]
        logger.debug("indices: %s" % indices)
        logger.debug("top scores: %s" % self.dc[indices])
        # I would like to sort on score, but can't figure out how.
        # skipping for now.
        for i,post in enumerate(site.posts):
            try:
                lang = post.lang
            except AttributeError:
                lang = site.default_lang
            post.related = []
            for r in indices[i,:]:
                post.related.append(site.posts[r])
                logger.debug('%s.related+=(%d)%s' %(post.meta('slug'),r,site.posts[r].meta('slug')))

    def set_words(self,site):
        stemmers={}
        default_stemmer=SnowballStemmer(self.stemmer_map[site.default_lang])
        for post in site.posts:
            try:
                lang = post.lang
            except AttributeError:
                lang = site.default_lang
            try:
                stemmer=stemmers[lang]
            except KeyError:
                stemmers[lang] = SnowballStemmer(self.stemmer_map[lang])
                stemmer=stemmers[lang]
            words=[]
            fulltext = post.meta('title') + post.text(strip_html=True)
            for word in word_tokenize(fulltext):
                words.append(stemmer.stem(word))
            post.meta[lang]['words'] = words
            self.allwords.extend(words)
            # print(post.meta[lang]['words'])
        self.allwords = list(unique_everseen(self.allwords))
        # logger.debug("allwords: %s" % self.allwords)

    def set_term_count(self,site):
        """set the post-word count matrix

        set self.tc to be a matrix where

            self.tc[i,j] = # of times word j appears in post i
        """
        logger.debug("set_term_count: begin")
        if not self.allwords:
            self.set_words(site)
        result = numpy.zeros((len(site.posts),len(self.allwords)))
        # max is column vector of row maxima
        for i, post in enumerate(site.posts):
            for j, word in enumerate(self.allwords):
                result[i,j] = post.meta('words').count(word)
        logger.debug("set_term_count: %s" % result)
        self.tc = result
        return result

    @property
    def tf(self):
        """term frequency matrix

        return a matrix TF, where

            TF[i,j] = frequency of word j in post i
            (relative to the most frequent word in post i)
        """
        if self._tf is None:
            term_count = self.tc
            wordmax=numpy.amax(term_count,axis=1)
            # jekyll-related-posts.rb uses a weight vector.
            # skipping that for now.
            self._tf = term_count / wordmax[:,None]
            logger.debug("tf: %s" % self._tf)
        return self._tf

    @property
    def idf(self):
        """inverse document frequency matrix

        return a vector IDF, where

        IDF[j] = log((# of posts)/(1 + # of posts containing word j ))
        """
        if self._idf is None:
            tf = self.tf
            nposts,nwords = tf.shape
            term_incidence = numpy.ceil(tf)
            num_containing = numpy.sum(term_incidence,axis=0)
            self._idf = numpy.log(nposts/(1+num_containing))
            logger.debug("idf: %s" % self._idf)
        return self._idf

    @property
    def tfidf(self):
        """the tf-idf matrix

        tfidf[i,j] = TF[i,j] * IDF[j]
        """
        if self._tfidf is None:
            # compute it!
            self._tfidf = self.tf * self.idf[None,:]
            logger.debug("tfidf: %s" % self._tfidf)
        return self._tfidf

    @property
    def dc(self):
        """the document correlation matrix"""
        if self._dc is None:
            tfidf = self.tfidf
            result = numpy.dot(tfidf,numpy.transpose(tfidf))
            m,n = result.shape # should be square, but shape returns both
            # voodoo
            for i in range(1,m):
                for j in range (1,n):
                    if i != j:
                        result[i,j] /= (result[i,i] + result[j,j] - result[i,j])
                    else:
                        result[i,j] = 0.0
            self._dc = result
            numpy.savetxt("cache/dc.txt",result)
            logger.debug("dc: %s" % self._dc)
        return self._dc
