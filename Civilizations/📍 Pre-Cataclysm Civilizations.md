*Before the Cataclysm, the world flourished with nations and societies across the world. Now, only one remains: Covalon. Still, many refugees keep the faith that one day they may be able to reclaim their homelands from the terrible fates that befell them.*

```base
formulas:
  SortTitle: file.name.replace(/^the /i, '')
filters:
  and:
    - file.hasTag("covalon/civilization")
views:
  - type: table
    name: Civilizations
    order:
      - file.name
      - Tagline
      - Government
      - Fate
      - Covalon Status
      - Expedition Summary
    sort:
      - property: formula.SortTitle
        direction: ASC
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("_Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/civilization" sortBy="title" />;
}
```
