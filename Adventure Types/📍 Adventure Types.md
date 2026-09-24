```base
filters:
  and:
    - file.hasTag("covalon/adventure-type")
views:
  - type: table
    name: Adventure Types
    order:
      - file.name
      - Duration
      - Description
    sort:
      - property: Order
        direction: ASC

```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/adventure-type" sortBy="Order" hide={["Order"]} />;
}
```
