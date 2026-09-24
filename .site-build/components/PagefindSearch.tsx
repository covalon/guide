// Advanced search page (the "search" page): Pagefind's search box with filters for page type and
// properties. Pagefind builds its index after Quartz, in the site build (see README.md).
import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"

const PagefindSearch: QuartzComponent = ({ fileData }: QuartzComponentProps) => {
  if (fileData.slug !== "search") return null
  return <div id="pagefind-search" class="pagefind-search"></div>
}

PagefindSearch.afterDOMLoaded = `
document.addEventListener("nav", () => {
  const el = document.getElementById("pagefind-search")
  if (!el || el.dataset.mounted) return
  el.dataset.mounted = "true"
  const base = new URL(".", location.href)            // the site's root folder
  const mount = () => {
    new PagefindUI({
      element: "#pagefind-search",
      baseUrl: base.pathname,
      showSubResults: true,
      showImages: false,
      resetStyles: false,
      openFilters: ["Type"],
      translations: { placeholder: "Search the guides" },
      processResult: (r) => {
        const clean = (u) => u.replace(/\\.html(?=#|$)/, "")
        r.url = clean(r.url)
        for (const s of r.sub_results ?? []) s.url = clean(s.url)
        return r
      },
    })
  }
  if (window.PagefindUI) return mount()
  const css = document.createElement("link")
  css.rel = "stylesheet"
  css.href = new URL("pagefind/pagefind-ui.css", base).href
  document.head.appendChild(css)
  const js = document.createElement("script")
  js.src = new URL("pagefind/pagefind-ui.js", base).href
  js.onload = mount
  js.onerror = () => { el.textContent = "Search isn't available in this build (the search index is created when the site is published)." }
  document.head.appendChild(js)
})
`

PagefindSearch.css = `
.pagefind-search {
  margin-top: 1rem;
  --pagefind-ui-primary: var(--secondary);
  --pagefind-ui-text: var(--dark);
  --pagefind-ui-background: var(--light);
  --pagefind-ui-border: var(--lightgray);
  --pagefind-ui-tag: var(--highlight);
  --pagefind-ui-border-width: 1px;
  --pagefind-ui-border-radius: 6px;
  --pagefind-ui-font: inherit;
}
`

export default (() => PagefindSearch) satisfies QuartzComponentConstructor
