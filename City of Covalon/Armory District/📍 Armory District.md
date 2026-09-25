---
Tags:
- covalon/district
Roleplay Channel:
- "[\\#⚒️armory-district](https://discord.com/channels/802423566196539412/1441545133219905616)"
---
Covalon, The City at the End of the World, to stand against the Maw has bolstered their populace and has kept their militant district primed to face the threats from beyond the walls. The sounds of steel and magic can often be heard from this district as adventurers and guards alike practice their abilities on the grounds, ready to protect the city!

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
