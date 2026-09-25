Covalon's major multitable events, in chronological order.

```base
filters:
  and:
    - file.hasTag("covalon/event")
formulas:
  EventDate: note["Date"].format("MMMM Do, YYYY")
properties:
  formula.EventDate:
    displayName: Date
  file.name:
    displayName: Event
views:
  - type: table
    name: Events
    order:
      - file.name
      - formula.EventDate
      - Type
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
