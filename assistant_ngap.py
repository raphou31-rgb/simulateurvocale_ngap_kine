import re

from analyse_message import extraire_indices, normaliser_texte
from debug_trace import trace
from formatage_reponse import decrire_reponse_finale, extraire_regle_depuis_reponse, formater_reponse_finale
from helpers_cliniques import (
    _age_moins_18,
    _contient_brut_un_des,
    _contient_mot,
    _contient_un_des,
    _membre_inf_bilateral_explicite,
    _membre_inf_meme_membre_explicite,
    _membre_sup_bilateral_explicite,
    _neuro_etendue,
    _plusieurs_membres_direct,
    _reponse_chirurgie_negative,
    _reponse_chirurgie_positive,
    _segment_deviation_direct,
    _segments_membre_direct,
    _segments_rachis_detectes,
    _texte_brut,
    _trauma_recent_mention,
)
from inference_familles import (
    inferer_regle_abdominal_perineal,
    inferer_regle_amputation,
    inferer_regle_brulures,
    inferer_regle_maxillo_vestibulaire_deglutition,
    inferer_regle_neurologie,
    inferer_regle_plusieurs_territoires,
    inferer_regle_respiratoire,
    inferer_regle_rhumatismal_inflammatoire,
    inferer_regle_soins_palliatifs,
    inferer_regle_sujet_age,
    inferer_regle_vasculaire,
)
from moteur_ngap import RULE_BY_ID, dedoublonner_regles, trouver_regle_par_id, trouver_regles_candidates


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
            # "cervicalgie commune" = RAM 8.07 directement, sans question supplémentaire.
            return None, ""
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

    if (
        "humerus" in message_normalise
        and "fracture" in message_normalise
    ) or _contient_un_des(message_normalise, ["fracture humerus", "fracture proximale humerus", "fracture de l humerus", "fracture extremite proximale humerus"]):
        if _reponse_chirurgie_negative(message_normalise):
            return {"kind": "rule", "value": "membre_sup_fracture_humerus_prox_non_operee"}
        if _reponse_chirurgie_positive(message_normalise):
            return {"kind": "rule", "value": "membre_sup_fracture_humerus_prox_operee"}
        return {"kind": "question", "text": "Question : operee ou non ?", "attente": "epaule_chirurgie"}

    if (
        _contient_un_des(message_normalise, ["lca", "ligament croise"])
        and "genou" in message_normalise
        and _reponse_chirurgie_negative(message_normalise)
    ):
        return {"kind": "rule", "value": "membre_inf_genou_jambe_non_opere"}

    if _contient_un_des(message_normalise, ["ligamentoplastie"]) or (_contient_un_des(message_normalise, ["lca", "ligament croise"]) and "genou" in message_normalise):
        return {"kind": "rule", "value": "membre_inf_lca"}

    if _contient_un_des(message_normalise, ["entorse genou", "entorse du genou"]):
        if _reponse_chirurgie_negative(message_normalise):
            return {"kind": "rule", "value": "membre_inf_genou_jambe_non_opere"}
        if _reponse_chirurgie_positive(message_normalise):
            if _contient_un_des(message_normalise, ["lca", "ligament croise"]):
                return {"kind": "rule", "value": "membre_inf_lca"}
            return {"kind": "rule", "value": "membre_inf_genou_jambe_opere"}
        return {"kind": "question", "text": "Question : chirurgie du genou ou non ?", "attente": "genou_chirurgie"}

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

    if _contient_brut_un_des(message_brut, ["cervicalgie commune"]) or _contient_un_des(message_normalise, ["rachis cervical commune"]):
        return {"kind": "rule", "value": "rachis_cervicalgie_commune"}

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
            return "Question : genou / cheville / hanche ?", "membre_inf_precision"

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
        # Note: ce handler est rarement declenche depuis la simplification du flux cervicalgie commune.
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
        # Note: ce handler est rarement declenche depuis la simplification du flux cervicalgie commune.
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
        contexte_complet = f"{contexte_precedent} {message}".strip()
        message_total = normaliser_texte(contexte_complet)
        if (
            "humerus" in message_total
            and "fracture" in message_total
        ) or _contient_un_des(message_total, ["fracture humerus", "fracture proximale humerus", "fracture de l humerus"]):
            if _reponse_chirurgie_positive(normaliser_texte(message)):
                regle = trouver_regle_par_id("membre_sup_fracture_humerus_prox_operee")
                return {
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                }
            if _reponse_chirurgie_negative(normaliser_texte(message)):
                regle = trouver_regle_par_id("membre_sup_fracture_humerus_prox_non_operee")
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
                "attente": "epaule_chirurgie"
            }
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
        if _contient_un_des(message_normalise, ["rachis", "lombaire", "lombo"]):
            regle = trouver_regle_par_id("rachis_lombosacre_non_opere")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _contient_un_des(message_normalise, ["peripherique", "périphérique", "neuro", "neurologique"]):
            regle = trouver_regle_par_id("neurologie_atteintes_peripheriques_radiculaires_tronculaires_un_membre")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
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
        tentative_directe = repondre(message)
        if tentative_directe["termine"] or tentative_directe["attente"] != "general_precision":
            return tentative_directe

        message_complet = f"{contexte_precedent} {message}".strip()
        tentative_combinee = repondre(message_complet)
        if tentative_combinee["termine"] or tentative_combinee["attente"] != "general_precision":
            return tentative_combinee

        return {
            "texte": "Question : quel diagnostic precis ?",
            "nouveau_contexte": message_complet,
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
        message_complet = f"{contexte_precedent} {message}".strip()
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

        reponse_normalisee = normaliser_texte(message)
        if _reponse_chirurgie_positive(reponse_normalisee):
            regle = trouver_regle_par_id("plusieurs_territoires_avec_chirurgie")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if _reponse_chirurgie_negative(reponse_normalisee):
            regle = trouver_regle_par_id("plusieurs_territoires_sans_chirurgie")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }

        message_brut = message.strip().lower()
        if message_brut in ["oui", "yes", "opere", "operes", "chirurgie"]:
            regle = trouver_regle_par_id("plusieurs_territoires_avec_chirurgie")
            return {
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            }
        if message_brut in ["non", "no", "pas opere", "pas operes", "medical"]:
            regle = trouver_regle_par_id("plusieurs_territoires_sans_chirurgie")
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
    trace("repondre_start", message=message, contexte=contexte_precedent, attente=attente)

    def _trace_result(result):
        trace(
            "repondre_result",
            termine=result["termine"],
            attente=result["attente"],
            nouveau_contexte=result["nouveau_contexte"],
        )
        return result

    if attente:
        resultat_court = gerer_reponse_courte(message, contexte_precedent, attente)
        if resultat_court is not None:
            return _trace_result(resultat_court)
        # Garde-fou: ne pas sortir de cotation finale si une attente est active mais non resolue.
        return _trace_result({
            "texte": "Question : pouvez-vous preciser le diagnostic ?",
            "nouveau_contexte": f"{contexte_precedent} {message}".strip(),
            "termine": False,
            "attente": "general_precision"
        })

    message_complet = f"{contexte_precedent} {message}".strip()
    prioritaire = decision_prioritaire(message_complet)
    if prioritaire is not None:
        if prioritaire["kind"] == "rule":
            regle = trouver_regle_par_id(prioritaire["value"])
            if regle_est_conclusive(regle):
                return _trace_result({
                    "texte": formater_reponse_finale(regle),
                    "nouveau_contexte": "",
                    "termine": True,
                    "attente": ""
                })
        if prioritaire["kind"] == "question":
            return _trace_result({
                "texte": prioritaire["text"],
                "nouveau_contexte": message_complet,
                "termine": False,
                "attente": prioritaire["attente"]
            })
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
            return _trace_result({
                "texte": formater_reponse_finale(regle),
                "nouveau_contexte": "",
                "termine": True,
                "attente": ""
            })

    familles_explicites = detecter_familles_explicites(message_complet)
    if len(familles_explicites) >= 2:
        return _trace_result({
            "texte": "Question : Quelle famille principale ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "general_precision"
        })

    message_normalise = normaliser_texte(message_complet)
    if any(term in message_brut for term in ["sciatique", "cruralgie"]):
        return _trace_result({
            "texte": "Question : neuro peripherique ou rachis ?",
            "nouveau_contexte": message_complet,
            "termine": False,
            "attente": "sciatique_orientation"
        })
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
        {"label": "Oui, opéré", "value": "oui"},
        {"label": "Non, pas opéré", "value": "non"},
    ],
    "general_precision": [
        {"label": "Membre inférieur", "value": "membre inferieur"},
        {"label": "Membre supérieur", "value": "membre superieur"},
        {"label": "Rachis", "value": "rachis"},
        {"label": "Autre", "value": "autre pathologie"},
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
