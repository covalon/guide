---
_preview: "[[CovalonCity.webp]]"
_sidebar_group: Compendiums
---
Before the Cataclysm, Covalon was nothing more than a small fief of nearly inhospitable land entrusted to the lesser baron Eagor Freetide as a cruel joke. But in a fortuitous twist of fate, the baron would discover something worth protecting in the wasteland - the seed of an artifact we now know as the [[The Shrine of Terra|Heart of Terra]].

The power of the heart protected Covalon from the destruction wrought by the Cataclysm; while his home kingdom was razed to the ground by dragons, the baron enjoyed peace and safety in Covalon. In the aftermath of the chaos, survivors began turning up at the gates of Covalon, and Baron Freetide welcomed them in with open arms, determined to rise to the responsibility fate had set before him.

Months later, the baron passed away due to natural causes, and the responsibility of leadership was thrust upon the heads of each of Covalon's major organizations and the City Planner. As Covalon's non-adventuring population grew, NPCs stepped up to manage most of the day to day governing of the city.

**Roleplay:** [\#💬roleplay-general](https://discord.com/channels/802423566196539412/1441510507386241156) · [🏰 Covalon Walls and Gate](https://discord.com/channels/802423566196539412/1441824177559699577) · [🌄 Covalon Grounds](https://discord.com/channels/802423566196539412/1441824080872476712)

#### Covalon
> [!statblock|Settlement 13]
> `City`
>
> *The last bastion of mortal civilization in Elleaterra.*
>
> **Government** Council of Covalon (appointed council of NPCs)
>
> **Population** 550 (65% common ancestries, 35% other)
>
> **Languages** Common, Dwarven, Sylvan, Iruxi, Other
>
> ---
>
> > **Religions** All
>
> > **Threats** Raiding bands of goblin and kobold tribes, dangerous creatures emerging from the Maw, denizens of the outer planes seeking to exterminate mortal life
>
> > **The City at the End of the World** Covalon is the only known civilization to have survived the Cataclysm, thanks to a living artifact known as the Heart of Terra. Though it started out as little more than a baron's keep on infertile land, it has grown into a hospitable place to live - though it lacks many of the modern conveniences that previous societies developed. Nevertheless, a stubbornness to survive has allowed Covalon to grow to its current state and is what keeps it standing to this day.

```base
formulas:
  SortTitle: file.name.replace(/^(the )?(kingdom of )?/i, '')
  DistrictSort: District.toString().replace(/[\[\]]/g, '').replace(/^(the )?(kingdom of )?/i, '')
filters:
  and:
    - or:
        - not:
            - file.hasProperty("_published")
        - note["_published"] == true
    - file.hasTag("covalon/location")
views:
  - type: table
    name: All Locations
    order:
      - file.name
      - District
      - Roleplay Channel
      - Guild Headquarters of
    sort:
      - property: formula.DistrictSort
        direction: ASC
      - property: formula.SortTitle
        direction: ASC
```
## City District
```datacorejsx
const { CovalonNote } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonNote name="📍 City District" propsFirst />;
}
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/location" sortBy="title" district="City District" heading="h3" hide={["District"]} />;
}
```
## Market District
```datacorejsx
const { CovalonNote } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonNote name="📍 Market District" propsFirst />;
}
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/location" sortBy="title" district="Market District" heading="h3" hide={["District"]} />;
}
```
## Encore District
```datacorejsx
const { CovalonNote } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonNote name="📍 Encore District" propsFirst />;
}
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/location" sortBy="title" district="Encore District" heading="h3" hide={["District"]} />;
}
```
## Armory District
```datacorejsx
const { CovalonNote } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonNote name="📍 Armory District" propsFirst />;
}
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/location" sortBy="title" district="Armory District" heading="h3" hide={["District"]} />;
}
```
## Lake District
```datacorejsx
const { CovalonNote } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonNote name="📍 Lake District" propsFirst />;
}
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/location" sortBy="title" district="Lake District" heading="h3" hide={["District"]} />;
}
```
## Heart's Forest
```datacorejsx
const { CovalonNote } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonNote name="📍 Heart's Forest" propsFirst />;
}
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/location" sortBy="title" district="Heart's Forest" heading="h3" hide={["District"]} />;
}
```
## The Docks
```datacorejsx
const { CovalonNote } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonNote name="📍 The Docks" propsFirst />;
}
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/location" sortBy="title" district="The Docks" heading="h3" hide={["District"]} />;
}
```
## The Farm
```datacorejsx
const { CovalonNote } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonNote name="📍 The Farm" propsFirst />;
}
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/location" sortBy="title" district="The Farm" heading="h3" hide={["District"]} />;
}
```
## Mountain View District
```datacorejsx
const { CovalonNote } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonNote name="📍 Mountain View District" propsFirst />;
}
```
## River Run District
```datacorejsx
const { CovalonNote } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonNote name="📍 River Run District" propsFirst />;
}
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/location" sortBy="title" district="River Run District" heading="h3" hide={["District"]} />;
}
```
## North Gate District
```datacorejsx
const { CovalonNote } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonNote name="📍 North Gate District" propsFirst />;
}
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/location" sortBy="title" district="North Gate District" heading="h3" hide={["District"]} />;
}
```
## Expedition Districts and Outside Covalon
```datacorejsx
const { CovalonNote } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonNote name="📍 Expedition Districts and Outside Covalon" propsFirst />;
}
```

```datacorejsx
const { CovalonEntries } = await dc.require(dc.headerLink("🔑 Setup/Datacore Components.md", "CovalonEntries"));
return function View() {
  return <CovalonEntries tag="covalon/location" sortBy="title" district="Expedition Districts and Outside Covalon" heading="h3" hide={["District"]} />;
}
```
