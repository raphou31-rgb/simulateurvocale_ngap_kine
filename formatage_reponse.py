"""Formatage des réponses NGAP et métadonnées d'affichage."""

from moteur_ngap import RULE_BY_ID
from ngap_database import NGAP_RULES


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
    famille = regle.get("famille", "")
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
