```base
filters:
  and:
    - or:
        - not:
            - file.hasProperty("_published")
        - note["_published"] == true
    - file.hasTag("covalon/adventure-type")
views:
  - type: table
    name: Adventure Types
    order:
      - file.name
      - Duration
      - Description
    sort:
      - property: Order
        direction: ASC

```
## Dungeons
![[Dungeons#For GMs]]
## Patrols
![[Patrols#For GMs]]
## Expeditions
![[Expeditions#For GMs]]
## Expedition Finales
![[Expedition Finales#For GMs]]
## Excursions and Sagas
![[Excursions and Sagas#For GMs]]
## Descents
![[Descents#For GMs]]
## Brawls
![[Brawls#For GMs]]
## Duels
![[Duels#For GMs]]
