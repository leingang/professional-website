.. title: Problem solving and algorithms
.. slug: problem-solving-and-algorithms
.. date: 2016-05-31 22:23:05 UTC-04:00
.. tags: math, education, mathjax
.. category: math
.. link:
.. description:
.. type: text

This evening at dinner my 9-year-old son talked about a problem he had been working
on for math homework.

    Ben and Cole have 36 toy cars.  Ben has 8 more than Cole.  How many does Ben have?

We had some fun discussing solutions to this problem, and a few wrong answers.

.. TEASER_END:

First, the wrong answer: more than one person at the table blurted out that Ben
had 28 cars.  Why?  Because :math:`36-8=28`.  The logic behind this solution
comes from skimming the problem: the only numbers are :math:`36` and :math:`8`,
and the word *more* usually indicates subtraction.

But this doesn't satisfy the original problem.  If Ben has 28 cars, Cole has 20,
and the two together have 48 cars, not 36 as the problem demands.  So we've learned
it can't be 20, and that we can't read word problems without reading every word.

In the assignment, my son was supposed to use the “guess-check-revise” method.
His first guess was :math:`18`.  This is obviously not a solution because Ben needs to have 8 more.
So he kept increasing Ben's number and decreasing Cole's until he found a difference of 8.

My daughter, age 13, is in pre-algebra.  Here was her approach, which you might
call combinatorial.  Take the eight “more” cars that Ben has and set them aside.
There are :math:`36-28=8` cars remaining (“See?” says the skimmer. “I told you
we had to do that.”)  They have to be divided evenly between Ben and Cole, since
all the inequity has already been accounted for.  So of these 28, Ben and Cole
each own 14.  Therefore Ben has :math:`14+8=22` and Cole has just the :math:`14`.

That shows good number sense.  By next year, she will probably solve the problem
this way: let :math:`x` be Cole's car count. Then Ben's car count is
:math:`x+8`.  Add the two (:math:`2x+8`) and the total is :math:`36`. Therefore
:math:`2x+8=36 \implies x=14 \implies x+8 = 22`.  This is totally efficient, and
if you read it carefully, mimics in mathematical language the argument from the
previous paragraph.  On the other hand, the price of algebraic efficiency is
that it's easy to lose number sense.  So I hope she doesn't forget her
seventh-grade techniques as she learns her eighth-grade ones.

My solution was the worst.  I immediately jumped to

.. math::

    \begin{aligned}
        x+y &= 36 \\
        x-y &= 8
    \end{aligned}

where :math:`x` is Ben's car count and :math:`y` is Cole's.   But I couldn't
solve two equations in two variables in my head while eating chicken and
couscous. So I gave up.

I found it interesting that my approach was the most sophisticated but also the
most technically difficult.  The kids haven't been boxed in by the standard
algorithms yet.  Common Core emphasizes procedural flexibility and choosing an
appropriate solution strategy among many.  I think this is a good thing.

Many of my calculus students arrive assuming that each problem has a unique best
solution method, which needs to be shown them before the problem can be solved.
But one of the findings detailed in *`Make it Stick`_* is that students learn
better when the attempt a problem before being shown its solution.  And having
many strategies to choose from allows students to find their own solutions.

Epilogue: Please do not get the impression that all of our dinner conversations
at home are about math!  I was just lucky on this particular evening.

.. _`Make it Stick`:
