.. title: Exceeding TeX's save_size with auto-multiple-choice
.. slug: exceeding-texs-save_size-with-auto-multiple-choice
.. date: 2016-05-12 13:46:46 UTC-04:00
.. tags: auto-multiple-choice, latex, tikz-pgf, calculus-ii
.. category: computing/tex
.. link:
.. description: Understanding why TeX's save stack was overflowing requires a deep dive into old TikZ libraries.
.. type: text

.. role:: latex(code)
   :language: latex

.. role:: bash(code)
  :language: bash


.. figure:: https://farm1.staticflickr.com/45/125351816_cffce6d7f7_o.jpg
    :class: img-responsive img-thumbnail
    :target: https://www.flickr.com/photos/karpacious/125351816

    Overflowing

    .. class:: credits

    Image_ by Karp_ via Flickr_ (CC-BY_)

    .. _Image: https://www.flickr.com/photos/karpacious/125351816
    .. _Karp: https://www.flickr.com/photos/karpacious/
    .. _Flickr: https://www.flickr.com/
    .. _CC-BY: https://creativecommons.org/licenses/by/2.0/

This semester in Calculus II we are doing our common exam with `auto-multiple-choice <http://home.gna.org/auto-qcm/>`__.  I have used this in my own sections for a couple of years and I wanted to see how it went on a grander scale.

You never know what's going to happen when you scale up.  After finalizing the exam content, we went to generate the copies.  The exam had 18 pages.  AMC makes individualized exam copies, each with its own randomization, and puts them in the same PDF.  We have seven sections, and we wanted the exam copy numbers to indicate the section.  AMC only generates series numbers sequentially.  So even though we have only 200 students we needed to generate 750 exams in order to give each student from section *n* an exam with a three-digit code whose first digit was *n*.  A little arithmetic says the resulting PDF should have 13,500 pages.

The number of pages was not a problem; the resulting PDF was only about 35MB large.  The issue was TeX's *save stack*.  There is a limit to the number of control sequences TeX can reserve.  Something in the process was overflowing this stack.  I was getting errors over the form "``TeX capacity exceeded; save size=80000``".  The error only happened at the moment of reading the `.aux` file for the last time.

Now most of the time when TeX gives you an error like this, it means you've done something wrong that's avoidable.  But I thought it might be true that my 13,500 page document really did need more memory.

Googling around I found several posts from frantic users (for instance `here <http://tex.stackexchange.com/q/185153/1402>`__ and `here <http://tex.stackexchange.com/q/24753/1402>`__) saying they need to increase TeX's memory.  In each of the cases that were resolved, the user had just done something wrong like created an infinite loop in their TeX document.  Something like :latex:`\def\a{\a}` will do that.

Yet I remained convinced, especially after I found `this page on the French AMC wiki <https://c2i.education.fr/wikipfc2i-X/index.php/Auto-multiple-choice#probl.C3.A8me_m.C3.A9moire_avec_Latex>`__ about how to increase TeX's main memory (not save size).  After several attempts to edit my ``texmf.cnf`` and increase the save size, I could not get any change in behavior.  In fact, I could not even get TeX to acknowledge that I had increased the save size.  Then I learned that in addition to editing the configuration file, the TeX executables needed to be recompiled to account for the new configuration.  I tried running :bash:`fmtutils --byfmt xelatex` (I use the xelatex engine in order to use TrueType fonts), but this didn't have any effect either.  I must have been doing something (else) wrong.

I started looking at the point of stack overflow to see what was raising the problem.  It turned out my aux file was getting insanely long with tens of thousands of lines of the form

.. code:: latex

    \pgfsyspdfmark{pgfid12345}{foo}{bar}

where *foo* and *bar* were large integers.  These macros expand to other macros that save the numbers *foo* and *bar* as control sequences of their own.  Right around :code:`pgfid79973` was where TeX barfed (Remember ``save_size=80000`` ?)

I knew that AMC didn't use the :code:`.aux` file; just an :code:`.xy` file it creates on its own.  So what if the macros in the :code:`.aux` file were neutered?  I tried putting

.. code:: latex

    \renewcommand{\pdfsyspdfmark}[3]{\relax}

in my TeX file preamble.  Success!  At least, the process was finishing without error.  I was not all that confident that ignoring all of those macros was going to work.

Then I got to thinking why those lines would get written that often to the aux file in the first place.  There were actually only two :code:`tikzpicture` environments in the whole document.  Actually, no, AMC uses :code:`tikz` (or maybe :code:`pgf`, which amounts to the same thing) for *each* of the bubbles on the document [#]_.  There are about 100 bubbles on the whole exam, so on the order of 750,000 :code:`tikz`/:code:`pgf` groups.  Something that was creating a macro for each of them will overflow the stack by tenfold!

.. [#] If you opt for round bubbles in your test, rather than square boxes.

So why was it adding a line to the aux file for each picture?  Because I asked it to.  The TikZ :code:`remember picture` key allows named TikZ nodes to be accessible outside the enclosing picture group.  This is handy if you want to `point from text to a node within a picture <http://www.texample.net/tikz/examples/beamer-arrows/>`__.

TikZ's key configuration mechanism is so flexible it's easy to do things globally.  I looked at my TikZ code, and sure enough, inside a library file I had created, was the line:

.. code:: latex

    \tikzstyle{every picture}+=[remember picture]

Because why wouldn't you want to do that?  Now I know why: if you have 750K tikzpictures in the same document!

Rather than change the library file, I negated this setting in my local tex file by invoking :latex:`\tikzstyle{every picture}+=[remember picture=false]` right after loading the library.  Now things ran just as expected.

Once again, the moral of the story is: **If you think you need to increase TeX's memory, you probably don't.**
