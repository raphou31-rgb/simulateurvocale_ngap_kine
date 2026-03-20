"""Inférence des familles cliniques NGAP."""

from analyse_message import extraire_indices, normaliser_texte
from helpers_cliniques import (
    _contient_mot,
    _contient_un_des,
    _neuro_etendue,
    _reponse_chirurgie_negative,
    _reponse_chirurgie_positive,
    _resp_mode,
)


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


def inferer_regle_soins_palliatifs(message):
    m = normaliser_texte(message)
    if _contient_un_des(m, ["soins palliatifs", "fin de vie", "accompagnement fin de vie"]):
        return "soins_palliatifs"
    return None
