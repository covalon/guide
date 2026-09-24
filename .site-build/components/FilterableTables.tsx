// Filterable tables: tables from the vault's Bases (the 📍 overview pages) get a filter box,
// a drop-down for each column with a short list of values, and headers that sort on click.
import { QuartzComponent, QuartzComponentConstructor } from "./types"

const FilterableTables: QuartzComponent = () => null

FilterableTables.afterDOMLoaded = `
document.addEventListener("nav", () => {
  for (const wrap of document.querySelectorAll(".covalon-filterable")) {
    const table = wrap.querySelector("table")
    if (!table || wrap.dataset.enhanced) continue
    wrap.dataset.enhanced = "true"
    const heads = [...table.querySelectorAll("thead th")]
    const rows = [...table.querySelectorAll("tbody tr")]
    const cellText = (tr, i) => (tr.children[i]?.textContent ?? "").trim()
    const cellValues = (tr, i) => cellText(tr, i).split(/,\\s*/).filter(Boolean)

    const bar = document.createElement("div")
    bar.className = "covalon-filter-bar"
    const text = document.createElement("input")
    text.type = "search"
    text.placeholder = "Filter " + rows.length + " entries…"
    bar.appendChild(text)

    const selects = []
    heads.forEach((th, i) => {
      if (i === 0) return
      const values = [...new Set(rows.flatMap((tr) => cellValues(tr, i)))].sort((a, b) => a.localeCompare(b))
      if (values.length < 2 || values.length > 60) return
      const sel = document.createElement("select")
      sel.innerHTML = '<option value="">All ' + th.textContent.trim() + '</option>' +
        values.map((v) => '<option></option>').join("")
      values.forEach((v, k) => { sel.options[k + 1].value = v; sel.options[k + 1].textContent = v })
      selects.push([sel, i])
      bar.appendChild(sel)
    })

    const count = document.createElement("span")
    count.className = "covalon-filter-count"
    bar.appendChild(count)

    const apply = () => {
      const q = text.value.trim().toLowerCase()
      let shown = 0
      for (const tr of rows) {
        const ok = (!q || tr.textContent.toLowerCase().includes(q)) &&
          selects.every(([sel, i]) => !sel.value || cellValues(tr, i).includes(sel.value))
        tr.hidden = !ok
        if (ok) shown++
      }
      count.textContent = shown === rows.length ? "" : shown + " of " + rows.length
    }
    text.addEventListener("input", apply)
    selects.forEach(([sel]) => sel.addEventListener("change", apply))

    const tbody = table.querySelector("tbody")
    heads.forEach((th, i) => {
      th.classList.add("covalon-sortable")
      th.addEventListener("click", () => {
        const dir = th.dataset.sort === "asc" ? "desc" : "asc"
        heads.forEach((h) => delete h.dataset.sort)
        th.dataset.sort = dir
        const key = (tr) => cellText(tr, i).replace(/^the /i, "")
        rows.sort((a, b) => key(a).localeCompare(key(b), undefined, { numeric: true }) * (dir === "asc" ? 1 : -1))
        rows.forEach((tr) => tbody.appendChild(tr))
      })
    })

    wrap.insertBefore(bar, wrap.firstChild)
  }
})
`

FilterableTables.css = `
.covalon-filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  margin: 1rem 0 0.5rem;
}
.covalon-filter-bar input,
.covalon-filter-bar select {
  font: inherit;
  font-size: 0.9rem;
  padding: 0.3rem 0.5rem;
  border: 1px solid var(--lightgray);
  border-radius: 6px;
  background: var(--light);
  color: var(--darkgray);
}
.covalon-filter-bar input { flex: 1 1 12rem; }
.covalon-filter-count { font-size: 0.85rem; color: var(--gray); }
th.covalon-sortable { cursor: pointer; user-select: none; }
th.covalon-sortable[data-sort="asc"]::after { content: " ▲"; font-size: 0.7em; }
th.covalon-sortable[data-sort="desc"]::after { content: " ▼"; font-size: 0.7em; }
`

export default (() => FilterableTables) satisfies QuartzComponentConstructor
