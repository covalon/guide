The expeditions Covalon has launched to reclaim the lost civilizations of Elleaterra. Each note covers the base camp, the three missions and the finale for one location, along with the Soul Seed unlock it grants.

```base
filters:
  and:
    - file.hasTag("covalon/expedition")
views:
  - type: table
    name: Expeditions
    order:
      - file.name
      - Journey Date
      - Civilization
      - Soul Seed
      - Finale
    sort:
      - property: Journey Date
        direction: ASC
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("_Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/expedition" sortBy="Journey Date" />;
}
```
