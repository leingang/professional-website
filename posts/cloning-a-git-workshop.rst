.. title: Cloning a git workshop
.. slug: cloning-a-git-workshop
.. date: 2016-06-15 16:46:01 UTC-04:00
.. tags: git,github
.. category: computing
.. link:
.. description: In which mathematicians pretend to be programmers for an afternoon
.. type: text
.. coverimage: https://c8.staticflickr.com/8/7148/6674301095_77bb086c19_b.jpg
.. previewimage: https://c8.staticflickr.com/8/7148/6674301095_77bb086c19_z.jpg

.. class:: post-intro

    When I was at the `MathBookXML workshop
    <http://aimath.org/pastworkshops/mathbookxml.html>`__ at AIM_ in April, `Rob
    Beezer`_ gave us a quick two-hour workshop on :code:`git` and github_.
    Although I had been using it to manage some of my projects, I couldn't quite
    understand how it worked in a collaborative environment (which is, after
    all, what it is chiefly designed for).  After a couple of hours, I could
    finally say that I got git.

    At least enough to teach my coworkers.  That's what I did today.  I made a fork
    of Rob's gitpractice_ repository, and we all practiced the development process.

.. _AIM: https://aimath.org/

.. _`Rob Beezer`: https://buzzard.ups.edu/

Here is the basic flow:

.. TEASER_END

1. In github, fork the central repository to your own account.

2. Clone your personal fork to your own machine.  The url of your fork can be copied from the repository page on github.
   In a terminal window run:

   .. code:: bash

       $ git clone <forkurl>

3. Create a branch of the repository on your clone of the fork, and switch to that branch.

   .. code:: bash

       $ git branch <branchname>
       $ git checkout <branchname>

   Creating a branch does not automatically switch to it! If you want to do both
   at the same time, at the expense of a more cryptic command, run

   .. code:: bash

       $ git checkout -b <branchname>

4. Edit files and commit changes to the branch.

   .. code:: bash

       $ git add <changed files>
       $ git commit -m "<message>"

   The message goes into the repository's log.  There are differing conventions on
   commit message styles.  Rob's advice is to write in sentence predicates (verb + object),
   with the verb in *imperative mood*.  So something like :code:`use display style by default`
   instead of :code:`configured to use display style by default`.  Another convention
   would be to start with a verb in *past tense*, but I must admit, after trying
   Rob's suggestion for a while, I find it more succinct and easier to write good messages.

5. Push changes to your fork on github.

   .. code:: bash

       $ git push origin <branchname>

   In many development environments the changes would be merged into the local
   master branch first, and then pushed to origin.  But here we plan to have this
   branch merged into the central repository, which will eventually reach our local and fork.

   Going back to github you can see that a new branch has been created.

6. Submit a pull request to have the central repository merge (or “pull”) the changes on your branch.

Everybody got it done.  You could say we successfully cloned the workshop.  Or is it forked?

The “exciting” part was that one of the pull requests created a conflict.  So I got to demo that as the master
of the central or base repository.  The process is:

1. Clone the central repository to a local machine

   .. code:: bash

       $ git clone <baseurl>

2. Create and switch to a temporary branch.  The branch can be called anything, but github suggests
   :code:`username-theirbranchname`

   .. code:: bash

       $ git checkout -b newbranch

3. Merge the changes from the fork branch (the one initiating the pull request)
   into the temporary branch (which has been checked out already).

   .. code:: bash

       $ git merge <forkurl> <forkbranch>

4. Checkout the master branch and merge in the temporary branch.

   .. code:: bash

       $ git checkout master
       $ git merge newbranch

   This recreates the conflict, only now between branches in the same repository.

5. Fix conflicts and push up to github.

I wrote up my workshop script (again, stolen from Rob) into the repository's :code:`README.md` file.
I also created a `new organization <//github.com/nyumathclinic>`__ and moved my repository over to it.

.. class:: credits

    Image_ by Pete Ashton via Flickr (CC-BY-NC_)

.. _Image: https://flic.kr/p/baMxbP
.. _CC-BY-NC: https://creativecommons.org/licenses/by-nc/2.0/

.. _gitpractice: https://github.com/BooksHTML/gitpractice

.. _github: https://github.com/
