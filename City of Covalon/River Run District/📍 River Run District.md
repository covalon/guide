---
Tags:
- covalon/district
Roleplay Channel:
- "[\\#🏞️farm-and-other-districts](https://discord.com/channels/802423566196539412/1441547491337175061)"
- "[💧 River Run District](https://discord.com/channels/802423566196539412/1441917250134212799)"
---
A primarily residential district along the western riverbank, River Run offers beautiful views and quiet relaxation, all not far from the liveliness of the Town Center. Many of the houses and businesses offer a riverside view, and the waterfront lots are particularly sought after.

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
