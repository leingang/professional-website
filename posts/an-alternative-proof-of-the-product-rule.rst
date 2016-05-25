.. title: An alternative proof of the product rule
.. slug: an-alternative-proof-of-the-product-rule
.. date: 2016-05-19 09:38:40 UTC-04:00
.. tags: mathjax, math, calculus, product rule
.. category: math
.. link: http://dx.doi.org/10.4169/amer.math.monthly.123.5.470
.. description:
.. type: text

.. class: figure

.. raw:: html

    <div class="getty embed image" style="background-color:#fff;display:inline-block;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#a7a7a7;font-size:11px;width:100%;max-width:507px;"><div style="padding:0;margin:0;text-align:left;"><a href="http://www.gettyimages.com/detail/97762204" target="_blank" style="color:#a7a7a7;text-decoration:none;font-weight:normal !important;border:none;display:inline-block;">Embed from Getty Images</a></div><div style="overflow:hidden;position:relative;height:0;padding:66.666667% 0 0 0;width:100%;"><iframe src="//embed.gettyimages.com/embed/97762204?et=J3CN1hpzQiRmjasVA7MUbA&viewMoreLink=on&sig=QaV_UJXnGDg6NJnGl3bR94AjW3xdQSJijJ5wyAJtIEc=" width="507" height="338" scrolling="no" frameborder="0" style="display:inline-block;position:absolute;top:0;left:0;width:100%;height:100%;margin:0;"></iframe></div><p style="margin:0;"></p></div>

Piotr Josevich wrote a short article_ (this post will probably end up longer
than it) in the American Mathematical Monthly about an alternative proof of the
product rule.  It requires nothing more than the generalized power rule for
:math:`n=2` and FOIL_.

First, let :math:`u` be differentiable at :math:`a`.  Let :math:`v(x) = u(x)^2`.
Then

.. math::

    \begin{aligned}
    v'(a) &= \lim_{x\to a} \frac{v(x)-v(a)}{x-a} \\
          &= \lim_{x\to a} \frac{u(x)^2 - u(a)^2}{x-a} \\
          &= \lim_{x\to a} \frac{(u(x)+u(a))(u(x)-u(a))}{x-a} \\
          &= \lim_{x\to a} (u(x)+u(a)) \cdot \lim_{x\to a}\frac{u(x)-u(a)}{x-a} \\
          &= 2 u(a) u'(a)
    \end{aligned}

So, in general, the derivative of :math:`u^2` is :math:`2u u`.

Now, let :math:`f` and :math:`g` be differentiable.  Let :math:`u = f+g` and :math:`v = u^2`.
Then

.. math::

   v' = 2 u u' = 2 (f+g)(f'+g') = 2(ff' + fg' + gf' + gg')

On the other hand, :math:`v = (f+g)^2 = f^2 + 2fg + g^2`, so

.. math::

   v' = 2ff' + 2(fg)' +2gg'

Therefore, after canceling the factor of :math:`2` from each,

.. math::

     ff' + fg' + gf' + gg' = ff' + (fg)' + gg'

Finally, after canceling :math:`ff'` and :math:`gg'` from both sides, we have

.. math::

    (fg)' = fg' + gf'


I like this proof.  I'm not sure it's better than the typical "add and subtract
the same thing" trick that's often used.  Both have a little bit of hocus-pocus
in them.

When I teach the product rule I ask this question: Say you're working for an
hourly wage (like, in a pizza parlor or burger chain), and you want to make more
money.  How can you do that?  The answers usually come from the class:

1. Work more hours.

2. Get a raise.

Each of these will change your income independently.  If you work more hours,
your income goes up by the change in hours worked times your wage.  If you get a
raise, your income goes up by the hours worked times the change in your wage.
If you do *both*, well, you get both!

In this story, :math:`f` is the hours worked and :math:`g` is the wage.  Their
product :math:`fg` is the income.  The change in income (:math:`(fg)'`) is the
sum of the change in hours times the original wage (:math:`f'g`) and the change
in wage times the original hours worked (:math:`fg'`).

.. _article: http://dx.doi.org/10.4169/amer.math.monthly.123.5.470

.. _FOIL: http://en.wikipedia.org/wiki/FOIL_method
