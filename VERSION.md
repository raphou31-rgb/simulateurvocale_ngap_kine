# Base NGAP — à jour au 23/11/2026

Source de vérité : `tableau-ngap-01-01-2026-metropole.pdf` (Alizé, NGAP 01/01/2026),
**sauf 8 lignes revalorisées depuis** (appliquées dans `ngap_database.py`) :

| Acte | PDF 01/01/2026 | En vigueur | Depuis | Source |
|---|---|---|---|---|
| Plusieurs territoires sans chirurgie | TER 9.49 | TER 9.79 | 28/05/2026 | Avenant 8 (JO 19/12/2025) |
| Plusieurs territoires avec chirurgie | TER 9.51 | TER 9.81 | 28/05/2026 | Avenant 8 (JO 19/12/2025) |
| Amputation ≥ 2 membres | APM 9.50 | APM 9.80 | 28/05/2026 | Avenant 8 (JO 19/12/2025) |
| Neuro périphérique, plusieurs membres | NMI 10.01 | NMI 11.01 | 01/09/2026 | Avenant 7 (FFMKR, Doctolib, Topaze) |
| Paraplégie / tétraplégie | NMI 11.01 | NMI 12.01 | 01/09/2026 | Avenant 7 |
| Affection neuro stable, ≥ 2 membres | NMI 10.00 | NMI 11.00 | 01/09/2026 | Avenant 7 |
| Myopathie | NMI 10.99 | NMI 11.99 | 01/09/2026 | Avenant 7 |
| Encéphalopathie infantile | NMI 11.00 | NMI 12.00 | 01/09/2026 | Avenant 7 |

## Prochaine échéance connue

**01/07/2027** : +0,3 sur les cotations 8.07 à 8.13 de l'article I (8.07 → 8.37 … 8.13 → 8.43).
Non appliquée d'avance (peut être suspendue par le comité d'alerte, comme en 2025).
L'app affiche une alerte sur les cotations concernées à partir de cette date.
À faire en juin 2027 : vérifier la confirmation, puis mettre à jour `ngap_database.py`
et `PROCHAINE_REVALORISATION`.

## Validation (23/11/2026)

`python3 -m pytest -q tests` : 159 tests OK, dont :
- `tests/test_matrice_tableau.py` : les 86 lignes de la base = tableau (+ revalorisations), et ~150 phrases types ;
- `tests/test_phrases_cabinet.py` : 200 dictées réelles de cabinet.

Contrôles hors tests (scripts de vérification) : 15 020 variantes de phrases, 930 formulations
opéré / non opéré, ~500 réponses aux questions, 642 chemins de boutons : 0 mauvaise cotation.

Principe : quand une information change la cotation et n'est pas donnée (opéré ?, diagnostic,
âge pour une scoliose, phase intensive, entorse externe...), l'app POSE UNE QUESTION au lieu de supposer.

Choix à valider par le kiné :
- Luxation du coude : l'app demande s'il y a une fracture associée (avec → R.. 8.12, sans → V.. 8.09).
- Fracture de l'avant-bras sans précision : l'app demande distale (RSM 8.11 / RSC 8.10) ou diaphyse/coude (8.12).
- Atteinte bilatérale (droite + gauche, ex. canal carpien bilatéral opéré) : TER 9.79 / 9.81 (plusieurs membres).
