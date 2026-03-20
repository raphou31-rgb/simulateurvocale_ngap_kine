import re
import unicodedata
from functools import lru_cache

from medical_abbreviations import expand_medical_language


CLINICAL_NORMALIZATION_MAP = {
    "pas de chirurgie": "non chirurgie",
    "sans chirurgie": "non chirurgie",
    "non operee": "non chirurgie",
    "non opere": "non chirurgie",
    "opere": "chirurgie",
    "operee": "chirurgie",
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
    "vis d osteosynthese": "chirurgie",
    "plaque d osteosynthese": "chirurgie",
    "clou centro medullaire": "chirurgie",
    "broche percutanee": "chirurgie",
    "lca": "ligament croise genou",
    "ligament croise anterieur": "ligament croise genou",
    "lcp": "ligament croise genou",
    "ligament croise": "ligament croise genou",
    "plastie ligamentaire": "ligament croise genou chirurgie",
    "plastie en croix": "ligament croise genou chirurgie",
    "refection des ligaments": "ligament croise genou chirurgie",
    "didt": "ligament croise genou chirurgie",
    "kenneth jones": "ligament croise genou chirurgie",
    "kenneth-jones": "ligament croise genou chirurgie",
    "ptg": "prothese genou chirurgie",
    "pth": "prothese hanche chirurgie",
    "pte": "prothese epaule chirurgie",
    "prothese de hanche": "prothese hanche chirurgie",
    "prothese de genou": "prothese genou chirurgie",
    "protheses de hanche": "prothese hanche chirurgie",
    "protheses de genou": "prothese genou chirurgie",
    "prothese epaule": "prothese epaule chirurgie",
    "arthroplastie epaule": "prothese epaule chirurgie",
    "changement de compartiment": "prothese genou chirurgie",
    "prothese totale genou": "prothese genou",
    "prothese totale du genou": "prothese genou",
    "prothese totale hanche": "prothese hanche",
    "prothese totale de hanche": "prothese hanche",
    "changement de prothese": "prothese chirurgie",
    "lle": "entorse cheville",
    "inversion": "entorse cheville",
    "foulure externe": "entorse cheville",
    "entorse interne": "cheville non chirurgie",
    "lli": "cheville non chirurgie",
    "fracture": "fracture orthopedique",
    "trait de fracture": "fracture orthopedique",
    "luxation du coude": "fracture orthopedique coude",
    "luxation coude": "fracture orthopedique coude",
    "pouteau colles": "fracture distale avant bras",
    "cassee": "fracture orthopedique",
    "non consolidation": "fracture orthopedique",
    "fracture de l extremite distale": "fracture distale avant bras",
    "meniscectomie": "meniscectomie genou chirurgie",
    "menisque": "meniscectomie genou chirurgie",
    "menisque interne": "meniscectomie genou chirurgie",
    "menisque externe": "meniscectomie genou chirurgie",
    "suture meniscale": "meniscectomie genou chirurgie",
    "coiffe des rotateurs": "coiffe epaule",
    "suture de coiffe": "coiffe epaule chirurgie",
    "reparation des tendons de l epaule": "coiffe epaule chirurgie",
    "acromioplastie": "coiffe epaule chirurgie",
    "epicondylite": "coude non chirurgie",
    "coude fracture": "fracture du coude",
    "coiffe": "coiffe epaule",
    "canal carpien": "canal carpien",
    "tunnel carpien": "canal carpien",
    "syndrome du tunnel carpien": "canal carpien",
    "bondage multicouche": "bandage multicouche",
    "bpco": "respiratoire chronique",
    "bpc0": "respiratoire chronique",
    "bpc o": "respiratoire chronique",
    "bronchopneumopathie chronique obstructive": "respiratoire chronique",
    "bronchiolite": "desencombrement urgent respiratoire",
    "mucoviscidose": "mucoviscidose respiratoire",
    "parkinson": "affection neurologique stable",
    "sep": "affection neurologique stable",
    "sclerose en plaques": "affection neurologique stable",
    "polyarthrite rhumatoide": "rhumatismal inflammatoire",
    "atm": "maxillo facial",
    "dysphagie": "trouble de deglutition",
    "vertiges": "vestibulaire troubles de l equilibre",
    "lombalgie": "rachis lombaire",
    "lumbago": "rachis lombaire",
    "cervicalgie": "rachis cervical",
    "cervicalgie simple": "rachis cervical",
    "dorsalgie": "rachis dorsal",
    "sciatique": "rachis lombaire radiculaire",
    "cruralgie": "rachis lombaire radiculaire",
    "accident de voiture": "trauma cervical recent",
    "whiplash": "trauma cervical recent",
    "entorse cervicale": "trauma cervical recent",
    "attitude scoliotique": "deviation rachis",
    "cyphose": "deviation rachis dorsal",
    "lordose": "deviation rachis lombaire",
    "lordose accentuee": "deviation rachis lombaire",
    "avc": "hemiplegie",
    "nevralgie cervico brachiale": "atteinte peripherique un membre",
    "névralgie cervico brachiale": "atteinte peripherique un membre",
    "paralysie faciale": "atteinte peripherique un membre",
    "retard moteur": "neurologie infantile",
    "nourrisson": "neurologie infantile",
    "bebe": "neurologie infantile",
    "bébé": "neurologie infantile",
    "imc": "paralysie cerebrale",
}

CLINICAL_NORMALIZATION_ITEMS = [
    (expression, CLINICAL_NORMALIZATION_MAP[expression])
    for expression in sorted(CLINICAL_NORMALIZATION_MAP, key=len, reverse=True)
]


def normaliser_termes_cliniques(texte):
    texte_normalise = texte
    for expression, remplacement in CLINICAL_NORMALIZATION_ITEMS:
        pattern = r"\b" + re.escape(expression) + r"\b"
        texte_normalise = re.sub(pattern, remplacement, texte_normalise)
    return texte_normalise


@lru_cache(maxsize=4096)
def normaliser_texte(texte):
    texte = texte.lower()
    texte = texte.replace(".", " ")
    texte = texte.replace("’", " ")
    texte = texte.replace("'", " ")
    texte = texte.strip()
    texte = "".join(
        caractere for caractere in unicodedata.normalize("NFD", texte)
        if unicodedata.category(caractere) != "Mn"
    )
    texte = expand_medical_language(texte)
    texte = normaliser_termes_cliniques(texte)
    return texte


def contient_expression(message_normalise, expression):
    return normaliser_texte(expression) in message_normalise


def detecter_territoires_segment(segment_normalise):
    territoires = set()

    if any(mot in segment_normalise for mot in [
        "genou", "genoux", "cheville", "hanche", "jambe", "jambes",
        "cuisse", "pied", "pieds", "membre inferieur", "membres inferieurs"
    ]):
        territoires.add("membre inferieur")

    if any(mot in segment_normalise for mot in [
        "epaule", "epaules", "bras", "coude", "coudes", "avant-bras",
        "poignet", "poignets", "main", "mains", "membre superieur",
        "membres superieurs", "canal carpien"
    ]):
        territoires.add("membre superieur")

    if any(mot in segment_normalise for mot in [
        "rachis", "cervical", "cervicale", "dorsal", "thoracique",
        "lombaire", "lombo", "cervicalgie", "lombalgie"
    ]):
        territoires.add("rachis")

    if any(mot in segment_normalise for mot in ["tronc", "thorax", "abdomen"]):
        territoires.add("tronc")

    return territoires


@lru_cache(maxsize=4096)
def _extraire_indices_cached(message):
    message_normalise = normaliser_texte(message)

    indices = {
        "message_normalise": message_normalise,
        "chirurgie": None,
        "moins_18": None,
        "territoire": None,
        "territoires_detectes": [],
        "multi_territoires": False,
        "segment": None,
        "multiple": False,
        "reeducation": False
    }

    if "reeducation" in message_normalise or "reeducation" in message_normalise:
        indices["reeducation"] = True

    mots_chirurgie_oui = [
        "post op", "post-op", "opere", "operee", "operé", "opérée",
        "chirurgie", "chirurgical", "prothese", "arthroplastie",
        "ligamentoplastie", "meniscectomie", "canal carpien",
        "suture", "sutures", "cicatrice", "reparation", "réparation",
        "vis d osteosynthese", "plaque d osteosynthese",
        "clou centro medullaire", "broche percutanee",
        "osteosynthese", "ostéosynthèse"
    ]
    mots_chirurgie_non = [
        "non chirurgie", "pas de chirurgie", "non opere", "non operee", "sans chirurgie", "medical", "médical"
    ]

    if any(mot in message_normalise for mot in mots_chirurgie_oui):
        indices["chirurgie"] = "oui"

    if any(mot in message_normalise for mot in mots_chirurgie_non):
        indices["chirurgie"] = "non"

    if any(mot in message_normalise for mot in [
        "moins de 18 ans", "mineur", "enfant", "adolescent", "ado", "pediatrique", "pédiatrique"
    ]):
        indices["moins_18"] = True
    elif any(mot in message_normalise for mot in [
        "adulte", "majeur", "plus de 18 ans"
    ]):
        indices["moins_18"] = False

    if any(mot in message_normalise for mot in ["deux", "2", "bilateral", "bilaterale", "bilateraux", "bilateralement", "genoux", "membres inferieurs"]):
        indices["multiple"] = True

    if all(mot in message_normalise for mot in ["tronc", "membre"]):
        indices["multi_territoires"] = True

    if all(mot in message_normalise for mot in ["membre superieur", "membre inferieur"]):
        indices["multi_territoires"] = True

    detecte_membre_inf = any(mot in message_normalise for mot in ["genou", "genoux", "cheville", "hanche", "jambe", "jambes", "cuisse", "pied", "pieds", "membre inferieur", "membres inferieurs"])
    if detecte_membre_inf:
        indices["territoire"] = "membre inferieur"
        indices["territoires_detectes"].append("membre inferieur")

    detecte_membre_sup = any(mot in message_normalise for mot in ["epaule", "epaules", "bras", "coude", "coudes", "avant-bras", "poignet", "poignets", "main", "mains", "membre superieur", "membres superieurs", "canal carpien"])
    if detecte_membre_sup:
        indices["territoire"] = "membre superieur"
        indices["territoires_detectes"].append("membre superieur")

    detecte_rachis = any(
        mot in message_normalise
        for mot in [
            "rachis", "cervical", "cervicale", "dorsal", "thoracique",
            "lombaire", "lombo", "cervicalgie", "lombalgie",
            "deviation", "scoliose", "cyphose", "lordose",
        ]
    )
    if detecte_rachis:
        indices["territoire"] = "rachis"
        indices["territoires_detectes"].append("rachis")

    detecte_tronc = any(mot in message_normalise for mot in ["tronc", "thorax", "abdomen"])
    if detecte_tronc:
        indices["territoires_detectes"].append("tronc")

    segments = [segment.strip() for segment in re.split(r"\s*(?:\+|/|,|\bet\b)\s*", message_normalise) if segment.strip()]
    if len(segments) >= 2:
        for segment in segments:
            indices["territoires_detectes"].extend(detecter_territoires_segment(segment))
        indices["territoires_detectes"] = list(set(indices["territoires_detectes"]))

    if "lombaire" in message_normalise or "lombo" in message_normalise or "lombalgie" in message_normalise:
        indices["segment"] = "lombaire"

    if "cervical" in message_normalise or "cervicale" in message_normalise or "cervicalgie" in message_normalise:
        indices["segment"] = "cervical"

    if "dorsal" in message_normalise or "thoracique" in message_normalise:
        indices["segment"] = "dorsal"

    if any(mot in message_normalise for mot in [
        "neurologie",
        "neuro",
        "neurologique",
        "hemiplegie", "hémiplégie",
        "paraplegie", "paraplégie",
        "tetraplegie", "tétraplégie",
        "myopathie",
        "avc",
        "parkinson",
        "sclerose en plaques", "sclérose en plaques", "sep",
        "neuropathie peripherique", "neuropathie périphérique",
        "radiculaire", "tronculaire", "atteinte peripherique", "cruralgie",
        "cervico brachiale", "cervico-brachiale", "paralysie faciale", "retard moteur",
        "central", "centrale",
        "encephalopathie infantile", "encéphalopathie infantile", "neurologie infantile",
        "paralysie cerebrale", "paralysie cérébrale", "polyhandicap"
    ]):
        indices["territoire"] = "neurologie"

    if any(mot in message_normalise for mot in [
        "bronchiolite", "bpco", "mucoviscidose", "respiratoire", "desencombrement",
        "désencombrement urgent",
        "urgence respiratoire",
        "obstructive", "restrictive", "mixte",
        "pre-op respiratoire", "pré-op respiratoire", "respiratoire pre-op", "respiratoire pré-op",
        "post-op respiratoire", "respiratoire post-op",
        "avant chirurgie thoracique", "apres chirurgie thoracique", "après chirurgie thoracique",
        "rehabilitation respiratoire", "réhabilitation respiratoire",
        "readaptation respiratoire", "réadaptation respiratoire",
        "respiratoire preoperatoire", "respiratoire préopératoire",
        "respiratoire post operatoire", "respiratoire post-opératoire",
        "handicap respiratoire chronique"
    ]):
        indices["territoire"] = "respiratoire"

    if any(mot in message_normalise for mot in [
        "vasculaire",
        "lymphoedeme", "lymphœdeme", "lymphœdème", "arteriopathie", "arterite", "artérite", "insuffisance veineuse",
        "drainage lymphatique", "drainage manuel", "bandage multicouche", "bandage", "troubles trophiques"
    ]):
        indices["territoire"] = "vasculaire"

    if any(mot in message_normalise for mot in [
        "cancer du sein", "post cancer du sein", "apres cancer du sein", "après cancer du sein"
    ]):
        indices["territoire"] = "vasculaire"

    # Nouvelles familles: detection minimale, sans perturber les familles deja prioritaires.
    if indices["territoire"] is None and any(mot in message_normalise for mot in [
        "polyarthrite",
        "polyarthrite rhumatoide",
        "polyarthrite rhumatoïde",
        "spondylarthrite",
        "rhumatisme inflammatoire",
        "rhumatismal inflammatoire"
    ]):
        indices["territoire"] = "maladies rhumatismales inflammatoires"

    if indices["territoire"] is None and any(mot in message_normalise for mot in [
        "maxillo", "maxillo-facial", "maxillo facial", "atm",
        "articulation temporo mandibulaire", "machoire", "mâchoire"
    ]):
        indices["territoire"] = "maxillo-facial / vestibulaire / ORL"

    if indices["territoire"] is None and any(mot in message_normalise for mot in [
        "vestibulaire", "vppb", "vertige positionnel", "vertiges",
        "troubles de l'equilibre", "troubles de l équilibre"
    ]):
        indices["territoire"] = "maxillo-facial / vestibulaire / ORL"

    if indices["territoire"] is None and any(mot in message_normalise for mot in [
        "orl", "deglutition", "déglutition", "dysphagie",
        "trouble de la deglutition", "trouble de la déglutition"
    ]):
        indices["territoire"] = "maxillo-facial / vestibulaire / ORL"

    if indices["territoire"] is None and any(mot in message_normalise for mot in [
        "paroi abdominale", "abdominal", "abdo", "sangle abdominale",
        "post partum", "post-partum", "postpartum", "suite de couches"
    ]):
        indices["territoire"] = "abdominal"

    if indices["territoire"] is None and any(mot in message_normalise for mot in [
        "perinee", "périnée", "perineal", "périnéal",
        "sphincterien", "sphinctérien",
        "reeducation perineale", "rééducation périnéale",
        "biofeedback", "electrostimulation perineale", "électrostimulation périnéale"
    ]):
        indices["territoire"] = "perinee"

    if indices["territoire"] is None and any(mot in message_normalise for mot in [
        "sujet age", "sujet âgé", "personne agee", "personne âgée",
        "reeducation personne agee", "rééducation personne âgée",
        "deambulation", "déambulation",
        "prevention chute", "prévention chute",
        "equilibre sujet age", "équilibre sujet âgé"
    ]):
        indices["territoire"] = "sujet age"

    if any(mot in message_normalise for mot in ["brulure", "brûlure", "brulures", "brûlures", "brule", "brûlé", "brulé"]):
        indices["territoire"] = "brulures"

    if any(mot in message_normalise for mot in [
        "amputation", "ampute", "amputé", "moignon"
    ]):
        indices["territoire"] = "amputations"

    if indices["territoire"] is None and any(mot in message_normalise for mot in [
        "soins palliatifs", "palliatif", "fin de vie", "accompagnement fin de vie"
    ]):
        indices["territoire"] = "soins palliatifs"

    indices["territoires_detectes"] = sorted(set(indices["territoires_detectes"]))
    if len(indices["territoires_detectes"]) >= 2:
        indices["multi_territoires"] = True
        if indices["territoire"] not in {"brulures", "amputations"}:
            indices["territoire"] = "plusieurs territoires"

    return indices


def extraire_indices(message):
    return dict(_extraire_indices_cached(message))
