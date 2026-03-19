import unittest

from assistant_ngap import repondre
from ngap_database import NGAP_RULES


KNOWN_COTATIONS = {
    r["cotation"]
    for r in NGAP_RULES
    if isinstance(r.get("cotation"), str) and r["cotation"].strip()
}
RULE_BY_ID = {r["id"]: r for r in NGAP_RULES}


def _extract_cotation(texte: str):
    for line in texte.splitlines():
        if line.startswith("Cotation : "):
            return line.replace("Cotation : ", "", 1).strip()
    return None


def _extract_seances(texte: str):
    for line in texte.splitlines():
        if line.startswith("Nombre de séances max : "):
            return line.replace("Nombre de séances max : ", "", 1).strip()
    return None


class TestNGAPNonRegression(unittest.TestCase):
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
            "membre_sup_plusieurs_segments_non_operes": "VSM 8.11",
            "membre_sup_plusieurs_segments_operes": "VSC 8.12",
            "vasculaire_bandage_un_membre": "RAV 1",
            "sujet_age_deambulation": "RPE 8.5",
            "amputation_un_membre_superieur": "APM 8.11",
            "amputation_un_membre_inferieur": "APM 8.10",
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
        self.assert_final_with_known_cotation(
            "canal carpien",
            RULE_BY_ID["membre_sup_canal_carpien"]["cotation"],
        )

    def test_hemiplegie_final(self):
        self.assert_final_with_known_cotation(
            "hemiplegie",
            RULE_BY_ID["neurologie_hemiplegie"]["cotation"],
        )

    def test_bpco_short_question(self):
        self.assert_short_question("BPCO", "Question : Individuel ou groupe ?")

    def test_lymphoedeme_short_question(self):
        self.assert_short_question("lymphoedeme", "Question : Un membre ou deux ?")

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
        result = repondre("Reeducation des genoux deux membres inférieurs")
        self.assertFalse(result["termine"])
        self.assertEqual(
            result["texte"],
            "Question : S'agit-il de deux segments du même membre inférieur, ou d'un segment sur chaque membre inférieur ?",
        )

    def test_deux_genoux_apres_chirurgie_final(self):
        result = repondre("les deux genoux apres chirurgie")
        self.assertFalse(result["termine"])
        self.assertEqual(
            result["texte"],
            "Question : S'agit-il de deux segments du même membre inférieur, ou d'un segment sur chaque membre inférieur ?",
        )
        self.assertEqual(result["attente"], "membre_inf_repartition_precision")

    def test_bilateral_genoux_operes_final(self):
        result = repondre("bilateral genoux operes")
        self.assertFalse(result["termine"])
        self.assertEqual(
            result["texte"],
            "Question : S'agit-il de deux segments du même membre inférieur, ou d'un segment sur chaque membre inférieur ?",
        )
        self.assertEqual(result["attente"], "membre_inf_repartition_precision")

    def test_deux_genoux_meme_membre_apres_chirurgie_final(self):
        result = repondre("les deux genoux apres chirurgie")
        result = repondre("meme membre", result["nouveau_contexte"], result["attente"])
        self.assertTrue(result["termine"])
        self.assertIn(RULE_BY_ID["membre_inf_plusieurs_segments_operes"]["cotation"], result["texte"])

    def test_deux_membres_inferieurs_non_operes_ne_donne_pas_reponse_fausse(self):
        result = repondre("reeducation des deux membres inferieurs pas operee")
        self.assertFalse(result["termine"])
        self.assertEqual(
            result["texte"],
            "Question : S'agit-il de deux segments du même membre inférieur, ou d'un segment sur chaque membre inférieur ?",
        )
        self.assertEqual(result["attente"], "membre_inf_repartition_precision")

    def test_genou_opere_demande_type_chirurgie(self):
        self.assert_short_question(
            "cotation pour un genou droit opéré",
            "Question : prothese / lca / meniscectomie / autre ?",
        )

    def test_plusieurs_territoires_demande_chirurgie(self):
        self.assert_short_question(
            "rééducation des deux membres inférieurs et du rachis dorsaux lombaire",
            "Question : Chirurgie sur un des territoires ?",
        )

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
        self.assert_short_question(
            "deviation rachis cervical",
            "Question : moins de 18 ans ?",
        )

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

    def test_cervicalgie_commune_final(self):
        self.assert_final_with_known_cotation(
            "cervicalgie commune",
            RULE_BY_ID["rachis_cervicalgie_commune"]["cotation"],
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

    def test_coiffe_operee_final(self):
        self.assert_final_with_known_cotation(
            "chirurgie coiffe",
            RULE_BY_ID["membre_sup_coiffe_operee"]["cotation"],
        )

    def test_tunnel_carpien_final(self):
        self.assert_final_with_known_cotation(
            "tunnel carpien",
            RULE_BY_ID["membre_sup_canal_carpien"]["cotation"],
        )

    def test_syndrome_tunnel_carpien_final(self):
        self.assert_final_with_known_cotation(
            "syndrome du tunnel carpien",
            RULE_BY_ID["membre_sup_canal_carpien"]["cotation"],
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

    def test_bpco_groupe_final(self):
        self.assert_final_with_known_cotation(
            "bpco groupe",
            RULE_BY_ID["respiratoire_handicap_chronique_groupe"]["cotation"],
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

    def test_seances_referentiel_missing_from_source(self):
        self.assert_seances("cervicalgie commune", "15")

    def test_deviation_rachis_cervical_adulte_trauma_non_final(self):
        result = repondre("deviation rachis cervical")
        self.assertFalse(result["termine"])
        self.assertEqual(result["attente"], "rachis_cervical_deviation_age")

        result = repondre("non", result["nouveau_contexte"], result["attente"])
        self.assertFalse(result["termine"])
        self.assertEqual(result["attente"], "rachis_cervical_deviation_trauma")

        result = repondre("non", result["nouveau_contexte"], result["attente"])
        self.assertTrue(result["termine"])
        self.assertEqual(_extract_cotation(result["texte"]), RULE_BY_ID["rachis_cervical_non_opere"]["cotation"])


if __name__ == "__main__":
    unittest.main()
