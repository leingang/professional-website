Base template architecture
==========================

This is just for me to figure out WTH is going on.

base.tmpl:

    * imports base_helper.tmpl, base_header.tmpl, base_footer.tmpl, annotation_helper.tmpl

    * base_helper.html_headstart() for initial <html><head>...

    * virtual block extra_head

    * template hook extra_head

    * </head><body>

    * div#container

        - calls function base_header.html_header()

        - main#content

            + virtual block content

        - base_footer.html_footer()

    * base_helper.late_load_js()

    * virtual block extra_js

    * context variable body_end

    * template hook body_end

    * </body></html>

 post.tmpl:

    * inherits base.tmpl

    * imports post_helper.tmpl, post_header.tmpl, comments_helper.tmpl

    * defines extra_head block

        - inserts metadata

    * defines content block

        - <article>

        - post_header.html_post_header

        - div.entry-content

        - $post.text()

        - aside.postpromonav

            + post_helper.html_tags(post)

            + post_helper.html_pager(post)

        - comments

        - post_helper.mathjax_script

        - </article>

        - ${comments_helper.comment_link_script()}
