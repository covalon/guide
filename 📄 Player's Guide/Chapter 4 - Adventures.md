"Adventures" in Covalon are scheduled play sessions between players and a Dungeon Guide where player characters work together to overcome adversaries, obstacles, and other challenges to receive experience points (XP) and loot.

> [!info] Server Time
> Events are scheduled according to "server time," which is Covalon's standard time zone. During the winter and spring, it operates on **Pacific Standard Time (UTC -8)**, and during the summer and fall, it uses **Pacific Daylight Time (UTC -7)**. 
> 
> It is common practice to use HammerTime or, if on Desktop, the `@time` command to add timestamps in Discord that show the user a given timestamp in their local time.


There are several types of adventures in Covalon, each with their own unique gameplay, challenges, and rewards. 

The amount of loot and XP your character gains varies based on your character's level and the game type, as seen in the summary below. The increased rewards and availability of patrols in Tiers 1–3 has been implemented as a 'catch up' mechanic to new characters climb the ranks.

```base
filters:
  and:
    - or:
        - not:
            - file.hasProperty("_published")
        - _published == true
    - file.hasTag("covalon/adventure-type")
    - file.name != "Duels"
views:
  - type: table
    name: Adventure Types
    order:
      - file.name
      - Duration
      - Description
      - T1–T3 EXP
      - T4–T5 EXP
    sort:
      - property: _order
        direction: ASC

```

> [!note] Hero Points
> Unlike a traditional campaign, not all [Hero Points](https://2e.aonprd.com/Rules.aspx?ID=2333) granted in Covalon expire at the end of a session; some stay with you until they are used.
> ##### Temporary Hero Points
> At the beginning of each adventure (excluding [[Brawls]]), players gain 1 Temporary Hero Point. If it's not used during the adventure, it expires.
> 
> This Temporary Hero Point doesn't allow players to exceed the 3 Hero Point Limit.
> ##### Non-Temporary Hero Points
> Players can obtain Hero Points that don't expire at the end of an adventure (but are still consumed upon use) by playing in adventures, participating in or hosting events with a guild, or participating in special server events.
## Dungeons
![[Dungeons#For Players]]
## Patrols
![[Patrols#For Players]]
## Brawls
![[Brawls#For Players]]
## Descents
![[Descents#For Players]]
## Expeditions
![[Expeditions#For Players]]
## Excursions
![[Excursions and Sagas#For Players]]
