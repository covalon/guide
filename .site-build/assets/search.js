// Search: a pop-over over the page (click the sidebar's search box, or press Ctrl/⌘ K or /), also shown
// inline on the Advanced Search page. Built on Pagefind's search index (the pagefind/ folder, created
// after the site is built; see build-local.sh), in the style of the Archives of Nethys' advanced search:
// a search box, a page type, "Add filter" rows (property · is / is not · value), and sort order.
(function () {
  var root = document.documentElement.getAttribute("data-root") || "";   // the site's root, relative to this page
  var pagefind = null;
  var loading = null;
  var load = function () {
    if (pagefind) return Promise.resolve(pagefind);
    if (!loading) loading = import(new URL(root + "pagefind/pagefind.js", document.baseURI).href).then(function (pf) {
      pagefind = pf;
      // result links are relative to the site's root, wherever the site is hosted (e.g. under /covalon/)
      return Promise.resolve(pf.options && pf.options({ baseUrl: new URL(root || "./", document.baseURI).pathname }))
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
    var field = el("div", "covalon-search-field");
    field.appendChild(input);
    var suggest = el("ul", "covalon-search-suggest");
    suggest.hidden = true;
    suggest.setAttribute("role", "listbox");
    field.appendChild(suggest);
    top.appendChild(field);
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
    var tips = el("a", "covalon-search-tips", "Search tips");
    tips.href = root + "how-to-search/";
    bar.appendChild(typeSel);
    bar.appendChild(add);
    bar.appendChild(tips);
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
    // Terms joined by OR (in capitals, like Obsidian) match pages that have any of them:
    // [domains:air] OR [alternate domains:air]. Everything else must all match.
    var parseBox = function () {
      var v = input.value, terms = [], m;
      PROP.lastIndex = 0;
      while ((m = PROP.exec(v))) terms.push({ m: m, start: m.index, end: m.index + m[0].length });
      // the OR between two terms (and nothing else between them) joins them into one group
      var joined = terms.map(function (t, i) { return i > 0 && !t.m[1] && !terms[i - 1].m[1] && /^\s+OR\s+$/.test(v.slice(terms[i - 1].end, t.start)); });
      var words = v;
      for (var i = terms.length - 1; i >= 0; i--) {
        var from = joined[i] ? terms[i - 1].end : terms[i].start;
        words = words.slice(0, from) + " " + words.slice(terms[i].end);
      }
      words = words.replace(/\s+/g, " ").trim();
      var matches = function (t) {
        var want = t.m[2].trim().toLowerCase(), text = (t.m[4] || "").trim().toLowerCase();
        var whole = t.m[3] === '"' && text ? new RegExp("(^|[^\\p{L}\\p{N}])" + text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "($|[^\\p{L}\\p{N}])", "u") : null;
        var out = [];
        Object.keys(allFilters).filter(function (k) { return k.replace(/^~/, "").toLowerCase() === want; }).forEach(function (k) {
          present(allFilters[k]).forEach(function (val) {
            var lv = val.toLowerCase();
            if (!text || (whole ? whole.test(lv) : lv.indexOf(text) >= 0)) { var f = {}; f[k] = val; out.push(f); }
          });
        });
        return out;
      };
      var all = [], none = [], group = null;
      terms.forEach(function (t, i) {
        if (joined[i] && group) group.push.apply(group, matches(t));
        else {
          group = matches(t);
          (t.m[1] ? none : all).push(group);
        }
      });
      var tidy = function (any) {
        if (!any.length) return { "~nothing": "~nothing" };   // no such property or value: no results
        return any.length === 1 ? any[0] : { any: any };
      };
      return { words: words, all: all.map(tidy), none: none.map(function (g) { return g.length ? tidy(g) : null; }).filter(Boolean) };
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

    // before anything is searched: a few quick tips, with examples to try (the full guide is behind "Search tips" above)
    var EXAMPLES = [
      ["dragon", "words anywhere on a page"],
      ["[soul seed:air]", "a property that contains a value"],
      ['[divine sanctification:"holy"]', "a whole word only"],
      ["dragon OR fey", "either word"],
      ["[domains:air] OR [alternate domains:air]", "either of two properties"],
      ["[domains:fire] -[domains:sun]", "leave some out"],
    ];
    var showTips = function () {
      list.innerHTML = "";
      var li = el("li", "covalon-search-help");
      li.appendChild(el("p", "covalon-search-help-intro", "Type to search every page, or try one of these (type [ for property suggestions):"));
      var ul = el("ul", "covalon-search-examples");
      EXAMPLES.forEach(function (x) {
        var item = el("li");
        var b = el("button", "covalon-search-example");
        b.type = "button";
        b.appendChild(el("code", "", x[0]));
        b.addEventListener("click", function () { input.value = x[0]; input.focus(); go(); });
        item.appendChild(b);
        item.appendChild(el("span", "covalon-search-example-note", x[1]));
        ul.appendChild(item);
      });
      li.appendChild(ul);
      list.appendChild(li);
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
      if (!any) { showTips(); status.textContent = ""; available = {}; rows.forEach(function (r) { fillProps(r); fillValues(r); }); return; }
      // words joined by OR (in capitals): one search for each side, merged, e.g. dragon OR air
      var alternatives = term ? term.split(/\s+OR\s+/).map(function (t) { return t.trim(); }).filter(Boolean) : [];
      if (!alternatives.length) alternatives = [null];
      var many = alternatives.length > 1;
      load().then(function (pf) {
        var o = { filters: filters };
        if (sortSel.value) o.sort = { title: sortSel.value };
        return Promise.all(alternatives.map(function (t) { return pf.search(t, o); }));
      }).then(function (found) {
        if (mine !== seq || !found || !found[0]) return;
        var res = found[0];
        if (many) {   // pages found by several alternatives rank higher; each keeps its own highlighted snippet
          var byId = {}, merged = [];
          available = {};
          found.forEach(function (r) {
            Object.keys(r.filters || {}).forEach(function (k) {
              available[k] = available[k] || {};
              Object.keys(r.filters[k]).forEach(function (v) { available[k][v] = Math.max(available[k][v] || 0, r.filters[k][v]); });
            });
            r.results.forEach(function (x) {
              if (byId[x.id]) byId[x.id].score += x.score || 0;
              else { byId[x.id] = { id: x.id, score: x.score || 0, data: x.data }; merged.push(byId[x.id]); }
            });
          });
          merged.sort(function (a, b) { return b.score - a.score; });
          res = { results: merged };
        } else available = res.filters || {};
        rows.forEach(function (r) { fillProps(r); fillValues(r); });
        status.textContent = res.results.length ? res.results.length + (res.results.length === 1 ? " result" : " results") : "No results";
        list.innerHTML = "";
        var sorted = many && sortSel.value;   // merged results sorted by title need every page's title first
        return Promise.all(res.results.slice(0, sorted ? 300 : 40).map(function (r) { return r.data(); })).then(function (data) {
          if (mine !== seq) return;
          if (sorted) {
            var key = function (d) { return String(d.meta.title || "").replace(/^(the )?(kingdom of )?/i, ""); };
            data.sort(function (a, b) { return byName(key(a), key(b)) * (sortSel.value === "desc" ? -1 : 1); });
            data = data.slice(0, 40);
          }
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
    showTips();

    // autocomplete for [property:value]: typing "[" offers property names, and after the ":" that
    // property's values. ↑/↓ to pick, Enter or Tab to take it, Esc to close the list.
    var picks = [], active = 0, span = null;
    var names = function () {
      var seen = {};
      Object.keys(allFilters).forEach(function (k) { if (present(allFilters[k]).length) seen[k.replace(/^~/, "")] = true; });
      return Object.keys(seen).sort(byName);
    };
    // matches that start with what's typed come first, then ones that contain it
    var ranked = function (list, typed) {
      return list.filter(function (x) { return x.toLowerCase().indexOf(typed) >= 0; })
        .sort(function (a, b) { return (a.toLowerCase().indexOf(typed) !== 0) - (b.toLowerCase().indexOf(typed) !== 0) || byName(a, b); });
    };
    var hideSuggest = function () { suggest.hidden = true; picks = []; };
    var showSuggest = function () {
      var caret = input.selectionStart, before = input.value.slice(0, caret);
      var m = /(-?)\[([^\]:]*)(?::\s*("?)([^\]"]*))?$/.exec(before);
      if (!m) return hideSuggest();
      var start = m.index + m[1].length, typed = m[2].trim().toLowerCase();
      if (m[4] === undefined && before.slice(m.index).indexOf(":") < 0) {
        picks = ranked(names(), typed).slice(0, 8)
          .map(function (n) { return { label: n, text: "[" + n + ":", hint: "property" }; });
      } else {
        var want = typed, text = (m[4] || "").toLowerCase(), vals = {};
        Object.keys(allFilters).forEach(function (k) {
          if (k.replace(/^~/, "").toLowerCase() !== want) return;
          present(allFilters[k]).forEach(function (v) { vals[v] = (vals[v] || 0) + allFilters[k][v]; });
        });
        var name = names().filter(function (n) { return n.toLowerCase() === want; })[0] || m[2].trim();
        picks = ranked(Object.keys(vals), text).slice(0, 8)
          .map(function (v) { return { label: v, text: "[" + name + ":" + (m[3] ? '"' + v + '"' : v) + "]", hint: vals[v] + (vals[v] === 1 ? " page" : " pages") }; });
      }
      if (!picks.length) return hideSuggest();
      span = [start, caret];
      active = 0;
      suggest.innerHTML = "";
      picks.forEach(function (p, i) {
        var li = el("li", "covalon-search-suggestion" + (i === active ? " is-active" : ""));
        li.setAttribute("role", "option");
        li.appendChild(el("span", "", p.label));
        li.appendChild(el("span", "covalon-search-suggestion-hint", p.hint));
        li.addEventListener("mousedown", function (e) { e.preventDefault(); take(i); });
        suggest.appendChild(li);
      });
      suggest.hidden = false;
    };
    var mark = function () {
      Array.prototype.forEach.call(suggest.children, function (li, i) { li.classList.toggle("is-active", i === active); });
    };
    var take = function (i) {
      var p = picks[i];
      if (!p) return;
      var v = input.value, after = v.slice(span[1]).replace(/^[^\]\s]*\]?/, "");
      var tail = p.text.slice(-1) === "]" && !/^\s/.test(after) ? " " : "";
      input.value = v.slice(0, span[0]) + p.text + tail + after;
      var caret = span[0] + p.text.length + tail.length;
      input.setSelectionRange(caret, caret);
      input.focus();
      run();
      showSuggest();   // after a property name, go straight on to its values
    };
    input.addEventListener("input", showSuggest);
    input.addEventListener("click", showSuggest);
    input.addEventListener("blur", function () { setTimeout(hideSuggest, 100); });
    input.addEventListener("keydown", function (e) {
      if (suggest.hidden) return;
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        active = (active + (e.key === "ArrowDown" ? 1 : picks.length - 1)) % picks.length;
        mark();
      } else if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        take(active);
      } else if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();   // close the list, not the search
        hideSuggest();
      }
    });
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
    // the "page not found" page: search for the words of the address that wasn't found
    // (/guide/city/market-district/iruxi/ -> "iruxi")
    if (!q && inlineHost.hasAttribute("data-from-address")) {
      var parts = decodeURIComponent(location.pathname).split("/").filter(Boolean);
      q = (parts[parts.length - 1] || "").replace(/\.html?$/, "").replace(/[-_]+/g, " ").trim();
    }
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
