.. title: Adding a category menu to Nikola
.. slug: adding-a-category-menu-to-nikola
.. date: 2016-06-07 14:47:26 UTC-04:00
.. tags: python, nikola
.. category: computing/blog
.. link:
.. description:
.. type: text

I have been obsessing about Nikola_ lately.  I wanted to add a “categories”
widget to the navigation menu.  It took me three tries but I finally figured out
a pretty decent way to do it.

.. TEASER_END

Nikola is just a pile of plugins, and its build process is derived from doit_.
There are many ways to plug or hook into the building process.  I pored over the
docs, especially the section on `Extending Nikola`_.

One twist to my problem was that I wanted to put the count of posts per category
in the menu.  Seems like a nice touch, and the theme I am adapting has that
feature. But the :code:`NAVIGATION_LINKS` configuration variable only allows menus
that have :code:`(link,name)` tuples in them.  No way to pass extra text to the template.

Then I thought I could do the whole thing in the page templates.  There are lots
of variables passed to the template.  If the site itself were passed, I could have
done that.  Alas, not so.

My first real effort was to create a Task plugin that generated the category
menu separately.  The plan was to render a snippet of HTML that I could include
in any page template.  The snippet generation worked, but then the templating
methods slapped :code:`<html>` and :code:`<body>` tags around the whole thing.  Not what I
wanted!  I either had to filter off those extra tags, go a level deeper into the
site object, or find another way.

Then I went back to the idea of a Config plugin, that put the category links in
a submenu of :code:`NAVIGATION_LINKS`.  Instead of `(link,name)` tuple, I added tuples
of the form :code:`(link,name,count)`.  In templates that were not aware of this extra
struture, I figured that the extra data would be ignored as the templating
system walked the list of links.  Nope, I got a :code:`Too many values to unpack`
error.  So this plugin breaks all existing page templates.

What if I passed the count to the template in a failsafe way?  Rather than as a
tuple,  I tried *appending* the post count to the category link in the query
string.  So rather than :code:`('/category/cat_foo.html','foo',3)`, I passed
:code:`('/category/cat_foo.html?count=3','foo')`. Then templates could check for the
existence of this count key in the query string, strip it off, and use it to
format the category menu.  Templates that didn't know to check for this would
still work, having meaningless query strings attached to the category URLS.

It worked!  Except I started struggling with the next step of putting the
category menu where I wanted it. My plugin was *appending* to
:code:`site.NAVIGATION_LINKS`.  That list (actually a tuple itself) is rendered into
the navbar in order, meaning the category menu would go at the end.  I didn't
want it to appear last in the navbar.  So I started rewriting the template to
walk the list of navigation links and select the category menu to put it first.
Then to render the other links, I would need to rewalk the list, skipping the
category menu.

At this point I realized that I was yet again trying to put a square peg in a
round hole. I didn't want to add the category menu to
:code:`site.NAVIGATION_LINKS`—the data I wanted to add didn't fit there, and
once it was there I didn't want it treated like the rest of the navigation
links.  I needed to pass the category menu as a separate bit of data to the
template.

Finally, after reading through the source code and :code:`conf.py` one more
time, I found was I was looking for.  The :code:`site.GLOBAL_CONTEXT` dictionary
can hold whatever you want, and *it gets passed to all templates*.  So really I
just needed to pass whatever data I wanted to
:code:`site.GLOBAL_CONTEXT['CATEGORY_MENU']`.  I gave it a list of 3-tuples
:code:`(link,count,name)`.  Then I adapted the page templates to put this
category menu exactly where I wanted in the navbar.

This is an example where the answer is obvious once you think about the problem
for several days.  If I were a real programmer I probably would have gotten it
done a lot quicker.  But I did do something that a real programmer would: I
committed my plugin to a `github repo`_.  It needs some love before I am ready
to submit a pull request, but it gets the job done for now.

.. _`github repo`: https://github.com/leingang/plugins/tree/category_menu/v7/category_menu

.. _doit: http://pydoit.org/

.. _Nikola: http://getnikola.com/

.. _`Extending Nikola`: https://getnikola.com/extending.html
