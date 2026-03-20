"""Moteur de recherche de règles NGAP par matching de mots-clés."""

from analyse_message import extraire_indices, normaliser_texte
from debug_trace import trace
from helpers_cliniques import _contient_un_des
from ngap_database import NGAP_RULES


RULE_BY_ID = {regle["id"]: regle for regle in NGAP_RULES}
NORMALIZED_RULE_EXPRESSIONS = {}
for _regle in NGAP_RULES:
    expressions = _regle.get("keywords_any", _regle.get("keywords", []))
    NORMALIZED_RULE_EXPRESSIONS[_regle["id"]] = [normaliser_texte(expression) for expression in expressions]


def trouver_regles_candidates(message):
    message_normalise = normaliser_texte(message)
    indices = extraire_indices(message)
    candidates = []

    trace("matching_start", message_original=message, message_normalise=message_normalise)

    for regle in NGAP_RULES:
        if regle.get("famille") == "plusieurs territoires" and not indices.get("multi_territoires"):
            continue
        if "fracture" in regle.get("id", ""):
            if not _contient_un_des(message_normalise, ["fracture", "luxation", "humerus"]):
                continue
        expressions = NORMALIZED_RULE_EXPRESSIONS.get(regle["id"], [])
        meilleur_score = 0
        for expression in expressions:
            if expression in message_normalise:
                meilleur_score = max(meilleur_score, len(expression))
        if meilleur_score:
            candidates.append((meilleur_score, regle))

    if not candidates:
        trace("matching_result", candidates_count=0, candidate_ids=[])
        return []

    if _contient_un_des(message_normalise, ["fracture", "luxation", "humerus"]):
        fracture_candidates = [(score, regle) for score, regle in candidates if "fracture" in regle.get("id", "")]
        if fracture_candidates:
            candidates = fracture_candidates

    trace(
        "matching_result",
        candidates_count=len(candidates),
        candidate_ids=[regle["id"] for _, regle in candidates[:5]],
    )

    meilleur_score = max(score for score, _ in candidates)
    if len(candidates) >= 2:
        second_score = sorted({score for score, _ in candidates}, reverse=True)[1] if len({score for score, _ in candidates}) >= 2 else 0
        if meilleur_score > second_score:
            return [regle for score, regle in candidates if score == meilleur_score]

    return [regle for _, regle in candidates]


def dedoublonner_regles(regles):
    uniques = []
    ids_vus = set()

    for regle in regles:
        if regle["id"] not in ids_vus:
            uniques.append(regle)
            ids_vus.add(regle["id"])

    return uniques


def trouver_regle_par_id(regle_id):
    return RULE_BY_ID.get(regle_id)
