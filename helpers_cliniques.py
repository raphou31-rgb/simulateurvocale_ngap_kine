"""Helpers de détection clinique partagés par le moteur NGAP."""

from analyse_message import normaliser_texte


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
    if "tronc" in m and ("membre" in m or "face" in m):
        return "plusieurs"
    return None


def _resp_mode(m):
    if _contient_un_des(m, ["en groupe", "groupe", "seance de groupe", "séance de groupe"]):
        return "groupe"
    if _contient_un_des(m, ["en individuel", "individuel"]):
        return "individuel"
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
        from inference_familles import inferer_regle_neurologie

        neuro_rule = inferer_regle_neurologie(message_normalise)
        return neuro_rule or "neurologie_affection_stable_plusieurs"
    from inference_familles import inferer_regle_sujet_age

    if inferer_regle_sujet_age(message_normalise) == "sujet_age_deambulation":
        return "sujet_age_deambulation"
    if _reponse_chirurgie_positive(message_normalise):
        return "plusieurs_territoires_avec_chirurgie"
    if _reponse_chirurgie_negative(message_normalise):
        return "plusieurs_territoires_sans_chirurgie"
    return "NEED_MULTI_CHIR"
