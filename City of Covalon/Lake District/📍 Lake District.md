---
Tags:
- covalon/district
Roleplay Channel:
- "[\\#🏖️lake-district](https://discord.com/channels/802423566196539412/1441545610229584043)"
- "[⛲ Lake](https://discord.com/channels/802423566196539412/1441834379470049370)"
- "[🌲 Lumber Mill and Mine](https://discord.com/channels/802423566196539412/1441835044829270036)"
---
Looking to escape the busier areas of the city? The Lake District may be of interest to you! From curated camp grounds, to properly organized guilds, the Lake District is the quietest district of the city, perfect for relaxing after adventuring!

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
