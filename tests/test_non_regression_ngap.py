import unittest
from collections import Counter

from assistant_ngap import proposer_choix, repondre
from ngap_database import NGAP_RULES


KNOWN_COTATIONS = {
    r["cotation"]
    for r in NGAP_RULES
    if isinstance(r.get("cotation"), str) and r["cotation"].strip()
}
RULE_BY_ID = {r["id"]: r for r in NGAP_RULES}
OFFICIAL_COTATIONS_2026 = {
    "APM 8.10", "APM 8.11", "APM 9.80",
    "ARL 7.99", "ARL 8.00", "ARL 8.01", "ARL 8.49", "ARL 8.50", "ARL 8.51", "ARL 10.00", "ARL 20.00", "ARL 28.00",
    "DRA 8.08", "DRA 8.09", "DRA 8.10", "DRA 8.11",
    "NMI 8.00", "NMI 8.50", "NMI 8.51", "NMI 9.00", "NMI 9.01", "NMI 11.00", "NMI 11.01", "NMI 11.99", "NMI 12.00", "NMI 12.01",
    "PLL 12.00",
    "RAB 8.00", "RAB 8.01", "RAB 8.50",
    "RAM 8.07", "RAM 8.08", "RAM 8.09", "RAM 8.10", "RAM 8.11", "RAM 8.12", "RAM 8.13",
    "RAO 8.08", "RAO 8.09", "RAO 8.10", "RAO 8.11",
    "RAV 1.00", "RAV 2.00", "RAV 7.99", "RAV 8.00", "RAV 8.01", "RAV 9.00", "RAV 15.50",
    "RIC 8.08", "RIC 8.09", "RIC 8.10", "RIC 8.11", "RIC 8.12",
    "RIM 8.10",
    "RPB 8.00", "RPB 9.00",
    "RPE 8.50",
    "RSC 8.09", "RSC 8.10", "RSC 8.11", "RSC 8.12",
    "RSM 8.09", "RSM 8.10", "RSM 8.11", "RSM 8.12",
    "TER 9.79", "TER 9.81", "TER 16.00",
    "VIC 8.09", "VIC 8.10", "VIC 8.11", "VIC 8.12",
    "VIM 8.09", "VIM 8.10", "VIM 8.11", "VIM 8.12",
    "VSC 8.09", "VSC 8.10", "VSC 8.11", "VSC 8.12",
    "VSM 8.08", "VSM 8.09", "VSM 8.10", "VSM 8.11",
}


def _extract_cotation(texte: str):
    for line in texte.splitlines():
        if line.startswith("Cotation NGAP : "):
            return line.replace("Cotation NGAP : ", "", 1).strip()
        if line.startswith("Cotation : "):
            return line.replace("Cotation : ", "", 1).strip()
    return None


def _extract_seances(texte: str):
    for line in texte.splitlines():
        if line.startswith("Nombre de séances max : "):
            return line.replace("Nombre de séances max : ", "", 1).strip()
    return None


class TestNGAPNonRegression(unittest.TestCase):
    def test_no_duplicate_rule_ids(self):
        duplicates = [key for key, value in Counter(r["id"] for r in NGAP_RULES).items() if value > 1]
        self.assertEqual(duplicates, [])

    def test_all_rule_cotations_are_official_2026(self):
        unknown = sorted({r["cotation"] for r in NGAP_RULES if r["cotation"] not in OFFICIAL_COTATIONS_2026})
        self.assertEqual(unknown, [])

    def test_catalog_aligned_cotations(self):
        expected = {
            "rachis_lombalgie_commune": "RAM 8.09",
            "rachis_lombosacre_non_opere": "RAM 8.11",
            "rachis_lombosacre_opere": "RAO 8.09",
            "rachis_dorsal_non_opere": "RAM 8.10",
            "rachis_dorsal_opere": "RAO 8.08",
            "rachis_cervical_non_opere": "RAM 8.12",
            "rachis_cervicalgie_commune": "RAM 8.07",
            "rachis_cervical_opere": "RAO 8.10",
            "rachis_plusieurs_segments_opere": "RAO 8.11",
            "rachis_trauma_cervical_recent": "RAM 8.08",
            "rachis_plusieurs_segments": "RAM 8.13",
            "deviation_rachis_lombosacre": "DRA 8.09",
            "deviation_rachis_dorsal": "DRA 8.08",
            "deviation_rachis_plusieurs_segments": "DRA 8.10",
            "membre_inf_lca": "RIC 8.08",
            "membre_inf_ptg": "RIC 8.12",
            "membre_inf_meniscectomie": "RIC 8.09",
            "membre_inf_genou_jambe_opere": "VIC 8.10",
            "membre_inf_hanche_cuisse_operee": "VIC 8.09",
            "membre_inf_plusieurs_segments_operes": "VIC 8.12",
            "membre_inf_genou_jambe_non_opere": "VIM 8.11",
            "membre_inf_hanche_cuisse_non_operee": "VIM 8.09",
            "membre_inf_plusieurs_segments_non_operes": "VIM 8.12",
            "membre_inf_entorse_cheville_non_operee": "RIM 8.10",
            "membre_inf_entorse_cheville_operee": "RIC 8.11",
            "membre_inf_cheville_pied_non_opere": "VIM 8.10",
            "membre_inf_cheville_pied_opere": "VIC 8.11",
            "membre_sup_canal_carpien": "RSC 8.09",
            "membre_sup_coiffe_non_operee": "RSM 8.09",
            "membre_sup_epaule_bras_opere": "VSC 8.10",
            "membre_sup_coude_avant_bras_opere": "VSC 8.09",
            "membre_sup_epaule_bras_non_opere": "VSM 8.08",
            "membre_sup_coude_avant_bras_non_opere": "VSM 8.09",
            "membre_sup_poignet_main_non_opere": "VSM 8.10",
            "membre_sup_poignet_main_opere": "VSC 8.11",
            "membre_sup_fracture_humerus_prox_operee": "VSC 8.10",
            "membre_sup_plusieurs_segments_non_operes": "VSM 8.11",
            "membre_sup_plusieurs_segments_operes": "VSC 8.12",
            "vasculaire_bandage_un_membre": "RAV 1.00",
            "sujet_age_deambulation": "RPE 8.50",
            "amputation_un_membre_superieur": "APM 8.11",
            "amputation_un_membre_inferieur": "APM 8.10",
            "rhumatismales_atteinte_localisee": "NMI 8.00",
            "neurologie_atteintes_peripheriques_radiculaires_tronculaires_un_membre": "NMI 8.50",
            "neurologie_hemiplegie": "NMI 9.00",
            "neurologie_affection_stable_plusieurs": "NMI 11.00",
            "neurologie_encephalopathie_infantile": "NMI 12.00",
            "neurologie_paralysie_cerebrale_polyhandicap": "TER 16.00",
            "respiratoire_bpco_sans_handicap_chronique": "ARL 8.50",
            "respiratoire_obstructive_restrictive_mixte": "ARL 8.50",
            "respiratoire_mucoviscidose": "ARL 10.00",
            "respiratoire_handicap_chronique_individuel": "ARL 28.00",
            "respiratoire_handicap_chronique_groupe": "ARL 20.00",
            "plusieurs_territoires_sans_chirurgie": "TER 9.79",
            "plusieurs_territoires_avec_chirurgie": "TER 9.81",
        }
        for rule_id, cotation in expected.items():
            self.assertEqual(RULE_BY_ID[rule_id]["cotation"], cotation, rule_id)

    def assert_final_with_known_cotation(self, message: str, expected_cotation: str):
        result = repondre(message)
        if not result["termine"] and result["attente"].startswith("type_"):
            # Segment sans diagnostic : l'app demande le type ; on répond "autre" (cotation générique).
            result = repondre("autre", result["nouveau_contexte"], result["attente"])
        self.assertTrue(result["termine"], f"Expected final answer for: {message}")
        cotation = _extract_cotation(result["texte"])
        self.assertEqual(cotation, expected_cotation)
        self.assertIn(cotation, KNOWN_COTATIONS, f"Unknown cotation returned: {cotation}")

    def assert_short_question(self, message: str, expected_question: str, max_len: int = 60):
        result = repondre(message)
        self.assertFalse(result["termine"], f"Expected question for: {message}")
        self.assertEqual(result["texte"], expected_question)
        self.assertLessEqual(len(result["texte"]), max_len)

    def assert_seances(self, message: str, expected_seances: str):
        result = repondre(message)
        self.assertTrue(result["termine"], f"Expected final answer for: {message}")
        self.assertEqual(_extract_seances(result["texte"]), expected_seances)

    def assert_choices_present(self, message: str):
        result = repondre(message)
        self.assertFalse(result["termine"], f"Expected question for: {message}")
        choices = proposer_choix(message, "", result["attente"])
        self.assertTrue(choices, f"Expected choices for attente={result['attente']} and message={message}")

    def test_rachis_lombaire_commune_final(self):
        self.assert_final_with_known_cotation(
            "lombalgie commune",
            RULE_BY_ID["rachis_lombalgie_commune"]["cotation"],
        )

    def test_lombalgie_simple_demande_precision(self):
        result = repondre("lombalgie")
        self.assertFalse(result["termine"])
        self.assertTrue(result["texte"].startswith("Question :"))
        self.assertNotEqual(result["attente"], "")

    def test_genou_lca_final(self):
        self.assert_final_with_known_cotation(
            "ligamentoplastie lca genou",
            RULE_BY_ID["membre_inf_lca"]["cotation"],
        )

    def test_ptg_voice_mapping_final(self):
        self.assert_final_with_known_cotation(
            "reeducation pour une ptg",
            RULE_BY_ID["membre_inf_ptg"]["cotation"],
        )

    def test_prothese_genou_voice_mapping_final(self):
        self.assert_final_with_known_cotation(
            "prothese de genou",
            RULE_BY_ID["membre_inf_ptg"]["cotation"],
        )

    def test_changement_compartiment_voice_mapping_final(self):
        self.assert_final_with_known_cotation(
            "changement de compartiment genou",
            RULE_BY_ID["membre_inf_ptg"]["cotation"],
        )

    def test_croise_anterieur_voice_mapping_final(self):
        self.assert_final_with_known_cotation(
            "suite a une ligamentoplastie du croise anterieur",
            RULE_BY_ID["membre_inf_lca"]["cotation"],
        )

    def test_lcp_voice_mapping_final(self):
        self.assert_final_with_known_cotation(
            "lcp genou opéré",
            "VIC 8.10",
        )

    def test_didt_voice_mapping_final(self):
        self.assert_final_with_known_cotation(
            "didt genou",
            RULE_BY_ID["membre_inf_lca"]["cotation"],
        )

    def test_kenneth_jones_voice_mapping_final(self):
        self.assert_final_with_known_cotation(
            "kenneth-jones genou",
            RULE_BY_ID["membre_inf_lca"]["cotation"],
        )

    def test_suture_meniscale_voice_mapping_final(self):
        self.assert_final_with_known_cotation(
            "suture meniscale du genou",
            "VIC 8.10",  # suture méniscale ≠ méniscectomie (référentiel RIC 8.09)
        )

    def test_menisque_interne_voice_mapping_final(self):
        result = repondre("menisque interne opere")
        self.assertEqual(result["attente"], "menisque_type")
        result = repondre("meniscectomie", result["nouveau_contexte"], result["attente"])
        self.assertEqual(_extract_cotation(result["texte"]), RULE_BY_ID["membre_inf_meniscectomie"]["cotation"])

    def test_canal_carpien_final(self):
        self.assert_short_question(
            "canal carpien",
            "Question : canal carpien opere ou non ?",
        )

    def test_hemiplegie_final(self):
        self.assert_final_with_known_cotation(
            "hemiplegie",
            RULE_BY_ID["neurologie_hemiplegie"]["cotation"],
        )

    def test_final_format_matches_expert_template(self):
        result = repondre("lca genou opéré")
        self.assertTrue(result["termine"])
        self.assertIn("Cotation NGAP : ", result["texte"])
        self.assertIn("Libellé NGAP : ", result["texte"])
        self.assertIn("Analyse :", result["texte"])
        self.assertIn("Justification :", result["texte"])
        self.assertIn("Confiance : ", result["texte"])

    def test_lca_non_opere_donne_genou_non_opere(self):
        self.assert_final_with_known_cotation(
            "rupture lca genou non opere",
            RULE_BY_ID["membre_inf_genou_jambe_non_opere"]["cotation"],
        )

    def test_bpco_majuscule_sans_handicap_chronique_final(self):
        result = repondre("BPCO")
        self.assertEqual(result["attente"], "bpco_type")
        result = repondre("sans rehabilitation", result["nouveau_contexte"], result["attente"])
        self.assertEqual(_extract_cotation(result["texte"]), RULE_BY_ID["respiratoire_bpco_sans_handicap_chronique"]["cotation"])

    def test_lymphoedeme_short_question(self):
        self.assert_short_question("lymphoedeme", "Question : quel type de lymphoedeme ?")

    def test_douleur_cheville_demande_precision_complete(self):
        self.assert_short_question(
            "douleur de cheville",
            "Question : opere ou non ?",
        )
        self.assert_choices_present("douleur de cheville")

    def test_douleur_epaule_demande_precision_complete(self):
        self.assert_short_question(
            "douleur d epaule",
            "Question : opere ou non ?",
        )
        self.assert_choices_present("douleur d epaule")

    def test_amputation_short_question(self):
        self.assert_short_question("amputation", "Question : Membre supérieur, inférieur ou plusieurs ?")

    def test_brulure_main_final(self):
        self.assert_final_with_known_cotation(
            "brulure main",
            RULE_BY_ID["brulure_un_membre"]["cotation"],
        )

    def test_brulure_tronc_bras_final(self):
        self.assert_final_with_known_cotation(
            "brulure tronc et bras",
            RULE_BY_ID["brulure_plusieurs_membres_tronc"]["cotation"],
        )

    def test_plusieurs_territoires_final(self):
        self.assert_final_with_known_cotation(
            "lombalgie + genou opere",
            RULE_BY_ID["plusieurs_territoires_avec_chirurgie"]["cotation"],
        )

    def test_soins_palliatifs_final(self):
        self.assert_final_with_known_cotation(
            "soins palliatifs",
            RULE_BY_ID["soins_palliatifs"]["cotation"],
        )

    def test_genou_non_opere_final(self):
        self.assert_final_with_known_cotation(
            "genou non opere",
            RULE_BY_ID["membre_inf_genou_jambe_non_opere"]["cotation"],
        )

    def test_epaule_tendinopathie_non_operee_final(self):
        self.assert_final_with_known_cotation(
            "reeducation thendinopathie de l epaule non opéré",
            RULE_BY_ID["membre_sup_coiffe_non_operee"]["cotation"],
        )

    def test_hanche_sans_operation_final(self):
        self.assert_final_with_known_cotation(
            "douleur de hanche sans operation",
            RULE_BY_ID["membre_inf_hanche_cuisse_non_operee"]["cotation"],
        )

    def test_sujet_age_langage_naturel_final(self):
        self.assert_final_with_known_cotation(
            "mamie tombe souvent et marche mal",
            RULE_BY_ID["sujet_age_deambulation"]["cotation"],
        )

    def test_lymphoedeme_cancer_sein_bras_final(self):
        self.assert_final_with_known_cotation(
            "lymphoedeme apres cancer du sein un bras phase intensive",
            RULE_BY_ID["vasculaire_lymphoedeme_sein"]["cotation"],
        )

    def test_asr_non_opere_variant_final(self):
        self.assert_final_with_known_cotation(
            "epaule n an opere",
            RULE_BY_ID["membre_sup_epaule_bras_non_opere"]["cotation"],
        )

    def test_rachis_lombaire_non_opere_langage_naturel_final(self):
        self.assert_final_with_known_cotation(
            "cotation rééducation rachis lombaire non opéré",
            RULE_BY_ID["rachis_lombosacre_non_opere"]["cotation"],
        )

    def test_epicondylite_coude_final(self):
        self.assert_final_with_known_cotation(
            "rééducation epicondyilite du coude",
            RULE_BY_ID["membre_sup_coude_avant_bras_non_opere"]["cotation"],
        )

    def test_epicondylite_seule_final(self):
        self.assert_final_with_known_cotation(
            "epicondylite",
            RULE_BY_ID["membre_sup_coude_avant_bras_non_opere"]["cotation"],
        )

    def test_tendinopathie_epaule_non_operee_final(self):
        self.assert_final_with_known_cotation(
            "reeducation thendinopathie de l’épaule non opéré",
            RULE_BY_ID["membre_sup_coiffe_non_operee"]["cotation"],
        )

    def test_deux_genoux_demande_operes_ou_non(self):
        self.assert_short_question(
            "Reeducation des genoux deux membres inférieurs",
            "Question : operes ou non ? confirmer bilateral.",
        )

    def test_deux_genoux_propose_des_choix(self):
        self.assert_choices_present("Reeducation des genoux deux membres inférieurs")

    def test_deux_genoux_apres_chirurgie_final(self):
        self.assert_final_with_known_cotation("les deux genoux apres chirurgie", "TER 9.81")

    def test_bilateral_genoux_operes_final(self):
        self.assert_final_with_known_cotation("bilateral genoux operes", "TER 9.81")

    def test_deux_segments_meme_membre_apres_chirurgie_final(self):
        self.assert_final_with_known_cotation(
            "deux segments membre inferieur operes",
            RULE_BY_ID["membre_inf_plusieurs_segments_operes"]["cotation"],
        )

    def test_deux_membres_inferieurs_non_operes_final(self):
        self.assert_final_with_known_cotation("reeducation des deux membres inferieurs pas operee", "TER 9.79")

    def test_membres_inferieurs_pluriel_demande_ter_et_non_segments(self):
        self.assert_short_question(
            "reeducation des membres inferieurs",
            "Question : operes ou non ? confirmer bilateral.",
        )

    def test_membres_inferieurs_pluriel_non_operes_final(self):
        self.assert_final_with_known_cotation(
            "reeducation des membres inferieurs non operes",
            RULE_BY_ID["plusieurs_territoires_sans_chirurgie"]["cotation"],
        )

    def test_deux_membres_superieurs_non_operes_final(self):
        self.assert_final_with_known_cotation("reeducation des deux membres superieurs non operes", "TER 9.79")

    def test_deux_membres_inf_puis_non_donne_ter_sans_chirurgie(self):
        r1 = repondre("Reeducation des genoux deux membres inferieurs")
        self.assertFalse(r1["termine"])
        r2 = repondre("non", r1["nouveau_contexte"], r1["attente"])
        self.assertTrue(r2["termine"])
        self.assertEqual(_extract_cotation(r2["texte"]), "TER 9.79")

    def test_deux_membres_inf_puis_oui_donne_ter_avec_chirurgie(self):
        r1 = repondre("Reeducation des genoux deux membres inferieurs")
        self.assertFalse(r1["termine"])
        r2 = repondre("oui", r1["nouveau_contexte"], r1["attente"])
        self.assertTrue(r2["termine"])
        self.assertEqual(_extract_cotation(r2["texte"]), "TER 9.81")

    def test_genou_opere_demande_type_chirurgie(self):
        self.assert_short_question(
            "cotation pour un genou droit opéré",
            "Question : prothese / lca / meniscectomie / autre ?",
        )

    def test_plusieurs_territoires_demande_chirurgie(self):
        self.assert_short_question(
            "rééducation des deux membres inférieurs et du rachis dorsaux lombaire",
            "Question : operes ou non ? confirmer bilateral.",
        )

    def test_vasculaire_precision_propose_des_choix(self):
        self.assert_choices_present("vasculaire")

    def test_bras_et_jambe_apres_chirurgie_final(self):
        self.assert_final_with_known_cotation(
            "bras droit et jambe gauche apres chirurgie",
            RULE_BY_ID["plusieurs_territoires_avec_chirurgie"]["cotation"],
        )

    def test_membres_sup_et_inf_final(self):
        result = repondre("membres sup et inf")
        self.assertFalse(result["termine"])  # chirurgie non précisée : on demande
        self.assert_final_with_known_cotation(
            "membres sup et inf non operes",
            RULE_BY_ID["plusieurs_territoires_sans_chirurgie"]["cotation"],
        )

    def test_deviation_rachis_cervical_demande_age(self):
        result = repondre("deviation rachis cervical")
        self.assertFalse(result["termine"])
        self.assertIn("18 ans", result["texte"])
        result = repondre("oui", result["nouveau_contexte"], result["attente"])
        self.assertEqual(_extract_cotation(result["texte"]), "DRA 8.11")

    def test_scoliose_demande_segment(self):
        result = repondre("scoliose")
        self.assertFalse(result["termine"])
        self.assertEqual(result["texte"], "Question : cervical / dorsal / lombaire / plusieurs segments ?")
        self.assertEqual(result["attente"], "rachis_deviation_segment")

    def test_scoliose_adolescent_cervical_final(self):
        result = repondre("scoliose adolescent")
        self.assertFalse(result["termine"])
        self.assertEqual(result["attente"], "rachis_deviation_segment")
        result = repondre("cervical", result["nouveau_contexte"], result["attente"])
        self.assertTrue(result["termine"])
        self.assertEqual(_extract_cotation(result["texte"]), RULE_BY_ID["deviation_rachis_cervical"]["cotation"])

    def test_deviation_rachis_cervical_enfant_final(self):
        self.assert_final_with_known_cotation(
            "deviation rachis cervical enfant",
            RULE_BY_ID["deviation_rachis_cervical"]["cotation"],
        )

    def test_sep_plusieurs_membres_final(self):
        self.assert_final_with_known_cotation(
            "sep plusieurs membres",
            RULE_BY_ID["neurologie_affection_stable_plusieurs"]["cotation"],
        )

    def test_voice_variant_epi_condylite_final(self):
        self.assert_final_with_known_cotation(
            "reeducation epi condylite du coude",
            RULE_BY_ID["membre_sup_coude_avant_bras_non_opere"]["cotation"],
        )

    def test_voice_variant_non_opere_final(self):
        self.assert_final_with_known_cotation(
            "cotation genou droit nan opere",
            RULE_BY_ID["membre_inf_genou_jambe_non_opere"]["cotation"],
        )

    def test_voice_variant_rachis_lombair_final(self):
        self.assert_final_with_known_cotation(
            "reeducation rachi lombair non opere",
            RULE_BY_ID["rachis_lombosacre_non_opere"]["cotation"],
        )

    def test_voice_variant_nono_perret_final(self):
        self.assert_final_with_known_cotation(
            "epaule nono perret",
            RULE_BY_ID["membre_sup_epaule_bras_non_opere"]["cotation"],
        )

    def test_voice_variant_rajhi_lombair_final(self):
        self.assert_final_with_known_cotation(
            "rajhi lombair non opere",
            RULE_BY_ID["rachis_lombosacre_non_opere"]["cotation"],
        )

    def test_voice_variant_epol_final(self):
        self.assert_final_with_known_cotation(
            "epol non opere",
            RULE_BY_ID["membre_sup_epaule_bras_non_opere"]["cotation"],
        )

    def test_voice_variant_lymfoedeme_final(self):
        result = repondre("lymfoedeme bras")
        self.assertEqual(result["attente"], "lymph_type")
        result = repondre("un membre", result["nouveau_contexte"], result["attente"])
        self.assertEqual(_extract_cotation(result["texte"]), RULE_BY_ID["vasculaire_lymphoedeme_un_membre"]["cotation"])

    def test_voice_variant_nom_ope_rez_final(self):
        self.assert_final_with_known_cotation(
            "epaule nom opé rez",
            RULE_BY_ID["membre_sup_epaule_bras_non_opere"]["cotation"],
        )

    def test_voice_variant_non_on_operee_final(self):
        self.assert_final_with_known_cotation(
            "epaule non on operee",
            RULE_BY_ID["membre_sup_epaule_bras_non_opere"]["cotation"],
        )

    def test_voice_variant_nom_de_operer_final(self):
        self.assert_final_with_known_cotation(
            "epaule nom de operer",
            RULE_BY_ID["membre_sup_epaule_bras_non_opere"]["cotation"],
        )

    def test_voice_variant_mon_operer_final(self):
        self.assert_final_with_known_cotation(
            "epaule mon operer",
            RULE_BY_ID["membre_sup_epaule_bras_non_opere"]["cotation"],
        )

    def test_cervicalgie_commune_reponse_directe(self):
        self.assert_final_with_known_cotation(
            "cervicalgie commune",
            RULE_BY_ID["rachis_cervicalgie_commune"]["cotation"],
        )

    def test_cervicalgie_commune_adulte_reponse_directe(self):
        self.assert_final_with_known_cotation(
            "cervicalgie commune adulte",
            RULE_BY_ID["rachis_cervicalgie_commune"]["cotation"],
        )

    def test_cervicalgie_commune_mineur_final(self):
        self.assert_final_with_known_cotation(
            "cervicalgie commune mineur",
            RULE_BY_ID["rachis_cervicalgie_commune"]["cotation"],
        )

    def test_cervicalgie_commune_enfant_reponse_directe(self):
        self.assert_final_with_known_cotation(
            "cervicalgie commune enfant",
            RULE_BY_ID["rachis_cervicalgie_commune"]["cotation"],
        )

    def test_cervicalgie_seule_demande_precision(self):
        result = repondre("cervicalgie")
        self.assertFalse(result["termine"])
        self.assertNotIn("18 ans", result["texte"])

    def test_general_precision_puis_message_complet_donne_reponse(self):
        r1 = repondre("reeducation")
        self.assertFalse(r1["termine"])
        self.assertEqual(r1["attente"], "general_precision")

        r2 = repondre(
            "reeducation des deux membres inferieurs non opere",
            r1["nouveau_contexte"],
            r1["attente"],
        )
        self.assertTrue(r2["termine"])
        self.assertEqual(_extract_cotation(r2["texte"]), "TER 9.79")

    def test_general_precision_propose_des_choix(self):
        result = repondre("douleur")
        self.assertFalse(result["termine"])
        self.assertEqual(result["attente"], "general_precision")
        choices = proposer_choix("douleur", "", result["attente"])
        self.assertEqual(
            choices,
            [
                {"label": "Membre inférieur", "value": "membre inferieur"},
                {"label": "Membre supérieur", "value": "membre superieur"},
                {"label": "Rachis", "value": "rachis"},
                {"label": "Neurologie", "value": "neurologie"},
                {"label": "Respiratoire", "value": "respiratoire"},
                {"label": "Lymphœdème / vasculaire", "value": "lymphoedeme"},
            ],
        )

    def test_trauma_cervical_recent_final(self):
        self.assert_final_with_known_cotation(
            "coup du lapin",
            RULE_BY_ID["rachis_trauma_cervical_recent"]["cotation"],
        )

    def test_lumbago_final(self):
        self.assert_final_with_known_cotation(
            "lumbago",
            RULE_BY_ID["rachis_lombalgie_commune"]["cotation"],
        )

    def test_whiplash_final(self):
        self.assert_final_with_known_cotation(
            "whiplash",
            RULE_BY_ID["rachis_trauma_cervical_recent"]["cotation"],
        )

    def test_accident_de_voiture_cervical_final(self):
        self.assert_final_with_known_cotation(
            "accident de voiture cervicales",
            RULE_BY_ID["rachis_trauma_cervical_recent"]["cotation"],
        )

    def test_dorsalgie_final(self):
        self.assert_final_with_known_cotation(
            "dorsalgie chronique",
            RULE_BY_ID["rachis_dorsal_non_opere"]["cotation"],
        )

    def test_lordose_final(self):
        self.assert_final_with_known_cotation("lordose 12 ans", "DRA 8.09")

    def test_pth_final(self):
        self.assert_final_with_known_cotation(
            "prothese totale de hanche",
            RULE_BY_ID["membre_inf_pth"]["cotation"],
        )

    def test_prothese_de_hanche_final(self):
        self.assert_final_with_known_cotation(
            "prothese de hanche",
            RULE_BY_ID["membre_inf_pth"]["cotation"],
        )

    def test_protheses_de_hanche_final(self):
        self.assert_final_with_known_cotation(
            "protheses de hanche",
            RULE_BY_ID["membre_inf_pth"]["cotation"],
        )

    def test_epaule_gauche_non_operee_final(self):
        self.assert_final_with_known_cotation(
            "epaule gauche non operee",
            RULE_BY_ID["membre_sup_epaule_bras_non_opere"]["cotation"],
        )

    def test_arthroplastie_epaule_final(self):
        self.assert_final_with_known_cotation(
            "arthroplastie epaule",
            RULE_BY_ID["membre_sup_epaule_bras_opere"]["cotation"],
        )

    def test_ligament_croise_opere_final(self):
        self.assert_final_with_known_cotation(
            "s est fait operer du ligament croise",
            RULE_BY_ID["membre_inf_lca"]["cotation"],
        )

    def test_bandage_bras_demande_etendue(self):
        result = repondre("bandage bras")
        self.assertFalse(result["termine"])
        self.assertEqual(result["texte"], "Question : Un membre ou deux ?")
        self.assertEqual(result["attente"], "vasculaire_bandage_etendue")

    def test_lymphoedeme_deux_bras_final(self):
        self.assert_final_with_known_cotation(
            "lymphoedeme deux bras",
            RULE_BY_ID["vasculaire_lymphoedeme_deux_membres"]["cotation"],
        )

    def test_bandage_multicouche_deux_membres_final(self):
        self.assert_final_with_known_cotation(
            "bandage multicouche deux membres",
            RULE_BY_ID["vasculaire_bandage_deux_membres"]["cotation"],
        )

    def test_bondage_multicouche_membres_demande_etendue(self):
        result = repondre("bondage multicouche de membres")
        self.assertFalse(result["termine"])
        self.assertEqual(result["attente"], "vasculaire_bandage_etendue")

    def test_cheville_non_operee_final(self):
        self.assert_final_with_known_cotation(
            "cheville non opérée",
            RULE_BY_ID["membre_inf_cheville_pied_non_opere"]["cotation"],
        )

    def test_cheville_operee_autre_final(self):
        self.assert_final_with_known_cotation(
            "cheville opérée autre",
            RULE_BY_ID["membre_inf_cheville_pied_opere"]["cotation"],
        )

    def test_entorse_cheville_operee_final(self):
        self.assert_final_with_known_cotation(
            "entorse externe cheville opérée",
            RULE_BY_ID["membre_inf_entorse_cheville_operee"]["cotation"],
        )

    def test_lle_cheville_final(self):
        self.assert_final_with_known_cotation(
            "lle cheville non opérée",
            RULE_BY_ID["membre_inf_entorse_cheville_non_operee"]["cotation"],
        )

    def test_entorse_interne_cheville_final(self):
        self.assert_final_with_known_cotation(
            "entorse interne cheville non opérée",
            RULE_BY_ID["membre_inf_cheville_pied_non_opere"]["cotation"],
        )

    def test_entorse_genou_ne_donne_pas_cheville(self):
        result = repondre("entorse du genou non operee")
        self.assertTrue(result["termine"])
        cotation = _extract_cotation(result["texte"])
        self.assertEqual(cotation, RULE_BY_ID["membre_inf_genou_jambe_non_opere"]["cotation"])

    def test_entorse_genou_non_operee_final(self):
        self.assert_final_with_known_cotation(
            "entorse du genou non operee",
            RULE_BY_ID["membre_inf_genou_jambe_non_opere"]["cotation"],
        )

    def test_entorse_genou_demande_chirurgie(self):
        result = repondre("entorse du genou")
        self.assertFalse(result["termine"])
        self.assertEqual(result["attente"], "genou_chirurgie")

    def test_fracture_cheville_operee_final(self):
        self.assert_final_with_known_cotation(
            "fracture cheville opérée",
            RULE_BY_ID["membre_inf_cheville_pied_opere"]["cotation"],
        )

    def test_rachis_cervical_opere_final(self):
        self.assert_final_with_known_cotation(
            "rachis cervical opéré",
            RULE_BY_ID["rachis_cervical_opere"]["cotation"],
        )

    def test_fracture_coude_non_operee_final(self):
        self.assert_final_with_known_cotation(
            "fracture du coude non opérée",
            RULE_BY_ID["membre_sup_fracture_coude_adulte_non_operee"]["cotation"],
        )

    def test_luxation_coude_non_operee_final(self):
        result = repondre("luxation coude non opérée")
        self.assertEqual(result["attente"], "luxation_coude_fracture")
        result = repondre("avec fracture", result["nouveau_contexte"], result["attente"])
        self.assertEqual(_extract_cotation(result["texte"]), RULE_BY_ID["membre_sup_fracture_coude_adulte_non_operee"]["cotation"])

    def test_luxation_coude_operee_final(self):
        result = repondre("luxation coude opérée")
        self.assertEqual(result["attente"], "luxation_coude_fracture")
        result = repondre("avec fracture", result["nouveau_contexte"], result["attente"])
        self.assertEqual(_extract_cotation(result["texte"]), RULE_BY_ID["membre_sup_fracture_coude_adulte_operee"]["cotation"])

    def test_coude_fracture_operee_final(self):
        self.assert_final_with_known_cotation(
            "coude fracture opérée",
            RULE_BY_ID["membre_sup_fracture_coude_adulte_operee"]["cotation"],
        )

    def test_pouteau_colles_demande_chirurgie(self):
        result = repondre("pouteau colles")
        self.assertFalse(result["termine"])
        self.assertEqual(result["attente"], "segment_chirurgie")
        result = repondre("non", result["nouveau_contexte"], result["attente"])
        self.assertEqual(_extract_cotation(result["texte"]), "RSM 8.11")

    def test_pouteau_colles_non_operee_final(self):
        reponse = repondre("pouteau colles")
        self.assertFalse(reponse["termine"])
        reponse = repondre("non operee", reponse["nouveau_contexte"], reponse["attente"])
        self.assertTrue(reponse["termine"])
        self.assertIn(RULE_BY_ID["membre_sup_fracture_avant_bras_distale_non_operee"]["cotation"], reponse["texte"])

    def test_fracture_humerus_prox_non_operee_final(self):
        self.assert_final_with_known_cotation(
            "fracture proximale humerus non opérée",
            RULE_BY_ID["membre_sup_fracture_humerus_prox_non_operee"]["cotation"],
        )

    def test_fracture_humerus_proximal_non_operee_final(self):
        self.assert_final_with_known_cotation(
            "fracture humerus proximal non operee",
            RULE_BY_ID["membre_sup_fracture_humerus_prox_non_operee"]["cotation"],
        )

    def test_fracture_humerus_prox_operee_final(self):
        self.assert_final_with_known_cotation(
            "fracture proximale humerus opérée",
            RULE_BY_ID["membre_sup_fracture_humerus_prox_operee"]["cotation"],
        )

    def test_fracture_humerus_operee_final(self):
        self.assert_final_with_known_cotation(
            "fracture humerus operee",
            RULE_BY_ID["membre_sup_fracture_humerus_prox_operee"]["cotation"],
        )

    def test_fracture_humerus_operee_demande_chirurgie(self):
        result = repondre("fracture humerus")
        self.assertFalse(result["termine"])
        self.assertEqual(result["texte"], "Question : operee ou non ?")

    def test_coiffe_operee_final(self):
        self.assert_final_with_known_cotation(
            "chirurgie coiffe",
            RULE_BY_ID["membre_sup_coiffe_operee"]["cotation"],
        )

    def test_tunnel_carpien_final(self):
        self.assert_short_question(
            "tunnel carpien",
            "Question : canal carpien opere ou non ?",
        )

    def test_syndrome_tunnel_carpien_final(self):
        self.assert_short_question(
            "syndrome du tunnel carpien",
            "Question : canal carpien opere ou non ?",
        )

    def test_poignet_casse_demande_chirurgie(self):
        result = repondre("poignet cassé")
        self.assertFalse(result["termine"])
        self.assertEqual(result["attente"], "fracture_poignet_type")
        result = repondre("radius distal", result["nouveau_contexte"], result["attente"])
        self.assertEqual(result["attente"], "segment_chirurgie")
        result = repondre("non", result["nouveau_contexte"], result["attente"])
        self.assertEqual(_extract_cotation(result["texte"]), "RSM 8.11")

    def test_genou_simple_demande_chirurgie(self):
        result = repondre("genou")
        self.assertFalse(result["termine"])
        self.assertEqual(result["texte"], "Question : chirurgie du genou ou non ?")
        self.assertEqual(result["attente"], "genou_chirurgie")

    def test_sciatique_rachis_donne_lombosacre(self):
        result = repondre("sciatique")
        self.assertFalse(result["termine"])
        result2 = repondre("rachis", result["nouveau_contexte"], result["attente"])
        self.assertTrue(result2["termine"])
        self.assertIn(RULE_BY_ID["rachis_lombosacre_non_opere"]["cotation"], result2["texte"])

    def test_sciatique_neuro_donne_peripherique_un_membre(self):
        result = repondre("sciatique")
        result2 = repondre("peripherique", result["nouveau_contexte"], result["attente"])
        self.assertTrue(result2["termine"])
        self.assertIn(
            RULE_BY_ID["neurologie_atteintes_peripheriques_radiculaires_tronculaires_un_membre"]["cotation"],
            result2["texte"],
        )

    def test_acromioplastie_final(self):
        self.assert_final_with_known_cotation(
            "acromioplastie epaule",
            RULE_BY_ID["membre_sup_coiffe_operee"]["cotation"],
        )

    def test_mucoviscidose_final(self):
        self.assert_final_with_known_cotation(
            "mucoviscidose",
            RULE_BY_ID["respiratoire_mucoviscidose"]["cotation"],
        )

    def test_bpco_groupe_sans_precision_handicap_final(self):
        self.assert_final_with_known_cotation(
            "bpco groupe",
            RULE_BY_ID["respiratoire_handicap_chronique_groupe"]["cotation"],
        )

    def test_bpco_sans_handicap_chronique_final(self):
        result = repondre("bpco")
        self.assertEqual(result["attente"], "bpco_type")
        result = repondre("sans rehabilitation", result["nouveau_contexte"], result["attente"])
        self.assertEqual(_extract_cotation(result["texte"]), RULE_BY_ID["respiratoire_bpco_sans_handicap_chronique"]["cotation"])

    def test_handicap_respiratoire_chronique_groupe_final(self):
        self.assert_final_with_known_cotation(
            "handicap respiratoire chronique groupe",
            RULE_BY_ID["respiratoire_handicap_chronique_groupe"]["cotation"],
        )

    def test_respiratoire_autre_pathologie_final(self):
        self.assert_final_with_known_cotation(
            "respiratoire obstructive",
            RULE_BY_ID["respiratoire_obstructive_restrictive_mixte"]["cotation"],
        )

    def test_neurologie_stable_un_membre_final(self):
        self.assert_final_with_known_cotation(
            "sep un membre",
            RULE_BY_ID["neurologie_affection_stable_un_membre"]["cotation"],
        )

    def test_avc_hemiplegie_final(self):
        self.assert_final_with_known_cotation(
            "patient avec une hémiplégie suite à un avc",
            RULE_BY_ID["neurologie_hemiplegie"]["cotation"],
        )

    def test_nevralgie_cervico_brachiale_final(self):
        self.assert_final_with_known_cotation(
            "névralgie cervico-brachiale",
            RULE_BY_ID["neurologie_atteintes_peripheriques_radiculaires_tronculaires_un_membre"]["cotation"],
        )

    def test_sciatique_demande_orientation(self):
        self.assert_short_question(
            "sciatique",
            "Question : neuro peripherique ou rachis ?",
        )
        self.assert_choices_present("sciatique")

    def test_lombalgie_demande_commune_ou_autre(self):
        self.assert_short_question(
            "lombalgie",
            "Question : lombalgie commune ou autre atteinte rachis ?",
        )

    def test_neurologique_demande_type(self):
        self.assert_short_question(
            "neurologique",
            "Question : quel type neurologique ?",
        )

    def test_retard_moteur_bebe_demande_type(self):
        self.assert_short_question(
            "retard moteur bébé",
            "Question : encéphalopathie infantile ou paralysie cérébrale / polyhandicap ?",
            max_len=90,
        )

    def test_seances_lca(self):
        self.assert_seances("lca genou opere", "40")

    def test_seances_pth(self):
        self.assert_seances("prothese totale de hanche", "15")

    def test_seances_cervicalgie_commune(self):
        self.assert_seances("cervicalgie commune", "15")

    def test_deviation_rachis_cervical_adulte_trauma_non_final(self):
        result = repondre("deviation rachis cervical adulte sans trauma")
        self.assertTrue(result["termine"])
        self.assertEqual(_extract_cotation(result["texte"]), "RAM 8.12")


class TestConformiteTableau2026(unittest.TestCase):
    """Cas corrigés lors de l'audit du 23/11/2026 (tableau NGAP 01-01-2026 métropole)."""

    def _cot(self, message, *suites):
        result = repondre(message)
        for suite in suites:
            result = repondre(suite, result["nouveau_contexte"], result["attente"])
        if not result["termine"] and result["attente"].startswith("type_"):
            result = repondre("autre", result["nouveau_contexte"], result["attente"])
        self.assertTrue(result["termine"], f"{message} {suites}: {result['texte']}")
        return _extract_cotation(result["texte"])

    def test_rotule_genou_pas_membre_sup(self):
        self.assertEqual(self._cot("fracture rotule opérée"), "VIC 8.10")
        self.assertEqual(self._cot("fracture de la rotule non opérée"), "VIM 8.11")
        self.assertEqual(self._cot("fracture de la rotule", "operee"), "VIC 8.10")

    def test_deviation_adulte_pas_dra(self):
        self.assertEqual(self._cot("scoliose adulte 45 ans", "lombaire"), "RAM 8.11")
        self.assertEqual(self._cot("scoliose dorsale 60 ans"), "RAM 8.10")
        self.assertEqual(self._cot("scoliose", "plusieurs segments", "non"), "RAM 8.13")
        self.assertEqual(self._cot("scoliose cervicale adulte trauma récent"), "RAM 8.08")

    def test_deviation_mineur_dra(self):
        self.assertEqual(self._cot("scoliose 14 ans", "lombaire"), "DRA 8.09")
        self.assertEqual(self._cot("scoliose dorsale adolescent"), "DRA 8.08")
        self.assertEqual(self._cot("scoliose", "plusieurs segments", "oui"), "DRA 8.10")
        self.assertEqual(self._cot("scoliose 15 ans cervical"), "DRA 8.11")

    def test_bpco_rehabilitation(self):
        self.assertEqual(self._cot("BPCO réhabilitation respiratoire individuelle"), "ARL 28.00")
        self.assertEqual(self._cot("BPCO réhabilitation respiratoire en groupe"), "ARL 20.00")
        self.assertEqual(self._cot("BPCO", "sans"), "ARL 8.50")

    def test_plusieurs_segments_meme_membre(self):
        self.assertEqual(self._cot("genou et cheville opérés"), "VIC 8.12")
        self.assertEqual(self._cot("hanche et genou opérés"), "VIC 8.12")
        self.assertEqual(self._cot("hanche et genou non opérés"), "VIM 8.12")
        self.assertEqual(self._cot("épaule et coude non opérés"), "VSM 8.11")
        self.assertEqual(self._cot("coude et poignet opérés"), "VSC 8.12")
        self.assertEqual(self._cot("épaule et coude", "non"), "VSM 8.11")

    def test_un_seul_segment_inchange(self):
        self.assertEqual(self._cot("coude avant-bras non opéré"), "VSM 8.09")
        self.assertEqual(self._cot("cheville non opérée"), "VIM 8.10")
        self.assertEqual(self._cot("prothèse totale de genou"), "RIC 8.12")

    def test_humerus_opere_vsc(self):
        self.assertEqual(self._cot("fracture humérus proximal opérée"), "VSC 8.10")
        self.assertEqual(self._cot("fracture de l'humérus non opérée"), "RSM 8.10")

    def test_hemiplegie_bras_jambe(self):
        self.assertEqual(self._cot("hémiplégie bras et jambe"), "NMI 9.00")

    def test_fracture_coude_avant_bras(self):
        self.assertEqual(self._cot("fracture du coude et de l'avant-bras opérée"), "RSC 8.12")
        self.assertEqual(self._cot("fracture du coude non opérée"), "RSM 8.12")

    def test_correcteur_ne_change_pas_les_vrais_mots(self):
        from analyse_message import normaliser_texte
        for mot, interdit in [("rotule", "epaule"), ("pouce", "coude"), ("paume", "epaule"),
                              ("orthese", "prothese"), ("chute", "coude"), ("moignon", "poignet")]:
            self.assertNotIn(interdit, normaliser_texte(mot), mot)


    def test_dictee_age_et_durees_ignores(self):
        self.assertEqual(self._cot("patiente de 72 ans opérée d'une prothèse de hanche il y a trois semaines"), "RIC 8.10")
        self.assertEqual(self._cot("PTH il y a 2 semaines"), "RIC 8.10")
        self.assertEqual(self._cot("PTG opérée il y a 2 mois"), "RIC 8.12")
        self.assertEqual(self._cot("monsieur a une lombalgie commune depuis deux mois"), "RAM 8.09")
        self.assertEqual(self._cot("moins de 18 ans scoliose dorsale"), "DRA 8.08")
        self.assertEqual(self._cot("scoliose dorsale 17 ans"), "DRA 8.08")
        self.assertEqual(self._cot("les deux genoux opérés"), "TER 9.81")

    def test_correcteur_ne_deforme_pas(self):
        from analyse_message import normaliser_texte
        self.assertNotIn("croise", normaliser_texte("il y a trois semaines"))
        self.assertNotIn("dorsal", normaliser_texte("radius distal"))
        self.assertIn("epaule", normaliser_texte("epaul"))
        self.assertIn("cheville", normaliser_texte("chevil"))

    def test_entorse_membre_superieur_pas_rim(self):
        self.assertEqual(self._cot("entorse du pouce non opérée"), "VSM 8.10")
        self.assertEqual(self._cot("entorse du pouce", "non"), "VSM 8.10")
        self.assertEqual(self._cot("entorse du coude", "oui"), "VSC 8.09")

    def test_questions_plutot_que_supposer(self):
        cas = {
            "LCA": ("lca_type", "non", "VIM 8.11"),
            "ligament croisé": ("lca_type", "opere", "RIC 8.08"),
            "ménisque": ("menisque_type", "meniscectomie", "RIC 8.09"),
            "BPCO": ("bpco_type", "groupe", "ARL 20.00"),
            "kiné respiratoire": ("respi_type", "aigu", "ARL 8.49"),
            "lymphoedème bras": ("lymph_type", "sein", None),
            "lymphoedème après cancer du sein": ("lymph_sein_phase", "intensive", "RAV 15.50"),
            "lymphoedème sein": ("lymph_sein_phase", "hors phase", "RAV 8.00"),
            "AVC": ("avc_type", "hemiplegie", "NMI 9.00"),
            "brûlure": ("brulure_etendue", "plusieurs", "RPB 9.00"),
            "entorse": ("entorse_localisation", "poignet", None),
            "entorse de la cheville non opérée": ("entorse_cheville_type", "externe", "RIM 8.10"),
        }
        for message, (attente, reponse, cotation) in cas.items():
            result = repondre(message)
            self.assertFalse(result["termine"], message)
            self.assertEqual(result["attente"], attente, message)
            result = repondre(reponse, result["nouveau_contexte"], result["attente"])
            if cotation:
                self.assertEqual(_extract_cotation(result["texte"]), cotation, message)
        self.assertEqual(self._cot("entorse cheville", "autre", "non"), "VIM 8.10")
        self.assertEqual(self._cot("tronc et bras", "avec"), "TER 9.81")
        self.assertEqual(self._cot("lcp genou non opéré"), "VIM 8.11")

    def test_alerte_revalorisation_2027(self):
        from datetime import date
        from formatage_reponse import alerte_revalorisation
        ram = RULE_BY_ID["rachis_lombalgie_commune"]
        self.assertEqual(alerte_revalorisation(ram, date(2026, 11, 23)), "")
        self.assertIn("RAM 8.39", alerte_revalorisation(ram, date(2027, 7, 1)))
        self.assertEqual(alerte_revalorisation(RULE_BY_ID["neurologie_hemiplegie"], date(2027, 7, 1)), "")

    def test_cotations_en_vigueur_23_11_2026(self):
        attendu = {
            "plusieurs_territoires_sans_chirurgie": "TER 9.79",
            "plusieurs_territoires_avec_chirurgie": "TER 9.81",
            "amputation_au_moins_deux_membres": "APM 9.80",
            "neurologie_atteintes_peripheriques_radiculaires_tronculaires_plusieurs_membres": "NMI 11.01",
            "neurologie_paraplegie_tetraplegie": "NMI 12.01",
            "neurologie_affection_stable_plusieurs": "NMI 11.00",
            "neurologie_myopathie": "NMI 11.99",
            "neurologie_encephalopathie_infantile": "NMI 12.00",
            "neurologie_hemiplegie": "NMI 9.00",
            "neurologie_affection_stable_un_membre": "NMI 8.51",
        }
        for rule_id, cotation in attendu.items():
            self.assertEqual(RULE_BY_ID[rule_id]["cotation"], cotation, rule_id)

    def test_entorse_cheville_formulations(self):
        for phrase in ["entorse externe cheville non opérée", "entorse externe de la cheville non opérée",
                       "c'est pour une entorse externe de la cheville droite non opérée"]:
            self.assertEqual(self._cot(phrase), "RIM 8.10", phrase)

    def test_fracture_poignet_radius_ou_carpe(self):
        self.assertEqual(self._cot("fracture du poignet non opérée", "radius distal"), "RSM 8.11")
        self.assertEqual(self._cot("fracture du poignet opérée", "os du poignet main"), "VSC 8.11")
        self.assertEqual(self._cot("fracture du radius distal opérée"), "RSC 8.10")
        self.assertEqual(self._cot("fracture de Pouteau-Colles non opérée"), "RSM 8.11")


if __name__ == "__main__":
    unittest.main()
