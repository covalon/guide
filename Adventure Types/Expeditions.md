---
Tags:
- covalon/adventure-type
Order: 3
Duration: 3-4 hours
Description: Narratively linked adventures that tie in to the Covalon Meta-Narrative.
---
## For Players
The Cataclysm wrought destruction across the world of Elleaterra, leveling all civilizations to the ground, save Covalon. These old locations are nothing more than ruins now, but those ruins may be worth searching for resources, treasures, and most importantly, answers on how to defeat the Maw once and for all.

Expeditions are multi-phase adventures that require players to cooperate together in order to reclaim these fallen societies. Each expedition consists of three phases.

> [!info] Requesting an Expedition Mission
> If there is a particular expedition adventure you'd like to play in, you can always use [\#🛡️lfgm-forum](https://discord.com/channels/802423566196539412/1472263264585908430) to create a party and request a Dungeon Guide to run the adventure for you. You can even choose which mission you'd like to play.
>
> Once Phase 2 has been unlocked for an expedition, three missions become available that are always referred to as Mission A, Mission B, and Mission C. Though the missions are all narratively linked, they can be experienced in any order, as they are not prequels or sequels to each other.
>
> It may also be worthwhile to select the mission that has been played the least, as all missions must be completed a number of times before the finale unlocks.

> [!info] Requesting an Expedition Finale
> Soul Seed aspects must be unlocked by completing specific expedition finales, which you can use [\#🛡️lfgm-forum](https://discord.com/channels/802423566196539412/1472263264585908430) to organize a party for.
>
> Normal mode finales utilize variant modifications to keep repeats interesting, so if you have a friend who needs help attempting a finale that you've already completed, give them a hand and you might see something new. Players with characters in the highest tier can alternatively request hard mode, which employs all variant modifications at once!

### Phase 1: Establish Base Camp
The first phase of an expedition is to establish a camp at the site of the former civilization to serve as a base of operations for the expedition itself. If the location is difficult to reach, this phase may involve constructing a vehicle to get there, or building a specialized structure in order to survive the unique circumstances of a location.

This phase of an expedition does not occur like a normal adventure, but instead functions as a community goal that players must contribute resources to complete. The specific resources that must be contributed vary depending on the expedition location, and the current requirements to establish a base camp for a given expedition can be found in the [\#📙expedition-logs](https://discord.com/channels/802423566196539412/927330508650725466) channel in the Discord server. Once base camp has been established for a location, this phase concludes and the next phase becomes available.
### Phase 2: Complete Missions
The second phase of an expedition requires adventurers to complete a variety of missions in order to explore the area, secure the base camp, and uncover clues about the Cataclysm. Missions are a subtype of expedition adventures that are similar to dungeons, but contribute to an overarching narrative, and are available to all tiers.

Each expedition features three missions which have distinct objectives and elements. Any individual mission is repeatable, though some content in the mission changes between repeats. Once several missions have been completed for a location, this phase concludes and the next phase becomes available (though the missions can still be played after the phase has concluded).
### Phase 3: Complete the Finale
Once each expedition has been completed a certain number of times, the expedition finale unlocks. A finale involves a singular encounter against a narratively significant threat to conclude the expedition.

Completing a finale unlocks a new way for participants to customize their Soul Seeds, and like missions, they are repeatable. Finales can be attempted by players in Tier 3 or higher and last 1 to 2 hours.

Finales have two difficulty modes. Normal mode is the standard finale experience, which can be scaled to any tier. Hard mode can only be attempted by characters in the highest and second highest tiers, and is intended for max level characters. When a finale first becomes available, it can only be attempted at hard mode. Once a finale has been cleared once, normal mode becomes available.
### Expedition Locations
The following is a list of currently active expeditions. For more information on each expedition, see the city's corresponding entry of the Campaign Lore chapter. Mission and finale details for each are in [[📍 Expeditions|Expeditions]].

```base
formulas:
  JourneyDate: note["Journey Date"].format("MMMM Do, YYYY")
  FinaleCleared: note["Finale First Cleared"].format("MMMM Do, YYYY")
filters:
  and:
    - file.hasTag("covalon/expedition")
properties:
  formula.JourneyDate:
    displayName: Journey Date
  formula.FinaleCleared:
    displayName: Finale First Cleared
  file.name:
    displayName: Expedition Location
views:
  - type: table
    name: Expeditions
    order:
      - file.name
      - Soul Seed
      - Finale
      - Civilization
      - formula.JourneyDate
      - formula.FinaleCleared
    sort:
      - property: Journey Date
        direction: ASC

```
## For GMs
Expedition missions are a special game-mode that is intertwined with the ongoing meta-narrative of Covalon. Expeditions represent our efforts to reclaim the world after the Cataclysm and face the challenges left behind in a shattered realm.

Expeditions require the installation of the Covalon Expedition Module on Foundry VTT.

Expeditions consist of a choice of three missions that have special instructions that can be found inside the module. Expedition missions are replayable even after the initial Expedition storyline to a location is completed, though some missions require reflavoring slightly to make narrative sense (such as the Maw creating facsimiles of enemies).
