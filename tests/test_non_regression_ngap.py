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
    "APM 8.10", "APM 8.11", "APM 9.50",
    "ARL 7.99", "ARL 8.00", "ARL 8.01", "ARL 8.49", "ARL 8.50", "ARL 8.51", "ARL 10.00", "ARL 20.00", "ARL 28.00",
    "DRA 8.08", "DRA 8.09", "DRA 8.10", "DRA 8.11",
    "NMI 8.00", "NMI 8.50", "NMI 8.51", "NMI 9.00", "NMI 9.01", "NMI 10.00", "NMI 10.01", "NMI 10.99", "NMI 11.00", "NMI 11.01",
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
    "TER 9.49", "TER 9.51", "TER 16.00",
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
            "membre_sup_fracture_humerus_prox_operee": "RSC 8.10",
            "membre_sup_plusieurs_segments_non_operes": "VSM 8.11",
            "membre_sup_plusieurs_segments_operes": "VSC 8.12",
            "vasculaire_bandage_un_membre": "RAV 1.00",
            "sujet_age_deambulation": "RPE 8.50",
            "amputation_un_membre_superieur": "APM 8.11",
            "amputation_un_membre_inferieur": "APM 8.10",
            "rhumatismales_atteinte_localisee": "NMI 8.00",
            "neurologie_atteintes_peripheriques_radiculaires_tronculaires_un_membre": "NMI 8.50",
            "neurologie_hemiplegie": "NMI 9.00",
            "neurologie_affection_stable_plusieurs": "NMI 10.00",
            "neurologie_encephalopathie_infantile": "NMI 11.00",
            "neurologie_paralysie_cerebrale_polyhandicap": "TER 16.00",
            "respiratoire_bpco_sans_handicap_chronique": "ARL 8.50",
            "respiratoire_obstructive_restrictive_mixte": "ARL 8.50",
            "respiratoire_mucoviscidose": "ARL 10.00",
            "respiratoire_handicap_chronique_individuel": "ARL 28.00",
            "respiratoire_handicap_chronique_groupe": "ARL 20.00",
            "plusieurs_territoires_sans_chirurgie": "TER 9.49",
            "plusieurs_territoires_avec_chirurgie": "TER 9.51",
        }
        for rule_id, cotation in expected.items():
            self.assertEqual(RULE_BY_ID[rule_id]["cotation"], cotation, rule_id)

    def assert_final_with_known_cotation(self, message: str, expected_cotation: str):
        result = repondre(message)
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
            "lca genou",
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
            "suite a une rupture du croise anterieur",
            RULE_BY_ID["membre_inf_lca"]["cotation"],
        )

    def test_lcp_voice_mapping_final(self):
        self.assert_final_with_known_cotation(
            "lcp genou",
            RULE_BY_ID["membre_inf_lca"]["cotation"],
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
            RULE_BY_ID["membre_inf_meniscectomie"]["cotation"],
        )

    def test_menisque_interne_voice_mapping_final(self):
        self.assert_final_with_known_cotation(
            "menisque interne opere",
            RULE_BY_ID["membre_inf_meniscectomie"]["cotation"],
        )

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
        result = repondre("lca genou")
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
        self.assert_final_with_known_cotation(
            "BPCO",
            RULE_BY_ID["respiratoire_bpco_sans_handicap_chronique"]["cotation"],
        )

    def test_lymphoedeme_short_question(self):
        self.assert_short_question("lymphoedeme", "Question : Un ou deux membres + localisation ?")

    def test_douleur_cheville_demande_precision_complete(self):
        self.assert_short_question(
            "douleur de cheville",
            "Question : operee ? entorse ? referentiel ?",
        )
        self.assert_choices_present("douleur de cheville")

    def test_douleur_epaule_demande_precision_complete(self):
        self.assert_short_question(
            "douleur d epaule",
            "Question : operee ? coiffe ? fracture ? referentiel ?",
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
            "lymphoedeme apres cancer du sein un bras",
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
        self.assert_final_with_known_cotation("les deux genoux apres chirurgie", "TER 9.51")

    def test_bilateral_genoux_operes_final(self):
        self.assert_final_with_known_cotation("bilateral genoux operes", "TER 9.51")

    def test_deux_segments_meme_membre_apres_chirurgie_final(self):
        self.assert_final_with_known_cotation(
            "deux segments membre inferieur operes",
            RULE_BY_ID["membre_inf_plusieurs_segments_operes"]["cotation"],
        )

    def test_deux_membres_inferieurs_non_operes_final(self):
        self.assert_final_with_known_cotation("reeducation des deux membres inferieurs pas operee", "TER 9.49")

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
        self.assert_final_with_known_cotation("reeducation des deux membres superieurs non operes", "TER 9.49")

    def test_deux_membres_inf_puis_non_donne_ter_sans_chirurgie(self):
        r1 = repondre("Reeducation des genoux deux membres inferieurs")
        self.assertFalse(r1["termine"])
        r2 = repondre("non", r1["nouveau_contexte"], r1["attente"])
        self.assertTrue(r2["termine"])
        self.assertEqual(_extract_cotation(r2["texte"]), "TER 9.49")

    def test_deux_membres_inf_puis_oui_donne_ter_avec_chirurgie(self):
        r1 = repondre("Reeducation des genoux deux membres inferieurs")
        self.assertFalse(r1["termine"])
        r2 = repondre("oui", r1["nouveau_contexte"], r1["attente"])
        self.assertTrue(r2["termine"])
        self.assertEqual(_extract_cotation(r2["texte"]), "TER 9.51")

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
        self.assert_final_with_known_cotation(
            "membres sup et inf",
            RULE_BY_ID["plusieurs_territoires_sans_chirurgie"]["cotation"],
        )

    def test_deviation_rachis_cervical_demande_age(self):
        self.assert_final_with_known_cotation("deviation rachis cervical", "DRA 8.11")

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
        self.assert_final_with_known_cotation(
            "lymfoedeme bras",
            RULE_BY_ID["vasculaire_lymphoedeme_un_membre"]["cotation"],
        )

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
        self.assertEqual(_extract_cotation(r2["texte"]), "TER 9.49")

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
                {"label": "Autre", "value": "autre pathologie"},
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
        self.assert_final_with_known_cotation(
            "lordose",
            RULE_BY_ID["deviation_rachis_lombosacre"]["cotation"],
        )

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
            "entorse cheville opérée",
            RULE_BY_ID["membre_inf_entorse_cheville_operee"]["cotation"],
        )

    def test_lle_cheville_final(self):
        self.assert_final_with_known_cotation(
            "lle cheville non opérée",
            RULE_BY_ID["membre_inf_entorse_cheville_non_operee"]["cotation"],
        )

    def test_entorse_interne_cheville_final(self):
        self.assert_final_with_known_cotation(
            "entorse interne cheville",
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
        self.assert_final_with_known_cotation(
            "luxation coude non opérée",
            RULE_BY_ID["membre_sup_fracture_coude_adulte_non_operee"]["cotation"],
        )

    def test_luxation_coude_operee_final(self):
        self.assert_final_with_known_cotation(
            "luxation coude opérée",
            RULE_BY_ID["membre_sup_fracture_coude_adulte_operee"]["cotation"],
        )

    def test_coude_fracture_operee_final(self):
        self.assert_final_with_known_cotation(
            "coude fracture opérée",
            RULE_BY_ID["membre_sup_fracture_coude_adulte_operee"]["cotation"],
        )

    def test_pouteau_colles_demande_chirurgie(self):
        result = repondre("pouteau colles")
        self.assertFalse(result["termine"])
        self.assertEqual(result["texte"], "Question : operee ou non ?")
        self.assertEqual(result["attente"], "coude_chirurgie")
        self.assertLessEqual(len(result["texte"]), 60)

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
        self.assertEqual(result["texte"], "Question : operee ou non ?")
        self.assertEqual(result["attente"], "poignet_chirurgie")

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
        self.assert_final_with_known_cotation(
            "bpco",
            RULE_BY_ID["respiratoire_bpco_sans_handicap_chronique"]["cotation"],
        )

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
        self.assert_seances("lca genou", "40")

    def test_seances_pth(self):
        self.assert_seances("prothese totale de hanche", "15")

    def test_seances_cervicalgie_commune(self):
        self.assert_seances("cervicalgie commune", "15")

    def test_deviation_rachis_cervical_adulte_trauma_non_final(self):
        result = repondre("deviation rachis cervical")
        self.assertTrue(result["termine"])
        self.assertEqual(_extract_cotation(result["texte"]), "DRA 8.11")


if __name__ == "__main__":
    unittest.main()
