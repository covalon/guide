---
_sidebar_group: Compendiums
---
The faiths practiced in Elleaterra are as varied as its people. This section is not a comprehensive list, but represents the major faiths in our setting. These deities are all player submitted and free for anyone to use for their PCs.

If you feel a specific niche is missing, you may [\#create-a-ticket](https://discord.com/channels/802423566196539412/889551411438825492) to submit a new deity for review. Your submission must not overlap with existing deities mechanically or thematically to be approved.

```base
filters:
  and:
    - or:
        - not:
            - file.hasProperty("_published")
        - note["_published"] == true
    - file.hasTag("covalon/deity")
formulas:
  SortTitle: file.name.replace(/^(the )?(kingdom of )?/i, '')
properties:
  Divine Sanctification:
    displayName: Sanctification
  Alternate Domains:
    displayName: Alt Domains
views:
  - type: table
    name: Deities
    order:
      - file.name
      - Divine Sanctification
      - Divine Font
      - Domains
      - Alternate Domains
      - Favored Weapon
      - Divine Skill
      - Edicts
      - Anathema
      - Cleric Spells
      - Pantheons
      - Pantheon Members
    sort:
      - property: formula.SortTitle
        direction: ASC

```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/deity" sortBy="title" aside propsFirst />;
}
```
