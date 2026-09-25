---
Tags:
- covalon/district
Roleplay Channel:
- "[\\#🛍️market-district](https://discord.com/channels/802423566196539412/1441517546367881266)"
- "[🛍️ Covalon Marketplace](https://discord.com/channels/802423566196539412/1441827101803024454)"
---
A far cry from the hustle and bustle of cities past, Covalon's marketplace nevertheless does its best to service its citizens with everything they need. Though most of the stalls that line the marketplace only sell mundane items, adventurers sometimes set up stands to sell magical equipment or alchemical supplies that they've found on their adventures or created themselves.

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
