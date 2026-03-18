# V2 pre-lancement

Date: 2026-03-18

Etat figé de la V2 pre-lancement:
- moteur NGAP aligné sur la logique métier issue du tableau 2026 utilisé pendant la recette
- compréhension du langage naturel fortement renforcée
- dictée navigateur renforcée avec corrections ASR ciblées
- questions courtes uniquement quand l'information est réellement discriminante
- réponses cliquables pour compléter un cas
- historique local avec rechargement d'un cas
- interface web locale prête pour recette cabinet
- cartes catalogue masquées pour éviter les contradictions visuelles avec la cotation finale

Validation actuelle:
- `npm run build` : OK
- `python3 -m unittest discover -s tests -q` : `Ran 101 tests ... OK`

Points prêts avant refonte visuelle:
- moteur métier
- dictée
- historique
- parcours assistant principal

Prochaine étape prévue:
- modélisation / refonte de la page web
