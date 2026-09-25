---
Tags:
- covalon/district
Roleplay Channel:
- "[\\#🌎outside-covalon](https://discord.com/channels/802423566196539412/1441551510377988126)"
---
As Covalon has reclaimed areas of Elleaterra, we have also successfully managed to fortify some of our expedition camp locations into fully inhabitable districts in their own right. Many citizens choose to have their residences, businesses, or guild halls in these outer districts.

**Expedition Districts:** these locations have been resettled, and Covalonians can own property and live here.

```datacorejsx
const { CovalonList } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonList tag="covalon/civilization" where="Covalon Status" is="district" after="Roleplay Channel" />;
}
```

**Expedition Camps:** these locations are rustic outposts.

```datacorejsx
const { CovalonList } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonList tag="covalon/civilization" where="Covalon Status" is="outpost camp" after="Roleplay Channel" />;
}
```

## Locations
```base
formulas:
  SortTitle: file.name.replace(/^(the )?(kingdom of )?/i, '')
filters:
  and:
    - file.hasTag("covalon/location")
    - District.linksTo(this.file)
views:
  - type: table
    name: Locations
    order:
      - file.name
      - Roleplay Channel
      - Guild Headquarters of
    sort:
      - property: formula.SortTitle
        direction: ASC
```
