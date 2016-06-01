.. title: A characteristic function for analysis experience
.. slug: a-characteristic-function-for-analysis-experience
.. date: 2016-05-23 11:29:14 UTC-04:00
.. tags: math, education, mathjax
.. category: math
.. link:
.. previewimage: http://c3.staticflickr.com/8/7098/7305951154_1abf87af4c_z.jpg
.. description: In which we wonder how to tell if someone has taken analysis, long after they have allegedly taken analysis.
.. type: text

.. raw:: html

    <a data-flickr-embed="true"  href="https://www.flickr.com/photos/69615420@N00/7305951154/in/photolist-c8AUK5-Nywpp-8AZeXr-8FPiR9-7w5s4w-6WvnzH-ciosuS-dnwMud-p3mzwe-4zC8oy-6xnjNG-7m2Rcp-7AsFGT-vbEd1W-edfAro-h2GYzy-83yHfJ-9yA31J-4PAtTo-8bAqPJ-9vt5rs-p69TzJ-egdSCj-6odksE-9c5jtN-9B93Bm-sou23R-c6aLK-5MQ8CZ-akCeuu-6zteAX-8Z6iDZ-9f8vjQ-5UYsgC-p2FFor-mvXQLr-5nKMj6-5UscRE-2LTAn-dkHt4F-7napFU-oCKYTa-p8KSGF-5wMcFN-6KKsH8-8g86VW-5FMmv6-kchD6Z-6Zq1Ws-6WCDBo" title="math"><img src="https://farm8.staticflickr.com/7098/7305951154_7e4a6f6d76_k.jpg" width="2048" height="1358" alt="math"></a><script async src="//embedr.flickr.com/assets/client-code.js" charset="utf-8"></script>

(This is a based on a Facebook post I made a couple of days ago.)

Here's a case study: a student with a very irregular course history insists they
have at one point in their college career learned analysis. What questions would
you ask the student to verify this?

.. TEASER_END:

In analysis, a *characteristic function* of a set determines whether points in a
space are in the given set.  To put it more formally, if :math:`X` is a set and :math:`E`
a subset of :math:`X`, the characteristic function of :math:`E` is the set

.. math::

    \chi_E(x) = \begin{cases} 1 & \text{if $x\in E$} \\ 0 & \text{otherwise} \\ \end{cases}

If :math:`X` is the set of all students, and :math:`E` is the subset of students
who have taken analysis, I could just apply :math:`\chi_E` to the student and
find the value. But this is no simple matter.  (Although :math:`\chi_E` is an
example of a *simple function* in measure theory.)

In our analysis course, students learn formal properties like the
:math:`\epsilon`, :math:`\delta` definition of a limit, and the integral as a
limit of Riemann sums.  But a student who had taken this course long ago may
have forgotten those precisely, or claim to have forgotten them.  I didn't want
to ask a question with a unique answer.

Here are some suggested questions I got that I quite liked:

* **What's so special about the real numbers?** If a student said that the real
  numbers were complete, that would be good evidence of analysis exposure.  Or
  they might mention the least upper bound property.  Or their uncountability.
  Someone without analysis could still answer the question, but they might say
  something like "they go on and on forever."

* **What's the difference between open and closed sets?**  A student could say
  that closed sets contain their limit points.  From there we could go into a
  discussion of some examples: discrete sets, closed intervals, etc.  A less-experienced
  student might instead say that closed sets are defined by less-than-or-equal-to or
  greater-than-or-equal-to inequalities.

* **Give an example of a function which is not continuous at a point, and show
  why it is not continuous.**  Students learn the notion of continuity in calculus.
  Someone who took calculus could probably draw the graph of a function with different
  left- and right-sided limits at a point.  How they answered the "show" part of
  the question would determine if they knew how to talk about the limit concept rigorously.

In the case that inspired this post, I got all the good answers far too late. Instead,
I emailed the head of the department of the students' previous school.  The information
she provided was definitive in deciding whether the student had learned analysis.  But
at least I know what to do next time.
