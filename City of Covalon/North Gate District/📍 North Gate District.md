---
Tags:
- covalon/district
Roleplay Channel:
- "[\\#🏞️farm-and-other-districts](https://discord.com/channels/802423566196539412/1441547491337175061)"
- "[🚪 North Gate District](https://discord.com/channels/802423566196539412/1441917910720446485)"
---
Nestled between the eastern mountains and the river the North Gate District boasts administrative buildings and fortifications for the wall's defences. The large plots of land make for prime locations for guild halls.

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
