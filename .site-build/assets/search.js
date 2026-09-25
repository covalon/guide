// Search: a pop-over over the page (click the sidebar's search box, or press Ctrl/⌘ K or /), also shown
// inline on the Advanced Search page. Built on Pagefind's search index (the pagefind/ folder, created
// after the site is built; see build-local.sh), in the style of the Archives of Nethys' advanced search:
// a search box, a page type, "Add filter" rows (property · is / is not · value), and sort order.
(function () {
  var root = (document.querySelector('link[href$="assets/site.css"]') || { getAttribute: function () { return "assets/site.css"; } })
    .getAttribute("href").replace(/assets\/site\.css$/, "");
  var pagefind = null;
  var loading = null;
  var load = function () {
    if (pagefind) return Promise.resolve(pagefind);
    if (!loading) loading = import(new URL(root + "pagefind/pagefind.js", location.href).href).then(function (pf) {
      pagefind = pf;
      // result links are relative to the site's root, wherever the site is hosted (e.g. under /covalon/)
      return Promise.resolve(pf.options && pf.options({ baseUrl: new URL(root || "./", location.href).pathname }))
        .then(function () { if (pf.init) pf.init(); return pf; });
    });
    return loading;
  };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var el = function (tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  var byName = function (a, b) { return a.localeCompare(b, undefined, { numeric: true }); };
  // Pagefind lists every value with its count for the current search; keep the ones that occur
  var present = function (vals) { return Object.keys(vals || {}).filter(function (v) { return vals[v] > 0; }); };

  function mount(host, opts) {
    var ui = el("div", "covalon-search");
    var top = el("div", "covalon-search-top");
    var input = el("input", "covalon-search-input");
    input.type = "search";
    input.placeholder = "Search the guides…  e.g. fire [domains:sun] [soul seed:air]";
    input.setAttribute("aria-label", "Search the guides");
    top.appendChild(input);
    if (opts.onClose) {
      var close = el("button", "covalon-search-close", "Esc");
      close.type = "button";
      close.title = "Close search";
      close.addEventListener("click", opts.onClose);
      top.appendChild(close);
    }
    ui.appendChild(top);

    var bar = el("div", "covalon-search-options");
    var typeSel = el("select");
    typeSel.appendChild(new Option("All pages", ""));
    var sortSel = el("select");
    sortSel.appendChild(new Option("Sort: best match", ""));
    sortSel.appendChild(new Option("Sort: title A–Z", "asc"));
    sortSel.appendChild(new Option("Sort: title Z–A", "desc"));
    var add = el("button", "covalon-search-add", "+ Add filter");
    add.type = "button";
    bar.appendChild(typeSel);
    bar.appendChild(add);
    bar.appendChild(sortSel);
    ui.appendChild(bar);
    var rowsBox = el("div", "covalon-search-filters");
    ui.appendChild(rowsBox);
    var status = el("div", "covalon-search-status");
    ui.appendChild(status);
    var list = el("ol", "covalon-search-results");
    ui.appendChild(list);
    host.appendChild(ui);

    var allFilters = {};    // property -> {value: count}, across the whole site
    var typeFilters = {};   // the same, for the chosen page type (so "Add filter" offers that type's properties)
    var available = {};     // the same, for the current search (so drop-downs only offer values that match)
    var rows = [];

    var props = function () {
      var src = typeSel.value ? typeFilters : allFilters;
      return Object.keys(src).filter(function (k) { return k !== "Type" && k[0] !== "~" && present(src[k]).length; }).sort(byName);
    };
    var fillValues = function (row) {
      var keep = row.value.value;
      var base = typeSel.value ? typeFilters : allFilters;
      var src = (present(available[row.prop.value]).length ? available : base)[row.prop.value] || {};
      row.value.innerHTML = "";
      row.value.appendChild(new Option("any value", ""));
      present(src).sort(byName).forEach(function (v) { row.value.appendChild(new Option(v + " (" + src[v] + ")", v)); });
      if (keep && !(src[keep] > 0)) row.value.appendChild(new Option(keep + " (0)", keep));
      row.value.value = keep;
    };
    var fillProps = function (row) {
      var keep = row.prop.value;
      row.prop.innerHTML = "";
      var ks = props();
      if (keep && ks.indexOf(keep) < 0) ks.unshift(keep);
      ks.forEach(function (k) { row.prop.appendChild(new Option(k, k)); });
      if (keep) row.prop.value = keep;
    };
    var addRow = function (prop, value, negate) {
      var r = { box: el("div", "covalon-search-filter"), prop: el("select"), op: el("select"), value: el("select"), del: el("button", "", "×") };
      r.op.appendChild(new Option("is", ""));
      r.op.appendChild(new Option("is not", "not"));
      r.del.type = "button";
      r.del.title = "Remove this filter";
      [r.prop, r.op, r.value, r.del].forEach(function (e) { r.box.appendChild(e); });
      rowsBox.appendChild(r.box);
      rows.push(r);
      fillProps(r);
      if (prop) r.prop.value = prop;
      fillValues(r);
      if (value) r.value.value = value;
      if (negate) r.op.value = "not";
      r.prop.addEventListener("change", function () { r.value.value = ""; fillValues(r); run(); });
      r.op.addEventListener("change", run);
      r.value.addEventListener("change", run);
      r.del.addEventListener("click", function () { rows.splice(rows.indexOf(r), 1); r.box.remove(); run(); });
      return r;
    };

    // Obsidian-style property search in the search box: [soul seed:air] finds pages whose Soul Seed
    // contains "air"; in quotes, [divine sanctification:"holy"] matches the whole word only (so not
    // "unholy"); [domains] finds pages that have Domains at all; -[domains:fire] leaves them out.
    var PROP = /(-?)\[([^\]:]+)(?::\s*("?)([^\]"]*)\3)?\s*\]/g;
    var parseBox = function () {
      var words = input.value.replace(PROP, " ").replace(/\s+/g, " ").trim();
      var all = [], none = [], m;
      PROP.lastIndex = 0;
      while ((m = PROP.exec(input.value))) {
        var want = m[2].trim().toLowerCase(), text = (m[4] || "").trim().toLowerCase();
        var whole = m[3] === '"' && text ? new RegExp("(^|[^\\p{L}\\p{N}])" + text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "($|[^\\p{L}\\p{N}])", "u") : null;
        var keys = Object.keys(allFilters).filter(function (k) { return k.replace(/^~/, "").toLowerCase() === want; });
        var any = [];
        keys.forEach(function (k) {
          present(allFilters[k]).forEach(function (v) {
            var lv = v.toLowerCase();
            if (!text || (whole ? whole.test(lv) : lv.indexOf(text) >= 0)) { var f = {}; f[k] = v; any.push(f); }
          });
        });
        if (!any.length) any.push({ "~nothing": "~nothing" });   // no such property or value: no results
        (m[1] ? none : all).push(any.length === 1 ? any[0] : { any: any });
      }
      return { words: words, all: all, none: none };
    };

    var filtersNow = function (box) {
      var all = box.all.slice(), none = box.none.slice();
      if (typeSel.value) all.push({ Type: typeSel.value });
      rows.forEach(function (r) {
        if (!r.value.value) return;
        var f = {}; f[r.prop.value] = r.value.value;
        (r.op.value === "not" ? none : all).push(f);
      });
      var out = {};
      if (all.length) out.all = all;
      if (none.length) out.none = none;
      return out;
    };

    var seq = 0;
    var timer = null;
    var run = function () { clearTimeout(timer); timer = setTimeout(go, 120); };
    var go = function () {
      var mine = ++seq;
      var box = parseBox();
      var term = box.words;
      var filters = filtersNow(box);
      var any = term || Object.keys(filters).length;
      if (!any) { list.innerHTML = ""; status.textContent = ""; available = {}; rows.forEach(function (r) { fillProps(r); fillValues(r); }); return; }
      load().then(function (pf) {
        var o = { filters: filters };
        if (sortSel.value) o.sort = { title: sortSel.value };
        return pf.search(term || null, o);
      }).then(function (res) {
        if (mine !== seq || !res) return;
        available = res.filters || {};
        rows.forEach(function (r) { fillProps(r); fillValues(r); });
        status.textContent = res.results.length ? res.results.length + (res.results.length === 1 ? " result" : " results") : "No results";
        list.innerHTML = "";
        return Promise.all(res.results.slice(0, 40).map(function (r) { return r.data(); })).then(function (data) {
          if (mine !== seq) return;
          data.forEach(function (d) {
            var li = el("li", "covalon-search-result");
            var type = (d.filters && d.filters.Type || [])[0];
            li.innerHTML = '<a href="' + esc(d.url) + '"><span class="covalon-search-title">' + esc(d.meta.title || d.url) + "</span>"
              + (type ? '<span class="covalon-search-type">' + esc(type) + "</span>" : "") + "</a>"
              + (term ? '<p class="covalon-search-excerpt">' + d.excerpt + "</p>"
                 : d.meta.snippet ? '<p class="covalon-search-excerpt">' + esc(d.meta.snippet) + "</p>" : "");
            list.appendChild(li);
          });
          if (res.results.length > 40) list.appendChild(el("li", "covalon-search-more", "Showing the first 40. Add words or filters to narrow it down."));
        });
      }).catch(function () {
        status.textContent = "Search isn't available in this build: the search index is created when the site is published (or by build-local.sh).";
      });
    };

    input.addEventListener("input", run);
    typeSel.addEventListener("change", function () {
      var t = typeSel.value;
      if (!t) { typeFilters = {}; rows.forEach(function (r) { fillProps(r); fillValues(r); }); run(); return; }
      load().then(function (pf) { return pf.search(null, { filters: { Type: t } }); }).then(function (res) {
        if (typeSel.value !== t) return;
        typeFilters = (res && res.filters) || {};
        rows.forEach(function (r) { fillProps(r); fillValues(r); });
        run();
      }).catch(run);
    });
    sortSel.addEventListener("change", run);
    add.addEventListener("click", function () { var r = addRow(); r.prop.focus(); });

    load().then(function (pf) { return pf.filters(); }).then(function (f) {
      allFilters = f || {};
      Object.keys(allFilters.Type || {}).sort(byName).forEach(function (t) { typeSel.appendChild(new Option(t, t)); });
      rows.forEach(function (r) { fillProps(r); fillValues(r); });
    }).catch(function () {});

    return {
      input: input,
      search: function (q) { input.value = q || ""; go(); },
    };
  }

  // the pop-over
  var overlay = null, popover = null, lastFocus = null;
  var open = function (q) {
    if (!overlay) {
      overlay = el("div", "covalon-search-overlay");
      overlay.hidden = true;
      var panel = el("div", "covalon-search-panel");
      panel.setAttribute("role", "dialog");
      panel.setAttribute("aria-label", "Search");
      overlay.appendChild(panel);
      document.body.appendChild(overlay);
      popover = mount(panel, { onClose: close });
      overlay.addEventListener("mousedown", function (e) { if (e.target === overlay) close(); });
    }
    lastFocus = document.activeElement;
    overlay.hidden = false;
    document.documentElement.classList.add("search-open");
    if (q != null && q !== "") popover.search(q);
    popover.input.focus();
    popover.input.select();
  };
  var close = function () {
    if (!overlay || overlay.hidden) return;
    overlay.hidden = true;
    document.documentElement.classList.remove("search-open");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  };

  var inlineHost = document.getElementById("search");
  var inline = inlineHost ? mount(inlineHost, {}) : null;
  if (inline) {
    var q = new URLSearchParams(location.search).get("q");
    if (q) inline.search(q);
  }

  var form = document.querySelector(".site-search");
  if (form) {
    var field = form.querySelector("input");
    form.addEventListener("submit", function (e) { e.preventDefault(); open(field.value); field.value = ""; });
    field.addEventListener("focus", function () { if (!inline) { field.blur(); open(field.value); } });
    field.readOnly = !inline ? true : false;
    if (inline) field.addEventListener("input", function () { inline.search(field.value); });
  }
  document.addEventListener("keydown", function (e) {
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target || {}).tagName || "") || (e.target && e.target.isContentEditable);
    if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !typing)) {
      e.preventDefault();
      if (inline) inline.input.focus(); else open();
    } else if (e.key === "Escape") close();
  });
})();
