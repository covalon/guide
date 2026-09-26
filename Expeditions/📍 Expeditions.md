---
_sidebar_group: Compendiums
---
The expeditions Covalon has launched to reclaim the lost civilizations of Elleaterra. Each note covers the base camp, the three missions and the finale for one location, along with the Soul Seed unlock it grants.

You can get a quick overview of all the Expedition Missions in [[📍 Mission Overview]].

```base
filters:
  and:
    - or:
        - not:
            - file.hasProperty("_published")
        - note["_published"] == true
    - file.hasTag("covalon/expedition")
formulas:
  JourneyDate: note["Journey Date"].format("MMMM Do, YYYY")
  FinaleCleared: note["Finale First Cleared"].format("MMMM Do, YYYY")
properties:
  file.name:
    displayName: Expedition Location
  formula.JourneyDate:
    displayName: Journey Date
  formula.FinaleCleared:
    displayName: Finale First Cleared
views:
  - type: table
    name: Expeditions
    order:
      - file.name
      - formula.JourneyDate
      - formula.FinaleCleared
      - Finale
      - Soul Seed
    sort:
      - property: Journey Date
        direction: ASC

```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/expedition" sortBy="Journey Date" />;
}
```
