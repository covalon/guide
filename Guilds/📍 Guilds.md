*Adventurers who share a common cause can band together to establish an official company known as a guild. Guilds foster cooperative and collaborative environments that benefit Covalon in a variety of ways.*

```base
formulas:
  SortTitle: file.name.replace(/^the /i, '')
filters:
  and:
    - file.hasTag("covalon/guild")
views:
  - type: table
    name: Guilds
    order:
      - file.name
      - Headquarters
      - Leader
      - Membership Requirements
    sort:
      - property: formula.SortTitle
        direction: ASC
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("_Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/guild" sortBy="title" />;
}
```
