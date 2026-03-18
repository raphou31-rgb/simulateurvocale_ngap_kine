import re


PHRASE_NORMALIZATION_MAP = {
    "cotation pour": "",
    "cotation de": "",
    "cotation": "",
    "reeduc": "reeducation",
    "reeducation du rachis lombaire": "rachis lombaire",
    "reeducation rachis lombaire": "rachis lombaire",
    "reeducation rachis lombaire non opere": "rachis lombo sacre",
    "reeducation rachis lombaire non operee": "rachis lombo sacre",
    "cotation reeducation rachis lombaire non opere": "rachis lombo sacre",
    "cotation reeducation rachis lombaire non operee": "rachis lombo sacre",
    "rachis lombaire non opere": "rachis lombo sacre",
    "rachis lombaire non operee": "rachis lombo sacre",
    "sans operation": "non chirurgie",
    "sans opération": "non chirurgie",
    "pas d operation": "non chirurgie",
    "pas d opération": "non chirurgie",
    "pas opere": "non chirurgie",
    "pas operee": "non chirurgie",
    "deja opere": "chirurgie",
    "deja operee": "chirurgie",
    "déjà opéré": "chirurgie",
    "déjà opérée": "chirurgie",
    "s est fait operer": "chirurgie",
    "s est fait opérer": "chirurgie",
    "s est faite operer": "chirurgie",
    "s est faite opérer": "chirurgie",
    "suite operation": "chirurgie",
    "suite opération": "chirurgie",
    "apres operation": "chirurgie",
    "apres opération": "chirurgie",
    "apres chirurgie": "chirurgie",
    "après chirurgie": "chirurgie",
    "post op": "chirurgie",
    "post-op": "chirurgie",
    "suites chirurgicales": "chirurgie",
    "suture": "chirurgie",
    "sutures": "chirurgie",
    "cicatrice": "chirurgie",
    "reparation": "chirurgie",
    "réparation": "chirurgie",
    "materiel d osteosynthese": "chirurgie",
    "matériel d ostéosynthèse": "chirurgie",
    "osteosynthese": "chirurgie",
    "ostéosynthèse": "chirurgie",
    "vis": "chirurgie",
    "plaque": "chirurgie",
    "clou": "chirurgie",
    "broche": "chirurgie",
    "prothese totale du genou": "prothese genou",
    "prothese totale de hanche": "prothese hanche",
    "protheses de hanche": "prothese hanche chirurgie",
    "protheses de genou": "prothese genou chirurgie",
    "prothese totale": "prothese chirurgie",
    "prothese de hanche": "prothese hanche chirurgie",
    "prothese de genou": "prothese genou chirurgie",
    "changement de compartiment": "prothese genou chirurgie",
    "ptg": "prothese genou chirurgie",
    "pth": "prothese hanche chirurgie",
    "pte": "prothese epaule chirurgie",
    "prothese epaule": "prothese epaule chirurgie",
    "arthroplastie epaule": "prothese epaule chirurgie",
    "changement de prothese": "prothese chirurgie",
    "ligament croise anterieur": "ligament croise genou chirurgie",
    "croise anterieur": "ligament croise genou chirurgie",
    "ligament croise posterieur": "ligament croise genou chirurgie",
    "croise posterieur": "ligament croise genou chirurgie",
    "ligament croise": "ligament croise genou chirurgie",
    "lcp": "ligament croise genou chirurgie",
    "plastie ligamentaire": "ligament croise genou chirurgie",
    "plastie en croix": "ligament croise genou chirurgie",
    "refection des ligaments": "ligament croise genou chirurgie",
    "didt": "ligament croise genou chirurgie",
    "kenneth jones": "ligament croise genou chirurgie",
    "kenneth-jones": "ligament croise genou chirurgie",
    "coiffe des rotateurs": "coiffe epaule",
    "suture de coiffe": "coiffe epaule chirurgie",
    "reparation des tendons de l epaule": "coiffe epaule chirurgie",
    "acromioplastie": "coiffe epaule chirurgie",
    "tendinopathie de l epaule": "tendinopathie coiffe",
    "tendinopathie epaule": "tendinopathie coiffe",
    "thendinopathie de l epaule": "tendinopathie coiffe",
    "thendinopathie epaule": "tendinopathie coiffe",
    "tendinite epaule": "tendinopathie epaule",
    "tendinite de l epaule": "tendinopathie epaule",
    "epicondylite du coude": "coude non opere",
    "epicondylite coude": "coude non opere",
    "epicondyilite du coude": "coude non opere",
    "epicondyilite coude": "coude non opere",
    "epi condylite du coude": "coude non opere",
    "epi condylite coude": "coude non opere",
    "epicondylite": "coude non opere",
    "coude fracture": "fracture du coude",
    "tunnel carpien": "canal carpien",
    "syndrome du tunnel carpien": "canal carpien",
    "bondage multicouche": "bandage multicouche",
    "luxation du coude": "fracture orthopedique coude",
    "luxation coude": "fracture orthopedique coude",
    "pouteau colles": "fracture distale avant bras",
    "pouteau-colles": "fracture distale avant bras",
    "menisque": "meniscectomie genou chirurgie",
    "menisque interne": "meniscectomie genou chirurgie",
    "menisque externe": "meniscectomie genou chirurgie",
    "menisque opere": "meniscectomie genou chirurgie",
    "menisque operee": "meniscectomie genou chirurgie",
    "suture meniscale": "meniscectomie genou chirurgie",
    "lesion du menisque operee": "meniscectomie genou chirurgie",
    "reeducation des genoux": "genoux",
    "deux genoux": "deux membres inferieurs",
    "les deux genoux": "deux membres inferieurs",
    "des deux cotes": "bilateral",
    "des deux côtés": "bilateral",
    "bilaterale": "bilateral",
    "bilatérale": "bilateral",
    "bilateraux": "bilateral",
    "bilatéraux": "bilateral",
    "membres sup et inf": "membre superieur membre inferieur",
    "membre sup et inf": "membre superieur membre inferieur",
    "membres superieurs et inferieurs": "membre superieur membre inferieur",
    "tronc et membres": "tronc membre superieur membre inferieur",
    "tronc et membre": "tronc membre",
    "tout le corps": "plusieurs territoires",
    "global": "plusieurs territoires",
    "generalise": "plusieurs territoires",
    "généralisé": "plusieurs territoires",
    "poly trauma": "plusieurs territoires trauma",
    "poly-trauma": "plusieurs territoires trauma",
    "genou droit non opere": "genou non opere",
    "genou gauche non opere": "genou non opere",
    "genou droit non operee": "genou non opere",
    "genou gauche non operee": "genou non opere",
    "epaule droite non opere": "epaule non opere",
    "epaule gauche non opere": "epaule non opere",
    "epaule droite non operee": "epaule non opere",
    "epaule gauche non operee": "epaule non opere",
    "hanche droite non opere": "hanche non opere",
    "hanche gauche non opere": "hanche non opere",
    "hanche droite non operee": "hanche non opere",
    "hanche gauche non operee": "hanche non opere",
    "douleur de hanche": "hanche",
    "douleur du genou": "genou",
    "douleur de l epaule": "epaule",
    "mal au dos": "rachis lombaire",
    "bas du dos": "rachis lombaire",
    "haut du dos": "rachis dorsal",
    "cou bloque": "rachis cervical",
    "lumbago": "lombalgie commune",
    "dorsalgie": "rachis dorsal",
    "cervicalgie simple": "cervicalgie commune",
    "accident de voiture": "trauma cervical recent",
    "whiplash": "trauma cervical recent",
    "entorse cervicale": "trauma cervical recent",
    "coup du lapin": "trauma cervical recent",
    "fracture vertebrale recente": "trauma rachis recent",
    "fracture vertébrale récente": "trauma rachis recent",
    "attitude scoliotique": "deviation rachis",
    "scoliose juvenile": "deviation rachis enfant",
    "scoliose juvénile": "deviation rachis enfant",
    "cyphose": "deviation rachis dorsal",
    "lordose": "deviation rachis lombaire",
    "lordose accentuee": "deviation rachis lombaire",
    "lordose accentuée": "deviation rachis lombaire",
    "vertiges": "vestibulaire troubles de l equilibre",
    "avaler difficile": "trouble de deglutition",
    "fausse route": "trouble de deglutition",
    "mamie tombe souvent": "sujet age prevention chute",
    "papy tombe souvent": "sujet age prevention chute",
    "personne agee tombe souvent": "sujet age prevention chute",
    "marche mal": "deambulation",
    "marche difficile": "deambulation",
    "equilibre precaire": "deambulation prevention chute",
    "equilibre fragile": "deambulation prevention chute",
    "cancer du sein bras": "cancer du sein membre superieur",
    "cancer du sein un bras": "cancer du sein membre superieur un membre",
    "lymphoedeme du bras": "lymphoedeme membre superieur un membre",
    "lymphoedeme bras": "lymphoedeme membre superieur un membre",
    "avc": "hemiplegie",
    "cruralgie": "atteinte peripherique un membre",
    "nevralgie cervico brachiale": "atteinte peripherique un membre",
    "névralgie cervico brachiale": "atteinte peripherique un membre",
    "paralysie faciale": "atteinte peripherique un membre",
    "syndrome du canal carpien severe": "atteinte peripherique un membre",
    "syndrome du canal carpien sévère": "atteinte peripherique un membre",
    "retard moteur": "neurologie infantile",
    "nourrisson": "neurologie infantile",
    "bebe": "neurologie infantile",
    "bébé": "neurologie infantile",
    "imc": "paralysie cerebrale",
    "lle": "entorse cheville",
    "inversion": "entorse cheville",
    "entorse de la cheville classique": "entorse cheville",
    "foulure externe": "entorse cheville",
    "entorse interne": "cheville non chirurgie",
    "lli": "cheville non chirurgie",
    "instabilite chronique sans traumatisme recent": "cheville non chirurgie",
    "instabilité chronique sans traumatisme récent": "cheville non chirurgie",
    "pouteau colles": "fracture distale avant bras",
    "trait de fracture": "fracture orthopedique",
    "casse": "fracture orthopedique",
    "cassee": "fracture orthopedique",
    "cassé": "fracture orthopedique",
    "cassée": "fracture orthopedique",
    "fracture de l extremite distale": "fracture distale avant bras",
    "non consolidation": "fracture orthopedique",
}


WORD_NORMALIZATION_MAP = {
    "thendinopathie": "tendinopathie",
    "tendinite": "tendinopathie",
    "rachi": "rachis",
    "lombair": "lombaire",
    "lombere": "lombaire",
    "coudes": "coude",
    "genoux": "genoux",
    "gauche": "gauche",
    "droite": "droite",
    "epicondyilite": "epicondylite",
    "epicondilite": "epicondylite",
    "epicondelite": "epicondylite",
    "epaulee": "epaule",
    "mamie": "sujet age",
    "papy": "sujet age",
    "senior": "sujet age",
    "seniors": "sujet age",
    "dorsaux": "dorsal",
    "bras": "bras",
}


FUZZY_CANONICAL_WORDS = {
    "reeducation": {"max_distance": 3},
    "cotation": {"max_distance": 3},
    "rachis": {"max_distance": 2},
    "lombaire": {"max_distance": 3},
    "cervical": {"max_distance": 3},
    "dorsal": {"max_distance": 3},
    "genou": {"max_distance": 2},
    "genoux": {"max_distance": 2},
    "gauche": {"max_distance": 2},
    "droite": {"max_distance": 2},
    "hanche": {"max_distance": 2},
    "cheville": {"max_distance": 3},
    "epaule": {"max_distance": 3},
    "coude": {"max_distance": 2},
    "poignet": {"max_distance": 3},
    "bras": {"max_distance": 2},
    "membre": {"max_distance": 2},
    "inferieur": {"max_distance": 3},
    "superieur": {"max_distance": 3},
    "non": {"max_distance": 1},
    "opere": {"max_distance": 2},
    "prothese": {"max_distance": 3},
    "tendinopathie": {"max_distance": 4},
    "epicondylite": {"max_distance": 4},
    "ligament": {"max_distance": 3},
    "croise": {"max_distance": 2},
    "meniscectomie": {"max_distance": 4},
    "coiffe": {"max_distance": 2},
    "lymphoedeme": {"max_distance": 4},
    "respiratoire": {"max_distance": 4},
    "neurologique": {"max_distance": 4},
    "parkinson": {"max_distance": 3},
    "sep": {"max_distance": 1},
}


ASR_REGEX_REPLACEMENTS = [
    (r"\bre[ -]?education\b", "reeducation"),
    (r"\bcotassion\b", "cotation"),
    (r"\bcotacion\b", "cotation"),
    (r"\bnono perr?e?t\b", "non opere"),
    (r"\bnono perr?e?y\b", "non opere"),
    (r"\bnono pere\b", "non opere"),
    (r"\bnono perret\b", "non opere"),
    (r"\bnonope?r[ée]?\b", "non opere"),
    (r"\bnom op[ée] rez\b", "non opere"),
    (r"\bnom op[ée]r[ée]z\b", "non opere"),
    (r"\bnom operez\b", "non opere"),
    (r"\bnom opé rez\b", "non opere"),
    (r"\bnon on operee\b", "non opere"),
    (r"\bnon on opere\b", "non opere"),
    (r"\bnom de op[ée]r[ée]?\b", "non opere"),
    (r"\bnom de operer\b", "non opere"),
    (r"\bmon op[ée]r[ée]?\b", "non opere"),
    (r"\bmon operer\b", "non opere"),
    (r"\br a c h i s\b", "rachis"),
    (r"\blomb[ae]r[e]?\b", "lombaire"),
    (r"\bdorso? lombaire\b", "dorsal lombaire"),
    (r"\bdorsaux lombaire\b", "dorsal lombaire"),
    (r"\bdorsaux lombair[e]?\b", "dorsal lombaire"),
    (r"\btendino?pathie\b", "tendinopathie"),
    (r"\bepi ?condylite\b", "epicondylite"),
    (r"\bnon op[ée]r[ée]?\b", "non opere"),
    (r"\bpas op[ée]r[ée]?\b", "pas opere"),
    (r"\bd[eé]j[aà] op[ée]r[ée]?\b", "deja opere"),
    (r"\bn[' ]?an opere(e)?\b", "non opere"),
    (r"\bn[' ]?en opere(e)?\b", "non opere"),
    (r"\bnan opere(e)?\b", "non opere"),
    (r"\bnonopere(e)?\b", "non opere"),
    (r"\bn[' ]?an operee\b", "non operee"),
    (r"\bn[' ]?en operee\b", "non operee"),
    (r"\bnan operee\b", "non operee"),
    (r"\bn[' ]?an operer\b", "non opere"),
    (r"\bn[' ]?en operer\b", "non opere"),
]


def expand_medical_language(text: str) -> str:
    normalized = text.replace("’", "'")

    for pattern, replacement in ASR_REGEX_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized)

    for source in sorted(PHRASE_NORMALIZATION_MAP, key=len, reverse=True):
        normalized = re.sub(
            r"\b" + re.escape(source) + r"\b",
            PHRASE_NORMALIZATION_MAP[source],
            normalized,
        )

    for source, target in WORD_NORMALIZATION_MAP.items():
        normalized = re.sub(r"\b" + re.escape(source) + r"\b", target, normalized)

    normalized = _apply_fuzzy_word_corrections(normalized)

    for source in sorted(PHRASE_NORMALIZATION_MAP, key=len, reverse=True):
        normalized = re.sub(
            r"\b" + re.escape(source) + r"\b",
            PHRASE_NORMALIZATION_MAP[source],
            normalized,
        )

    return re.sub(r"\s+", " ", normalized).strip()


def _apply_fuzzy_word_corrections(text: str) -> str:
    words = text.split()
    corrected = []
    for word in words:
        replacement = _find_fuzzy_replacement(word)
        corrected.append(replacement or word)
    return " ".join(corrected)


def _find_fuzzy_replacement(word: str) -> str | None:
    clean_word = re.sub(r"[^a-z]", "", word.lower())
    if len(clean_word) < 4:
        return None
    if clean_word in FUZZY_CANONICAL_WORDS:
        return clean_word

    best_word = None
    best_distance = None
    for canonical, options in FUZZY_CANONICAL_WORDS.items():
        distance = _levenshtein_distance(clean_word, canonical)
        if distance > options["max_distance"]:
            continue
        if best_distance is None or distance < best_distance:
            best_word = canonical
            best_distance = distance

    return best_word


def _levenshtein_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (char_a != char_b)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]
