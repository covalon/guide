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
    if (name === "width") return get("width") || "readable";
    if (name === "textSize") return get("textSize") || "default";
    if (name === "fonts") return get("fonts") === "serif" ? "serif" : "sans";
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
      else if (name === "textSize") {
        put("textSize", b.dataset.value === "default" ? null : b.dataset.value);
        ["small", "large", "larger"].forEach(function (t) { document.documentElement.classList.toggle("text-" + t, b.dataset.value === t); });
      }
      else if (name === "fonts") {   // serif: add the original guide's fonts (see SERIF_SNIPPET in build.py)
        var serif = b.dataset.value === "serif";
        put("fonts", serif ? "serif" : null);
        var fl = document.getElementById("serif-fonts");
        if (serif && !fl) {
          fl = document.createElement("link");
          fl.rel = "stylesheet"; fl.id = "serif-fonts"; fl.href = document.documentElement.dataset.serifFonts;
          document.head.appendChild(fl);
        } else if (!serif && fl) fl.remove();
      }
      else if (name === "width") {
        put("width", b.dataset.value === "wide" ? "wide" : null);
        document.documentElement.classList.toggle("wide-mode", b.dataset.value === "wide");
      }
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

  // small screens: an app bar at the bottom with Menu (the file tree, search and settings) and On this page
  // (the outline). Each opens its panel from the bottom; its button again closes it, the other button swaps
  // to the other panel, so only one is open at a time. While a panel is open the page itself doesn't scroll.
  // (on medium screens, where the outline has no column of its own, a tab on the right edge opens it
  // from the side instead; it uses the same "outline" panel)
  var appButtons = Array.prototype.slice.call(document.querySelectorAll(".site-appbar-button, .site-outline-tab"));
  var openPanel = null;
  var setPanel = function (name) {
    openPanel = name;
    document.body.classList.toggle("panel-menu", name === "menu");
    document.body.classList.toggle("panel-outline", name === "outline");
    document.documentElement.classList.toggle("panel-open", !!name);
    appButtons.forEach(function (b) { b.setAttribute("aria-expanded", b.dataset.panel === name ? "true" : "false"); });
    if (name === "outline") {   // show the heading being read
      var here = document.querySelector(".site-toc a.is-active");
      if (here) scrollWithin(here, here.closest(".site-toc-list"), true);
    }
  };
  appButtons.forEach(function (b) {
    b.addEventListener("click", function (e) { e.stopPropagation(); setPanel(openPanel === b.dataset.panel ? null : b.dataset.panel); });
  });
  document.addEventListener("click", function (e) {   // a tap outside the panel closes it
    if (openPanel && !e.target.closest(".site-left, .site-right, .site-appbar, .site-outline-tab, .site-settings, .covalon-search-overlay")) setPanel(null);
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && openPanel) setPanel(null); });
  document.querySelectorAll(".site-toc a").forEach(function (a) {   // picking a heading closes the outline
    a.addEventListener("click", function () { if (openPanel === "outline") setPanel(null); });
  });
  var searchField = document.querySelector(".site-search input");
  if (searchField) searchField.addEventListener("focus", function () { if (openPanel) setPanel(null); });
  // a panel that no longer applies at the new size (e.g. turning a tablet) closes
  ["(min-width: 761px)", "(min-width: 1101px)"].forEach(function (q) { matchMedia(q).addEventListener("change", function () { setPanel(null); }); });

  // foldable callouts: > [!note]- Title
  document.querySelectorAll(".callout.is-collapsible > .callout-title").forEach(function (title) {
    title.addEventListener("click", function (e) {
      if (e.target.closest("a")) return;
      title.parentElement.classList.toggle("is-collapsed");
    });
  });

  // file tree: a folder's name opens its overview, and the folder stays open there (it would otherwise
  // fold shut as the summary is clicked, just before the new page loads)
  // (on small screens the name just folds / unfolds the folder, like its arrow: the overview is the
  // folder's first item anyway)
  var small = matchMedia("(max-width: 760px)");
  document.querySelectorAll(".tree-folder-link").forEach(function (a) {
    a.addEventListener("click", function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey) return;
      e.preventDefault();
      if (small.matches) { var d = a.closest("details"); d.open = !d.open; return; }
      a.closest("details").open = true;
      location.href = a.href;
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

  // table of contents: highlight the heading being read. A heading counts as reached once it passes a
  // line near the top of the window. The last few sections are too short to ever reach that line, so over
  // the last screen of scrolling the line slides down to the bottom of the window: each of them lights up in
  // turn, the last one at the very bottom, and the outline scrolls along to its end.
  var links = Array.prototype.slice.call(document.querySelectorAll(".site-toc a"));
  if (links.length) {
    var byId = {};
    links.forEach(function (a) { byId[decodeURIComponent(a.getAttribute("href").slice(1))] = a; });
    var heads = Object.keys(byId).map(function (id) { return document.getElementById(id); }).filter(Boolean);
    var tocList = links[0].closest(".site-toc-list");
    var current = null, queued = false;
    var READ_LINE = 120;
    var update = function () {
      queued = false;
      var view = window.innerHeight;
      var left = document.documentElement.scrollHeight - view - window.scrollY;   // scrolling still to go
      var line = left < view ? READ_LINE + (view - READ_LINE) * (1 - Math.max(0, left) / view) : READ_LINE;
      var top = null;
      heads.forEach(function (h) { if (h.getBoundingClientRect().top < line) top = h; });
      var link = top ? byId[top.id] : null;
      if (link !== current) {
        if (current) current.classList.remove("is-active");
        if (link) { link.classList.add("is-active"); scrollWithin(link, tocList, false, 40); }
        current = link;
      }
      if (tocList && left <= 2) tocList.scrollTop = tocList.scrollHeight;   // at the very end: the outline's end too
    };
    var queue = function () { if (!queued) { queued = true; requestAnimationFrame(update); } };
    window.addEventListener("scroll", queue, { passive: true });
    window.addEventListener("resize", queue);
    update();
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
    text.placeholder = "Filter " + rows.length + " entries…  (-word to leave out, \"word\" for whole words)";
    bar.appendChild(text);

    var count = document.createElement("span");
    count.className = "covalon-filter-count";
    bar.appendChild(count);

    // the filter box: every word has to be in the row; -word leaves out rows with it; "quotes" match a
    // whole word or phrase only (so "holy" doesn't match unholy); -"holy" leaves out rows with the word holy
    var escRe = function (t) { return t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); };
    var terms = function (q) {
      var out = [], m, re = /(-?)(?:"([^"]*)"?|(\S+))/g;
      while ((m = re.exec(q))) {
        var t = (m[2] !== undefined ? m[2] : m[3] || "").trim().toLowerCase();
        if (!t) continue;
        out.push({ not: !!m[1] && t !== "", test: m[2] !== undefined
          ? (function (w) { return function (s) { return w.test(s); }; })(new RegExp("(^|[^\\p{L}\\p{N}])" + escRe(t) + "($|[^\\p{L}\\p{N}])", "u"))
          : (function (w) { return function (s) { return s.indexOf(w) >= 0; }; })(t) });
      }
      return out;
    };
    var apply = function () {
      var want = terms(text.value);
      var shown = 0;
      rows.forEach(function (tr) {
        var row = tr.textContent.toLowerCase();
        var ok = want.every(function (t) { return t.test(row) !== t.not; });
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
        var key = function (tr) { return cellText(tr, i).replace(/^(the )?(kingdom of )?/i, ""); };
        rows.sort(function (a, b) { return key(a).localeCompare(key(b), undefined, { numeric: true }) * (dir === "asc" ? 1 : -1); });
        rows.forEach(function (tr) { tbody.appendChild(tr); });
      });
    });
    wrap.insertBefore(bar, wrap.firstChild);

    // tables taller than the screen scroll inside their box (see site.css)
    var scroller = table.closest(".table-wrapper");
    if (scroller) {
      var box = scroller.parentElement;
      box.classList.add("covalon-table-box");
      // a slight shadow under the pinned header row once rows are scrolling beneath it
      var pinned = function () { box.classList.toggle("is-scrolled", scroller.scrollTop > 0); };
      scroller.addEventListener("scroll", pinned, { passive: true });
      pinned();
    }
  });
})();

// Lightbox: click a picture in the text to see it large, over the page. ← / → (or the buttons) step
// through the page's pictures, clicking the big picture zooms to its full size (drag or scroll to look
// around), and Esc, the × button or a click beside the picture closes it.
(function () {
  var pics = Array.prototype.filter.call(document.querySelectorAll(".markdown-rendered img"), function (img) {
    return !img.closest("a") && !/logo/i.test(img.getAttribute("src") || "");
  });
  if (!pics.length) return;
  var el = function (tag, cls) { var e = document.createElement(tag); e.className = cls; return e; };
  var box = el("div", "covalon-lightbox");
  box.hidden = true;
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");
  box.setAttribute("aria-label", "Picture");
  var stage = el("div", "covalon-lightbox-stage");
  var big = el("img", "covalon-lightbox-img");
  var caption = el("div", "covalon-lightbox-caption");
  var count = el("span", "covalon-lightbox-count");
  var text = el("span", "covalon-lightbox-text");
  caption.appendChild(text);
  caption.appendChild(count);
  var button = function (cls, label, glyph) {
    var b = el("button", "covalon-lightbox-button " + cls);
    b.type = "button"; b.title = label; b.setAttribute("aria-label", label); b.textContent = glyph;
    return b;
  };
  var close = button("is-close", "Close (Esc)", "×");
  var prev = button("is-prev", "Previous picture (←)", "‹");
  var next = button("is-next", "Next picture (→)", "›");
  stage.appendChild(big);
  [stage, caption, close, prev, next].forEach(function (e) { box.appendChild(e); });
  document.body.appendChild(box);

  var at = 0, lastFocus = null;
  var show = function (i) {
    at = (i + pics.length) % pics.length;
    var img = pics[at];
    var fig = img.closest("figure");
    var cap = fig && fig.querySelector("figcaption");
    box.classList.remove("is-zoomed");
    big.src = img.currentSrc || img.src;
    big.alt = img.alt || "";
    text.textContent = cap ? cap.textContent : (img.alt && !/\.(webp|png|jpe?g|gif|avif)$/i.test(img.alt) ? img.alt : "");
    count.textContent = pics.length > 1 ? (at + 1) + " / " + pics.length : "";
    caption.hidden = !text.textContent && !count.textContent;
    prev.hidden = next.hidden = pics.length < 2;
  };
  var open = function (i) {
    lastFocus = document.activeElement;
    show(i);
    box.hidden = false;
    document.documentElement.classList.add("lightbox-open");
    close.focus();
  };
  var shut = function () {
    if (box.hidden) return;
    box.hidden = true;
    big.removeAttribute("src");
    document.documentElement.classList.remove("lightbox-open");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  };
  // zoom only helps when the picture is bigger than it's shown
  var canZoom = function () { return big.naturalWidth > big.clientWidth + 8 || big.naturalHeight > big.clientHeight + 8; };
  big.addEventListener("load", function () { box.classList.toggle("can-zoom", canZoom()); });

  pics.forEach(function (img, i) {
    img.classList.add("covalon-zoomable");
    img.tabIndex = 0;
    img.setAttribute("role", "button");
    img.setAttribute("aria-label", "View larger" + (img.alt ? ": " + img.alt : ""));
    img.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); open(i); });
    img.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(i); } });
  });
  close.addEventListener("click", shut);
  prev.addEventListener("click", function () { show(at - 1); });
  next.addEventListener("click", function () { show(at + 1); });
  big.addEventListener("click", function (e) {
    e.stopPropagation();
    if (box.classList.contains("is-zoomed")) { box.classList.remove("is-zoomed"); return; }
    if (!box.classList.contains("can-zoom")) return;
    // zoom in on the spot that was clicked
    var r = big.getBoundingClientRect(), fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
    box.classList.add("is-zoomed");
    stage.scrollLeft = fx * big.naturalWidth - stage.clientWidth / 2;
    stage.scrollTop = fy * big.naturalHeight - stage.clientHeight / 2;
  });
  // drag to look around a zoomed picture
  var drag = null;
  stage.addEventListener("pointerdown", function (e) {
    if (!box.classList.contains("is-zoomed") || e.pointerType !== "mouse") return;
    drag = { x: e.clientX, y: e.clientY, l: stage.scrollLeft, t: stage.scrollTop, moved: false };
  });
  window.addEventListener("pointermove", function (e) {
    if (!drag) return;
    var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) drag.moved = true;
    stage.scrollLeft = drag.l - dx; stage.scrollTop = drag.t - dy;
  });
  window.addEventListener("pointerup", function () { if (drag && drag.moved) big.addEventListener("click", swallow, { capture: true, once: true }); drag = null; });
  var swallow = function (e) { e.stopPropagation(); e.preventDefault(); };
  stage.addEventListener("click", function (e) { if (e.target === stage && !box.classList.contains("is-zoomed")) shut(); });
  box.addEventListener("click", function (e) { if (e.target === box) shut(); });
  document.addEventListener("keydown", function (e) {
    if (box.hidden) return;
    if (e.key === "Escape") { e.stopPropagation(); shut(); }
    else if (e.key === "ArrowLeft" && pics.length > 1) show(at - 1);
    else if (e.key === "ArrowRight" && pics.length > 1) show(at + 1);
    else if (e.key === "Tab") {   // keep the keyboard inside the lightbox
      var stops = [close, prev, next].filter(function (b) { return !b.hidden; });
      var i = stops.indexOf(document.activeElement);
      e.preventDefault();
      stops[(i + (e.shiftKey ? -1 : 1) + stops.length) % stops.length].focus();
    }
  }, true);
})();


// Copy buttons: every code block gets one (e.g. the Covalon Module's manifest URL, written as a code block
// so Obsidian offers its own copy button too). A short "Copied" notice confirms it.
(function () {
  var blocks = document.querySelectorAll(".markdown-rendered pre");
  var ICON_COPY = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>';
  var ICON_DONE = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';
  var toast = null, toastTimer = null;
  var notify = function (text, failed) {
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "covalon-toast";
      toast.setAttribute("role", "status");
      toast.setAttribute("aria-live", "polite");
      document.body.appendChild(toast);
    }
    toast.innerHTML = (failed ? "" : ICON_DONE) + "<span></span>";
    toast.lastChild.textContent = text;
    toast.classList.toggle("is-failed", !!failed);
    toast.classList.remove("is-shown");
    void toast.offsetWidth;   // restart the fade when copying twice in a row
    toast.classList.add("is-shown");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove("is-shown"); }, 2200);
  };
  var copyText = function (text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (ok, fail) {   // older browsers, or the site opened from a file
      var area = document.createElement("textarea");
      area.value = text; area.setAttribute("readonly", ""); area.style.position = "fixed"; area.style.opacity = "0";
      document.body.appendChild(area); area.select();
      var done = false;
      try { done = document.execCommand("copy"); } catch (e) {}
      area.remove();
      done ? ok() : fail();
    });
  };
  // Heading links: a small link icon beside each heading (shown on hover, faintly always on touch screens)
  // copies the address of that heading, e.g. to point someone at a rule in Discord.
  var ICON_LINK = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>';
  document.querySelectorAll(".markdown-rendered :is(h1, h2, h3, h4, h5, h6)[id]").forEach(function (h) {
    if (h.closest(".callout, .covalon-search, .site-toc")) return;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "covalon-heading-link";
    b.innerHTML = ICON_LINK;
    b.title = "Copy a link to this heading";
    b.setAttribute("aria-label", "Copy a link to “" + h.textContent.trim() + "”");
    b.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      var url = location.href.split("#")[0] + "#" + encodeURIComponent(h.id);
      copyText(url).then(function () {
        try { history.replaceState(null, "", "#" + encodeURIComponent(h.id)); } catch (err) {}
        notify("Link to “" + h.textContent.trim() + "” copied");
      }, function () { notify("Couldn't copy the link", true); });
    });
    h.appendChild(b);
  });

  blocks.forEach(function (pre) {
    var code = pre.querySelector("code") || pre;
    var wrap = document.createElement("div");
    wrap.className = "covalon-code";
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(pre);
    var b = document.createElement("button");
    b.type = "button";
    b.className = "covalon-copy";
    b.innerHTML = ICON_COPY + "<span>Copy</span>";
    b.title = "Copy to clipboard";
    b.addEventListener("click", function () {
      copyText(code.textContent.replace(/\n$/, "")).then(function () {
        b.innerHTML = ICON_DONE + "<span>Copied</span>";
        b.classList.add("is-done");
        setTimeout(function () { b.innerHTML = ICON_COPY + "<span>Copy</span>"; b.classList.remove("is-done"); }, 2000);
        notify("Copied to clipboard");
      }, function () { notify("Couldn't copy — select the text and copy it instead", true); });
    });
    wrap.appendChild(b);
  });
})();


// ||inline spoilers||: hidden until clicked (or Enter / Space); Settings → Spoilers → Shown shows them all
(function () {
  document.querySelectorAll(".covalon-inline-spoiler").forEach(function (sp) {
    var reveal = function (e) {
      if (sp.classList.contains("is-revealed") || document.documentElement.classList.contains("show-spoilers")) return;
      e.preventDefault();
      e.stopPropagation();   // the first click only uncovers it (a link inside works on the next click)
      sp.classList.add("is-revealed");
      sp.removeAttribute("role");
      sp.removeAttribute("tabindex");
      sp.removeAttribute("aria-label");
    };
    sp.addEventListener("click", reveal, true);
    sp.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") reveal(e); });
  });
})();
