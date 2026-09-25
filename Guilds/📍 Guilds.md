Adventurers who share a common cause can band together to establish an official company known as a guild. Guilds foster cooperative and collaborative environments that benefit Covalon in a variety of ways.

```base
filters:
  and:
    - or:
        - not:
            - file.hasProperty("_published")
        - note["_published"] == true
    - file.hasTag("covalon/guild")
formulas:
  SortTitle: file.name.replace(/^(the )?(kingdom of )?/i, '')
properties:
  file.name:
    displayName: Guild
views:
  - type: table
    name: Guilds
    order:
      - file.name
      - Headquarters
      - Membership Requirements
      - Leader
      - Members
      - Goals
      - Values
      - Anathema
    sort:
      - property: formula.SortTitle
        direction: ASC

```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/guild" sortBy="title" aside imagesBesideProps />;
}
```
