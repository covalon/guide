---
Tags:
- covalon/district
Roleplay Channel:
- "[\\#🏞️farm-and-other-districts](https://discord.com/channels/802423566196539412/1441547491337175061)"
- "[⛰️ Mountain View District](https://discord.com/channels/802423566196539412/1441916742531158107)"
---
On the western side of the city overlooking the farmlands and encore district stands the Mountain View District. Predominantly a residential district this region can be called home to those that simply prefer the comforts of the mountains or the protection of dwellings built into the hard stone of the mountains. The mountains give a perfect overlook of Covalon as the light touches this district a few moments before the rest of the city.
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
