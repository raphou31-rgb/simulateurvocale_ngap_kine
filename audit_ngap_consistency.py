import re
import unicodedata

from ngap_database import NGAP_RULES
from ngap_truth_catalog import load_truth_catalog
CATALOG_RULE_HINTS = {
    "rachis_lombalgie_commune": 1,
    "rachis_lombosacre_non_opere": 2,
    "rachis_dorsal_non_opere": 4,
    "rachis_cervicalgie_commune": 6,
    "rachis_trauma_cervical_recent": 7,
    "rachis_plusieurs_segments": 10,
    "deviation_rachis_lombosacre": 42,
    "deviation_rachis_dorsal": 43,
    "deviation_rachis_cervical": 44,
    "deviation_rachis_plusieurs_segments": 45,
    "membre_inf_lca": 33,
    "membre_inf_ptg": 32,
    "membre_inf_meniscectomie": 34,
    "membre_inf_entorse_cheville_non_operee": 29,
    "membre_inf_genou_jambe_non_opere": 35,
    "membre_inf_genou_jambe_opere": 36,
    "membre_inf_pth": 37,
    "membre_inf_hanche_cuisse_non_operee": 38,
    "membre_inf_hanche_cuisse_operee": 39,
    "membre_inf_plusieurs_segments_non_operes": 40,
    "membre_inf_plusieurs_segments_operes": 41,
    "membre_sup_canal_carpien": 12,
    "membre_sup_coiffe_non_operee": 21,
    "membre_sup_coiffe_operee": 22,
    "membre_sup_poignet_main_non_opere": 13,
    "membre_sup_poignet_main_opere": 14,
    "membre_sup_epaule_bras_non_opere": 24,
    "membre_sup_epaule_bras_opere": 25,
    "membre_sup_coude_avant_bras_non_opere": 19,
    "membre_sup_coude_avant_bras_opere": 20,
    "membre_sup_plusieurs_segments_non_operes": 26,
    "membre_sup_plusieurs_segments_operes": 27,
    "respiratoire_obstructive_restrictive_mixte": 65,
    "respiratoire_mucoviscidose": 67,
    "respiratoire_handicap_chronique_individuel": 68,
    "respiratoire_handicap_chronique_groupe": 69,
    "neurologie_hemiplegie": 57,
    "neurologie_atteintes_peripheriques_radiculaires_tronculaires_un_membre": 55,
    "neurologie_atteintes_peripheriques_radiculaires_tronculaires_plusieurs_membres": 56,
    "neurologie_paraplegie_tetraplegie": 58,
    "neurologie_affection_stable_un_membre": 59,
    "neurologie_affection_stable_plusieurs": 60,
    "neurologie_myopathie": 62,
    "neurologie_encephalopathie_infantile": 63,
    "neurologie_paralysie_cerebrale_polyhandicap": 61,
    "vestibulaire_troubles_equilibre": 71,
    "vasculaire_arteriopathie_membres_inferieurs": 73,
    "vasculaire_insuffisance_veineuse": 74,
    "vasculaire_lymphoedeme_un_membre": 75,
    "vasculaire_lymphoedeme_deux_membres": 76,
    "vasculaire_lymphoedeme_sein": 77,
    "vasculaire_bandage_un_membre": 78,
    "vasculaire_bandage_deux_membres": 79,
    "abdominal_post_partum": 54,
    "perinee_active": 80,
    "sujet_age_deambulation": 81,
    "brulure_un_membre": 83,
    "brulure_plusieurs_membres_tronc": 84,
    "soins_palliatifs": 85,
    "rhumatismales_atteinte_localisee": 51,
    "rhumatismales_atteinte_plusieurs_membres": 52,
    "plusieurs_territoires_sans_chirurgie": 48,
    "plusieurs_territoires_avec_chirurgie": 49,
    "amputation_un_membre_superieur": 46,
    "amputation_un_membre_inferieur": 47,
    "amputation_au_moins_deux_membres": 50,
}


def normalize_text(value: str) -> str:
    value = (value or "").lower()
    value = "".join(
        char
        for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def format_catalog_cotation(item: dict) -> str:
    return f"{item.get('lettre_cle', '').strip()} {item.get('cotation_valeur', '').strip()}".strip()


def normalize_cotation(value: str) -> str:
    normalized = str(value or "").replace(",", ".").strip()
    parts = normalized.split()
    if len(parts) != 2:
        return normalized
    code, amount = parts
    try:
        numeric = float(amount)
    except ValueError:
        return normalized
    return f"{code} {numeric:g}"


def catalog_search_blob(item: dict) -> str:
    fields = [
        item.get("libelle", ""),
        item.get("theme", ""),
        item.get("pathologies", ""),
        item.get("reeducation", ""),
        item.get("sous_division", ""),
        item.get("vignette_label_0", ""),
        item.get("vignette_label_1", ""),
        item.get("vignette_label_2", ""),
        item.get("vignette_label_3", ""),
        item.get("vignette_label_4", ""),
    ]
    return normalize_text(" ".join(str(field or "") for field in fields))


def score_candidate(rule: dict, item: dict) -> int:
    rule_label = normalize_text(rule.get("acte", ""))
    detail = normalize_text(rule.get("detail", ""))
    family = normalize_text(rule.get("famille", ""))
    blob = catalog_search_blob(item)
    label = normalize_text(item.get("libelle", ""))
    score = 0

    if label == rule_label:
        score += 100
    elif rule_label and (rule_label in label or label in rule_label):
        score += 60

    for token in detail.split():
        if len(token) > 2 and token in blob:
            score += 4

    for token in family.split():
        if len(token) > 3 and token in blob:
            score += 2

    if "non opere" in detail and "non opere" in blob:
        score += 20
    if "opere" in detail and "non opere" not in detail and "opere" in blob:
        score += 20
    if "un membre" in detail and "un membre" in blob:
        score += 20
    if "deux membres" in detail and "deux membres" in blob:
        score += 20
    if "plusieurs membres" in detail and "plusieurs membres" in blob:
        score += 20
    if "individuel" in detail and "individuel" in blob:
        score += 20
    if "groupe" in detail and "groupe" in blob:
        score += 20

    return score


def find_catalog_match(rule: dict, catalog: list[dict]) -> dict | None:
    hint_id = CATALOG_RULE_HINTS.get(rule.get("id"))
    if hint_id is not None:
        for item in catalog:
            if item.get("ID") == hint_id:
                return item

    rule_label = normalize_text(rule.get("acte", ""))
    if not rule_label:
        return None

    direct_matches = [item for item in catalog if normalize_text(item.get("libelle", "")) == rule_label]
    if direct_matches:
        return direct_matches[0]

    inclusive_matches = []
    for item in catalog:
        label = normalize_text(item.get("libelle", ""))
        if rule_label in label or label in rule_label:
            inclusive_matches.append(item)

    if not inclusive_matches:
        return None

    ranked = sorted(
        inclusive_matches,
        key=lambda item: (score_candidate(rule, item), len(normalize_text(item.get("libelle", "")))),
        reverse=True,
    )
    return ranked[0]


def main():
    catalog = load_truth_catalog()

    matched = []
    missing = []
    mismatches = []

    for rule in NGAP_RULES:
        catalog_item = find_catalog_match(rule, catalog)
        if catalog_item is None:
            missing.append(rule)
            continue

        matched.append((rule, catalog_item))
        rule_cotation = normalize_cotation(rule.get("cotation", ""))
        catalog_cotation = normalize_cotation(format_catalog_cotation(catalog_item))
        if rule_cotation != catalog_cotation:
            mismatches.append((rule, catalog_item))

    print(f"Regles locales : {len(NGAP_RULES)}")
    print(f"Entrees catalogue : {len(catalog)}")
    print(f"Correspondances libellees : {len(matched)}")
    print(f"Libelles sans match catalogue : {len(missing)}")
    print(f"Cotations differentes parmi les matches : {len(mismatches)}")

    if mismatches:
        print("\nExemples d'ecarts de cotation :")
        for rule, catalog_item in mismatches[:20]:
            print(
                f"- {rule['id']}: local={rule['cotation']} / catalogue={format_catalog_cotation(catalog_item)}"
            )

    if missing:
        print("\nExemples de regles sans match catalogue :")
        for rule in missing[:20]:
            print(f"- {rule['id']}: {rule['acte']}")


if __name__ == "__main__":
    main()
