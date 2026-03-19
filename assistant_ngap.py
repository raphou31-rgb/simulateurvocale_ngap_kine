import re

from analyse_message import extraire_indices, normaliser_texte
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
        return []

    if _contient_un_des(message_normalise, ["fracture", "luxation", "humerus"]):
        fracture_candidates = [(score, regle) for score, regle in candidates if "fracture" in regle.get("id", "")]
        if fracture_candidates:
            candidates = fracture_candidates

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


def _libelle_regle(regle):
    return str(regle.get("acte", "")).strip()


def _analyse_pathologie(regle):
    famille = str(regle.get("famille", "")).strip().lower()
    if famille == "neurologie":
        return "neurologique"
    if famille == "respiratoire":
        return "respiratoire"
    if famille == "vasculaire":
        return "vasculaire"
    if famille == "sujet age":
        return "sujet âgé / déambulation"
    if famille == "perinee":
        return "périnéo-sphinctérien"
    if famille == "abdominal":
        return "abdominal"
    if famille == "amputations":
        return "amputation"
    if famille == "soins palliatifs":
        return "soins palliatifs"
    if famille == "brulures":
        return "brûlure"
    if famille == "deviation rachis":
        return "déviation du rachis"
    if famille == "rachis":
        return "rachis"
    if famille == "maladies rhumatismales inflammatoires":
        return "rhumatismale inflammatoire"
    if famille in {"membre inferieur", "membre superieur", "plusieurs territoires"}:
        return "orthopédique / rhumatologique"
    if famille == "maxillo-facial / vestibulaire / ORL":
        return "orl / vestibulaire / maxillo-facial"
    return "clinique non précisée"


def _analyse_membres(regle):
    regle_id = str(regle.get("id", ""))
    famille = str(regle.get("famille", "")).strip().lower()
    detail = str(regle.get("detail", "")).strip().lower()
    code = str(regle.get("cotation", "")).split()[0]
    if famille == "plusieurs territoires":
        return "plusieurs membres ou tronc + membre"
    if "plusieurs segments du rachis" in detail:
        return "plusieurs segments d'un même rachis"
    if "plusieurs segments" in detail:
        return "plusieurs segments du même membre"
    if code in {"RIC", "RIM", "VIC", "VIM"}:
        return "un membre inférieur"
    if code in {"RSC", "RSM", "VSC", "VSM"}:
        return "un membre supérieur"
    if "membre inférieur" in _libelle_regle(regle) or "membre inférieur" in detail:
        return "un membre inférieur"
    if "membre supérieur" in _libelle_regle(regle) or "membre supérieur" in detail:
        return "un membre supérieur"
    if regle_id.startswith("rachis_") or regle_id.startswith("deviation_rachis_"):
        return "rachis"
    if famille == "neurologie" and "plusieurs" in regle_id:
        return "plusieurs membres ou membre + tronc/face"
    if famille == "neurologie":
        return "un membre ou la face"
    return "à préciser selon le contexte clinique"


def _analyse_operation(regle):
    texte = f"{_libelle_regle(regle)} {regle.get('detail', '')}".lower()
    code = str(regle.get("cotation", "")).split()[0]
    if code in {"RIM", "RSM", "RAM", "VIM", "VSM"} or "non opéré" in texte or "sans chirurgie" in texte:
        return "non"
    if code in {"RIC", "RSC", "RAO", "VIC", "VSC"} or "opéré" in texte or "chirurgie" in texte:
        return "oui"
    if code in {"TER", "NMI", "ARL", "RAV", "RAB", "RPE", "RPB", "APM", "PLL", "DRA"}:
        return "non déterminant pour cet acte"
    return "à préciser"


def _analyse_type(regle):
    famille = str(regle.get("famille", "")).strip().lower()
    if famille == "neurologie":
        return "neurologique"
    if famille == "respiratoire":
        return "respiratoire"
    if famille == "vasculaire":
        return "vasculaire"
    if famille == "sujet age":
        return "gériatrique"
    if famille in {"membre inferieur", "membre superieur", "rachis", "deviation rachis", "plusieurs territoires"}:
        return "orthopédique / rhumatologique"
    if famille == "maladies rhumatismales inflammatoires":
        return "rhumatologique inflammatoire"
    if famille == "perinee":
        return "périnéal"
    if famille == "abdominal":
        return "abdominal"
    if famille == "soins palliatifs":
        return "soins palliatifs"
    if famille == "brulures":
        return "cutané / brûlures"
    if famille == "amputations":
        return "amputation"
    return "à confirmer"


def _confiance_reponse(regle):
    referentiel = str(regle.get("referentiel", "")).strip().lower()
    code = str(regle.get("cotation", "")).split()[0]
    if referentiel == "oui" or code in {"RIC", "RIM", "RSC", "RSM", "PLL", "RPE", "APM"}:
        return "ÉLEVÉ"
    if code in {"TER", "NMI", "ARL", "RAV"}:
        return "MOYEN"
    return "ÉLEVÉ"


def _resume_seances(regle):
    referentiel = str(regle.get("referentiel", "")).strip().lower()
    if regle.get("seances_max") is not None:
        return str(regle["seances_max"])
    if referentiel == "oui":
        return "non fourni par les données de référence"
    return "hors référentiel / non précisé"


def _resume_referentiel(regle):
    return "oui" if str(regle.get("referentiel", "")).strip().lower() == "oui" else "non"


def formater_reponse_finale(regle):
    return (
        f"Cotation NGAP : {regle['cotation']}\n"
        f"Libellé NGAP : {_libelle_regle(regle)}\n\n"
        "Analyse :\n"
        f"- Pathologie : {_analyse_pathologie(regle)}\n"
        f"- Membres : {_analyse_membres(regle)}\n"
        f"- Opéré : {_analyse_operation(regle)}\n"
        f"- Type : {_analyse_type(regle)}\n\n"
        "Justification :\n"
        "- logique NGAP stricte appliquée à partir du contexte clinique reconnu.\n\n"
        f"Confiance : {_confiance_reponse(regle)}\n"
        f"Nombre de séances max : {_resume_seances(regle)}\n"
        f"Référentiel : {_resume_referentiel(regle)}"
    )


def extraire_regle_depuis_reponse(texte_reponse):
    acte = None
    cotation = None
    for ligne in texte_reponse.splitlines():
        if ligne.startswith("Acte : "):
            acte = ligne.replace("Acte : ", "", 1).strip()
        elif ligne.startswith("Libellé NGAP : "):
            acte = ligne.replace("Libellé NGAP : ", "", 1).strip()
        elif ligne.startswith("Cotation : "):
            cotation = ligne.replace("Cotation : ", "", 1).strip()
        elif ligne.startswith("Cotation NGAP : "):
            cotation = ligne.replace("Cotation NGAP : ", "", 1).strip()
    if not acte or not cotation:
        return None
    for regle in NGAP_RULES:
        if _libelle_regle(regle) == acte and regle.get("cotation") == cotation:
            return regle
    return None


def _resume_domaine(regle):
    famille = regle.get("famille", "")
    if famille in {"rachis", "deviation rachis", "membre inferieur", "membre superieur", "plusieurs territoires", "maladies rhumatismales inflammatoires"}:
        return "Orthopédie / Rhumatologie"
    if famille == "neurologie":
        return "Neurologie"
    if famille == "respiratoire":
        return "Respiratoire"
    if famille == "vasculaire":
        return "Vasculaire"
    if famille == "abdominal":
        return "Abdominal"
    if famille == "perinee":
        return "Périnéal"
    if famille == "brulures":
        return "Brûlures"
    if famille == "amputations":
        return "Amputations"
    if famille == "maxillo-facial / vestibulaire / ORL":
        return "Maxillo / ORL / Vestibulaire"
    if famille == "sujet age":
        return "Sujet âgé"
    return "NGAP kiné"


def _resume_zone(regle):
    detail = (regle.get("detail") or "").lower()
    regle_id = regle.get("id", "")
    if "rachis" in detail or "rachis" in regle_id or "cervicalgie" in detail or "lombalgie" in detail:
        return "Rachis"
    if any(term in detail for term in ["hanche", "cuisse"]) or "hanche" in regle_id:
        return "Hanche / cuisse"
    if any(term in detail for term in ["genou", "jambe"]) or "genou" in regle_id:
        return "Genou / jambe"
    if any(term in detail for term in ["cheville", "pied"]) or "cheville" in regle_id:
        return "Cheville / pied"
    if any(term in detail for term in ["épaule", "epaule", "bras"]) or "epaule" in regle_id:
        return "Épaule / bras"
    if any(term in detail for term in ["coude", "avant-bras", "avant bras"]) or "coude" in regle_id:
        return "Coude / avant-bras"
    if any(term in detail for term in ["poignet", "main", "canal carpien"]) or "poignet" in regle_id:
        return "Poignet / main"
    if "lymph" in detail or "bandage" in detail:
        return "Système vasculaire"
    if famille := regle.get("famille", ""):
        if famille == "respiratoire":
            return "Respiration"
        if famille == "neurologie":
            return "Système nerveux"
        if famille == "perinee":
            return "Périnée"
        if famille == "abdominal":
            return "Abdomen"
        if famille == "brulures":
            return "Peau / brûlures"
    return "Zone clinique"


def _resume_contexte(regle):
    detail = (regle.get("detail") or "").lower()
    acte = (regle.get("acte") or "").lower()
    if "opéré" in acte or "operee" in acte or "opéré" in detail or "operee" in detail:
        return "Chirurgie"
    if "non opéré" in acte or "non operee" in acte or "sans chirurgie" in detail:
        return "Sans chirurgie"
    if any(term in acte for term in ["arthroplastie", "ligament", "méniscectomie", "meniscectomie", "libération du nerf médian", "chirurgie"]):
        return "Chirurgie"
    if "trauma" in detail or "traumatisme" in acte:
        return "Trauma récent"
    if "commune" in detail:
        return "Forme commune"
    if "déviation" in acte or "deviation" in acte:
        return "Déviation"
    return "Contexte ciblé"


def _resume_sous_type(regle):
    acte = (regle.get("acte") or "").lower()
    detail = (regle.get("detail") or "").lower()
    if "arthroplastie" in acte:
        return "Arthroplastie"
    if "ligament croisé" in acte or "ligament croise" in acte:
        return "Ligamentoplastie"
    if "méniscectomie" in acte or "meniscectomie" in acte:
        return "Méniscectomie"
    if "canal carpien" in acte:
        return "Canal carpien"
    if "coiffe" in acte:
        return "Coiffe des rotateurs"
    if "lombalgie commune" in acte:
        return "Lombalgie commune"
    if "cervicalgie commune" in acte:
        return "Cervicalgie commune"
    if "lymph" in acte:
        return "Drainage lymphatique"
    if "bandage" in acte:
        return "Bandage multicouche"
    if "brûlures" in acte or "brulures" in acte:
        return "Brûlures"
    if "plusieurs segments" in detail:
        return "Plusieurs segments"
    return ""


def _schema_kind(regle):
    zone = _resume_zone(regle)
    mapping = {
        "Rachis": "rachis",
        "Hanche / cuisse": "hanche",
        "Genou / jambe": "genou",
        "Cheville / pied": "cheville",
        "Épaule / bras": "epaule",
        "Coude / avant-bras": "coude",
        "Poignet / main": "main",
        "Système vasculaire": "vasculaire",
        "Respiration": "respiratoire",
        "Système nerveux": "neurologie",
        "Périnée": "perinee",
        "Abdomen": "abdominal",
        "Peau / brûlures": "brulures",
    }
    return mapping.get(zone, "generic")


def _visual_mapping_for_rule(regle):
    cotation = str(regle.get("cotation", "")).strip().upper()
    code = cotation.split()[0] if cotation else ""
    famille = regle.get("famille", "")

    if cotation == "NMI 9.01" or code in {"TER", "APM"}:
        return {
            "pdf_source": "Schema-NGAP-Kine.pdf",
            "page": 2 if code == "NMI" else 1,
            "color_code": "Multi",
            "anatomical_tag": "multi",
        }
    if famille in {"plusieurs territoires", "amputations", "brulures"}:
        return {
            "pdf_source": "Schema-NGAP-Kine.pdf",
            "page": 1,
            "color_code": "Blanc",
            "anatomical_tag": "corps_entier",
        }
    if code in {"RAM", "RAO", "DRA"} or famille in {"rachis", "deviation rachis"}:
        return {
            "pdf_source": "Schema-NGAP-Kine.pdf",
            "page": 1,
            "color_code": "Blanc",
            "anatomical_tag": "rachis",
        }
    if "S" in code:
        return {
            "pdf_source": "Schema-NGAP-Kine.pdf",
            "page": 1,
            "color_code": "Bleu",
            "anatomical_tag": "membre_superieur",
        }
    if "I" in code:
        return {
            "pdf_source": "Schema-NGAP-Kine.pdf",
            "page": 1,
            "color_code": "Rose",
            "anatomical_tag": "membre_inferieur",
        }
    if famille == "neurologie":
        return {
            "pdf_source": "Schema-NGAP-Kine.pdf",
            "page": 2,
            "color_code": "Rose",
            "anatomical_tag": "neuromusculaire",
        }
    if famille == "respiratoire":
        return {
            "pdf_source": "Schema-NGAP-Kine.pdf",
            "page": 2,
            "color_code": "Rose",
            "anatomical_tag": "respiratoire",
        }
    if famille == "vasculaire":
        return {
            "pdf_source": "Schema-NGAP-Kine.pdf",
            "page": 2,
            "color_code": "Rose",
            "anatomical_tag": "vasculaire",
        }
    if famille in {"abdominal", "perinee"}:
        return {
            "pdf_source": "Schema-NGAP-Kine.pdf",
            "page": 2,
            "color_code": "Rose",
            "anatomical_tag": "abdomino_perineal",
        }
    return {
        "pdf_source": "Schema-NGAP-Kine.pdf",
        "page": 1,
        "color_code": "Blanc",
        "anatomical_tag": "corps_entier",
    }


def _visual_render_for_rule(regle):
    mapping = _visual_mapping_for_rule(regle)
    color_code = mapping["color_code"]
    color_map = {
        "Bleu": "#A3D8E2",
        "Rose": "#E96393",
        "Multi": "#E96393",
        "Blanc": "#FFFFFF",
    }
    focus_map = {
        "membre_superieur": "MEMBRE SUPÉRIEUR",
        "membre_inferieur": "MEMBRE INFÉRIEUR",
        "rachis": "RACHIS",
        "multi": "PLUSIEURS ZONES",
        "corps_entier": "CORPS ENTIER",
        "neuromusculaire": "AFFECTION NEUROMUSCULAIRE",
        "respiratoire": "AFFECTION RESPIRATOIRE",
        "vasculaire": "AFFECTION VASCULAIRE",
        "abdomino_perineal": "ABDOMINO-PÉRINÉAL",
    }
    return {
        "primary_color": color_map.get(color_code, "#FFFFFF"),
        "anatomical_focus": focus_map.get(mapping["anatomical_tag"], "CORPS ENTIER"),
        "background_style": "Rounded_Gradient_Teal",
        "instruction_image": (
            "Générer une silhouette minimaliste type PDF Kiné avec la zone "
            f"{focus_map.get(mapping['anatomical_tag'], 'CORPS ENTIER')} "
            f"en surbrillance couleur {color_code}"
        ),
    }


def _visual_config_for_rule(regle):
    mapping = _visual_mapping_for_rule(regle)
    tag = mapping["anatomical_tag"]
    if tag == "membre_superieur":
        active_zone_color = "A3D8E2"
        highlight_target = "ARMS"
    elif tag == "membre_inferieur":
        active_zone_color = "E96393"
        highlight_target = "LEGS"
    elif tag == "multi":
        active_zone_color = "E96393"
        highlight_target = "MULTI"
    elif tag == "rachis":
        active_zone_color = "2F4F4F"
        highlight_target = "SPINE"
    else:
        active_zone_color = "FFFFFF"
        highlight_target = "BODY"
    return {
        "body_base_color": "FFFFFF",
        "active_zone_color": active_zone_color,
        "highlight_target": highlight_target,
        "ui_background": "Rounded_Teal_Gradient",
    }


def _visual_layer_for_rule(regle):
    config = _visual_config_for_rule(regle)
    return {
        "background": config["ui_background"],
        "base_body": "White_Fill_Black_Outline",
        "active_overlay": {
            "zone": config["highlight_target"],
            "hex_color": f"#{config['active_zone_color']}",
            "opacity": 1.0,
        },
    }


def _clinique_payload_for_rule(regle):
    cotation = str(regle.get("cotation", "")).strip()
    if regle.get("seances_max") is not None:
        dap = f"{regle['seances_max']} séances"
    else:
        dap = None
    return {
        "zone": _resume_zone(regle),
        "cotation": cotation,
        "dap": dap,
    }


def decrire_reponse_finale(texte_reponse, message="", contexte_precedent=""):
    regle = extraire_regle_depuis_reponse(texte_reponse)
    if regle is None:
        return None

    domaine = _resume_domaine(regle)
    zone = _resume_zone(regle)
    contexte = _resume_contexte(regle)
    sous_type = _resume_sous_type(regle)
    parcours = [domaine, zone, contexte]
    if sous_type:
        parcours.append(sous_type)

    return {
        "clinique": _clinique_payload_for_rule(regle),
        "affichage_visuel": _visual_layer_for_rule(regle),
        "schema_kind": _schema_kind(regle),
        "title": zone,
        "subtitle": " | ".join(parcours),
        "description": f"Zone concernée : {zone.lower()}. Décision prise via : {' > '.join(parcours)}.",
        "path": parcours,
        "rule_id": regle["id"],
        "visual_mapping": _visual_mapping_for_rule(regle),
        "visual_render": _visual_render_for_rule(regle),
        "visual_config": _visual_config_for_rule(regle),
        "visual_layer": _visual_layer_for_rule(regle),
    }


def reponse_prudente(contexte_precedent="", attente="general_precision"):
    return {
        "texte": "Cotation impossible sans précision clinique complémentaire.",
        "nouveau_contexte": contexte_precedent,
        "termine": False,
        "attente": attente
    }


def regle_est_conclusive(regle):
    if regle is None:
        return False
    cotation = regle.get("cotation")
    if cotation is None:
        return False
    if isinstance(cotation, str) and cotation.strip() == "":
        return False
    return True


def question_precision_pour_candidat_unique(message, regle):
    if regle is None:
        return None, ""

    message_normalise = normaliser_texte(message)
    indices = extraire_indices(message)
    famille = str(regle.get("famille", "")).strip().lower()

    if famille in {"rachis", "deviation rachis"}:
        if regle.get("id") == "rachis_cervicalgie_commune":
            age_moins_18 = _age_moins_18(message_normalise)
            if age_moins_18 is None:
                return "Question : moins de 18 ans ?", "rachis_cervicalgie_age"
            if age_moins_18 is False:
                return "Question : trauma recent ou autre atteinte rachis ?", "rachis_cervicalgie_adulte_precision"
        if (
            indices["segment"] == "lombaire"
            and indices.get("chirurgie") is None
            and not _contient_un_des(
                message_normalise,
                ["commune", "lombo sacre", "lombo-sacre", "deviation", "scoliose", "lordose", "sciatique", "cruralgie"],
            )
        ):
            return "Question : lombalgie commune / lombo-sacre / deviation ?", "rachis_lombaire_precision"
        if (
            indices["segment"] == "cervical"
            and indices.get("chirurgie") is None
            and not _contient_un_des(message_normalise, ["cervicalgie commune", "commune"])
            and not _contient_un_des(
                message_normalise,
                ["trauma", "traumatisme", "recent", "récent", "deviation", "scoliose"],
            )
        ):
            return "Question : cervicalgie / trauma recent / deviation ?", "rachis_cervical_precision"
        if (
            indices["segment"] == "dorsal"
            and indices.get("chirurgie") is None
            and not _contient_un_des(message_normalise, ["dorsalgie", "rachis dorsal", "rachis thoracique"])
            and not _contient_un_des(message_normalise, ["deviation", "cyphose"])
        ):
            return "Question : dorsal ou deviation ?", "rachis_dorsal_precision"
        if (
            indices["territoire"] == "rachis"
            and indices["segment"] is None
            and not _contient_un_des(message_normalise, ["deviation", "scoliose", "cyphose", "lordose"])
        ):
            return "Question : plusieurs segments ou deviation ?", "rachis_precision"

    if famille == "membre inferieur":
        if _membre_inf_bilateral_explicite(message_normalise) and indices.get("chirurgie") is None:
            return "Question : operes ou non ?", "deux_membres_precision"
        if indices["multiple"] and _membre_inf_meme_membre_explicite(message_normalise) and indices.get("chirurgie") is None:
            return "Question : operes ou non ?", "deux_membres_precision"
        if indices["multiple"] and indices.get("chirurgie") is None:
            return "Question : operes ou non ?", "deux_membres_precision"
        if "genou" in message_normalise or "genoux" in message_normalise:
            if indices.get("chirurgie") is None and not _contient_un_des(
                message_normalise,
                ["lca", "ligament croise", "meniscectomie", "prothese", "fracture"],
            ):
                return "Question : chirurgie du genou ou non ?", "genou_chirurgie"
            if indices.get("chirurgie") == "oui" and not _contient_un_des(
                message_normalise,
                ["lca", "ligament croise", "meniscectomie", "prothese", "fracture"],
            ):
                return "Question : prothese / lca / meniscectomie / autre ?", "genou_chirurgie_type"
        if "cheville" in message_normalise and indices.get("chirurgie") is None:
            return "Question : operee ? entorse ? referentiel ?", "cheville_precision"
        if ("hanche" in message_normalise or "cuisse" in message_normalise) and indices.get("chirurgie") is None:
            return "Question : chirurgie de hanche ou non ?", "hanche_chirurgie"

    if famille == "membre superieur":
        if indices["multiple"] and indices.get("chirurgie") is None:
            return "Question : operes ou non ?", "membre_sup_multiple_precision"
        if "canal carpien" in message_normalise:
            return None, ""
        if (
            ("coude" in message_normalise or "avant bras" in message_normalise or "avant-bras" in message_normalise)
            and indices.get("chirurgie") is None
            and not _contient_un_des(message_normalise, ["fracture", "luxation"])
        ):
            return "Question : operee ou non ?", "coude_chirurgie"
        if (
            ("poignet" in message_normalise or "main" in message_normalise)
            and indices.get("chirurgie") is None
            and not _contient_un_des(message_normalise, ["fracture", "canal carpien"])
        ):
            return "Question : operee ou non ?", "poignet_chirurgie"
        if (
            ("epaule" in message_normalise or "epaules" in message_normalise or "bras" in message_normalise)
            and indices.get("chirurgie") is None
            and not _contient_un_des(message_normalise, ["coiffe", "prothese"])
        ):
            return "Question : operee ? coiffe ? fracture ? referentiel ?", "epaule_precision"

    return None, ""


def _contient_un_des(m, expressions):
    return any(expr in m for expr in expressions)


def _contient_mot(m, mot):
    return mot in m.split()


def _reponse_chirurgie_positive(m):
    if _reponse_chirurgie_negative(m):
        return False
    return _contient_un_des(
        m,
        ["oui", "chirurgie", "opere", "operee", "post op", "post-op", "postoperatoire", "post operatoire"],
    )


def _reponse_chirurgie_negative(m):
    return _contient_un_des(
        m,
        [
            "non chirurgie",
            "sans chirurgie",
            "pas de chirurgie",
            "sans operation",
            "sans opération",
            "pas opere",
            "pas operee",
            "pas opéré",
            "pas opérée",
            "non opere",
            "non operee",
            "non opéré",
            "non opérée",
            "non op",
            "non",
            "medical",
        ],
    )


def _segments_rachis_detectes(m):
    segments = set()
    if _contient_un_des(m, ["cervical", "cervicale", "cervicalgie"]):
        segments.add("cervical")
    if _contient_un_des(m, ["dorsal", "thoracique"]):
        segments.add("dorsal")
    if _contient_un_des(m, ["lombaire", "lombo", "lombo sacre", "lombo-sacre", "lombalgie"]):
        segments.add("lombaire")
    return segments


def _membre_inf_bilateral_explicite(m):
    return (
        _contient_un_des(
            m,
            [
                "deux membres inferieurs",
                "deux membre inferieur",
                "membres inferieurs",
                "des membre inferieur",
                "les membre inferieur",
                "bilateral",
                "bilaterale",
                "bilateraux",
                "bilateralement",
                "bilateral genoux",
                "deux genoux",
                "deux jambes",
            ],
        )
        or (
            "gauche" in m
            and "droit" in m
            and _contient_un_des(m, ["genou", "jambe", "cheville", "hanche", "cuisse", "pied"])
        )
    )


def _membre_sup_bilateral_explicite(m):
    return (
        _contient_un_des(
            m,
            [
                "deux membres superieurs",
                "deux membre superieur",
                "membres superieurs",
                "des membre superieur",
                "les membre superieur",
                "bilateral",
                "bilaterale",
                "bilateraux",
                "bilateralement",
                "deux bras",
                "deux epaules",
                "deux épaules",
                "deux coudes",
                "deux poignets",
                "deux mains",
            ],
        )
        or (
            "gauche" in m
            and "droit" in m
            and _contient_un_des(m, ["bras", "epaule", "épaule", "coude", "poignet", "main"])
        )
    )


def _membre_inf_meme_membre_explicite(m):
    return _contient_un_des(
        m,
        [
            "deux segments membre inferieur",
            "2 segments membre inferieur",
            "plusieurs segments membre inferieur",
            "meme membre",
            "même membre",
            "membre membre",
            "un seul membre",
            "sur le meme membre",
            "sur le même membre",
        ],
    )


def _age_moins_18(m):
    if _contient_un_des(m, ["moins de 18 ans", "mineur", "enfant", "adolescent", "ado", "pediatrique", "pédiatrique"]):
        return True
    if _contient_un_des(m, ["adulte", "majeur", "plus de 18 ans"]):
        return False
    return None


def _trauma_recent_mention(m):
    if _contient_un_des(m, ["non traumatique", "pas de trauma", "pas de traumatisme", "sans trauma", "sans traumatisme"]):
        return False
    if _contient_un_des(m, ["trauma", "traumatisme", "recent", "récent", "coup du lapin"]):
        return True
    return None


def _neuro_etendue(m):
    if _contient_un_des(m, ["deux membres", "2 membres", "plusieurs membres"]):
        return "plusieurs"
    if _contient_mot(m, "plusieurs") or _contient_mot(m, "deux") or _contient_mot(m, "2"):
        return "plusieurs"
    if _contient_un_des(m, ["un membre", "1 membre", "face"]):
        return "un"
    if _contient_mot(m, "un"):
        return "un"
    if ("tronc" in m and ("membre" in m or "face" in m)):
        return "plusieurs"
    return None


def inferer_regle_neurologie(message):
    m = normaliser_texte(message)

    infantile = _contient_un_des(
        m,
        ["neurologie infantile", "neurologique infantile", "retard moteur", "nourrisson", "bebe", "bébé", "enfant neurologique"]
    )
    if _contient_un_des(m, ["paralysie cerebrale", "paralysie cérébrale", "polyhandicap"]):
        return "neurologie_paralysie_cerebrale_polyhandicap"
    if _contient_un_des(m, ["encephalopathie infantile", "encéphalopathie infantile"]):
        return "neurologie_encephalopathie_infantile"
    if infantile:
        return "NEED_INFANTILE_TYPE"
    if "myopathie" in m:
        return "neurologie_myopathie"
    if _contient_un_des(m, ["paraplegie", "paraplégie", "tetraplegie", "tétraplégie"]):
        return "neurologie_paraplegie_tetraplegie"
    if _contient_un_des(m, ["hemiplegie", "hémiplégie", "avc"]):
        return "neurologie_hemiplegie"

    peripherique = _contient_un_des(
        m,
        [
            "neuropathie peripherique", "neuropathie périphérique", "peripherique", "périphérique",
            "radiculaire", "tronculaire", "sciatique", "cruralgie", "cervico brachiale",
            "cervico-brachiale", "paralysie faciale", "canal carpien severe", "canal carpien sévère"
        ]
    )
    stable = _contient_un_des(
        m,
        ["sep", "sclerose en plaques", "sclérose en plaques", "parkinson", "central", "centrale", "stable", "evolutive", "évolutive"]
    )
    etendue = _neuro_etendue(m)

    if peripherique and etendue is None and _contient_un_des(
        m,
        ["sciatique", "cruralgie", "cervico brachiale", "cervico-brachiale", "paralysie faciale", "canal carpien severe", "canal carpien sévère"]
    ):
        etendue = "un"

    if peripherique and etendue == "un":
        return "neurologie_atteintes_peripheriques_radiculaires_tronculaires_un_membre"
    if peripherique and etendue == "plusieurs":
        return "neurologie_atteintes_peripheriques_radiculaires_tronculaires_plusieurs_membres"
    if stable and etendue == "un":
        return "neurologie_affection_stable_un_membre"
    if stable and etendue == "plusieurs":
        return "neurologie_affection_stable_plusieurs"

    return None


def _resp_mode(m):
    if _contient_un_des(m, ["en groupe", "groupe", "seance de groupe", "séance de groupe"]):
        return "groupe"
    if _contient_un_des(m, ["en individuel", "individuel"]):
        return "individuel"
    return None


def inferer_regle_respiratoire(message):
    message_brut = str(message).lower()
    m = normaliser_texte(message)

    if _contient_un_des(m, ["bronchiolite", "desencombrement urgent", "désencombrement urgent", "urgence respiratoire"]):
        return "respiratoire_desencombrement_urgent"

    if "mucoviscidose" in m:
        return "respiratoire_mucoviscidose"

    if _contient_un_des(message_brut, ["bpco", "bronchopneumopathie chronique obstructive"]):
        if _contient_un_des(m, ["handicap respiratoire chronique"]) or _contient_un_des(message_brut, ["handicap respiratoire chronique"]):
            mode = _resp_mode(m)
            if mode == "individuel":
                return "respiratoire_handicap_chronique_individuel"
            if mode == "groupe":
                return "respiratoire_handicap_chronique_groupe"
            return "NEED_MODE"
        return "respiratoire_bpco_sans_handicap_chronique"

    if _contient_un_des(
        m,
        [
            "pre-op respiratoire", "pré-op respiratoire", "preop respiratoire", "préop respiratoire",
            "respiratoire pre-op", "respiratoire pré-op", "respiratoire preop", "respiratoire préop",
            "postop respiratoire", "post-op respiratoire", "respiratoire post-op", "respiratoire postop",
            "avant chirurgie thoracique", "apres chirurgie thoracique", "après chirurgie thoracique"
        ]
    ):
        return "respiratoire_preop_postop"

    chronique = _contient_un_des(
        m,
        [
            "insuffisance respiratoire chronique", "handicap respiratoire chronique",
            "rehabilitation respiratoire", "réhabilitation respiratoire",
            "readaptation respiratoire", "réadaptation respiratoire", "respiratoire chronique"
        ]
    )
    if chronique:
        mode = _resp_mode(m)
        if mode == "individuel":
            return "respiratoire_handicap_chronique_individuel"
        if mode == "groupe":
            return "respiratoire_handicap_chronique_groupe"
        return "NEED_MODE"

    if _contient_un_des(m, ["obstructive", "restrictive", "mixte", "respiratoire", "insuffisance respiratoire"]):
        return "respiratoire_obstructive_restrictive_mixte"

    return None


def _vasc_etendue(m):
    if _contient_un_des(m, ["deux membres", "deux membre", "2 membres", "deux bras", "deux jambes"]):
        return "deux"
    if _contient_un_des(m, ["un membre", "1 membre", "un bras", "une jambe"]):
        return "un"
    if _contient_mot(m, "cou") or _contient_mot(m, "face"):
        return "un"
    return None


def inferer_regle_vasculaire(message):
    m = normaliser_texte(message)

    if _contient_un_des(m, ["arteriopathie", "artériopathie", "arterite", "artérite"]):
        return "vasculaire_arteriopathie_membres_inferieurs"

    if _contient_un_des(m, ["insuffisance veineuse", "troubles trophiques"]):
        return "vasculaire_insuffisance_veineuse"

    lymph = _contient_un_des(m, ["lymphoedeme", "lymphœdeme", "lymphœdème", "drainage lymphatique", "drainage manuel"])
    post_sein = _contient_un_des(m, ["cancer du sein", "post cancer du sein", "apres cancer du sein", "après cancer du sein"])
    epaule_associee = _contient_un_des(m, ["epaule", "épaule", "bras", "membre superieur", "membre supérieur"])

    if lymph and (post_sein or "sein" in m):
        return "vasculaire_lymphoedeme_sein"

    if _contient_un_des(m, ["bandage multicouche", "bandage"]):
        etendue = _vasc_etendue(m)
        if etendue == "un":
            return "vasculaire_bandage_un_membre"
        if etendue == "deux":
            return "vasculaire_bandage_deux_membres"
        return "NEED_EXTENT_BANDAGE"

    if lymph:
        if post_sein and not epaule_associee:
            return "NEED_LYMPH_TYPE"
        etendue = _vasc_etendue(m)
        if etendue == "un":
            return "vasculaire_lymphoedeme_un_membre"
        if etendue == "deux":
            return "vasculaire_lymphoedeme_deux_membres"
        return "NEED_EXTENT_LYMPH"

    if "vasculaire" in m:
        return "NEED_VASC_TYPE"

    return None


def inferer_regle_abdominal_perineal(message):
    m = normaliser_texte(message)
    abdominal = _contient_un_des(m, ["abdominal", "abdo", "paroi abdominale", "sangle abdominale"])
    perineal = _contient_un_des(
        m,
        [
            "perinee", "périnée", "perineal", "périnéal",
            "reeducation perineale", "rééducation périnéale",
            "biofeedback", "electrostimulation perineale", "électrostimulation périnéale"
        ]
    )
    postop = _contient_un_des(
        m,
        ["pre-op", "pré-op", "preop", "préop", "post-op", "postop", "post operatoire", "post-opératoire", "pre operatoire", "préopératoire"]
    )
    postpartum = _contient_un_des(m, ["post partum", "post-partum", "postpartum", "suite de couches"])

    if abdominal and perineal:
        return "NEED_ABDO_OR_PERINEAL"
    if perineal:
        return "perinee_active"
    if abdominal and postpartum:
        return "abdominal_post_partum"
    if abdominal and postop:
        return "abdominal_preop_postop"
    if abdominal:
        return "NEED_ABDO_TYPE"
    if postpartum and not abdominal:
        return "NEED_ABDO_OR_PERINEAL"
    return None


def inferer_regle_amputation(message):
    m = normaliser_texte(message)

    plusieurs = _contient_un_des(
        m,
        ["deux membres", "2 membres", "plusieurs membres", "bilateral", "bilaterale", "bilatéral", "bilatérale", "plusieurs"]
    )
    sup = _contient_un_des(
        m,
        ["membre superieur", "membre supérieur", "superieur", "supérieur", "bras", "avant bras", "avant-bras", "main", "poignet"]
    )
    inf = _contient_un_des(
        m,
        ["membre inferieur", "membre inférieur", "inferieur", "inférieur", "jambe", "cuisse", "genou", "cheville", "pied"]
    )
    amputation_mention = _contient_un_des(m, ["amputation", "ampute", "amputé", "apres amputation", "après amputation"])

    if sup and inf:
        return "amputation_au_moins_deux_membres"
    if plusieurs:
        return "amputation_au_moins_deux_membres"
    if sup:
        return "amputation_un_membre_superieur"
    if inf:
        return "amputation_un_membre_inferieur"
    if amputation_mention:
        return "NEED_TYPE"
    return None


def inferer_regle_brulures(message):
    m = normaliser_texte(message)
    brulure_mention = _contient_un_des(m, ["brulure", "brûlure", "brulures", "brûlures", "brule", "brûlé", "brulé"])
    if not brulure_mention:
        return None

    etendue = _contient_un_des(
        m,
        ["plusieurs membres", "deux membres", "2 membres", "tronc", "thorax", "abdomen", "brulure etendue", "brûlure étendue"]
    )
    localisee = _contient_un_des(
        m,
        ["un membre", "1 membre", "un segment", "segment", "main", "bras", "jambe", "pied"]
    )

    if etendue:
        return "brulure_plusieurs_membres_tronc"
    if localisee:
        return "brulure_un_membre"
    return "NEED_EXTENT"


def inferer_regle_plusieurs_territoires(message):
    m = normaliser_texte(message)
    indices = extraire_indices(message)

    if not indices.get("multi_territoires"):
        return None

    if indices.get("chirurgie") == "oui":
        return "plusieurs_territoires_avec_chirurgie"
    if indices.get("chirurgie") == "non":
        return "plusieurs_territoires_sans_chirurgie"

    if _reponse_chirurgie_negative(m):
        return "plusieurs_territoires_sans_chirurgie"
    if _reponse_chirurgie_positive(m):
        return "plusieurs_territoires_avec_chirurgie"

    # Arbitrage minimal: demander la chirurgie si le message contient des territoires
    # classiquement ambigus dans l'arborescence existante.
    if _contient_un_des(m, ["genou", "rachis"]):
        return "NEED_CHIR_MULTI"

    return "plusieurs_territoires_sans_chirurgie"


def inferer_regle_maxillo_vestibulaire_deglutition(message):
    m = normaliser_texte(message)

    if _contient_un_des(
        m,
        ["deglutition", "déglutition", "dysphagie", "trouble de la deglutition", "trouble de la déglutition"]
    ):
        return "orl_troubles_deglutition_isoles"

    if _contient_un_des(
        m,
        ["vestibulaire", "vertiges", "troubles de l'equilibre", "troubles de l équilibre", "reeducation vestibulaire", "rééducation vestibulaire"]
    ):
        return "vestibulaire_troubles_equilibre"

    if _contient_un_des(
        m,
        ["maxillo", "maxillo-facial", "maxillo facial", "machoire", "mâchoire", "atm", "articulation temporo mandibulaire"]
    ):
        return "maxillo_facial_hors_paralysie_faciale"

    if _contient_mot(m, "orl"):
        return "NEED_TYPE"

    return None


def inferer_regle_rhumatismal_inflammatoire(message):
    m = normaliser_texte(message)
    diagnostic_rhum = _contient_un_des(
        m,
        [
            "polyarthrite",
            "polyarthrite rhumatoide",
            "polyarthrite rhumatoïde",
            "spondylarthrite",
            "rhumatisme inflammatoire",
            "rhumatismal inflammatoire"
        ]
    )
    if not diagnostic_rhum:
        return None

    atteinte_localisee = _contient_un_des(
        m,
        ["atteinte localisee", "atteinte localisée", "un membre", "1 membre"]
    )
    atteinte_plusieurs = _contient_un_des(
        m,
        ["plusieurs membres", "deux membres", "2 membres", "tronc et", "tronc +", "tronc membre"]
    )
    if atteinte_plusieurs:
        return "rhumatismales_atteinte_plusieurs_membres"
    if atteinte_localisee:
        return "rhumatismales_atteinte_localisee"
    return "NEED_EXTENT"


def inferer_regle_sujet_age(message):
    m = normaliser_texte(message)
    if _contient_un_des(
        m,
        [
            "sujet age", "sujet âgé", "personne agee", "personne âgée",
            "reeducation personne agee", "rééducation personne âgée",
            "prevention chute", "prévention chute",
            "equilibre sujet age", "équilibre sujet âgé"
        ]
    ):
        return "sujet_age_deambulation"
    return None


def _texte_brut(message):
    return str(message).lower()


def _contient_brut_un_des(message_brut, expressions):
    return any(expression in message_brut for expression in expressions)


def _segment_deviation_direct(message_brut, message_normalise):
    if not (_contient_un_des(message_normalise, ["deviation", "deviation rachis", "scoliose"]) or _contient_brut_un_des(message_brut, ["déviation", "scoliose"])):
        return None
    if _contient_un_des(message_normalise, ["plusieurs segments", "deux segments", "thoraco lombaire", "thoraco-lombaire"]) or (
        "plusieurs" in message_normalise and "rachis" in message_normalise
    ):
        return "deviation_rachis_plusieurs_segments"
    if _contient_un_des(message_normalise, ["cervical"]):
        return "deviation_rachis_cervical"
    if _contient_un_des(message_normalise, ["dorsal", "thoracique"]):
        return "deviation_rachis_dorsal"
    if _contient_un_des(message_normalise, ["lombo", "lombaire", "lombosacre", "lombo sacre", "lordose"]):
        return "deviation_rachis_lombosacre"
    return "NEED_DEVIATION_SEGMENT"


def _segments_membre_direct(message_normalise):
    if not _contient_un_des(message_normalise, ["plusieurs segments", "deux segments", "2 segments"]):
        return None
    if _contient_un_des(message_normalise, ["rachis"]):
        return "rachis_plusieurs_segments_opere" if _reponse_chirurgie_positive(message_normalise) else "rachis_plusieurs_segments"
    if _contient_un_des(message_normalise, ["membre superieur", "membre supérieur", "ms", "bras", "epaule", "épaule", "coude", "poignet", "main"]):
        return "membre_sup_plusieurs_segments_operes" if _reponse_chirurgie_positive(message_normalise) else "membre_sup_plusieurs_segments_non_operes"
    if _contient_un_des(message_normalise, ["membre inferieur", "membre inférieur", "mi", "jambe", "genou", "cheville", "hanche", "cuisse", "pied"]):
        return "membre_inf_plusieurs_segments_operes" if _reponse_chirurgie_positive(message_normalise) else "membre_inf_plusieurs_segments_non_operes"
    return None


def _plusieurs_membres_direct(message_brut, message_normalise):
    bilateral = (
        _membre_inf_bilateral_explicite(message_normalise)
        or _membre_sup_bilateral_explicite(message_normalise)
        or _contient_brut_un_des(message_brut, ["deux membres", "les deux membres", "plusieurs membres", "bilatéral", "bilatérale", "bilateral", "bilaterale"])
        or ("tronc" in message_normalise and "membre" in message_normalise)
    )
    if not bilateral:
        return None
    if _contient_un_des(message_normalise, ["neuro", "neurologie", "neurologique", "hemiplegie", "hémiplégie", "paraplegie", "paraplégie", "tetraplegie", "tétraplégie", "myopathie", "sep", "parkinson", "paralysie faciale"]):
        neuro_rule = inferer_regle_neurologie(message_normalise)
        return neuro_rule or "neurologie_affection_stable_plusieurs"
    if inferer_regle_sujet_age(message_normalise) == "sujet_age_deambulation":
        return "sujet_age_deambulation"
    if _reponse_chirurgie_positive(message_normalise):
        return "plusieurs_territoires_avec_chirurgie"
    if _reponse_chirurgie_negative(message_normalise):
        return "plusieurs_territoires_sans_chirurgie"
    return "NEED_MULTI_CHIR"


def decision_prioritaire(message):
    message_brut = _texte_brut(message)
    message_normalise = normaliser_texte(message)

    if _contient_un_des(message_normalise, ["maxillo"]) and _contient_brut_un_des(message_brut, ["hors paralysie faciale"]):
        return {"kind": "rule", "value": "maxillo_facial_hors_paralysie_faciale"}

    if _contient_un_des(message_normalise, ["paralysie faciale", "face neurologique"]):
        return {"kind": "rule", "value": "neurologie_atteintes_peripheriques_radiculaires_tronculaires_un_membre"}

    if _contient_un_des(message_normalise, ["canal carpien", "tunnel carpien", "syndrome du tunnel carpien"]) and _reponse_chirurgie_positive(message_normalise):
        return {"kind": "rule", "value": "membre_sup_canal_carpien"}
    if _contient_un_des(message_normalise, ["canal carpien", "tunnel carpien", "syndrome du tunnel carpien"]):
        return {"kind": "question", "text": "Question : canal carpien opere ou non ?", "attente": "poignet_chirurgie"}

    if _contient_un_des(message_normalise, ["coiffe"]) or (
        _contient_un_des(message_normalise, ["epaule", "épaule"])
        and _contient_un_des(message_normalise, ["tendinopathie", "tendinite"])
    ):
        if _reponse_chirurgie_negative(message_normalise):
            return {"kind": "rule", "value": "membre_sup_coiffe_non_operee"}
        if _reponse_chirurgie_positive(message_normalise):
            return {"kind": "rule", "value": "membre_sup_coiffe_operee"}

    if _contient_un_des(message_normalise, ["ligamentoplastie"]) or (_contient_un_des(message_normalise, ["lca", "ligament croise"]) and "genou" in message_normalise):
        return {"kind": "rule", "value": "membre_inf_lca"}

    if _contient_un_des(message_normalise, ["entorse cheville", "entorse externe"]) or (
        "cheville" in message_normalise and _contient_mot(message_normalise, "lle")
    ):
        if _reponse_chirurgie_negative(message_normalise):
            return {"kind": "rule", "value": "membre_inf_entorse_cheville_non_operee"}
        if _reponse_chirurgie_positive(message_normalise):
            return {"kind": "rule", "value": "membre_inf_entorse_cheville_operee"}

    if "cheville" in message_normalise:
        if "fracture" in message_normalise:
            if _reponse_chirurgie_negative(message_normalise):
                return {"kind": "rule", "value": "membre_inf_cheville_pied_non_opere"}
            if _reponse_chirurgie_positive(message_normalise):
                return {"kind": "rule", "value": "membre_inf_cheville_pied_opere"}
        if "entorse" in message_normalise and not _contient_un_des(message_normalise, ["entorse externe"]) and "lle" not in message_normalise:
            if _reponse_chirurgie_positive(message_normalise):
                return {"kind": "rule", "value": "membre_inf_cheville_pied_opere"}
            return {"kind": "rule", "value": "membre_inf_cheville_pied_non_opere"}
        if _reponse_chirurgie_negative(message_normalise):
            return {"kind": "rule", "value": "membre_inf_cheville_pied_non_opere"}
        if _reponse_chirurgie_positive(message_normalise):
            return {"kind": "rule", "value": "membre_inf_cheville_pied_opere"}

    if _contient_un_des(message_normalise, ["polyarthrite", "polyarthrite rhumatoide", "polyarthrite rhumatoïde"]):
        if _contient_un_des(message_normalise, ["deux mains", "plusieurs membres", "deux membres", "2 membres"]):
            return {"kind": "rule", "value": "rhumatismales_atteinte_plusieurs_membres"}
        if _contient_un_des(message_normalise, ["une main", "un membre", "1 membre", "localisee", "localisée"]):
            return {"kind": "rule", "value": "rhumatismales_atteinte_localisee"}

    regle_vasc = inferer_regle_vasculaire(message)
    if regle_vasc == "NEED_EXTENT_BANDAGE":
        return {"kind": "question", "text": "Question : Un membre ou deux ?", "attente": "vasculaire_bandage_etendue"}
    if regle_vasc == "NEED_EXTENT_LYMPH":
        return {"kind": "question", "text": "Question : Un ou deux membres + localisation ?", "attente": "vasculaire_lymphoedeme_etendue"}
    if regle_vasc == "NEED_LYMPH_TYPE":
        return {"kind": "question", "text": "Question : Lymphœdème simple ou post-cancer du sein ?", "attente": "vasculaire_lymphoedeme_type"}
    if regle_vasc and not regle_vasc.startswith("NEED_"):
        return {"kind": "rule", "value": regle_vasc}

    if _contient_un_des(message_normalise, ["brulure", "brûlure", "brulures", "brûlures"]):
        return {"kind": "rule", "value": "brulure_plusieurs_membres_tronc" if _contient_un_des(message_normalise, ["plusieurs", "deux", "tronc"]) else "brulure_un_membre"}

    if _contient_un_des(message_normalise, ["amputation", "ampute", "amputé"]):
        if _contient_un_des(message_normalise, ["deux", "plusieurs", "bilateral", "bilatéral"]):
            return {"kind": "rule", "value": "amputation_au_moins_deux_membres"}
        if _contient_un_des(message_normalise, ["inferieur", "inférieur", "mi", "jambe", "pied", "cuisse", "genou"]):
            return {"kind": "rule", "value": "amputation_un_membre_inferieur"}
        if _contient_un_des(message_normalise, ["superieur", "supérieur", "ms", "bras", "main", "poignet"]):
            return {"kind": "rule", "value": "amputation_un_membre_superieur"}

    if _contient_un_des(message_normalise, ["abdominal", "abdo", "paroi abdominale", "sangle abdominale"]):
        if _contient_un_des(message_normalise, ["post partum", "post-partum", "postpartum"]):
            return {"kind": "rule", "value": "abdominal_post_partum"}
        if _contient_un_des(message_normalise, ["preop", "préop", "pre-op", "pré-op", "postop", "post-op", "pre operatoire", "préopératoire", "post operatoire", "post-opératoire"]):
            return {"kind": "rule", "value": "abdominal_preop_postop"}

    if _contient_un_des(message_normalise, ["perinee", "périnée"]) and _contient_un_des(message_normalise, ["actif", "active", "biofeedback", "electrostimulation", "électrostimulation"]):
        return {"kind": "rule", "value": "perinee_active"}

    deviation = _segment_deviation_direct(message_brut, message_normalise)
    if deviation == "NEED_DEVIATION_SEGMENT":
        return {"kind": "question", "text": "Question : cervical / dorsal / lombaire / plusieurs segments ?", "attente": "rachis_deviation_segment"}
    if deviation:
        return {"kind": "rule", "value": deviation}

    if _contient_un_des(message_normalise, ["trauma cervical", "traumatisme cervical", "trauma cervical recent", "trauma cervical", "coup du lapin"]) or ("rachis cervical" in message_normalise and _trauma_recent_mention(message_normalise)):
        return {"kind": "rule", "value": "rachis_trauma_cervical_recent"}

    segments = _segments_membre_direct(message_normalise)
    if segments:
        return {"kind": "rule", "value": segments}

    if _contient_brut_un_des(message_brut, ["bpco groupe"]):
        return {"kind": "rule", "value": "respiratoire_handicap_chronique_groupe"}
    if _contient_brut_un_des(message_brut, ["bpco individuel"]):
        return {"kind": "rule", "value": "respiratoire_handicap_chronique_individuel"}
    if message_normalise.strip() in {"respiratoire", "respi"}:
        return {"kind": "question", "text": "Question : Quel type d'atteinte respiratoire ?", "attente": "respiratoire_precision"}

    multi = _plusieurs_membres_direct(message_brut, message_normalise)
    if multi == "NEED_MULTI_CHIR":
        return {"kind": "question", "text": "Question : operes ou non ? confirmer bilateral.", "attente": "plusieurs_territoires_precision"}
    if multi:
        return {"kind": "rule", "value": multi}

    return None


def inferer_regle_soins_palliatifs(message):
    m = normaliser_texte(message)
    if _contient_un_des(m, ["soins palliatifs", "fin de vie", "accompagnement fin de vie"]):
        return "soins_palliatifs"
    return None


def detecter_familles_explicites(message):
    m = normaliser_texte(message)
    familles = set()

    if _contient_un_des(m, ["neuro", "neurologie", "neurologique", "hemiplegie", "hémiplégie", "parkinson", "sep"]):
        familles.add("neurologie")
    if _contient_un_des(m, ["respiratoire", "respi", "bpco", "mucoviscidose", "bronchiolite"]):
        familles.add("respiratoire")
    if _contient_un_des(m, ["vasculaire", "lymphoedeme", "lymphœdème", "arteriopathie", "insuffisance veineuse"]):
        familles.add("vasculaire")
    if _contient_un_des(m, ["amputation", "ampute", "amputé"]):
        familles.add("amputations")
    if _contient_un_des(m, ["brulure", "brûlure", "brulures", "brûlures"]):
        familles.add("brulures")
    if _contient_un_des(m, ["polyarthrite", "spondylarthrite", "rhumatisme inflammatoire", "rhumatismal inflammatoire"]):
        familles.add("maladies rhumatismales inflammatoires")

    return familles


def essayer_resolution_depuis_message(message, contexte_precedent):
    # 1) Essayer d'abord le dernier message de precision uniquement.
    candidates = dedoublonner_regles(trouver_regles_candidates(message))
    candidate_ids = {regle["id"] for regle in candidates}
    if candidate_ids == {"rachis_lombalgie_commune", "rachis_lombosacre_non_opere"}:
        return {
            "texte": "Question : lombalgie commune ou autre atteinte rachis ?",
            "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
            "termine": False,
            "attente": "rachis_lombaire_precision"
        }
    conclusive = [regle for regle in candidates if regle_est_conclusive(regle)]
    if len(conclusive) == 1:
        question, attente = question_precision_pour_candidat_unique(message, conclusive[0])
        if question:
            return {
                "texte": question,
                "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
                "termine": False,
                "attente": attente
            }
        return {
            "texte": formater_reponse_finale(conclusive[0]),
            "nouveau_contexte": "",
            "termine": True,
            "attente": ""
        }
    if len(candidates) > 1:
        details = [regle["detail"] for regle in candidates[:3]]
        return {
            "texte": "Question : precisez parmi : " + " / ".join(details),
            "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
            "termine": False,
            "attente": "precision_multiple"
        }

    # 2) Puis retomber sur contexte + message si le dernier message est trop court.
    message_complet = f"{contexte_precedent} {message}".strip()
    candidates = dedoublonner_regles(trouver_regles_candidates(message_complet))
    candidate_ids = {regle["id"] for regle in candidates}
    if candidate_ids == {"rachis_lombalgie_commune", "rachis_lombosacre_non_opere"}:
        return {
            "texte": "Question : lombalgie commune ou autre atteinte rachis ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "rachis_lombaire_precision"
        }
    conclusive = [regle for regle in candidates if regle_est_conclusive(regle)]
    if len(conclusive) == 1:
        question, attente = question_precision_pour_candidat_unique(message_complet, conclusive[0])
        if question:
            return {
                "texte": question,
                "nouveau_contexte": message_complet,
                "termine": False,
                "attente": attente
            }
        return {
            "texte": formater_reponse_finale(conclusive[0]),
            "nouveau_contexte": "",
            "termine": True,
            "attente": ""
        }
    if len(candidates) > 1:
        details = [regle["detail"] for regle in candidates[:3]]
        return {
            "texte": "Question : precisez parmi : " + " / ".join(details),
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "precision_multiple"
        }

    return None


def determiner_question(message, candidates):
    message_normalise = normaliser_texte(message)
    indices = extraire_indices(message)

    deviation_cervicale = (
        indices["territoire"] == "rachis"
        and indices["segment"] == "cervical"
        and _contient_un_des(message_normalise, ["deviation", "déviation", "scoliose"])
    )
    if deviation_cervicale:
        age_moins_18 = _age_moins_18(message_normalise)
        trauma_recent = _trauma_recent_mention(message_normalise)
        if age_moins_18 is None:
            return "Question : moins de 18 ans ?", "rachis_cervical_deviation_age"
        if age_moins_18 is False and trauma_recent is None:
            return "Question : trauma recent ?", "rachis_cervical_deviation_trauma"

    if indices["territoire"] == "neurologie":
        peripherique = _contient_un_des(
            message_normalise,
            ["neuropathie peripherique", "neuropathie périphérique", "peripherique", "périphérique", "radiculaire", "tronculaire", "sciatique", "cruralgie", "cervico brachiale", "cervico-brachiale", "paralysie faciale"]
        )
        stable = _contient_un_des(
            message_normalise,
            ["sep", "sclerose en plaques", "sclérose en plaques", "parkinson", "stable", "evolutive", "évolutive", "central", "centrale", "avc"]
        )
        infantile = _contient_un_des(message_normalise, ["neurologie infantile", "neurologique infantile", "retard moteur", "nourrisson", "bebe", "bébé"])
        etendue = _neuro_etendue(message_normalise)

        if infantile:
            return "Question : encéphalopathie infantile ou paralysie cérébrale / polyhandicap ?", "neuro_infantile_type"
        if _contient_un_des(message_normalise, ["sciatique", "cruralgie"]):
            return "Question : neuro peripherique ou rachis ?", "sciatique_orientation"
        if (peripherique or stable) and etendue is None:
            return "Question : Un membre ou plusieurs ?", "neuro_peripherique_etendue" if peripherique else "neuro_stable_etendue"
        if "neurologie" in message_normalise or "atteinte neurologique" in message_normalise:
            return "Question : quel type neurologique ?", "neuro_precision"
        if "central" in message_normalise or "centrale" in message_normalise:
            return "Question : Hémiplégie, paraplégie/tétraplégie, myopathie ou autre ?", "neuro_centrale_type"
        if not candidates:
            return "Question : Quelle atteinte neurologique ?", "neuro_precision"

    if indices["territoire"] == "respiratoire":
        regle_resp = inferer_regle_respiratoire(message)
        if regle_resp == "NEED_MODE":
            return "Question : Individuel ou groupe ?", "respiratoire_chronique_mode"
        if regle_resp is None:
            return "Question : Quel type d'atteinte respiratoire ?", "respiratoire_precision"

    if indices["territoire"] == "vasculaire":
        regle_vasc = inferer_regle_vasculaire(message)
        if regle_vasc == "NEED_EXTENT_BANDAGE":
            return "Question : Un membre ou deux ?", "vasculaire_bandage_etendue"
        if regle_vasc == "NEED_EXTENT_LYMPH":
            return "Question : Un ou deux membres + localisation ?", "vasculaire_lymphoedeme_etendue"
        if regle_vasc == "NEED_LYMPH_TYPE":
            return "Question : Lymphœdème simple ou post-cancer du sein ?", "vasculaire_lymphoedeme_type"
        if regle_vasc == "NEED_VASC_TYPE" or regle_vasc is None:
            return "Question : Quel type d'atteinte vasculaire ?", "vasculaire_precision"

    if indices["territoire"] in ["abdominal", "perinee"]:
        regle_abdo = inferer_regle_abdominal_perineal(message)
        if regle_abdo == "NEED_ABDO_TYPE":
            return "Question : Pré/post-op ou post-partum ?", "abdominal_precision"
        if regle_abdo == "NEED_ABDO_OR_PERINEAL" or regle_abdo is None:
            return "Question : Abdominal ou périnéal ?", "abdo_or_perineal_precision"

    if indices["territoire"] == "amputations":
        regle_amp = inferer_regle_amputation(message)
        if regle_amp in [
            "amputation_un_membre_superieur",
            "amputation_un_membre_inferieur",
            "amputation_au_moins_deux_membres"
        ]:
            return None, ""
        return "Question : Membre supérieur, inférieur ou plusieurs ?", "amputations_precision"

    if indices["territoire"] == "brulures":
        regle_bru = inferer_regle_brulures(message)
        if regle_bru in ["brulure_un_membre", "brulure_plusieurs_membres_tronc"]:
            return None, ""
        return "Question : Un membre ou plusieurs / tronc ?", "brulures_precision"

    if indices["territoire"] == "plusieurs territoires":
        regle_multi = inferer_regle_plusieurs_territoires(message)
        if regle_multi == "NEED_CHIR_MULTI":
            return "Question : Chirurgie sur un des territoires ?", "plusieurs_territoires_precision"
        if regle_multi in ["plusieurs_territoires_sans_chirurgie", "plusieurs_territoires_avec_chirurgie"]:
            return None, ""

    if indices["territoire"] == "maxillo-facial / vestibulaire / ORL":
        regle_maxillo = inferer_regle_maxillo_vestibulaire_deglutition(message)
        if regle_maxillo in [
            "maxillo_facial_hors_paralysie_faciale",
            "vestibulaire_troubles_equilibre",
            "orl_troubles_deglutition_isoles"
        ]:
            return None, ""
        return "Question : Maxillo, vestibulaire ou déglutition ?", "maxillo_vestibulaire_orl_precision"

    if indices["territoire"] == "maladies rhumatismales inflammatoires":
        regle_rhum = inferer_regle_rhumatismal_inflammatoire(message)
        if regle_rhum in ["rhumatismales_atteinte_localisee", "rhumatismales_atteinte_plusieurs_membres"]:
            return None, ""

    if indices["territoire"] == "sujet age":
        regle_age = inferer_regle_sujet_age(message)
        if regle_age == "sujet_age_deambulation":
            return None, ""

    if indices["territoire"] == "soins palliatifs":
        regle_pall = inferer_regle_soins_palliatifs(message)
        if regle_pall == "soins_palliatifs":
            return None, ""

    if not candidates and _contient_un_des(message_normalise, ["post-op", "post op", "postoperatoire", "post operatoire"]):
        return "Question : Quel territoire ?", "general_precision"

    if len(candidates) == 1:
        return question_precision_pour_candidat_unique(message, candidates[0])

    if not candidates:
        if indices["territoire"] == "rachis":
            if _contient_un_des(message_normalise, ["deviation", "déviation", "scoliose", "cyphose", "lordose"]):
                return "Question : cervical / dorsal / lombaire / plusieurs segments ?", "rachis_deviation_segment"
            if indices["segment"] == "lombaire":
                return "Question : lombalgie commune ou autre atteinte rachis ?", "rachis_lombaire_precision"
            if indices["segment"] == "cervical":
                return "Question : cervicalgie / trauma recent / deviation ?", "rachis_cervical_precision"
            if indices["segment"] == "dorsal":
                return "Question : dorsal ou deviation ?", "rachis_dorsal_precision"
            return "Question : plusieurs segments ou deviation ?", "rachis_precision"

        if indices["territoire"] == "membre inferieur":
            if indices["multiple"] or _membre_inf_bilateral_explicite(message_normalise):
                return "Question : operes ou non ? confirmer bilateral.", "deux_membres_precision"
            if "genou" in message_normalise or "genoux" in message_normalise:
                if indices.get("chirurgie") == "oui":
                    return "Question : prothese / lca / meniscectomie / autre ?", "genou_chirurgie_type"
                return "Question : chirurgie du genou ou non ?", "genou_chirurgie"
            if "cheville" in message_normalise:
                if "entorse" in message_normalise and indices.get("chirurgie") is None:
                    return "Question : operee ? entorse ? referentiel ?", "cheville_precision"
                if "entorse" in message_normalise:
                    return None, ""
                if indices.get("chirurgie") == "oui":
                    if "fracture" in message_normalise:
                        return None, ""
                    return "Question : entorse externe recente ?", "cheville_entorse"
                if indices.get("chirurgie") == "non":
                    if "fracture" in message_normalise:
                        return None, ""
                    return "Question : entorse externe recente ?", "cheville_entorse"
                return "Question : operee ? entorse ? referentiel ?", "cheville_precision"
            if "hanche" in message_normalise or "cuisse" in message_normalise:
                return "Question : chirurgie de hanche ou non ?", "hanche_chirurgie"
            return "Question : quel contexte du membre inferieur ?", "membre_inf_precision"

        if indices["territoire"] == "membre superieur":
            if indices["multiple"] or _membre_sup_bilateral_explicite(message_normalise):
                return "Question : operes ou non ?", "membre_sup_multiple_precision"
            if "canal carpien" in message_normalise:
                regle = trouver_regle_par_id("membre_sup_canal_carpien")
                return None, ""
            if "coude" in message_normalise or "avant bras" in message_normalise or "avant-bras" in message_normalise:
                return "Question : operee ou non ?", "coude_chirurgie"
            if "poignet" in message_normalise or "main" in message_normalise:
                return "Question : operee ou non ?", "poignet_chirurgie"
            if "epaule" in message_normalise or "epaules" in message_normalise or "bras" in message_normalise:
                return "Question : operee ? coiffe ? fracture ? referentiel ?", "epaule_precision"
            return "Question : epaule / coude / poignet ?", "membre_sup_precision" 
        if indices["territoire"] == "neurologie":
            if _contient_un_des(message_normalise, ["sciatique", "cruralgie"]):
                return "Question : neuro peripherique ou rachis ?", "sciatique_orientation"
            return "Question : quel type neurologique ?", "neuro_precision"

        if indices["territoire"] == "respiratoire":
            return "Question : Quel type d'atteinte respiratoire ?", "respiratoire_precision"

        if indices["territoire"] == "vasculaire":
            return "Question : Quel type d'atteinte vasculaire ?", "vasculaire_precision"

        if indices["territoire"] == "maladies rhumatismales inflammatoires":
            return "Question : Atteinte localisée ou plusieurs membres ?", "rhumatismal_precision"

        if indices["territoire"] == "plusieurs territoires":
            return "Question : Chirurgie sur un des territoires ?", "plusieurs_territoires_precision"

        if indices["territoire"] == "maxillo-facial / vestibulaire / ORL":
            return "Question : Maxillo, vestibulaire ou déglutition ?", "maxillo_vestibulaire_orl_precision"

        if indices["territoire"] == "abdominal":
            return "Question : Pré/post-op ou post-partum ?", "abdominal_precision"

        if indices["territoire"] == "perinee":
            return "Question : Abdominal ou périnéal ?", "abdo_or_perineal_precision"

        if indices["territoire"] == "sujet age":
            return "Question : deambulation sujet age confirmee ?", "sujet_age_precision"

        if indices["territoire"] == "brulures":
            return "Question : Un membre ou plusieurs / tronc ?", "brulures_precision"

        if indices["territoire"] == "amputations":
            return "Question : Membre supérieur, inférieur ou plusieurs ?", "amputations_precision"

        if indices["territoire"] == "soins palliatifs":
            return "Question : soins palliatifs - cotation journaliere forfaitaire confirmee ?", "soins_palliatifs_precision"

        return "Question : quel diagnostic precis ?", "general_precision"

    if len(candidates) > 1:
        details = [regle["detail"] for regle in candidates[:3]]
        return "Question : precisez parmi : " + " / ".join(details), "precision_multiple"

    return None, ""


def gerer_reponse_courte(message, contexte_precedent, attente):
    message_normalise = normaliser_texte(message)
    message_normalise = message_normalise.lower().strip()
    message_normalise = re.sub(r"[?!.,]+\s*$", "", message_normalise).strip()

    if attente == "rachis_lombaire_precision":
        if "commune" in message_normalise or "lombalgie" in message_normalise:
            regle = trouver_regle_par_id("rachis_lombalgie_commune")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if (
            "deviation" in message_normalise
            or "déviation" in message_normalise
            or "scoliose" in message_normalise
            or "structurel" in message_normalise
            or "structural" in message_normalise
        ):
            regle = trouver_regle_par_id("deviation_rachis_lombosacre")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if "autre" in message_normalise or "lombo" in message_normalise:
            regle = trouver_regle_par_id("rachis_lombosacre_non_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : lombalgie commune / lombo-sacre / deviation ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "rachis_lombaire_precision"
        }

    if attente == "rachis_cervical_precision":
        if "cervicalgie" in message_normalise:
            regle = trouver_regle_par_id("rachis_cervicalgie_commune")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if (
            "trauma" in message_normalise
            or "traumatisme" in message_normalise
            or "recent" in message_normalise
            or "récent" in message_normalise
        ):
            regle = trouver_regle_par_id("rachis_trauma_cervical_recent")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if "deviation" in message_normalise or "déviation" in message_normalise or "scoliose" in message_normalise:
            age_moins_18 = _age_moins_18(f"{contexte_precedent} {message_normalise}".strip())
            if age_moins_18 is True:
                regle = trouver_regle_par_id("deviation_rachis_cervical")
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
            if age_moins_18 is False:
                trauma_recent = _trauma_recent_mention(f"{contexte_precedent} {message_normalise}".strip())
                if trauma_recent is True:
                    regle = trouver_regle_par_id("rachis_trauma_cervical_recent")
                    return {
                        "texte": formater_reponse_finale(regle),
                        "nouveau_contexte": "",
                        "termine": True,
                        "attente": ""
                    }
                if trauma_recent is False:
                    regle = trouver_regle_par_id("rachis_cervical_non_opere")
                    return {
                        "texte": formater_reponse_finale(regle),
                        "nouveau_contexte": "",
                        "termine": True,
                        "attente": ""
                    }
                return {
                    "texte": "Question : trauma recent ?",
                    "nouveau_contexte": f"{contexte_precedent} deviation cervicale adulte".strip(),
                    "termine": False,
                    "attente": "rachis_cervical_deviation_trauma"
                }
            return {
                "texte": "Question : moins de 18 ans ?",
                "nouveau_contexte": f"{contexte_precedent} deviation cervicale".strip(),
                "termine": False,
                "attente": "rachis_cervical_deviation_age"
            }
        return {
            "texte": "Question : cervicalgie / trauma recent / deviation ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "rachis_cervical_precision"
        }

    if attente == "rachis_cervicalgie_age":
        indices_cervicalgie = extraire_indices(f"{contexte_precedent} {message}".strip())
        if indices_cervicalgie.get("moins_18") is True or _contient_un_des(message_normalise, ["oui", "mineur", "enfant", "adolescent"]):
            regle = trouver_regle_par_id("rachis_cervicalgie_commune")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : trauma recent ou autre atteinte rachis ?",
            "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
            "termine": False,
            "attente": "rachis_cervicalgie_adulte_precision"
        }

    if attente == "rachis_cervicalgie_adulte_precision":
        contexte_complet = f"{contexte_precedent} {message}".strip()
        message_total = normaliser_texte(contexte_complet)
        if _contient_un_des(message_total, ["trauma", "traumatisme", "recent", "récent", "coup du lapin"]):
            regle = trouver_regle_par_id("rachis_trauma_cervical_recent")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Cotation impossible sans précision clinique complémentaire.",
            "nouveau_contexte": contexte_complet,
            "termine": False,
            "attente": "general_precision"
        }

    if attente == "rachis_cervical_deviation_age":
        age_moins_18 = _age_moins_18(message_normalise)
        if age_moins_18 is True or _contient_un_des(message_normalise, ["oui"]):
            regle = trouver_regle_par_id("deviation_rachis_cervical")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if age_moins_18 is False or _contient_un_des(message_normalise, ["non"]):
            trauma_recent = _trauma_recent_mention(f"{contexte_precedent} {message_normalise}".strip())
            if trauma_recent is True:
                regle = trouver_regle_par_id("rachis_trauma_cervical_recent")
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
            if trauma_recent is False:
                regle = trouver_regle_par_id("rachis_cervical_non_opere")
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
            return {
                "texte": "Question : trauma recent ?",
                "nouveau_contexte": f"{contexte_precedent} adulte".strip(),
                "termine": False,
                "attente": "rachis_cervical_deviation_trauma"
            }
        return {
            "texte": "Question : moins de 18 ans ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "rachis_cervical_deviation_age"
        }

    if attente == "rachis_cervical_deviation_trauma":
        trauma_recent = _trauma_recent_mention(message_normalise)
        if trauma_recent is True or _contient_un_des(message_normalise, ["oui"]):
            regle = trouver_regle_par_id("rachis_trauma_cervical_recent")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if trauma_recent is False or _contient_un_des(message_normalise, ["non"]):
            regle = trouver_regle_par_id("rachis_cervical_non_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : trauma recent ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "rachis_cervical_deviation_trauma"
        }

    if attente == "rachis_dorsal_precision":
        if "deviation" in message_normalise or "déviation" in message_normalise or "scoliose" in message_normalise:
            regle = trouver_regle_par_id("deviation_rachis_dorsal")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if "dorsal" in message_normalise or "thoracique" in message_normalise or "autre" in message_normalise:
            regle = trouver_regle_par_id("rachis_dorsal_non_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : dorsal ou deviation ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "rachis_dorsal_precision"
        }

    if attente == "rachis_precision":
        if "deviation" in message_normalise or "déviation" in message_normalise or "scoliose" in message_normalise:
            regle = trouver_regle_par_id("deviation_rachis_plusieurs_segments")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if "plusieurs" in message_normalise or "segments" in message_normalise or "deux segments" in message_normalise:
            regle = trouver_regle_par_id("rachis_plusieurs_segments")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : plusieurs segments ou deviation ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "rachis_precision"
        }  
    if attente == "rachis_deviation_segment":
        contexte_complet = f"{contexte_precedent} {message_normalise}".strip()
        if _contient_un_des(message_normalise, ["plusieurs", "thoraco", "thoraco lombaire", "thoraco-lombaire", "deux segments", "2 segments"]):
            regle = trouver_regle_par_id("deviation_rachis_plusieurs_segments")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _contient_un_des(message_normalise, ["dorsal", "thoracique", "cyphose"]):
            regle = trouver_regle_par_id("deviation_rachis_dorsal")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _contient_un_des(message_normalise, ["lombaire", "lombo", "lordose"]):
            regle = trouver_regle_par_id("deviation_rachis_lombosacre")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if "cervical" in message_normalise:
            age_moins_18 = _age_moins_18(contexte_complet)
            if age_moins_18 is True:
                regle = trouver_regle_par_id("deviation_rachis_cervical")
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
            if age_moins_18 is False:
                trauma_recent = _trauma_recent_mention(contexte_complet)
                if trauma_recent is True:
                    regle = trouver_regle_par_id("rachis_trauma_cervical_recent")
                    return {
                        "texte": formater_reponse_finale(regle),
                        "nouveau_contexte": "",
                        "termine": True,
                        "attente": ""
                    }
                if trauma_recent is False:
                    regle = trouver_regle_par_id("rachis_cervical_non_opere")
                    return {
                        "texte": formater_reponse_finale(regle),
                        "nouveau_contexte": "",
                        "termine": True,
                        "attente": ""
                    }
                return {
                    "texte": "Question : trauma recent ?",
                    "nouveau_contexte": f"{contexte_precedent} deviation cervicale adulte".strip(),
                    "termine": False,
                    "attente": "rachis_cervical_deviation_trauma"
                }
            return {
                "texte": "Question : moins de 18 ans ?",
                "nouveau_contexte": f"{contexte_precedent} deviation cervicale".strip(),
                "termine": False,
                "attente": "rachis_cervical_deviation_age"
            }
        return {
            "texte": "Question : cervical / dorsal / lombaire / plusieurs segments ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "rachis_deviation_segment"
        }
    if attente == "membre_sup_multiple_precision" :
        if _reponse_chirurgie_negative(message_normalise) or "non operes" in message_normalise or "non opérés" in message_normalise:
            contexte_normalise = normaliser_texte(f"{contexte_precedent} {message}".strip())
            regle = trouver_regle_par_id(
                "plusieurs_territoires_sans_chirurgie" if _membre_sup_bilateral_explicite(contexte_normalise) else "membre_sup_plusieurs_segments_non_operes"
            )
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _reponse_chirurgie_positive(message_normalise) or "operes" in message_normalise or "opérés" in message_normalise:
            contexte_normalise = normaliser_texte(f"{contexte_precedent} {message}".strip())
            regle = trouver_regle_par_id(
                "plusieurs_territoires_avec_chirurgie" if _membre_sup_bilateral_explicite(contexte_normalise) else "membre_sup_plusieurs_segments_operes"
            )
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : operes ou non ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "membre_sup_multiple_precision"
        }

    if attente == "epaule_chirurgie":
        if "coiffe" in message_normalise and ("oui" not in message_normalise and "non" not in message_normalise):
            return {
                "texte": "Question : coiffe operee ou non ?",
                "nouveau_contexte": contexte_precedent + " coiffe",
                "termine": False,
                "attente": "coiffe_chirurgie"
            }
        if _reponse_chirurgie_negative(message_normalise):
            regle = trouver_regle_par_id("membre_sup_epaule_bras_non_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _reponse_chirurgie_positive(message_normalise):
            regle = trouver_regle_par_id("membre_sup_epaule_bras_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if "coiffe" in message_normalise:
            return {
                "texte": "Question : coiffe operee ou non ?",
                "nouveau_contexte": contexte_precedent + " coiffe",
                "termine": False,
                "attente": "coiffe_chirurgie"
            }
        return {
            "texte": "Question : operee ou non ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "epaule_chirurgie"
        }

    if attente == "coiffe_chirurgie":
        if _reponse_chirurgie_negative(message_normalise):
            regle = trouver_regle_par_id("membre_sup_coiffe_non_operee")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _reponse_chirurgie_positive(message_normalise):
            regle = trouver_regle_par_id("membre_sup_coiffe_operee")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : coiffe operee ou non ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "coiffe_chirurgie"
        }

    if attente == "coude_chirurgie":
        contexte_normalise = normaliser_texte(contexte_precedent)
        fracture_avant_bras_distale = _contient_un_des(
            contexte_normalise,
            ["distale avant bras", "distale avant-bras", "pouteau colles"],
        )
        fracture_ou_luxation_coude = (
            _contient_un_des(contexte_normalise, ["fracture", "luxation", "fracture orthopedique"])
            and "coude" in contexte_normalise
        )
        if _reponse_chirurgie_negative(message_normalise):
            if fracture_avant_bras_distale:
                regle = trouver_regle_par_id("membre_sup_fracture_avant_bras_distale_non_operee")
            elif fracture_ou_luxation_coude:
                regle = trouver_regle_par_id("membre_sup_fracture_coude_adulte_non_operee")
            else:
                regle = trouver_regle_par_id("membre_sup_coude_avant_bras_non_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _reponse_chirurgie_positive(message_normalise):
            if fracture_avant_bras_distale:
                regle = trouver_regle_par_id("membre_sup_fracture_avant_bras_distale_operee")
            elif fracture_ou_luxation_coude:
                regle = trouver_regle_par_id("membre_sup_fracture_coude_adulte_operee")
            else:
                regle = trouver_regle_par_id("membre_sup_coude_avant_bras_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : operee ou non ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "coude_chirurgie"
        }

    if attente == "poignet_chirurgie":
        if "canal carpien" in message_normalise:
            regle = trouver_regle_par_id("membre_sup_canal_carpien")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _reponse_chirurgie_negative(message_normalise):
            regle = trouver_regle_par_id("membre_sup_poignet_main_non_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _reponse_chirurgie_positive(message_normalise):
            regle = trouver_regle_par_id("membre_sup_poignet_main_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : operee ou non ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "poignet_chirurgie"
        }
    if attente == "deux_membres_precision":
        contexte_complet = f"{contexte_precedent} {message}".strip()
        contexte_normalise = normaliser_texte(contexte_complet)
        if _reponse_chirurgie_positive(message_normalise) or "operes" in message_normalise or "opérés" in message_normalise:
            if "genou" in contexte_normalise or "genoux" in contexte_normalise:
                return {
                    "texte": "Question : type + confirmer bilateral (prothese / lca / meniscectomie / autre)",
                    "nouveau_contexte": contexte_complet,
                    "termine": False,
                    "attente": "deux_membres_genou_type"
                }
            regle_id = "plusieurs_territoires_avec_chirurgie" if _membre_inf_bilateral_explicite(contexte_normalise) else "membre_inf_plusieurs_segments_operes"
            regle = trouver_regle_par_id(regle_id)
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _reponse_chirurgie_negative(message_normalise) or "non operes" in message_normalise or "non opérés" in message_normalise:
            regle_id = "plusieurs_territoires_sans_chirurgie" if _membre_inf_bilateral_explicite(contexte_normalise) else "membre_inf_plusieurs_segments_non_operes"
            regle = trouver_regle_par_id(regle_id)
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : operes ou non ? confirmer bilateral.",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "deux_membres_precision"
        }

    if attente == "deux_membres_genou_type":
        contexte_complet = f"{contexte_precedent} {message}".strip()
        if not _membre_inf_bilateral_explicite(normaliser_texte(contexte_complet)):
            return {
                "texte": "Question : confirmer bilateral + type (prothese / lca / meniscectomie / autre)",
                "nouveau_contexte": contexte_complet,
                "termine": False,
                "attente": "deux_membres_genou_type"
            }
        regle = trouver_regle_par_id("plusieurs_territoires_avec_chirurgie")
        return {
            "texte": formater_reponse_finale(regle),
            "nouveau_contexte": "",
            "termine": True,
            "attente": ""
        }

    if attente == "cheville_precision":
        contexte_complet = f"{contexte_precedent} {message}".strip()
        message_total = normaliser_texte(contexte_complet)
        if _contient_un_des(message_total, ["entorse"]):
            return {
                "texte": "Question : chirurgie ou non ?",
                "nouveau_contexte": contexte_complet,
                "termine": False,
                "attente": "cheville_chirurgie"
            }
        if _reponse_chirurgie_positive(normaliser_texte(message)):
            regle = trouver_regle_par_id("membre_inf_cheville_pied_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _reponse_chirurgie_negative(normaliser_texte(message)):
            regle = trouver_regle_par_id("membre_inf_cheville_pied_non_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : operee ? entorse ? referentiel ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "cheville_precision"
        }

    if attente == "epaule_precision":
        contexte_complet = f"{contexte_precedent} {message}".strip()
        message_total = normaliser_texte(contexte_complet)
        if _contient_un_des(message_total, ["coiffe"]):
            return {
                "texte": "Question : coiffe operee ou non ?",
                "nouveau_contexte": contexte_complet,
                "termine": False,
                "attente": "coiffe_chirurgie"
            }
        if _contient_un_des(message_total, ["fracture", "humerus", "humerus"]):
            return {
                "texte": "Question : operee ou non ?",
                "nouveau_contexte": contexte_complet,
                "termine": False,
                "attente": "epaule_chirurgie"
            }
        if _reponse_chirurgie_positive(normaliser_texte(message)):
            regle = trouver_regle_par_id("membre_sup_epaule_bras_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _reponse_chirurgie_negative(normaliser_texte(message)):
            regle = trouver_regle_par_id("membre_sup_epaule_bras_non_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : operee ? coiffe ? fracture ? referentiel ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "epaule_precision"
        }

    if attente == "genou_non_opere_precision":
        if "genou" in contexte_precedent or "genoux" in contexte_precedent:
            regle = trouver_regle_par_id("membre_inf_genou_jambe_non_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : quel diagnostic du genou non opere ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "genou_non_opere_precision"
        }

    if attente == "membre_inf_precision":
        if "hanche" in message_normalise or "cuisse" in message_normalise:
            return {
                "texte": "Question : chirurgie de hanche ou non ?",
                "nouveau_contexte": contexte_precedent + " hanche",
                "termine": False,
                "attente": "hanche_chirurgie"
            }
        if "genou" in message_normalise or "jambe" in message_normalise:
            return {
                "texte": "Question : chirurgie du genou ou non ?",
                "nouveau_contexte": contexte_precedent + " genou",
                "termine": False,
                "attente": "genou_chirurgie"
            }
        return {
            "texte": "Question : genou / cheville / hanche ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "membre_inf_precision"
        }

    if attente == "hanche_chirurgie":
        if _reponse_chirurgie_positive(message_normalise):
            return {
                "texte": "Question : prothese de hanche ou autre ?",
                "nouveau_contexte": contexte_precedent + " chirurgie",
                "termine": False,
                "attente": "hanche_chirurgie_type"
            }
        if "prothese" in message_normalise or "prothèse" in message_normalise:
            regle = trouver_regle_par_id("membre_inf_pth")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _reponse_chirurgie_negative(message_normalise):
            regle = trouver_regle_par_id("membre_inf_hanche_cuisse_non_operee")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : chirurgie de hanche ou non ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "hanche_chirurgie"
        }
    if attente == "hanche_chirurgie_type":
        if "prothese" in message_normalise or "prothèse" in message_normalise:
            regle = trouver_regle_par_id("membre_inf_pth")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if "autre" in message_normalise:
            regle = trouver_regle_par_id("membre_inf_hanche_cuisse_operee")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : prothese de hanche ou autre ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "hanche_chirurgie_type"
        }
    if attente == "genou_chirurgie":
        if _reponse_chirurgie_positive(message_normalise):
            return {
                "texte": "Question : prothese / lca / meniscectomie / autre ?",
                "nouveau_contexte": contexte_precedent + " chirurgie",
                "termine": False,
                "attente": "genou_chirurgie_type"
            }
        if _reponse_chirurgie_negative(message_normalise):
            regle = trouver_regle_par_id("membre_inf_genou_jambe_non_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : chirurgie du genou ou non ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "genou_chirurgie"
        }

    if attente == "genou_chirurgie_type":
        if "prothese" in message_normalise or "prothèse" in message_normalise:
            regle = trouver_regle_par_id("membre_inf_ptg")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if "lca" in message_normalise or "ligament" in message_normalise or "ligamentoplastie" in message_normalise:
            regle = trouver_regle_par_id("membre_inf_lca")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if "meniscectomie" in message_normalise or "menisque" in message_normalise or "ménisque" in message_normalise:
            regle = trouver_regle_par_id("membre_inf_meniscectomie")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _contient_un_des(message_normalise, ["autre", "intervention", "chirurgie"]):
            regle = trouver_regle_par_id("membre_inf_genou_jambe_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : prothese / lca / meniscectomie / autre ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "genou_chirurgie_type"
        }

    if attente == "cheville_chirurgie":
        if _reponse_chirurgie_positive(message_normalise):
            contexte = f"{contexte_precedent} chirurgie".strip()
            if "entorse" in contexte_precedent:
                regle = trouver_regle_par_id("membre_inf_entorse_cheville_operee")
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
            if "fracture" in contexte_precedent:
                regle = trouver_regle_par_id("membre_inf_cheville_pied_opere")
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
            return {
                "texte": "Question : entorse externe recente ?",
                "nouveau_contexte": contexte,
                "termine": False,
                "attente": "cheville_entorse"
            }
        if _reponse_chirurgie_negative(message_normalise):
            contexte = f"{contexte_precedent} non chirurgie".strip()
            if "entorse" in contexte_precedent:
                regle = trouver_regle_par_id("membre_inf_entorse_cheville_non_operee")
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
            if "fracture" in contexte_precedent:
                regle = trouver_regle_par_id("membre_inf_cheville_pied_non_opere")
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
            return {
                "texte": "Question : entorse externe recente ?",
                "nouveau_contexte": contexte,
                "termine": False,
                "attente": "cheville_entorse"
            }
        return {
            "texte": "Question : chirurgie ou non ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "cheville_chirurgie"
        }

    if attente == "cheville_entorse":
        chirurgie_positive = _reponse_chirurgie_positive(contexte_precedent)
        if "entorse" in message_normalise or _contient_un_des(message_normalise, ["oui"]):
            regle_id = "membre_inf_entorse_cheville_operee" if chirurgie_positive else "membre_inf_entorse_cheville_non_operee"
            regle = trouver_regle_par_id(regle_id)
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _contient_un_des(message_normalise, ["non", "autre", "fracture"]):
            regle_id = "membre_inf_cheville_pied_opere" if chirurgie_positive else "membre_inf_cheville_pied_non_opere"
            regle = trouver_regle_par_id(regle_id)
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : entorse externe recente ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "cheville_entorse"
        }

    if attente == "membre_sup_precision":
        if "epaule" in message_normalise or "epaules" in message_normalise or "bras" in message_normalise:
            return {
                "texte": "Question : operee ou non ?",
                "nouveau_contexte": contexte_precedent + " epaule",
                "termine": False,
                "attente": "epaule_chirurgie"
            }
        if "coude" in message_normalise or "avant bras" in message_normalise or "avant-bras" in message_normalise:
            return {
                "texte": "Question : operee ou non ?",
                "nouveau_contexte": contexte_precedent + " coude",
                "termine": False,
                "attente": "coude_chirurgie"
            }
        if "poignet" in message_normalise or "main" in message_normalise:
            return {
                "texte": "Question : operee ou non ?",
                "nouveau_contexte": contexte_precedent + " poignet",
                "termine": False,
                "attente": "poignet_chirurgie"
            }
        if "canal carpien" in message_normalise:
            regle = trouver_regle_par_id("membre_sup_canal_carpien")
            if regle is None:
                return reponse_prudente(contexte_precedent, "general_precision")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : epaule / coude / poignet ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "membre_sup_precision"
        }

    if attente == "precision_multiple":
        resolution = essayer_resolution_depuis_message(message, contexte_precedent)
        if resolution is not None:
            return resolution
        message_complet = f"{contexte_precedent} {message}".strip()
        candidates = dedoublonner_regles(trouver_regles_candidates(message_complet))
        if len(candidates) == 1:
            question, nouvelle_attente = question_precision_pour_candidat_unique(message_complet, candidates[0])
            if question:
                return {
                    "texte": question,
                    "nouveau_contexte": message_complet,
                    "termine": False,
                    "attente": nouvelle_attente
                }
            return {
                "texte": formater_reponse_finale(candidates[0]),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if len(candidates) > 1:
            details = [regle["detail"] for regle in candidates[:3]]
            return {
                "texte": "Question : precisez parmi : " + " / ".join(details),
                "nouveau_contexte": message_complet,
                "termine": False,
                "attente": "precision_multiple"
            }
        return {
            "texte": "Question : quel diagnostic precis ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "general_precision"
        }

    if attente == "neuro_precision":
        neuro_rule = inferer_regle_neurologie(message)
        if neuro_rule == "NEED_INFANTILE_TYPE":
            return {
                "texte": "Question : encéphalopathie infantile ou paralysie cérébrale / polyhandicap ?",
                "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
                "termine": False,
                "attente": "neuro_infantile_type"
            }
        if neuro_rule is not None:
            regle = trouver_regle_par_id(neuro_rule)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        resolution = essayer_resolution_depuis_message(message, contexte_precedent)
        if resolution is not None:
            return resolution
        if _contient_un_des(message_normalise, ["peripherique", "périphérique", "radiculaire", "tronculaire", "neuropathie"]):
            return {
                "texte": "Question : Un membre ou plusieurs ?",
                "nouveau_contexte": contexte_precedent + " peripherique",
                "termine": False,
                "attente": "neuro_peripherique_etendue"
            }
        if _contient_un_des(message_normalise, ["central", "centrale", "sep", "sclerose en plaques", "sclérose en plaques", "parkinson"]):
            return {
                "texte": "Question : Un membre ou plusieurs ?",
                "nouveau_contexte": contexte_precedent + " centrale",
                "termine": False,
                "attente": "neuro_stable_etendue"
            }
        return {
            "texte": "Question : Quelle atteinte neurologique ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "neuro_precision"
        }

    if attente == "neuro_infantile_type":
        neuro_rule = inferer_regle_neurologie(f"{contexte_precedent} {message}".strip())
        if neuro_rule in ["neurologie_encephalopathie_infantile", "neurologie_paralysie_cerebrale_polyhandicap"]:
            regle = trouver_regle_par_id(neuro_rule)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        if _contient_un_des(message_normalise, ["encephalopathie", "encéphalopathie"]):
            regle = trouver_regle_par_id("neurologie_encephalopathie_infantile")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _contient_un_des(message_normalise, ["paralysie cerebrale", "paralysie cérébrale", "polyhandicap", "imc"]):
            regle = trouver_regle_par_id("neurologie_paralysie_cerebrale_polyhandicap")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        return {
            "texte": "Question : encéphalopathie infantile ou paralysie cérébrale / polyhandicap ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "neuro_infantile_type"
        }

    if attente == "neuro_orientation":
        if _contient_un_des(message_normalise, ["peripherique", "périphérique", "radiculaire", "tronculaire", "neuropathie"]):
            return {
                "texte": "Question : Un membre ou plusieurs ?",
                "nouveau_contexte": contexte_precedent + " peripherique",
                "termine": False,
                "attente": "neuro_peripherique_etendue"
            }
        if _contient_un_des(message_normalise, ["central", "centrale"]):
            return {
                "texte": "Question : Hémiplégie, paraplégie/tétraplégie, myopathie ou autre ?",
                "nouveau_contexte": contexte_precedent + " centrale",
                "termine": False,
                "attente": "neuro_centrale_type"
            }
        return {
            "texte": "Question : Atteinte périphérique ou centrale ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "neuro_orientation"
        }

    if attente == "neuro_centrale_type":
        neuro_rule = inferer_regle_neurologie(message)
        if neuro_rule is not None:
            regle = trouver_regle_par_id(neuro_rule)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        if _contient_un_des(message_normalise, ["sep", "sclerose en plaques", "sclérose en plaques", "parkinson", "autre"]):
            return {
                "texte": "Question : Un membre ou plusieurs ?",
                "nouveau_contexte": contexte_precedent + " stable",
                "termine": False,
                "attente": "neuro_stable_etendue"
            }
        return {
            "texte": "Question : Hémiplégie, paraplégie/tétraplégie, myopathie ou autre ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "neuro_centrale_type"
        }

    if attente == "neuro_peripherique_etendue":
        etendue = _neuro_etendue(message_normalise)
        if etendue == "un":
            regle = trouver_regle_par_id("neurologie_atteintes_peripheriques_radiculaires_tronculaires_un_membre")
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        if etendue == "plusieurs":
            regle = trouver_regle_par_id("neurologie_atteintes_peripheriques_radiculaires_tronculaires_plusieurs_membres")
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Un membre ou plusieurs ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "neuro_peripherique_etendue"
        }

    if attente == "neuro_stable_etendue":
        if _contient_un_des(message_normalise, ["plusieurs", "plusieurs membres", "deux membres", "2 membres"]):
            etendue = "plusieurs"
        elif _contient_un_des(message_normalise, ["un", "un membre", "face"]):
            etendue = "un"
        else:
            etendue = _neuro_etendue(message_normalise)
        if etendue == "un":
            regle = trouver_regle_par_id("neurologie_affection_stable_un_membre")
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        if etendue == "plusieurs":
            regle = trouver_regle_par_id("neurologie_affection_stable_plusieurs")
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Un membre ou plusieurs ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "neuro_stable_etendue"
        }

    if attente == "respiratoire_precision":
        regle_resp = inferer_regle_respiratoire(f"{contexte_precedent} {message}".strip())
        if regle_resp == "NEED_MODE":
            return {
                "texte": "Question : Individuel ou groupe ?",
                "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
                "termine": False,
                "attente": "respiratoire_chronique_mode"
            }
        if regle_resp is not None:
            regle = trouver_regle_par_id(regle_resp)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        resolution = essayer_resolution_depuis_message(message, contexte_precedent)
        if resolution is not None:
            return resolution
        return {
            "texte": "Question : Quel type d'atteinte respiratoire ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "respiratoire_precision"
        }

    if attente == "respiratoire_chronique_mode":
        regle_resp = inferer_regle_respiratoire(f"{contexte_precedent} {message}".strip())
        if regle_resp in ["respiratoire_handicap_chronique_individuel", "respiratoire_handicap_chronique_groupe"]:
            regle = trouver_regle_par_id(regle_resp)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Individuel ou groupe ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "respiratoire_chronique_mode"
        }

    if attente == "vasculaire_precision":
        regle_vasc = inferer_regle_vasculaire(f"{contexte_precedent} {message}".strip())
        if regle_vasc == "NEED_EXTENT_BANDAGE":
            return {
                "texte": "Question : Un membre ou deux ?",
                "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
                "termine": False,
                "attente": "vasculaire_bandage_etendue"
            }
        if regle_vasc == "NEED_EXTENT_LYMPH":
            return {
                "texte": "Question : Un membre ou deux ?",
                "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
                "termine": False,
                "attente": "vasculaire_lymphoedeme_etendue"
            }
        if regle_vasc == "NEED_LYMPH_TYPE":
            return {
                "texte": "Question : Lymphœdème simple ou post-cancer du sein ?",
                "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
                "termine": False,
                "attente": "vasculaire_lymphoedeme_type"
            }
        if regle_vasc is not None and regle_vasc not in ["NEED_VASC_TYPE"]:
            regle = trouver_regle_par_id(regle_vasc)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        resolution = essayer_resolution_depuis_message(message, contexte_precedent)
        if resolution is not None:
            return resolution
        return {
            "texte": "Question : Quel type d'atteinte vasculaire ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "vasculaire_precision"
        }

    if attente == "vasculaire_lymphoedeme_type":
        regle_vasc = inferer_regle_vasculaire(f"{contexte_precedent} {message}".strip())
        if regle_vasc == "vasculaire_lymphoedeme_sein":
            regle = trouver_regle_par_id(regle_vasc)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        if _contient_un_des(message_normalise, ["simple", "lymphoedeme", "lymphœdème"]):
            return {
                "texte": "Question : Un ou deux membres + localisation ?",
                "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
                "termine": False,
                "attente": "vasculaire_lymphoedeme_etendue"
            }
        return {
            "texte": "Question : Lymphœdème simple ou post-cancer du sein ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "vasculaire_lymphoedeme_type"
        }

    if attente == "vasculaire_lymphoedeme_etendue":
        regle_vasc = inferer_regle_vasculaire(f"{contexte_precedent} {message}".strip())
        if regle_vasc in ["vasculaire_lymphoedeme_un_membre", "vasculaire_lymphoedeme_deux_membres"]:
            regle = trouver_regle_par_id(regle_vasc)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Un ou deux membres + localisation ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "vasculaire_lymphoedeme_etendue"
        }

    if attente == "sciatique_orientation":
        contexte_complet = f"{contexte_precedent} {message}".strip()
        message_total = normaliser_texte(contexte_complet)
        if _contient_un_des(message_total, ["rachis", "lombalgie", "lombaire", "ram"]):
            return {
                "texte": "Question : lombalgie commune ou autre atteinte rachis ?",
                "nouveau_contexte": contexte_complet,
                "termine": False,
                "attente": "rachis_lombaire_precision"
            }
        if _contient_un_des(message_total, ["peripherique", "périphérique", "neuro"]):
            return {
                "texte": "Question : Un membre ou plusieurs ?",
                "nouveau_contexte": contexte_complet,
                "termine": False,
                "attente": "neuro_peripherique_etendue"
            }
        return {
            "texte": "Question : neuro peripherique ou rachis ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "sciatique_orientation"
        }

    if attente == "vasculaire_bandage_etendue":
        regle_vasc = inferer_regle_vasculaire(f"{contexte_precedent} {message}".strip())
        if regle_vasc in ["vasculaire_bandage_un_membre", "vasculaire_bandage_deux_membres"]:
            regle = trouver_regle_par_id(regle_vasc)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Un membre ou deux ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "vasculaire_bandage_etendue"
        }

    if attente == "general_precision":
        return {
            "texte": "Question : quel diagnostic precis ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "general_precision"
        }

    if attente == "rhumatismal_precision":
        regle_rhum = inferer_regle_rhumatismal_inflammatoire(f"{contexte_precedent} {message}".strip())
        if regle_rhum in ["rhumatismales_atteinte_localisee", "rhumatismales_atteinte_plusieurs_membres"]:
            regle = trouver_regle_par_id(regle_rhum)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Atteinte localisée ou plusieurs membres ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "rhumatismal_precision"
        }

    if attente == "plusieurs_territoires_precision":
        regle_multi = inferer_regle_plusieurs_territoires(f"{contexte_precedent} {message}".strip())
        if regle_multi in ["plusieurs_territoires_sans_chirurgie", "plusieurs_territoires_avec_chirurgie"]:
            regle = trouver_regle_par_id(regle_multi)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Chirurgie sur un des territoires ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "plusieurs_territoires_precision"
        }

    if attente == "maxillo_vestibulaire_orl_precision":
        regle_maxillo = inferer_regle_maxillo_vestibulaire_deglutition(f"{contexte_precedent} {message}".strip())
        if regle_maxillo in [
            "maxillo_facial_hors_paralysie_faciale",
            "vestibulaire_troubles_equilibre",
            "orl_troubles_deglutition_isoles"
        ]:
            regle = trouver_regle_par_id(regle_maxillo)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Maxillo, vestibulaire ou déglutition ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "maxillo_vestibulaire_orl_precision"
        }

    if attente == "abdominal_precision":
        regle_abdo = inferer_regle_abdominal_perineal(f"{contexte_precedent} {message}".strip())
        if regle_abdo in ["abdominal_preop_postop", "abdominal_post_partum"]:
            regle = trouver_regle_par_id(regle_abdo)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Pré/post-op ou post-partum ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "abdominal_precision"
        }

    if attente == "perinee_precision":
        regle_abdo = inferer_regle_abdominal_perineal(f"{contexte_precedent} {message}".strip())
        if regle_abdo == "perinee_active":
            regle = trouver_regle_par_id("perinee_active")
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : quel contexte perineo-sphincterien ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "perinee_precision"
        }

    if attente == "abdo_or_perineal_precision":
        regle_abdo = inferer_regle_abdominal_perineal(f"{contexte_precedent} {message}".strip())
        if regle_abdo == "perinee_active":
            regle = trouver_regle_par_id("perinee_active")
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        if regle_abdo in ["abdominal_preop_postop", "abdominal_post_partum"]:
            regle = trouver_regle_par_id(regle_abdo)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        if regle_abdo == "NEED_ABDO_TYPE":
            return {
                "texte": "Question : Pré/post-op ou post-partum ?",
                "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
                "termine": False,
                "attente": "abdominal_precision"
            }
        return {
            "texte": "Question : Abdominal ou périnéal ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "abdo_or_perineal_precision"
        }

    if attente == "sujet_age_precision":
        regle_age = inferer_regle_sujet_age(f"{contexte_precedent} {message}".strip())
        if regle_age == "sujet_age_deambulation":
            regle = trouver_regle_par_id(regle_age)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : deambulation sujet age confirmee ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "sujet_age_precision"
        }

    if attente == "brulures_precision":
        regle_bru = inferer_regle_brulures(f"{contexte_precedent} {message}".strip())
        if regle_bru in ["brulure_un_membre", "brulure_plusieurs_membres_tronc"]:
            regle = trouver_regle_par_id(regle_bru)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Un membre ou plusieurs / tronc ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "brulures_precision"
        }

    if attente == "amputations_precision":
        regle_amp = inferer_regle_amputation(f"{contexte_precedent} {message}".strip())
        if regle_amp in [
            "amputation_un_membre_superieur",
            "amputation_un_membre_inferieur",
            "amputation_au_moins_deux_membres"
        ]:
            regle = trouver_regle_par_id(regle_amp)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Membre supérieur, inférieur ou plusieurs ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "amputations_precision"
        }

    if attente == "soins_palliatifs_precision":
        regle_pall = inferer_regle_soins_palliatifs(f"{contexte_precedent} {message}".strip())
        if regle_pall == "soins_palliatifs":
            regle = trouver_regle_par_id(regle_pall)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : soins palliatifs - cotation journaliere forfaitaire confirmee ?",
            "nouveau_contexte": contexte_precedent,
            "termine": False,
            "attente": "soins_palliatifs_precision"
        }

    return None


def repondre(message, contexte_precedent="", attente=""):
    if attente:
        resultat_court = gerer_reponse_courte(message, contexte_precedent, attente)
        if resultat_court is not None:
            return resultat_court
        # Garde-fou: ne pas sortir de cotation finale si une attente est active mais non resolue.
        return {
            "texte": "Question : pouvez-vous preciser le diagnostic ?",
            "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
            "termine": False,
            "attente": "general_precision"
        }

    message_complet = f"{contexte_precedent} {message}".strip()
    prioritaire = decision_prioritaire(message_complet)
    if prioritaire is not None:
        if prioritaire["kind"] == "rule":
            regle = trouver_regle_par_id(prioritaire["value"])
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        if prioritaire["kind"] == "question":
            return {
                "texte": prioritaire["text"],
                "nouveau_contexte": message_complet,
                "termine": False,
                "attente": prioritaire["attente"]
            }
    message_brut = str(message_complet).lower()
    message_normalise = normaliser_texte(message_complet)
    indices = extraire_indices(message_complet)

    # Priorité NGAP rachis: au moins 2 segments rachidiens distincts -> rachis_plusieurs_segments / rachis_plusieurs_segments_opere,
    # sauf contexte de déviation qui reste géré par la branche dédiée.
    segments_rachis = _segments_rachis_detectes(message_normalise)
    if (
        len(segments_rachis) >= 2
        and not indices.get("multi_territoires")
        and not _contient_un_des(message_normalise, ["deviation", "déviation", "scoliose"])
    ):
        regle = trouver_regle_par_id("rachis_plusieurs_segments_opere" if indices.get("chirurgie") == "oui" else "rachis_plusieurs_segments")
        if regle_est_conclusive(regle):
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }

    familles_explicites = detecter_familles_explicites(message_complet)
    if len(familles_explicites) >= 2:
        return {
            "texte": "Question : Quelle famille principale ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "general_precision"
        }

    message_normalise = normaliser_texte(message_complet)
    if any(term in message_brut for term in ["sciatique", "cruralgie"]):
        return {
            "texte": "Question : neuro peripherique ou rachis ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "sciatique_orientation"
        }
    regle_vasc_directe = inferer_regle_vasculaire(message_complet) if indices["territoire"] == "vasculaire" else None
    if regle_vasc_directe == "NEED_EXTENT_LYMPH":
        return {
            "texte": "Question : Un ou deux membres + localisation ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "vasculaire_lymphoedeme_etendue"
        }
    if indices["territoire"] == "neurologie" and any(term in message_brut for term in ["neurologie", "neurologique", " neuro "]) and not any(term in message_brut for term in ["hémiplég", "hemipleg", "paraplég", "parapleg", "tétraplég", "tetrapleg", "myopath", "parkinson", "sep", "retard moteur", "paralysie faciale"]):
        return {
            "texte": "Question : quel type neurologique ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "neuro_precision"
        }
    if indices["territoire"] == "rachis" and "lombalgie" in message_brut and not any(term in message_brut for term in ["commune", "lombo sacre", "lombo-sacre", "deviation", "scoliose", "lordose", "cyphose"]):
        return {
            "texte": "Question : lombalgie commune ou autre atteinte rachis ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "rachis_lombaire_precision"
        }
    if "genou" in message_normalise and _contient_un_des(message_normalise, ["lca", "ligament croise"]):
        regle = trouver_regle_par_id("membre_inf_lca")
        if regle_est_conclusive(regle):
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }

    regle_rhum = inferer_regle_rhumatismal_inflammatoire(message_complet)
    if regle_rhum in ["rhumatismales_atteinte_localisee", "rhumatismales_atteinte_plusieurs_membres"]:
        regle = trouver_regle_par_id(regle_rhum)
        if regle_est_conclusive(regle):
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
    if regle_rhum == "NEED_EXTENT":
        return {
            "texte": "Question : Atteinte localisée ou plusieurs membres ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "rhumatismal_precision"
        }

    regle_age = inferer_regle_sujet_age(message_complet)
    if regle_age == "sujet_age_deambulation":
        regle = trouver_regle_par_id(regle_age)
        if regle_est_conclusive(regle):
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }

    regle_pall = inferer_regle_soins_palliatifs(message_complet)
    if regle_pall == "soins_palliatifs":
        regle = trouver_regle_par_id(regle_pall)
        if regle_est_conclusive(regle):
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }

    if indices["territoire"] == "membre inferieur" and (indices.get("multiple") or _membre_inf_bilateral_explicite(message_normalise)):
        regle_id = None
        if indices.get("chirurgie") == "oui":
            regle_id = "plusieurs_territoires_avec_chirurgie" if _membre_inf_bilateral_explicite(message_normalise) else "membre_inf_plusieurs_segments_operes"
        elif indices.get("chirurgie") == "non":
            regle_id = "plusieurs_territoires_sans_chirurgie" if _membre_inf_bilateral_explicite(message_normalise) else "membre_inf_plusieurs_segments_non_operes"
        if regle_id:
            regle = trouver_regle_par_id(regle_id)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }

    if indices["territoire"] == "membre superieur" and (indices.get("multiple") or _membre_sup_bilateral_explicite(message_normalise)):
        regle_id = None
        if indices.get("chirurgie") == "oui":
            regle_id = "plusieurs_territoires_avec_chirurgie" if _membre_sup_bilateral_explicite(message_normalise) else "membre_sup_plusieurs_segments_operes"
        elif indices.get("chirurgie") == "non":
            regle_id = "plusieurs_territoires_sans_chirurgie" if _membre_sup_bilateral_explicite(message_normalise) else "membre_sup_plusieurs_segments_non_operes"
        if regle_id:
            regle = trouver_regle_par_id(regle_id)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }

    if indices["territoire"] == "neurologie":
        neuro_rule = inferer_regle_neurologie(message_complet)
        if neuro_rule is not None:
            regle = trouver_regle_par_id(neuro_rule)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
    if indices["territoire"] == "respiratoire":
        regle_resp = inferer_regle_respiratoire(message_complet)
        if regle_resp == "NEED_MODE":
            return {
                "texte": "Question : Individuel ou groupe ?",
                "nouveau_contexte": message_complet,
                "termine": False,
                "attente": "respiratoire_chronique_mode"
            }
        if regle_resp is not None:
            regle = trouver_regle_par_id(regle_resp)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        if _contient_un_des(normaliser_texte(message_complet), ["respiratoire", "respi"]):
            return {
                "texte": "Question : Quel type d'atteinte respiratoire ?",
                "nouveau_contexte": message_complet,
                "termine": False,
                "attente": "respiratoire_precision"
            }
    if indices["territoire"] == "vasculaire":
        regle_vasc = inferer_regle_vasculaire(message_complet)
        if regle_vasc == "NEED_EXTENT_BANDAGE":
            return {
                "texte": "Question : Un membre ou deux ?",
                "nouveau_contexte": message_complet,
                "termine": False,
                "attente": "vasculaire_bandage_etendue"
            }
        if regle_vasc == "NEED_EXTENT_LYMPH":
            return {
                "texte": "Question : Un ou deux membres + localisation ?",
                "nouveau_contexte": message_complet,
                "termine": False,
                "attente": "vasculaire_lymphoedeme_etendue"
            }
        if regle_vasc == "NEED_LYMPH_TYPE":
            return {
                "texte": "Question : Lymphœdème simple ou post-cancer du sein ?",
                "nouveau_contexte": message_complet,
                "termine": False,
                "attente": "vasculaire_lymphoedeme_type"
            }
        if regle_vasc is not None and regle_vasc not in ["NEED_VASC_TYPE"]:
            regle = trouver_regle_par_id(regle_vasc)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Quel type d'atteinte vasculaire ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "vasculaire_precision"
        }
    if indices["territoire"] in ["abdominal", "perinee"]:
        regle_abdo = inferer_regle_abdominal_perineal(message_complet)
        if regle_abdo in ["abdominal_preop_postop", "abdominal_post_partum", "perinee_active"]:
            regle = trouver_regle_par_id(regle_abdo)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        if regle_abdo == "NEED_ABDO_TYPE":
            return {
                "texte": "Question : Pré/post-op ou post-partum ?",
                "nouveau_contexte": message_complet,
                "termine": False,
                "attente": "abdominal_precision"
            }
        return {
            "texte": "Question : Abdominal ou périnéal ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "abdo_or_perineal_precision"
        }
    if indices["territoire"] == "amputations":
        regle_amp = inferer_regle_amputation(message_complet)
        if regle_amp in [
            "amputation_un_membre_superieur",
            "amputation_un_membre_inferieur",
            "amputation_au_moins_deux_membres"
        ]:
            regle = trouver_regle_par_id(regle_amp)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Membre supérieur, inférieur ou plusieurs ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "amputations_precision"
        }
    if indices["territoire"] == "brulures":
        regle_bru = inferer_regle_brulures(message_complet)
        if regle_bru in ["brulure_un_membre", "brulure_plusieurs_membres_tronc"]:
            regle = trouver_regle_par_id(regle_bru)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Un membre ou plusieurs / tronc ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "brulures_precision"
        }
    if indices["territoire"] == "plusieurs territoires":
        regle_multi = inferer_regle_plusieurs_territoires(message_complet)
        if regle_multi in ["plusieurs_territoires_sans_chirurgie", "plusieurs_territoires_avec_chirurgie"]:
            regle = trouver_regle_par_id(regle_multi)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Chirurgie sur un des territoires ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "plusieurs_territoires_precision"
        }
    if indices["territoire"] == "maxillo-facial / vestibulaire / ORL":
        regle_maxillo = inferer_regle_maxillo_vestibulaire_deglutition(message_complet)
        if regle_maxillo in [
            "maxillo_facial_hors_paralysie_faciale",
            "vestibulaire_troubles_equilibre",
            "orl_troubles_deglutition_isoles"
        ]:
            regle = trouver_regle_par_id(regle_maxillo)
            if regle_est_conclusive(regle):
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
        return {
            "texte": "Question : Maxillo, vestibulaire ou déglutition ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "maxillo_vestibulaire_orl_precision"
        }
    candidates = trouver_regles_candidates(message_complet)
    candidates = dedoublonner_regles(candidates)

    question, nouvelle_attente = determiner_question(message_complet, candidates)
    if question:
        return {
            "texte": question,
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": nouvelle_attente
        }

    if len(candidates) == 1:
        question, nouvelle_attente = question_precision_pour_candidat_unique(message_complet, candidates[0])
        if question:
            return {
                "texte": question,
                "nouveau_contexte": message_complet,
                "termine": False,
                "attente": nouvelle_attente
            }
        if not regle_est_conclusive(candidates[0]):
            return reponse_prudente(message_complet, "general_precision")
        return {
            "texte": formater_reponse_finale(candidates[0]),
            "nouveau_contexte": "",
            "termine": True,
            "attente": ""
        }

    return {
        "texte": "Question : quel diagnostic precis ?",
        "nouveau_contexte": message_complet,
        "termine": False,
        "attente": "general_precision"
    }


def traiter_transcription_texte(message: str, contexte_precedent: str = "", attente: str = ""):
    return repondre(message, contexte_precedent, attente)


CHOIX_ATTENTE = {
    "rachis_lombaire_precision": [
        {"label": "Lombalgie commune", "value": "lombalgie commune"},
        {"label": "Lombo-sacré", "value": "lombo sacre"},
        {"label": "Déviation", "value": "deviation"},
    ],
    "rachis_cervical_precision": [
        {"label": "Cervicalgie", "value": "cervicalgie"},
        {"label": "Trauma récent", "value": "trauma recent"},
        {"label": "Déviation", "value": "deviation"},
    ],
    "rachis_cervicalgie_age": [
        {"label": "Oui", "value": "oui"},
        {"label": "Non", "value": "non"},
    ],
    "rachis_cervicalgie_adulte_precision": [
        {"label": "Trauma récent", "value": "trauma recent"},
        {"label": "Autre atteinte", "value": "autre"},
    ],
    "rachis_cervical_deviation_age": [
        {"label": "Oui", "value": "oui"},
        {"label": "Non", "value": "non"},
    ],
    "rachis_cervical_deviation_trauma": [
        {"label": "Oui", "value": "oui"},
        {"label": "Non", "value": "non"},
    ],
    "rachis_dorsal_precision": [
        {"label": "Dorsal", "value": "dorsal"},
        {"label": "Déviation", "value": "deviation"},
    ],
    "rachis_precision": [
        {"label": "Plusieurs segments", "value": "plusieurs segments"},
        {"label": "Déviation", "value": "deviation"},
    ],
    "rachis_deviation_segment": [
        {"label": "Cervical", "value": "cervical"},
        {"label": "Dorsal", "value": "dorsal"},
        {"label": "Lombaire", "value": "lombaire"},
        {"label": "Plusieurs segments", "value": "plusieurs segments"},
    ],
    "membre_sup_multiple_precision": [
        {"label": "Opérés", "value": "operes"},
        {"label": "Non opérés", "value": "non operes"},
    ],
    "epaule_chirurgie": [
        {"label": "Opérée", "value": "operee"},
        {"label": "Non opérée", "value": "non operee"},
        {"label": "Coiffe", "value": "coiffe"},
    ],
    "coiffe_chirurgie": [
        {"label": "Coiffe opérée", "value": "operee"},
        {"label": "Coiffe non opérée", "value": "non operee"},
    ],
    "coude_chirurgie": [
        {"label": "Opéré", "value": "operee"},
        {"label": "Non opéré", "value": "non operee"},
    ],
    "poignet_chirurgie": [
        {"label": "Opéré", "value": "operee"},
        {"label": "Non opéré", "value": "non operee"},
        {"label": "Canal carpien", "value": "canal carpien"},
    ],
    "deux_membres_precision": [
        {"label": "Opérés", "value": "operes"},
        {"label": "Non opérés", "value": "non operes"},
    ],
    "deux_membres_genou_type": [
        {"label": "Prothèse", "value": "bilateral prothese"},
        {"label": "LCA", "value": "bilateral lca"},
        {"label": "Méniscectomie", "value": "bilateral meniscectomie"},
        {"label": "Autre", "value": "bilateral autre"},
    ],
    "membre_inf_precision": [
        {"label": "Genou", "value": "genou"},
        {"label": "Cheville", "value": "cheville"},
        {"label": "Hanche", "value": "hanche"},
    ],
    "hanche_chirurgie": [
        {"label": "Chirurgie", "value": "chirurgie"},
        {"label": "Non opérée", "value": "non operee"},
    ],
    "hanche_chirurgie_type": [
        {"label": "Prothèse", "value": "prothese"},
        {"label": "Autre", "value": "autre"},
    ],
    "genou_chirurgie": [
        {"label": "Chirurgie", "value": "chirurgie"},
        {"label": "Non opéré", "value": "non operee"},
    ],
    "genou_chirurgie_type": [
        {"label": "Prothèse", "value": "prothese"},
        {"label": "LCA", "value": "lca"},
        {"label": "Méniscectomie", "value": "meniscectomie"},
        {"label": "Autre", "value": "autre"},
    ],
    "cheville_chirurgie": [
        {"label": "Chirurgie", "value": "chirurgie"},
        {"label": "Non opérée", "value": "non operee"},
    ],
    "cheville_precision": [
        {"label": "Opérée", "value": "operee"},
        {"label": "Entorse", "value": "entorse"},
        {"label": "Autre / référentiel", "value": "autre"},
    ],
    "cheville_entorse": [
        {"label": "Oui", "value": "oui"},
        {"label": "Non", "value": "non"},
    ],
    "membre_sup_precision": [
        {"label": "Épaule", "value": "epaule"},
        {"label": "Coude", "value": "coude"},
        {"label": "Poignet / main", "value": "poignet"},
    ],
    "epaule_precision": [
        {"label": "Opérée", "value": "operee"},
        {"label": "Coiffe", "value": "coiffe"},
        {"label": "Fracture", "value": "fracture"},
        {"label": "Autre / référentiel", "value": "autre"},
    ],
    "neuro_precision": [
        {"label": "Hémiplégie", "value": "hemiplegie"},
        {"label": "Paraplégie / tétraplégie", "value": "paraplegie"},
        {"label": "Myopathie", "value": "myopathie"},
        {"label": "SEP / Parkinson", "value": "parkinson"},
    ],
    "neuro_infantile_type": [
        {"label": "Encéphalopathie", "value": "encephalopathie"},
        {"label": "Paralysie cérébrale", "value": "paralysie cerebrale"},
        {"label": "Polyhandicap", "value": "polyhandicap"},
    ],
    "neuro_centrale_type": [
        {"label": "Hémiplégie", "value": "hemiplegie"},
        {"label": "Paraplégie / tétraplégie", "value": "paraplegie"},
        {"label": "Myopathie", "value": "myopathie"},
        {"label": "Autre stable", "value": "parkinson"},
    ],
    "neuro_peripherique_etendue": [
        {"label": "Un membre", "value": "un membre"},
        {"label": "Plusieurs", "value": "plusieurs membres"},
    ],
    "neuro_stable_etendue": [
        {"label": "Un membre", "value": "un membre"},
        {"label": "Plusieurs", "value": "plusieurs membres"},
    ],
    "neuro_orientation": [
        {"label": "Périphérique", "value": "peripherique"},
        {"label": "Centrale", "value": "centrale"},
    ],
    "sciatique_orientation": [
        {"label": "Neuro périphérique", "value": "peripherique"},
        {"label": "Rachis", "value": "rachis"},
    ],
    "respiratoire_precision": [
        {"label": "Bronchiolite", "value": "bronchiolite"},
        {"label": "Mucoviscidose", "value": "mucoviscidose"},
        {"label": "Pré / post-op", "value": "post op respiratoire"},
        {"label": "BPCO", "value": "bpco"},
        {"label": "Autre pathologie", "value": "respiratoire obstructive"},
    ],
    "respiratoire_chronique_mode": [
        {"label": "Individuel", "value": "individuel"},
        {"label": "Groupe", "value": "groupe"},
    ],
    "vasculaire_precision": [
        {"label": "Bandage", "value": "bandage multicouche"},
        {"label": "Lymphœdème", "value": "lymphoedeme"},
        {"label": "Artériopathie", "value": "arteriopathie"},
        {"label": "Insuffisance veineuse", "value": "insuffisance veineuse"},
    ],
    "vasculaire_lymphoedeme_type": [
        {"label": "Simple", "value": "simple"},
        {"label": "Post-cancer du sein", "value": "post cancer du sein"},
    ],
    "vasculaire_lymphoedeme_etendue": [
        {"label": "Un membre", "value": "un membre"},
        {"label": "Deux membres", "value": "deux membres"},
    ],
    "vasculaire_bandage_etendue": [
        {"label": "Un membre", "value": "un membre"},
        {"label": "Deux membres", "value": "deux membres"},
    ],
    "rhumatismal_precision": [
        {"label": "Atteinte localisée", "value": "atteinte localisee"},
        {"label": "Plusieurs membres", "value": "plusieurs membres"},
    ],
    "plusieurs_territoires_precision": [
        {"label": "Oui", "value": "oui"},
        {"label": "Non", "value": "non"},
    ],
    "maxillo_vestibulaire_orl_precision": [
        {"label": "Maxillo", "value": "maxillo"},
        {"label": "Vestibulaire", "value": "vestibulaire"},
        {"label": "Déglutition", "value": "deglutition"},
    ],
    "abdominal_precision": [
        {"label": "Pré / post-op", "value": "post op"},
        {"label": "Post-partum", "value": "post partum"},
    ],
    "abdo_or_perineal_precision": [
        {"label": "Abdominal", "value": "abdominal"},
        {"label": "Périnéal", "value": "perinee"},
    ],
    "perinee_precision": [
        {"label": "Rééducation périnéale", "value": "perinee"},
    ],
    "sujet_age_precision": [
        {"label": "Oui", "value": "deambulation sujet age"},
    ],
    "brulures_precision": [
        {"label": "Un membre", "value": "un membre"},
        {"label": "Plusieurs / tronc", "value": "plusieurs membres tronc"},
    ],
    "amputations_precision": [
        {"label": "Membre supérieur", "value": "membre superieur"},
        {"label": "Membre inférieur", "value": "membre inferieur"},
        {"label": "Plusieurs", "value": "plusieurs membres"},
    ],
    "soins_palliatifs_precision": [
        {"label": "Oui", "value": "soins palliatifs"},
    ],
    "genou_non_opere_precision": [
        {"label": "Genou", "value": "genou"},
        {"label": "Jambe", "value": "jambe"},
    ],
}


def proposer_choix(message: str, contexte_precedent: str = "", attente: str = ""):
    if attente == "precision_multiple":
        message_complet = f"{contexte_precedent} {message}".strip()
        candidates = dedoublonner_regles(trouver_regles_candidates(message_complet))
        return [
            {"label": regle["detail"], "value": regle["detail"]}
            for regle in candidates[:4]
        ]

    return CHOIX_ATTENTE.get(attente, [])
