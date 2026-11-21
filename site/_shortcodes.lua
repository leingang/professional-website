-- Shortcodes that render shared YAML data (../_shared/*.yml) on any page.
--   {{< courses-taught >}}  table of current + past courses
--   {{< contact >}}         contact list from person.yml
local str = pandoc.utils.stringify

local function inlines(v)
  if v == nil then return pandoc.Inlines{} end
  if type(v) == "table" and v.t == nil and #v > 0 and v[1].t then return pandoc.Inlines(v) end
  if type(v) == "table" and (v.t == "MetaInlines" or v.t == nil) then return pandoc.Inlines(v) end
  return pandoc.Inlines{ pandoc.Str(str(v)) }
end

local function cell(v) return { pandoc.Plain(inlines(v)) } end

local function is_todo(v) return v == nil or str(v):match("^TODO") end

return {
  ["courses-taught"] = function(args, kwargs, meta)
    local rows = {}
    for _, c in ipairs(meta["current-courses"] or {}) do
      table.insert(rows, { cell(meta.term), cell(c.code), cell(c.title) })
    end
    for _, c in ipairs(meta["past-courses"] or {}) do
      local code = is_todo(c.code) and "" or c.code
      table.insert(rows, { cell(c.term), cell(code), cell(c.title) })
    end
    local header = { cell("Term"), cell("Course"), cell("Title") }
    return pandoc.utils.from_simple_table(pandoc.SimpleTable(
      {}, { pandoc.AlignDefault, pandoc.AlignDefault, pandoc.AlignDefault },
      { 0, 0, 0 }, header, rows))
  end,

  ["contact"] = function(args, kwargs, meta)
    local p = meta.person
    local items = {}
    local function add(label, value, url)
      if value == nil then return end
      local inl = pandoc.Inlines{ pandoc.Strong(label), pandoc.Str(":"), pandoc.Space() }
      if url then inl:insert(pandoc.Link(str(value), url)) else inl:extend(inlines(value)) end
      table.insert(items, { pandoc.Plain(inl) })
    end
    add("Email", p["personal-email"] or p.email, "mailto:" .. str(p["personal-email"] or p.email))
    add("Office", p.office)
    for _, l in ipairs(p.links or {}) do add(str(l.label), str(l.url), str(l.url)) end
    return pandoc.BulletList(items)
  end,
}
