---
_url: how-to-search
---
Everything in the guides can be searched using the search bar in the sidebar. Click it (or use **Ctrl K**, **⌘ K** on a Mac, or **/**) and a search window opens over the page you're on. 

The [Advanced Search](../search/) page is a dedicated page for the search that does the same thing.
## Searching for words
Type what you're looking for, and the results update as you type. Each result shows the page's name, its type (Deity, Guild, Location…) and a snippet with your words highlighted. When there are no words to highlight, the snippet is the page's first paragraph instead.

- Every word has to be on the page: `fire forge` finds pages with both words.
- Put `OR` (in capitals) between words to find pages with either: `dragon OR fey`. Pages with both come first. Each side can be more than one word: `fire forge OR ice`.
## Filtering by Controls
- **Page type**: the first drop-down keeps only one kind of page, such as Deity, Expedition or Player's Guide.
- **+ Add filter**: adds a row of *property · is / is not · value*, e.g. *Domains · is · fire*. 
  Once a page type is picked, only that type's properties are offered, and each value shows how many pages have it. Each filter narrows the results further. The **×** removes a filter.
- **Sort**: best match (the default), or by title A–Z or Z–A.

You can use the filters without typing any words at all, e.g. just *Deity* and *Domains · is · cities* to list every deity of cities.
## Filtering by Search
You can also search properties right in the search box. 

Typing `[` shows a list of properties; pick one and the list moves on to that property's values, with how many pages have each.

- **↑ / ↓** moves through the list, **Enter** or **Tab** takes the highlighted one, and **Esc** closes the list.
- You can also click a suggestion.

| Type this | To find pages… |
| --- | --- |
| `[soul seed:air]` | whose Soul Seed contains *air* |
| `[divine sanctification:"holy"]` | with the whole word *holy* (so not *unholy*) |
| `[domains]` | that have any Domains at all |
| `-[domains:sun]` | without *sun* in their Domains |
| `[domains:air] OR [alternate domains:air]` | with *air* in either one |

- Capitals don't matter in property names or values: `[Soul Seed:Air]` works too.
- `OR` joins the property searches either side of it, and has to be written in capitals. Everything else in the box still has to match, so `[domains:fire] OR [domains:water] [pantheons:circle]` finds pages in the Circle of Stars with fire or water.
- Property searches and ordinary words can be mixed: `fire [domains:sun]`.
- A property that doesn't exist gives no results.
## Filtering the tables
Some tables have a filter box of their own above them. Use them to filter to rows that contain that text. You can also click a column's heading to sort by it (click again to reverse).

- Every word has to be in the row: `fire cities` keeps rows with both.
- Put `-` in front of a word to leave out the rows that have it: `holy -unholy`.
- Put a word or phrase in quotes to match it as a whole word only: `"holy"` keeps *can choose holy* but not *must choose unholy*, and `-"holy"` leaves out rows with the word *holy*.
