// The site's small bits of behaviour: the settings pop-over (light/dark, spoilers), foldable callouts, the menu on small screens,
// highlighting the current heading in the table of contents, and the filterable tables.
(function () {
  // settings pop-over (the gear icon): appearance (light / dark / auto) and spoilers
  var get = function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } };
  var put = function (k, v) { try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) {} };
  var gear = document.querySelector(".site-settings-toggle");
  var panel = document.querySelector(".site-settings");
  var dark = matchMedia("(prefers-color-scheme: dark)");
  var applyTheme = function () {
    var t = get("theme") || (dark.matches ? "dark" : "light");
    [document.documentElement, document.body].forEach(function (el) {   // on <html> too, for the page's own scrollbar
      el.classList.toggle("theme-dark", t === "dark");
      el.classList.toggle("theme-light", t !== "dark");
    });
  };
  dark.addEventListener && dark.addEventListener("change", function () { if (!get("theme")) applyTheme(); });
  var settingValue = function (name) {
    if (name === "theme") return get("theme") || "auto";
    return get("spoilers") || "hide";
  };
  var mark = function () {
    if (!panel) return;
    panel.querySelectorAll(".site-setting").forEach(function (row) {
      var v = settingValue(row.dataset.setting);
      row.querySelectorAll(".site-setting-option").forEach(function (b) {
        b.classList.toggle("is-active", b.dataset.value === v);
        b.setAttribute("aria-pressed", b.dataset.value === v ? "true" : "false");
      });
    });
  };
  var openPanel = function (open) {
    if (!panel) return;
    panel.hidden = !open;
    gear.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) mark();
  };
  if (gear && panel) {
    gear.addEventListener("click", function (e) { e.stopPropagation(); openPanel(panel.hidden); });
    panel.addEventListener("click", function (e) {
      var b = e.target.closest(".site-setting-option");
      if (!b) return;
      var name = b.closest(".site-setting").dataset.setting;
      if (name === "theme") { put("theme", b.dataset.value === "auto" ? null : b.dataset.value); applyTheme(); }
      else if (name === "spoilers") {
        put("spoilers", b.dataset.value === "show" ? "show" : null);
        document.documentElement.classList.toggle("show-spoilers", b.dataset.value === "show");
      }
      mark();
    });
    document.addEventListener("click", function (e) {
      if (!panel.hidden && !e.target.closest(".site-settings, .site-settings-toggle")) openPanel(false);
    });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !panel.hidden) { openPanel(false); gear.focus(); } });
  }

  // spoilers (the GM sections of the adventure type pages): click to show
  // anywhere on the blurred block shows it (the button is there for keyboards and as the label)
  document.querySelectorAll(".covalon-spoiler").forEach(function (box) {
    box.addEventListener("click", function () {
      if (box.classList.contains("is-revealed") || document.documentElement.classList.contains("show-spoilers")) return;
      box.classList.add("is-revealed");
    });
  });

  // the outline ("On this page"): fade the list's top / bottom edge while there's more to scroll that way
  document.querySelectorAll(".site-toc-list").forEach(function (bar) {
    var edges = function () {
      bar.classList.toggle("has-more-above", bar.scrollTop > 1);
      bar.classList.toggle("has-more-below", bar.scrollTop + bar.clientHeight < bar.scrollHeight - 1);
    };
    bar.addEventListener("scroll", edges, { passive: true });
    window.addEventListener("resize", edges);
    edges();
    setTimeout(edges, 0);   // after the current page / heading has been scrolled into view
  });

  // breadcrumbs: a shadow under them once the page scrolls beneath them
  var crumbs = document.querySelector(".site-breadcrumbs");
  if (crumbs) {
    var stuck = function () { crumbs.classList.toggle("is-stuck", window.scrollY > 0 && crumbs.getBoundingClientRect().top <= 0.5); };
    window.addEventListener("scroll", stuck, { passive: true });
    stuck();
  }

  // menu (small screens)
  var menu = document.querySelector(".site-menu-button");
  if (menu) menu.addEventListener("click", function () { document.body.classList.toggle("menu-open"); });
  document.addEventListener("click", function (e) {
    if (document.body.classList.contains("menu-open") && !e.target.closest(".site-left, .site-menu-button"))
      document.body.classList.remove("menu-open");
  });

  // foldable callouts: > [!note]- Title
  document.querySelectorAll(".callout.is-collapsible > .callout-title").forEach(function (title) {
    title.addEventListener("click", function (e) {
      if (e.target.closest("a")) return;
      title.parentElement.classList.toggle("is-collapsed");
    });
  });

  // keep the current page visible in the file tree
  var active = document.querySelector(".site-tree .is-active");
  // (scrolls only the sidebar: scrollIntoView would also scroll the page itself, so some pages
  // opened a little way down)
  var scrollWithin = function (el, box, center, margin) {
    if (!el || !box) return;
    margin = margin || 0;   // keep this far from the edges (e.g. clear of the outline's faded ends)
    var top = el.getBoundingClientRect().top - box.getBoundingClientRect().top + box.scrollTop;
    if (center) box.scrollTop = top - box.clientHeight / 2 + el.offsetHeight / 2;
    else if (top - margin < box.scrollTop) box.scrollTop = top - margin;
    else if (top + el.offsetHeight + margin > box.scrollTop + box.clientHeight) box.scrollTop = top + el.offsetHeight + margin - box.clientHeight;
  };
  if (active) scrollWithin(active, active.closest(".site-sidebar"), true);

  // table of contents: highlight the heading being read
  var links = Array.prototype.slice.call(document.querySelectorAll(".site-toc a"));
  if (links.length && "IntersectionObserver" in window) {
    var byId = {};
    links.forEach(function (a) { byId[decodeURIComponent(a.getAttribute("href").slice(1))] = a; });
    var heads = Object.keys(byId).map(function (id) { return document.getElementById(id); }).filter(Boolean);
    var current = null;
    var observer = new IntersectionObserver(function () {
      var top = null;
      heads.forEach(function (h) { if (h.getBoundingClientRect().top < 120) top = h; });
      var link = top ? byId[top.id] : null;
      if (link !== current) {
        if (current) current.classList.remove("is-active");
        if (link) { link.classList.add("is-active"); scrollWithin(link, link.closest(".site-toc-list"), false, 40); }
        current = link;
      }
    }, { rootMargin: "0px 0px -70% 0px", threshold: [0, 1] });
    heads.forEach(function (h) { observer.observe(h); });
  }

  // filterable tables (the Bases tables): a filter box, and headers that sort on click
  document.querySelectorAll(".covalon-filterable").forEach(function (wrap) {
    var table = wrap.querySelector("table");
    if (!table) return;
    var heads = Array.prototype.slice.call(table.querySelectorAll("thead th"));
    var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
    var cellText = function (tr, i) { return ((tr.children[i] || {}).textContent || "").trim(); };

    var bar = document.createElement("div");
    bar.className = "covalon-filter-bar";
    var text = document.createElement("input");
    text.type = "search";
    text.placeholder = "Filter " + rows.length + " entries…";
    bar.appendChild(text);

    var count = document.createElement("span");
    count.className = "covalon-filter-count";
    bar.appendChild(count);

    var apply = function () {
      var q = text.value.trim().toLowerCase();
      var shown = 0;
      rows.forEach(function (tr) {
        var ok = !q || tr.textContent.toLowerCase().indexOf(q) >= 0;
        tr.hidden = !ok;
        if (ok) shown++;
      });
      count.textContent = shown === rows.length ? "" : shown + " of " + rows.length;
    };
    text.addEventListener("input", apply);

    var tbody = table.querySelector("tbody");
    heads.forEach(function (th, i) {
      th.classList.add("covalon-sortable");
      th.addEventListener("click", function () {
        var dir = th.dataset.sort === "asc" ? "desc" : "asc";
        heads.forEach(function (h) { delete h.dataset.sort; });
        th.dataset.sort = dir;
        var key = function (tr) { return cellText(tr, i).replace(/^the /i, ""); };
        rows.sort(function (a, b) { return key(a).localeCompare(key(b), undefined, { numeric: true }) * (dir === "asc" ? 1 : -1); });
        rows.forEach(function (tr) { tbody.appendChild(tr); });
      });
    });
    wrap.insertBefore(bar, wrap.firstChild);

    // tables taller than the screen scroll inside their box (see site.css)
    var scroller = table.closest(".table-wrapper");
    if (scroller) scroller.parentElement.classList.add("covalon-table-box");
  });
})();
