---
_sidebar_group: Compendiums
---
```base
filters:
  and:
    - or:
        - not:
            - file.hasProperty("_published")
        - note["_published"] == true
    - file.hasTag("covalon/adventure-type")
views:
  - type: table
    name: Adventure Types
    order:
      - file.name
      - Duration
      - Description
      - T1–T3 EXP
      - T4–T5 EXP
    sort:
      - property: _order
        direction: ASC
    columnSize:
      note.Description: 229

```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/adventure-type" sortBy="_order" hide={["_order"]} />;
}
```
