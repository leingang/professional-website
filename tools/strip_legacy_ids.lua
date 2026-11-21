-- Used by migrate_nikola.py: drop element ids carried over from old HTML
-- (e.g. id="fullSizedImage"), which Quarto would treat as cross-references.
-- Header ids are kept so in-page anchors still work.
local function strip(el)
  if el.identifier and el.identifier ~= "" then el.identifier = "" end
  return el
end
return {{
  Image = strip, Link = strip, Span = strip, Div = strip, Figure = strip,
  CodeBlock = strip, Code = strip, Table = strip,
}}
