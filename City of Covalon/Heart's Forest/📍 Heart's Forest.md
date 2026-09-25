---
Tags:
- covalon/district
Roleplay Channel:
- "[\\#🌻hearts-forest](https://discord.com/channels/802423566196539412/1441546927735836713)"
- "[🌲 Forest](https://discord.com/channels/802423566196539412/1441867542577545237)"
- "[Campground and Warden Station](https://discord.com/channels/802423566196539412/1524217858433745026)"
---
Amid the arid conditions of the region, Covalon, and more specifically the Heart's Forest stands in defiance to the wastes beyond the walls. Tall trees, sturdy shrubs, and bountiful flora have been brought forward by the [[The Shrine of Terra|Heart of Terra's]] magic, leaving visible evidence of the powerful artifact's effects on the city.

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
