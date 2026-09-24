Covalon's major multitable events, in chronological order.

```base
filters:
  and:
    - file.hasTag("covalon/event")
views:
  - type: table
    name: Events
    order:
      - file.name
      - Date
    sort:
      - property: Date
        direction: ASC

```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/event" sortBy="date" />;
}
```
