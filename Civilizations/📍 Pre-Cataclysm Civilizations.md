---
_preview: "[[PC-Elleaterra_World_Map.webp]]"
_sidebar_group: Compendiums
---
Before the Cataclysm, the world flourished with nations and societies across the world. Now, only one remains: Covalon. Still, many refugees keep the faith that one day they may be able to reclaim their homelands from the terrible fates that befell them.

```base
filters:
  and:
    - or:
        - not:
            - file.hasProperty("_published")
        - note["_published"] == true
    - file.hasTag("covalon/civilization")
formulas:
  SortTitle: file.name.replace(/^(the )?(kingdom of )?/i, '')
views:
  - type: table
    name: Civilizations
    order:
      - file.name
      - Tagline
      - Covalon Status
      - Created by
      - Government
      - Population
      - Religions
      - Primary Exports
      - Geography
      - Fate
    sort:
      - property: formula.SortTitle
        direction: ASC

```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/civilization" sortBy="title" tagline="Tagline" aside propsFirst />;
}
```
