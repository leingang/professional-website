# Two Quarto sites, one repo.
#   make office          render the cims.nyu.edu office page   -> office/_site
#   make site            render matthewleingang.com            -> site/_site
#   make preview-office  live preview (auto-reload) of the office page
#   make preview-site    live preview of the professional site
#   make deploy-office   render + rsync office page to CIMS (dry run first!)
#   make migrate         re-run the legacy blog migration (uses tools/posts_manifest.csv)
#   make preview-post POST=<folder>   preview one post (draft or published), live reload
#   make publish POST=<folder>        move a draft from drafts/answers/ into the site
#   make import-se       import new Stack Exchange answers as draft posts (tools/stackexchange.yml)

QUARTO   ?= quarto
CIMS_USER ?= mpl5
CIMS_HOST ?= access.cims.nyu.edu
CIMS_DIR  ?= public_html/
# Anything already in public_html that is NOT part of this site must be
# protected here, or --delete will remove it. (P = protect from deletion.)
RSYNC_PROTECT ?= --filter='P grading/'
RSYNC_FLAGS ?= -rltvz --delete --exclude .DS_Store $(RSYNC_PROTECT)
# macOS's bundled rsync ignores --chmod and files synced from Box arrive as 600,
# so fix permissions on the server after each deploy: dirs 711, files 644.
SITE_PATHS = index.html courses.html office-hours.html assets
FIX_PERMS = cd $(CIMS_DIR) && find $(SITE_PATHS) -type d -exec chmod 711 {} + && find $(SITE_PATHS) -type f -exec chmod 644 {} +

.PHONY: all office site preview-office preview-site preview-post publish deploy-office deploy-office-dry migrate import-se clean

all: office site

office/assets/headshot.jpg site/images/headshot.jpg: _shared/headshot.jpg
	cp $< $@

office: office/assets/headshot.jpg
	$(QUARTO) render office

site: site/images/headshot.jpg
	$(QUARTO) render site --profile production

preview-office: office/assets/headshot.jpg
	cd office && $(QUARTO) preview index.qmd

preview-site: site/images/headshot.jpg
	$(QUARTO) preview site

# POST is a post folder or its index.qmd, in drafts/answers/ or site/blog/.
preview-post:
	@test -n "$(POST)" || { echo "usage: make preview-post POST=drafts/answers/<folder>"; exit 1; }
	$(QUARTO) preview "$(patsubst %/,%,$(POST:%/index.qmd=%))/index.qmd" -M draft:false

publish:
	@test -n "$(POST)" || { echo "usage: make publish POST=drafts/answers/<folder>"; exit 1; }
	python3 tools/import_stackexchange.py --publish "$(POST)"

deploy-office-dry: office
	rsync $(RSYNC_FLAGS) --dry-run office/_site/ $(CIMS_USER)@$(CIMS_HOST):$(CIMS_DIR)

deploy-office: office
	rsync $(RSYNC_FLAGS) office/_site/ $(CIMS_USER)@$(CIMS_HOST):$(CIMS_DIR)
	ssh $(CIMS_USER)@$(CIMS_HOST) '$(FIX_PERMS)'
	@curl -s -o /dev/null -w 'https://cims.nyu.edu/~$(CIMS_USER)/ -> HTTP %{http_code}\n' https://cims.nyu.edu/~$(CIMS_USER)/

migrate:
	python3 tools/migrate_nikola.py

import-se:
	python3 tools/import_stackexchange.py

clean:
	rm -rf office/_site site/_site site/.quarto office/.quarto
