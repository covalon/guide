---
Tags:
- covalon/district
Roleplay Channel:
- "[\\#🎶encore-district](https://discord.com/channels/802423566196539412/1441517739628822590)"
- "[🎵 Encore District](https://discord.com/channels/802423566196539412/1441827950960972037)"
---
The district of yurts akin to that of Drifthaven has shops and businesses for your relaxation! The Encore District is a contrast to the busier Market District in both appearance and ambiance, with much more colourful and cozy yurts, come on by if you need some relaxation!

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
