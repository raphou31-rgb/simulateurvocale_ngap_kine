"""Matrice de conformité au tableau NGAP (source de vérité : tableau-ngap-01-01-2026-metropole.pdf,
+ revalorisations listées dans VERSION.md).

1. Chaque ligne du tableau existe dans la base avec la bonne cotation.
2. Chaque ligne est testée avec des phrases réelles : la réponse finale doit être la bonne
   cotation ; une question de précision est tolérée, une MAUVAISE cotation ne l'est jamais.
"""
import re
import unittest

from assistant_ngap import repondre
from ngap_database import NGAP_RULES

REFERENCE = {'membre_sup_poignet_main_non_opere': 'VSM 8.10',
    'membre_sup_poignet_main_opere': 'VSC 8.11',
    'membre_sup_canal_carpien': 'RSC 8.09',
    'membre_sup_fracture_avant_bras_distale_non_operee': 'RSM 8.11',
    'membre_sup_fracture_avant_bras_distale_operee': 'RSC 8.10',
    'membre_sup_coude_avant_bras_non_opere': 'VSM 8.09',
    'membre_sup_fracture_coude_adulte_non_operee': 'RSM 8.12',
    'membre_sup_coude_avant_bras_opere': 'VSC 8.09',
    'membre_sup_fracture_coude_adulte_operee': 'RSC 8.12',
    'membre_sup_coiffe_non_operee': 'RSM 8.09',
    'membre_sup_coiffe_operee': 'RSC 8.11',
    'membre_sup_epaule_bras_non_opere': 'VSM 8.08',
    'membre_sup_fracture_humerus_prox_non_operee': 'RSM 8.10',
    'membre_sup_epaule_bras_opere': 'VSC 8.10',
    'membre_sup_fracture_humerus_prox_operee': 'VSC 8.10',
    'membre_sup_plusieurs_segments_non_operes': 'VSM 8.11',
    'membre_sup_plusieurs_segments_operes': 'VSC 8.12',
    'amputation_un_membre_superieur': 'APM 8.11',
    'amputation_un_membre_inferieur': 'APM 8.10',
    'amputation_au_moins_deux_membres': 'APM 9.80',
    'membre_inf_cheville_pied_non_opere': 'VIM 8.10',
    'membre_inf_entorse_cheville_non_operee': 'RIM 8.10',
    'membre_inf_cheville_pied_opere': 'VIC 8.11',
    'membre_inf_entorse_cheville_operee': 'RIC 8.11',
    'membre_inf_genou_jambe_non_opere': 'VIM 8.11',
    'membre_inf_ptg': 'RIC 8.12',
    'membre_inf_lca': 'RIC 8.08',
    'membre_inf_meniscectomie': 'RIC 8.09',
    'membre_inf_genou_jambe_opere': 'VIC 8.10',
    'membre_inf_hanche_cuisse_non_operee': 'VIM 8.09',
    'membre_inf_pth': 'RIC 8.10',
    'membre_inf_hanche_cuisse_operee': 'VIC 8.09',
    'membre_inf_plusieurs_segments_non_operes': 'VIM 8.12',
    'membre_inf_plusieurs_segments_operes': 'VIC 8.12',
    'plusieurs_territoires_sans_chirurgie': 'TER 9.79',
    'plusieurs_territoires_avec_chirurgie': 'TER 9.81',
    'rachis_cervical_non_opere': 'RAM 8.12',
    'rachis_trauma_cervical_recent': 'RAM 8.08',
    'rachis_cervicalgie_commune': 'RAM 8.07',
    'rachis_cervical_opere': 'RAO 8.10',
    'deviation_rachis_cervical': 'DRA 8.11',
    'rachis_dorsal_non_opere': 'RAM 8.10',
    'rachis_dorsal_opere': 'RAO 8.08',
    'deviation_rachis_dorsal': 'DRA 8.08',
    'rachis_lombosacre_non_opere': 'RAM 8.11',
    'rachis_lombalgie_commune': 'RAM 8.09',
    'rachis_lombosacre_opere': 'RAO 8.09',
    'deviation_rachis_lombosacre': 'DRA 8.09',
    'rachis_plusieurs_segments': 'RAM 8.13',
    'rachis_plusieurs_segments_opere': 'RAO 8.11',
    'deviation_rachis_plusieurs_segments': 'DRA 8.10',
    'rhumatismales_atteinte_localisee': 'NMI 8.00',
    'rhumatismales_atteinte_plusieurs_membres': 'NMI 9.01',
    'abdominal_preop_postop': 'RAB 8.01',
    'abdominal_post_partum': 'RAB 8.00',
    'neurologie_atteintes_peripheriques_radiculaires_tronculaires_un_membre': 'NMI 8.50',
    'neurologie_atteintes_peripheriques_radiculaires_tronculaires_plusieurs_membres': 'NMI 11.01',
    'neurologie_hemiplegie': 'NMI 9.00',
    'neurologie_paraplegie_tetraplegie': 'NMI 12.01',
    'neurologie_myopathie': 'NMI 11.99',
    'neurologie_affection_stable_un_membre': 'NMI 8.51',
    'neurologie_affection_stable_plusieurs': 'NMI 11.00',
    'neurologie_encephalopathie_infantile': 'NMI 12.00',
    'neurologie_paralysie_cerebrale_polyhandicap': 'TER 16.00',
    'respiratoire_desencombrement_urgent': 'ARL 8.49',
    'respiratoire_preop_postop': 'ARL 8.51',
    'respiratoire_mucoviscidose': 'ARL 10.00',
    'respiratoire_bpco_sans_handicap_chronique': 'ARL 8.50',
    'respiratoire_handicap_chronique_individuel': 'ARL 28.00',
    'respiratoire_handicap_chronique_groupe': 'ARL 20.00',
    'respiratoire_obstructive_restrictive_mixte': 'ARL 8.50',
    'maxillo_facial_hors_paralysie_faciale': 'ARL 7.99',
    'vestibulaire_troubles_equilibre': 'ARL 8.00',
    'orl_troubles_deglutition_isoles': 'ARL 8.01',
    'vasculaire_arteriopathie_membres_inferieurs': 'RAV 8.01',
    'vasculaire_insuffisance_veineuse': 'RAV 7.99',
    'vasculaire_bandage_un_membre': 'RAV 1.00',
    'vasculaire_lymphoedeme_un_membre': 'RAV 8.00',
    'vasculaire_lymphoedeme_sein': 'RAV 15.50',
    'vasculaire_lymphoedeme_deux_membres': 'RAV 9.00',
    'vasculaire_bandage_deux_membres': 'RAV 2.00',
    'perinee_active': 'RAB 8.50',
    'sujet_age_deambulation': 'RPE 8.50',
    'brulure_un_membre': 'RPB 8.00',
    'brulure_plusieurs_membres_tronc': 'RPB 9.00',
    'soins_palliatifs': 'PLL 12.00'}

# (phrase, [réponses aux questions], cotation attendue)
CAS = [
# --- Membre supérieur
("poignet non opéré",[],"VSM 8.10"),("douleur main non opérée",[],"VSM 8.10"),("tendinite du poignet",["non"],"VSM 8.10"),
("poignet opéré",[],"VSC 8.11"),("main opérée",[],"VSC 8.11"),("fracture du scaphoïde opérée",[],"VSC 8.11"),("doigt à ressaut opéré",[],"VSC 8.11"),
("canal carpien opéré",[],"RSC 8.09"),("canal carpien",["opere"],"RSC 8.09"),("libération du canal carpien",[],"RSC 8.09"),
("fracture du radius distal non opérée",[],"RSM 8.11"),("fracture pouteau colles plâtrée non opérée",[],"RSM 8.11"),("fracture du poignet non opérée",["radius distal"],"RSM 8.11"),
("fracture du radius distal opérée",[],"RSC 8.10"),("fracture extrémité distale avant-bras opérée",[],"RSC 8.10"),
("coude non opéré",[],"VSM 8.09"),("épicondylite",[],"VSM 8.09"),("avant-bras non opéré",[],"VSM 8.09"),
("fracture du coude non opérée",[],"RSM 8.12"),("fracture olécrane non opérée",[],"RSM 8.12"),
("coude opéré",[],"VSC 8.09"),("fracture du coude opérée",[],"RSC 8.12"),("fracture olécrane opérée",[],"RSC 8.12"),
("tendinopathie coiffe des rotateurs non opérée",[],"RSM 8.09"),("coiffe non opérée",[],"RSM 8.09"),
("rupture de coiffe opérée",[],"RSC 8.11"),("suture de la coiffe",[],"RSC 8.11"),("acromioplastie",[],"RSC 8.11"),
("épaule non opérée",[],"VSM 8.08"),("capsulite épaule non opérée",[],"VSM 8.08"),("épaule",["non"],"VSM 8.08"),
("fracture humérus non opérée",[],"RSM 8.10"),("fracture de l'épaule non opérée",[],"RSM 8.10"),
("épaule opérée",[],"VSC 8.10"),("prothèse d'épaule",[],"VSC 8.10"),("fracture humérus opérée",[],"VSC 8.10"),("luxation épaule opérée",[],"VSC 8.10"),
("épaule et coude non opérés",[],"VSM 8.11"),("épaule et poignet opérés",[],"VSC 8.12"),
("amputation membre supérieur",[],"APM 8.11"),("amputation de la main",[],"APM 8.11"),
# --- Membre inférieur
("amputation de jambe",[],"APM 8.10"),("amputation tibiale",[],"APM 8.10"),("amputation des deux jambes",[],"APM 9.80"),
("cheville non opérée",[],"VIM 8.10"),("fracture cheville non opérée",[],"VIM 8.10"),("tendinite d'Achille non opérée",[],"VIM 8.10"),
("entorse externe cheville non opérée",[],"RIM 8.10"),("entorse cheville",["externe","non"],"RIM 8.10"),("LLE cheville non opérée",[],"RIM 8.10"),
("cheville opérée",[],"VIC 8.11"),("fracture malléole opérée",[],"VIC 8.11"),("hallux valgus opéré",[],"VIC 8.11"),
("entorse externe cheville opérée",[],"RIC 8.11"),("ligamentoplastie de cheville",[],"RIC 8.11"),
("genou non opéré",[],"VIM 8.11"),("gonarthrose",["non"],"VIM 8.11"),("LCA",["non"],"VIM 8.11"),("ménisque non opéré",[],"VIM 8.11"),
("prothèse totale de genou",[],"RIC 8.12"),("PTG",[],"RIC 8.12"),("prothèse unicompartimentale du genou",[],"RIC 8.12"),
("ligamentoplastie du LCA",[],"RIC 8.08"),("LCA opéré",[],"RIC 8.08"),("reconstruction du croisé antérieur",[],"RIC 8.08"),
("méniscectomie",[],"RIC 8.09"),("ménisque",["meniscectomie"],"RIC 8.09"),
("genou opéré autre",[],"VIC 8.10"),("fracture rotule opérée",[],"VIC 8.10"),("ostéotomie tibiale",[],"VIC 8.10"),("suture méniscale",[],"VIC 8.10"),
("hanche non opérée",[],"VIM 8.09"),("coxarthrose",["non"],"VIM 8.09"),("cuisse non opérée",[],"VIM 8.09"),
("prothèse totale de hanche",[],"RIC 8.10"),("PTH",[],"RIC 8.10"),
("hanche opérée autre",[],"VIC 8.09"),("fracture du col du fémur opérée ostéosynthèse",[],"VIC 8.09"),
("genou et cheville non opérés",[],"VIM 8.12"),("hanche et genou opérés",[],"VIC 8.12"),
("les deux genoux non opérés",[],"TER 9.79"),("deux membres opérés",[],"TER 9.81"),("tronc et un membre",["avec"],"TER 9.81"),
# --- Rachis
("cervical non opéré",[],"RAM 8.12"),("rachis cervical non opéré",[],"RAM 8.12"),
("traumatisme cervical récent",[],"RAM 8.08"),("coup du lapin",[],"RAM 8.08"),
("cervicalgie commune",[],"RAM 8.07"),("cervicalgie non spécifique",[],"RAM 8.07"),
("rachis cervical opéré",[],"RAO 8.10"),("arthrodèse cervicale",[],"RAO 8.10"),
("scoliose cervicale 12 ans",[],"DRA 8.11"),
("dorsalgie",[],"RAM 8.10"),("rachis dorsal non opéré",[],"RAM 8.10"),("rachis dorsal opéré",[],"RAO 8.08"),("cyphose 15 ans",[],"DRA 8.08"),
("rachis lombo-sacré non opéré",[],"RAM 8.11"),("lombalgie commune",[],"RAM 8.09"),("lombalgie non spécifique",[],"RAM 8.09"),
("rachis lombaire opéré",[],"RAO 8.09"),("hernie discale lombaire opérée",[],"RAO 8.09"),("arthrodèse lombaire",[],"RAO 8.09"),
("scoliose lombaire 14 ans",[],"DRA 8.09"),("scoliose lombaire adulte",[],"RAM 8.11"),
("lombaire et cervical non opérés",[],"RAM 8.13"),("rachis plusieurs segments opéré",[],"RAO 8.11"),("scoliose thoraco-lombaire 13 ans",[],"DRA 8.10"),
# --- Rhumato, abdo, neuro
("polyarthrite rhumatoïde un membre",[],"NMI 8.00"),("spondylarthrite ankylosante tronc",[],"NMI 8.00"),("polyarthrite plusieurs membres",[],"NMI 9.01"),
("rééducation abdominale post-opératoire",[],"RAB 8.01"),("abdominal post-partum",[],"RAB 8.00"),
("paralysie faciale",[],"NMI 8.50"),("sciatique paralysante un membre",["neuro"],"NMI 8.50"),("neuropathie périphérique plusieurs membres",[],"NMI 11.01"),
("hémiplégie",[],"NMI 9.00"),("AVC",["hemiplegie"],"NMI 9.00"),("paraplégie",[],"NMI 12.01"),("tétraplégie",[],"NMI 12.01"),
("myopathie",[],"NMI 11.99"),("sclérose en plaques un membre",[],"NMI 8.51"),("parkinson plusieurs membres",[],"NMI 11.00"),
("encéphalopathie infantile",[],"NMI 12.00"),("paralysie cérébrale",[],"TER 16.00"),("polyhandicap",[],"TER 16.00"),
# --- Respi, ORL, vasculaire, autres
("bronchiolite",[],"ARL 8.49"),("désencombrement urgent",[],"ARL 8.49"),("kiné respiratoire pré-opératoire",[],"ARL 8.51"),
("mucoviscidose",[],"ARL 10.00"),("BPCO",["sans"],"ARL 8.50"),("BPCO réhabilitation individuelle",[],"ARL 28.00"),("BPCO réhabilitation en groupe",[],"ARL 20.00"),
("asthme",[],"ARL 8.50"),
("rééducation maxillo-faciale hors paralysie faciale",[],"ARL 7.99"),("rééducation vestibulaire",[],"ARL 8.00"),("troubles de la déglutition",[],"ARL 8.01"),
("artériopathie des membres inférieurs",[],"RAV 8.01"),("insuffisance veineuse",[],"RAV 7.99"),
("lymphoedème un membre",[],"RAV 8.00"),("lymphoedème après cancer du sein",["intensive"],"RAV 15.50"),("lymphoedème deux membres",[],"RAV 9.00"),
("bandage un membre",[],"RAV 1.00"),("bandage deux membres",[],"RAV 2.00"),
("rééducation périnéale",[],"RAB 8.50"),("incontinence urinaire rééducation périnéale active",[],"RAB 8.50"),
("déambulation du sujet âgé",[],"RPE 8.50"),("rééducation gériatrique chute",[],"RPE 8.50"),
("brûlure d'un membre",[],"RPB 8.00"),("brûlure main",[],"RPB 8.00"),("brûlures étendues tronc et bras",[],"RPB 9.00"),
("soins palliatifs",[],"PLL 12.00"),
]


class TestMatriceTableau(unittest.TestCase):
    def test_base_identique_au_tableau(self):
        base = {r["id"]: r["cotation"] for r in NGAP_RULES}
        self.assertEqual(set(base), set(REFERENCE))
        for rule_id, cotation in REFERENCE.items():
            self.assertEqual(base[rule_id], cotation, rule_id)

    def test_jamais_de_mauvaise_cotation(self):
        mauvaises, questions = [], []
        for phrase, suites, attendu in CAS:
            result = repondre(phrase)
            for suite in suites:
                result = repondre(suite, result["nouveau_contexte"], result["attente"])
            if not result["termine"] and result["attente"].startswith("type_"):
                result = repondre("autre", result["nouveau_contexte"], result["attente"])
            if not result["termine"]:
                questions.append(phrase)
                continue
            cotation = re.findall(r"\b[A-Z]{3} ?\d+\.\d+", result["texte"])
            if not cotation or cotation[0] != attendu:
                mauvaises.append((phrase, suites, attendu, cotation[:1]))
        self.assertEqual(mauvaises, [])
        # Au plus 10 cas sur ~150 se terminent par une question supplémentaire.
        self.assertLessEqual(len(questions), 3, questions)


if __name__ == "__main__":
    unittest.main()
