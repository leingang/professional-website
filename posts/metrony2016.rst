.. title: MAA MetroNY Section Meeting 2016
.. date: 2016-05-01 18:42:52
.. tags: MAA, MAA MetroNY Section, mathjax
.. author: Matthew Leingang
.. link:
.. description: How I spent a rainy Sunday in May.
.. category: math/talks


.. figure:: /images/MAAMetroNYProgramMay1_2016.png
	:class: img-responsive, img-thumbnail
	:target: /images/MAAMetroNYProgramMay1_2016.png
	:alt: Cover of the program for the MAA MetroNY Section Meeting, May 1, 2016.

	Cover of the meeting program

	.. class:: credits

	Artwork by `Mandy Mei <http://www.mandymei.com/>`__

I had a good time at the 2016 annual meeting of the `MetroNY Section of
the MAA <http://sections.maa.org/metrony/index.html>`__.  I saw some of
my heroes, and a few interesting talks.

The meeting was at `Vaughn College of Aeronautics and Technology
<http://vaughn.edu/>`__, which is built into an airplane hangar just off
of Laguardia Airport.  It's been recently renovated and is a very nice
space.  It was the perfect size for our 200-ish meeting.  It's a college
for students who want to pilots, air traffic controllers, or engineers.
They have a `world-champion robotics team
<http://www.vaughn.edu/news-vaughn-college-robotics-team-named-world-
champions-at-record-setting-2016-vex-robotics-competition>`__, and
simulators for both flight and traffic control.  We got to try those out
over lunch and they are definitely cool.

Starbird
--------

The keynote speaker was Mike Starbird, whom I always enjoy listening to.
He talked about “Geometric Gems,” simple proofs of famous theorems.
The one I liked the most was a proof of the Pythagorean Theorem by
Leonardo da Vinci.

.. fixme: put in TikZ for Leonardo's proof.

His closing remark was strong, too: We have taught Euclidean geometry to
students since, well, the days of Euclid (he didn't say that this
practice is currently threatened).  It's simple, accessible, elegant,
and fun.  We should continue to do so.

Strang
------

The second talk was by Gil Strang, author of several books including a
very popular linear algebra text (the one we use in MATH-UA 140 Linear
Algebra).  He talked about the importance of thinking of matrices as
objects, rather than as arrays of numbers.  In his opinion, the best
matrices are the triangular matrices and the orthogonal matrices.

He also pointed out that dimension count can be used to understand
decomposition better.  For instance, every (invertible? not quite sure
on the conditions here) :math:`2\times2` matrix can be decomposed into a
rotation, a stretching, and another rotation.  Since the space of
:math:`2\times2` matrices is four-dimensional, we ought to be able to
see four numbers in the decomposition.  And we can: one for each
rotation, two for the stretching (along each axis).  Symmetric
:math:`2\times2` matrices have one less dimension, and that is reflected
in the decomposition: the two rotations are inverses.

Lecturing with slides
---------------------

I was honored to be part of a panel discussion on enrichment strategies
for teaching.  I talked about creating good lecture slides.

.. fixme: add slideshare embed.

I use two modes for slide generation.  When I create slides for
teaching, I use LaTeX and beamer.  I generate handouts for posting to
the course website the night before.  These handouts have many solutions
to examples (and jokes) removed.  The version I do in class steps
through calculations carefully, and of course, includes solutions.
These get posted after class.

When I create slides for professional talks I like to use Keynote on the
mac.  I prefer it to PowerPoint mostly because I am Mac-native.  It has
a few more transitions than PowerPoint, most of which I don't need.

I don't use a lot of flashy transitions and animations, for their own
sake, but I am fond of automatic builds.  Having a slide with a lot of
material on it build out in stages, not advanced by a click, can be just
as good as clicking through each stage of the build.  The other
transition I really like is Magic Move, with which an object on one
slide morphs into a copy on the next slide.  This is useful if you want
to zoom in on an object.

Anyway, my contributions to the panel were well received.  I got a lot of good
questions.  One I was stumped on was, “If you put up your slides after class,
what stops people from just getting the slides instead of going to class?”  I
suppose I could *not* put up the slides, but that doesn't seem fair to the
diligent students who miss class for excusable reasons.  In the end, I hope
that I add value to the slides by delivering them and interposing my remarks.

Fischer and Warner
------------------

In the contributed paper sessions I saw a `talk
<http://fdfisher.com/2016/04/27/maa-metro-nyc-talk/>`__ by `Forest Fisher`_
and `Jared Warner`_ of Guttman College of CUNY.  They have developed a board
game modeling housing in New York City, to teach the mathematical concept of
ratio and the socioscientific phenomenon of gentrification.  They developed
the materials with open source software (Gimp_ and Inkscape_) and had the game
manufactured by an online company.  It made me think a course in game design
for math teachers would be a great professional development opportunity.

.. _`Forest Fisher`: https://guttman-cuny.digication.com/forest_fisher/Contact_Info

.. _`Jared Warner`: https://guttman-cuny.digication.com/drj/Welcome/published

.. _Gimp: http://gimp.org/

.. _Inkscape: http://inkscape.org/

.. fixme: who prints the games?

PEMDAS
------

I saw another `talk by David Sher
<http://matcmp.ncc.edu/sherd/talks/MAA16/>`__ of Nassau Community College
about the **PEMDAS** acronym.  In the US, the typical mnemonic for remembering
the arithmetic order of operations is “Parentheses, Exponents, Multiplication,
Division, Addition, Subtraction.”

The major issue with this device is that multiplication does not precede
division in the same way that it precedes addition.  Consider the problem of
simplifying the expression :math:`24 \div 6 \times 2`.  If we do the
multiplication, then the division, we get :math:`24 \div 12 = 2`.  But if we
convert the division to a multiplication we get

.. math::
	24 \div 6 \times 2 = 24 \times \frac{1}{6} \times 2 = 8

The second one has to be correct since we know multiplication is associative;
multiplying three terms together will not depend on the grouping.  We went
wrong when we decided to do the multiplication first, even though the division
came first in left-to-right order.  To summarize, multiplication and division
need to be simplified together, grouping left-to-right.  The same is true for
addition and subtraction.

So the mnemonic needs to be modified.  One can simply add a couple of words,
creating “Parentheses, Exponents, Multiplication *and* Division, Addition
*and* Subtraction.”  Remembered this way, multiplication and division are
placed on an equal footing. [#]_ Another is to elide the inverse operations
and remember **PEMA** for “Parentheses, Exponentiation, Multiplication
[including its inverse, division], Addition [including its inverse,
subtraction].”  We could shorten it even further to **EMA**, if you keep in
mind that parentheses are used to override the normal order of operations, and
so naturally come first.

Sher says if you *reverse* the order of division and multiplication
(repsectively, addition and subtraction), you will not be led into these
traps.  Considering :math:`24 \div 6 \times 2`, division first gives :math:`4
\times 2= 8`.  I hadn't heard this before, but if you think about it, it makes
sense. [#]_  You are effectively converting each division into multiplication by
the reciprocal, then immediately simplifying the multiplication with its
predecessor.  You still have to group left-to-right, however.

If you phrase the order of operations this way, the initials become
**PEDMSA.**  Unlike **PEMDAS**, which is pronounceable as an acronym,
**PEDMSA** could use a mnemonic to aid with memorization.  Sher produced many
examples, which you can read in his slides.

.. [#] `xkcd <http://xkcd.com/992>`__ has it right.

.. [#] Interesting discussion on `Math Stackexchange <http://math.stackexchange.com/q/550880/2785>`__ about this.
