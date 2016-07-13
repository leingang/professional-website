.. title: Document correlation with Nikola, NLTK, and NumPy
.. slug: document-correlation-with-nikola-nltk-and-numpy
.. date: 2016-07-11 07:40:32 UTC-04:00
.. tags: nikola, python, linear algebra, mathjax
.. category: computing
.. link:
.. description: what I've learned in the last week implementing related posts in Nikola
.. type: text

One nice website feature is having a set of related posts to a given post.  That way
a reader can quickly browse from one article to something similar.  I wanted to
implement this feature on my Nikola blog in a smart way, but first I had to learn
something about the underlying math.

.. TEASER_END

One way to decide if two posts are related is to check their metadata.  If they
are in the same category, or share one or more tags, they are probably related
in some obvious  sense.  But humans (or at least this human) are pretty lazy
with tagging and categorizing. And within the same category or shared tags, some
posts will be “more” related than others.  So I wanted a fulltext match instead of
a metadata match.

In a blog with a relational database on the backend, finding posts related to a
given post by fulltext matching is a relatively straightforward process.  By
diving into a WordPress plugin called YARPP_, I discovered that the whole
process is window dressing for an SQL query using a `MATCH
<https://dev.mysql.com/doc/refman/5.5/en/fulltext-search.html>`__ keyword. The
indices and query can be tweaked, but the function is already there for the
using.

.. _YARPP: https://wordpress.org/plugins/yet-another-related-posts-plugin/

But Nikola's “database” is posts in flat files, so the matching needs to be done
by hand.  Luckily, this is a math problem.  A high-dimensional, linear algebra
problem, which makes it a good application for numerical computing.

Eventually I found a `related posts
<https://github.com/alfanick/jekyll-related-posts>`__ plugin for jekyll_. Jekyll
is a static site generator much like Nikola, but written in ruby.  In studying
the code for the jekyll plugin, I figured out the process.

.. _jekyll: https://jekyllrb.com

Document correlation
--------------------

Consider a corpus of documents (or posts) :math:`p_1, p_2, \dots, p_m`, written
using words :math:`w_1, w_2, \dots, w_n`. Then each post can be represented as a
vector in an an :math:`n`-dimensional vector space, whose :math:`j`-th component
is the number of times word :math:`j` appears in the post.   Two posts would be
represented by the same vector if one were a word-by-word rearrangement of the
other, which seems unlikely on a practical basis.  Posts that share a lot of
words should probably be considered related to each other.

Let :math:`\mathrm{tc}` be the :math:`m\times n` matrix  whose :math:`(i,j)`-th entry is
the number of times word :math:`j` appears in post :math:`i`.  The matrix
:math:`\mathrm{tc}` is called the **term count** matrix. To normalize slightly, let
:math:`\mathrm{tf}` be the matrix whose :math:`i`-th row is the :math:`i`-th row of
:math:`\mathrm{tc}` divided by the maximum entry in the row. This is called the **term
frequency** matrix.  Each row has entries between zero and one, and the closer
the entry is to one, the closer it is to being the most frequent word in the
post.

Of course, some words are going to appear frequently no matter what the post is
truly about.  Words like *the*, *a*, *of*, and so on.  More specifically, if
your blog is all about cars, it's not so significant if every document contains
the word *car.* So term frequency needs to be controlled by how often the words
appear in the corpus in general.  This is  where the notion of *inverse document
frequency* comes in.  We create a row vector :math:`\mathrm{idf}`, whose
:math:`j`-th component measures how many documents word :math:`j` appears in,
but inverted so that the more often it appears, the smaller the component is.
There are several ways to construct this measure. One popular formula is:

.. math::

    \mathrm{idf}_j = \frac{\#\left\{\text{posts}\right\}}{\log(1+\#\left\{\text{posts which contain word $j$}\right\})}

The **term frequency-inverse document frequency** matrix is the :math:`m \times
n` matrix whose :math:`(i,j)`-th entry is
:math:`\mathrm{tf}_{ij}\mathrm{idf}_j`.  In matrix terms, the :math:`i`-th row
of :math:`A` is the :math:`i`-th row of :math:`\mathrm{tf}` multiplied
componentwise by :math:`\mathrm{idf}`. Tf-idf ranks words highly if they appear
relatively frequently in a post and not so frequently in the set of all posts.

We'll declare two posts to be related if their rows in the tf-idf matrix are
close together in :math:`n`-dimensional space.  A good measure of closeness for
this discussion is the angle between the vectors.  The smaller the angle, the
closer the vectors. The cosine of the angle between two vectors can be computed
with the dot product:

.. math::

    \mathbf{v}\cdot\mathbf{w} = \sum_{i=1}^n v_i w_i

The law of cosines states that

.. math::

    \mathbf{v}\cdot\mathbf{w} = ||\mathbf{v}|| || \mathbf{w} || \cos(\theta)

where :math:`\theta` is the angle between the vectors.  Therefore

.. math::

     \cos(\theta) = \frac{\mathbf{v}\cdot\mathbf{w}}{||\mathbf{v}|| || \mathbf{w} ||}

The rows of the tf-idf matrix (which I'm going to call :math:`A`) are the
vectors we want to measure the angles between.  This can be done in one fell
swoop with matrix operations. Let the rows of :math:`A` be called
:math:`\mathbf{a}_1,\dots,\mathbf{a}_n`.  Let :math:`B` be the the matrix whose
:math:`(i,j)`-th entry is the cosine of the angle between :math:`\mathbf{a}_i`
and :math:`\mathbf{a}_j`.  We know

.. math::

    b_{ij} = \frac{\mathbf{a}_i \cdot \mathbf{a}_j}{||\mathbf{a}_i|| ||\mathbf{a}_j||}

Let :math:`A^T` be the transpose of :math:`A`. Then :math:`AA^T` is the :math:`m
\times m` matrix whose :math:`(i,j)`-th entry is the dot product of
:math:`\mathbf{a}_i` and :math:`\mathbf{a}_j`. This is because

.. math::

    (AA^T)_{ij} = \sum_{k=1}^n (A)_{ik}(A^T)_{kj} = \sum_{k=1}^n a_{ik}a_{jk}

This matrix is symmetric, and its diagonal entries are the dot products of each row with itself.
That is, :math:`(AA^T)_{ii} = \mathbf{a}_i \cdot \mathbf{a}_i = ||\mathbf{a}_i||^2`.

If :math:`B` is the matrix whose :math:`(i,j)`-th entry is the cosine of the
angle between :math:`\mathbf{a}_i` and :math:`\mathbf{a}_j`, we are halfway
there (the numerator half) with :math:`AA^T`. The denominator of :math:`b_{ij}`
is the product :math:`||\mathbf{a}_i|| ||\mathbf{a}_j||`. This can be
constructed by letting :math:`\mathbf{d}` be the vector of the diagonal entries
of :math:`AA^T`, and taking the *outer product* of that vector with itself:

.. math::

    (\mathbf{d}^T \mathbf{d})_{ij} = d_i d_j = ||\mathbf{a}_i||^2 ||\mathbf{a}_j||^2

Putting this together, we see that

.. math::

    B = \frac{AA^T}{\sqrt{\mathbf{d}^T \mathbf{d}}}

where the fraction bar stands for component-by-component division of the matrices.

For more on the math behind this, see:

* `tf–idf <https://en.wikipedia.org/wiki/Tf%E2%80%93idf>`__ from Wikipedia
* `Introduction to Information Retrieval <http://nlp.stanford.edu/IR-book/html/htmledition/irbook.html>`__ by Manning, Raghavan, and Schütze
* `Tf-idf :: A Single-Page Tutorial - Information Retrieval and Text Mining <http://www.tfidf.com/>`__
* `Cosine similarity <https://en.wikipedia.org/wiki/Cosine_similarity>`__ from Wikipedia

Numpy implementation
--------------------

Nikola is written in python, and Numpy_ is a powerful library for doing
calculations on large matrices.  It provides lots of methods for doing
matrix/vector operations quickly.

Here is the code that creates the term count matrix:

.. code:: python
    :number-lines:

    class RelatedPosts(ConfigPlugin):

    # ...

    def set_term_count(self,site):
        """set the post-word count matrix

        set self.tc to be a matrix where

            self.tc[i,j] = # of times word j appears in post i
        """
        if not self.allwords:
            self.set_words(site)
        result = numpy.zeros((len(site.posts),len(self.allwords)))
        for i,post in enumerate(site.posts):
            # wordcount[word] is the number of times 'word' appears in the post
            wordcount= defaultdict(int,zip(*numpy.unique(numpy.array(post.meta('words')), return_counts=True)))
            for j,word in enumerate(self.allwords):
                result[i,j] = wordcount[word]
        # logger.debug("set_term_count: %s" % result)
        self.tc = result
        return result

I don't want to go into what a :code:`ConfigPlugin` is; read the `Nikola
manual`_ if you want to know. The important thing to know for context is that
:code:`site` is a reference to the whole Nikola site object, and
:code:`site.posts` refers to the list of all posts.  The list :code:`self.allwords` is
a list of all the words used in the site.  For each post,
:code:`post.meta('words')` is a list of all the words used in the post, with multiplicity.

Originally I had something like :code:`result[i,j] =
post.meta('words').count(word)`, but I realized after watching the site build
many times that I had introduced a lot of slowdown.  I was essentially checking
each word of each post against each word of the whole site. This is terribly
redundant since once it matches a word, we can stop checking it!  In fact, we
can just make a tally of all the words in the post as a dictionary, and look up
each word of the site in that dictionary.  That is what :code:`wordcount=
defaultdict(int,zip(*numpy.unique(numpy.array(post.meta('words')),
return_counts=True)))` does.  The unique_ function returns a tuple of
unique items in the array, and their multiplicities or “counts.”  This is
converted into python dictionary with the :code:`zip` function, and then into a
:code:`defaultdict` that returns zero (the :code:`int` version of :code:`None`)
if the looked-up term is not in the post.  This optimization cut the time to build by about 75%.

The next matrix to compute is the term frequency matrix:

.. code:: python
    :number-lines:

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
            self._tf = term_count / wordmax[:,None]
            logger.debug("tf: %s" % self._tf)
        return self._tf

The :code:`@property` line is an example of a python function decorator. In
general, function decorators are amazing and complicated. This one is not,
though: it allows us to treat the output of a function as if it were a regular
property. That is, :code:`self.tc` will return the output of `self.tc()`.  This
is just some syntactic sugar, but like sugar, it's pretty sweet.

We use *lazy evaluation* to compute the tf matrix once, stash it in a “private”
property :code:`self._tc`, and after subsequent calls just return that private
property.  Remember no properties are *really* private in Python, but the
leading underscore is customary for properties you don't want people to mess with.

Lines 12 and 13 compute the tf matrix.  The :code:`amax` command in numpy
computes the maximum value of an array along an axis.   In this case, we want
the row maximum (the second axis, which has index 1 because we start counting
from zero). We want to divide each row of tf by its maximum.   Numpy can divide
matrices component-by-component if their shapes match. Alas, :code:`term_count`
is an :math:`m \times n` matrix and :code:`wordmax` is a vector of length
:math:`m`. But no matter; the array :code:`wordmax[:,None]` converts this vector to
the appropriate matrix.  Essentially, :code:`:` in the first index means the
rows come from the whole vector, and :code:`None` in the second index means to
extend the rows as far to the right as necessary.

The fact that this method is implemented with numpy-only functions, and not by
walking the array in a python loop, makes it run faster.

Here is the idf propery:

.. code:: python
    :number-lines:

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
        return self._idf

To count the number of posts containing a word, I rounded up the term-frequency
matrix. Since term frequency is between zero and one, and positive only if the
term appears in the post, this will return a matrix of zeros and ones.
Then summing the *columns* will give a (row) vector of the post-count per word.

With tf and idf we compute tf-idf:

.. code:: python
    :number-lines:

    @property
    def tfidf(self):
        """the tf-idf matrix

        tfidf[i,j] = TF[i,j] * IDF[j]
        """
        if self._tfidf is None:
            # compute it!
            self._tfidf = self.tf * self.idf[None,:]
        return self._tfidf

Remember that :code:`self.tf` and :code:`self.idf` are methods, but because of
the :code:`@property` decorator, we get to pretend that they are properties.
Otherwise we would need to write :code:`self.tf()` and so on.

.. code:: python
    :number-lines:

    @property
    def dc(self):
        """the document cosine similarity matrix"""
        if self._dc is None:
            tfidf = self.tfidf
            result = numpy.dot(tfidf,numpy.transpose(tfidf))
            d = numpy.diagonal(result)
            self._dc = result/numpy.sqrt(numpy.outer(d,d))
        return self._dc

Line 6 is where we compute :math:`AA^T`.  We then extract its diagonal vector
and  form the outer product with `numpy.outer`.  Again, a pure numpy
implementation means a fast execution.

The last method to implement sets the related posts for each post.

.. code:: python
    :number-lines:

    def set_related(self,site):
        """ set the top related posts for each post"""
        dcs = self.dc - numpy.identity(self.dc.shape[0])
        indices_sorted = dcs.argsort(axis=1)[:,-self.num_related:][:,::-1]
        for i,post in enumerate(site.posts):
            post.related = []
            for r in indices_sorted[i,:]:
                post.related.append(site.posts[r])

The array :code:`dcs` in line 3 subtracts one from every diagonal entry of
:code:`self.dc`. Notice that :code:`self.dc` is going to have ones on the
diagonal, because it measures the correlation of each post with itself.  For
purposes of displaying interesting related content, it doesn't help to link to
the original document.  Subtracting the identity matrix replaces the ones with zeros.
This forces each post's self-correlation value to the minimum instead of the maximum,
ensuring the post will not be counted as related to itself.

The numpy function :code:`argsort` returns the indices of the array in
increasing order of their corresponding values (as opposed to :code:`sort` which
would just sort the values.)  The property :code:`self.num_related` is just a
config value that stores how many posts to return.  So line 4 sorts each row by
index of increasing value, selects the :code:`self.num_related` rightmost
columns, then reverses the columns. Therefore :code:`indices_sorted` has a row
for each post, :code:`self.num_related` columns, and the values are the post
indices of the most related posts (not including the post itself.)

The for loop in lines 5 through 8 just walks the list of posts, creating a list property
:code:`self.related`, and adding a reference to each related post.

Of course, whether this information appears in the presented page is up to the post's
template.  That is a post for another day.  Suffice it to say the mako_ templating engine can
handle this easily.

.. _mako: http://www.makotemplates.org/

Natural language processing
---------------------------

I lied a bit when I said that :code:`post.meta('words')` was a list of “words”
in the post, and that :code:`site.allwords` was a list of all words in the site.
For purposes of relating documents, we don't want to distinguish between words
like *python*, *python's*, or *pythonic*.

Enter python's `Natural Language Toolkit (NLTK) <http://www.nltk.org/>`__.  NLTK
contains many, many resources for processing texts.  One such resource is a
package of *stemmers*, which truncate a word to its “stem”.  If one word is just
a form of another word, the two words should have the same stem.

Here is a quick example:

.. code:: python

    >>> import nltk
    >>> s = nltk.stem.SnowballStemmer("english")
    >>> [s.stem(word) for word in ["python","python's","pythonic"]]
    ['python', 'python', 'python']

The :code:`set_words` methods applies this stemming first to shorten the word
list and consolidate forms:

.. code:: python
    :number-lines:

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
        self.allwords = list(unique_everseen(self.allwords))

Lines 5 through 13 produce a stemmer object depending on the post's language.
(A potential bug is that not all languages supported by Nikola have SnowballStemmers.
Also, this probably should be a factory method to clean up the code.)

:code:`word_tokenize` is an NLTK function that splits text into tokens like
words, but smartly. You might wonder why not do a simple :code:`split` on the
string by whitespace or some other regular expression. Then you realize this is
probably harder than it looks at first glance, and remember that someone has
probably already solved this problem. With :code:`word_tokenize`, bits like
punctuation get split off, and contractions are split into separate tokens.
So “doesn't?” becomes :code:`["does","n't","?"]`.

So we tokenize each post's text, stem each word, and add the list to the post as
a property (not sure it needs to be in the :code:`meta` dictionary). We extend
the “master” word list with these words.  Once finished, we apply
:code:`unique_everseen` from the :code:`more_itertools` package to remove
repated words from the master list. (We do *not* want to do this for the
individual posts; if they contain a word several times that is going to increase
term frequency.)

Next steps
----------

This post took about as long to write as the plugin!  And now that I've done a full
exegesis of my code, I realize that I could improve it in many ways.  Not just adding features, but
by cleanup and streamlining.

Right now this plugin is a config plugin, which means it generates the related
posts each time the site builds.  But the underlying data only changes every
time a post is updated.  So perhaps this is better implemented as a Task plugin,
which depends on the post timeline.  For that I need to learn more about the doit_ package for python.

.. _doit: https://pydoit.org/

Nikola has support for posts in several languages, and even translated versions
of posts. Before merging any of this work into Nikola it would have to handle
that, at least partially.  NLTK has stemmers for several languages (though not
as many as Nikola supports).  Now that I think of it, as long as the post's
:code:`words` property contained the words, stemmed in the appropriate language,
and the plugin's :code:`allwords` property contained all wordstems used in all languages,
the matching algorithm should naturally match posts in each language to posts in the same language.

Inverse document frequency takes care of common words like *the*, *an*, *of*,
etc., by giving them a small coefficient. However, NLTK knows how to do this
too.  Stemmers can be configured to simply ignore “stop words” such as these. It might
make the tf-idf matrix a little smaller to use this feature.

I've also realized that numpy can be used with an object-oriented approach.
I can replace lines like :code:`numpy.dot(tfidf,numpy.transpose(tfidf))`
with :code:`numpy.dot(tfidf,tfidf.transpose())`.  That might be the more pythonic approach.

Weights could be introduced, as they are in the inspiring jekyll plugin.  But as
of now I'm not dissatisfied with the results I'm getting with uniform weights.

It would be fun to add the degree of correlation to the match, and maybe pass it
to HTML as a :code:`data` attribute.

.. _numpy: https://www.numpy.org/
.. _`Nikola manual`: https://getnikola.com/handbook.html
.. _unique: http://docs.scipy.org/doc/numpy/reference/generated/numpy.unique.html
