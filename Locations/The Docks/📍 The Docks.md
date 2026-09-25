---
Tags:
- covalon/district
Roleplay Channel:
- "[\\#🌻hearts-forest](https://discord.com/channels/802423566196539412/1441546927735836713)"
- "[🛶 The Docks](https://discord.com/channels/802423566196539412/1441867017530511553)"
---
The bustle on the docks in the morning is a surprising contrast to the remainder of the day. Early mornings on the docks have fishermen going about their business heading out to provide food for the city. Sturdy boats and sturdier nets are found in abundance in the dockyards ready for the daily needs of Covalon.

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
