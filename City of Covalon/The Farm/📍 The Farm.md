---
Tags:
- covalon/district
Roleplay Channel:
- "[\\#🏞️farm-and-other-districts](https://discord.com/channels/802423566196539412/1441547491337175061)"
- "[🌽 The Farm](https://discord.com/channels/802423566196539412/1441916097820360826)"
---
Thanks to the magic of the [[The Shrine of Terra|Heart of Terra]], the soil and climate of Covalon have shifted from an arid wasteland to a temperate oasis, allowing crops to grow. Without the city's hardworking farmers and ranchers, Covalon would struggle to survive; hunger is a dragon that cannot be slain with a sword.

## Locations
```base
formulas:
  SortTitle: file.name.replace(/^(the )?(kingdom of )?/i, '')
filters:
  and:
    - or:
        - not:
            - file.hasProperty("_published")
        - note["_published"] == true
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
