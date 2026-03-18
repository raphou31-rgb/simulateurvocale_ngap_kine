NGAP_RULES = [
    {
    "id": "rachis_lombalgie_commune",
    "acte": "Rééducation dans le cadre de la prise en charge d'une lombalgie commune",
    "famille": "rachis",
    "detail": "lombalgie commune",
    "cotation": "RAM 8.09",
    "seances_max": 15,
    "referentiel": "oui",
    "keywords_any": [
        "lombalgie",
        "lombalgie commune",
        "douleur lombaire commune",
        "rachis lombaire commune"
    ],
    "required_fields": []
},
{
    "id": "rachis_lombosacre_non_opere",
    "acte": "Rééducation du rachis lombo-sacré non opéré",
    "famille": "rachis",
    "detail": "rachis lombo-sacré",
    "cotation": "RAM 8.11",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "rachis lombo sacre",
        "rachis lombo-sacre",
        "lombo sacre",
        "lombo-sacre",
        "rachis lombaire non opere",
        "rachis lombaire non opéré",
        "rachis lombaire sans chirurgie"
    ],
    "required_fields": []
},
{
    "id": "rachis_lombosacre_opere",
    "acte": "Rééducation du rachis lombo-sacré opéré",
    "famille": "rachis",
    "detail": "rachis lombo-sacré opéré",
    "cotation": "RAO 8.09",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "rachis lombo sacre opere",
        "rachis lombo sacre opéré",
        "rachis lombo-sacre opere",
        "rachis lombo-sacre opéré",
        "rachis lombaire opere",
        "rachis lombaire opéré",
        "rachis lombaire chirurgie",
        "lombo sacre opere",
        "lombo sacre opéré"
    ],
    "required_fields": []
},
{
    "id": "rachis_dorsal_non_opere",
    "acte": "Rééducation du rachis dorsal non opéré",
    "famille": "rachis",
    "detail": "rachis dorsal",
    "cotation": "RAM 8.10",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "rachis dorsal",
        "rachis thoracique"
    ],
    "required_fields": []
},
{
    "id": "rachis_dorsal_opere",
    "acte": "Rééducation du rachis dorsal opéré",
    "famille": "rachis",
    "detail": "rachis dorsal opéré",
    "cotation": "RAO 8.08",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "rachis dorsal opere",
        "rachis dorsal opéré",
        "rachis thoracique opere",
        "rachis thoracique opéré",
        "rachis dorsal chirurgie"
    ],
    "required_fields": []
},
{
    "id": "rachis_cervical_non_opere",
    "acte": "Rééducation du rachis cervical non opéré",
    "famille": "rachis",
    "detail": "rachis cervical non opéré",
    "cotation": "RAM 8.12",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "rachis cervical non opere",
        "rachis cervical non opéré",
        "rachis cervical sans chirurgie",
        "rachis cervical",
        "cervical non opere",
        "cervical non opéré"
    ],
    "required_fields": []
},
{
    "id": "rachis_cervicalgie_commune",
    "acte": "Rééducation dans le cadre d'une cervicalgie commune sans atteinte neurologique",
    "famille": "rachis",
    "detail": "cervicalgie commune",
    "cotation": "RAM 8.07",
    "seances_max": 15,
    "referentiel": "oui",
    "keywords_any": [
        "cervicalgie",
        "cervicalgie commune",
    ],
    "required_fields": []
},
{
    "id": "rachis_cervical_opere",
    "acte": "Rééducation du rachis cervical opéré",
    "famille": "rachis",
    "detail": "rachis cervical opéré",
    "cotation": "RAO 8.10",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "rachis cervical opere",
        "rachis cervical opéré",
        "cervical opere",
        "cervical opéré",
        "chirurgie cervicale",
        "rachis cervical chirurgie"
    ],
    "required_fields": []
},
{
    "id": "rachis_trauma_cervical_recent",
    "acte": "Rééducation d'un traumatisme cervical récent sans neuropathie",
    "famille": "rachis",
    "detail": "trauma cervical récent",
    "cotation": "RAM 8.08",
    "seances_max": 10,
    "referentiel": "oui",
    "keywords_any": [
        "trauma cervical",
        "traumatisme cervical",
        "trauma cervical recent",
        "traumatisme cervical recent",
        "coup du lapin"
    ],
    "required_fields": []
},
{
    "id": "rachis_plusieurs_segments",
    "acte": "Rééducation portant sur au moins deux segments du rachis non opéré",
    "famille": "rachis",
    "detail": "plusieurs segments du rachis",
    "cotation": "RAM 8.13",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "plusieurs segments rachis",
        "deux segments rachis",
        "2 segments rachis",
        "plusieurs segments du rachis"
    ],
    "required_fields": []
},
{
    "id": "deviation_rachis_lombosacre",
    "acte": "Rééducation pour déviation du rachis lombo-sacré",
    "famille": "deviation rachis",
    "detail": "déviation du rachis lombo-sacré",
    "cotation": "DRA 8.09",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "deviation rachis lombaire",
        "deviation rachis lombo sacre",
        "déviation rachis lombaire",
        "déviation rachis lombo-sacré",
        "scoliose lombaire"
    ],
    "required_fields": []
},
{
    "id": "deviation_rachis_dorsal",
    "acte": "Rééducation pour déviation du rachis dorsal",
    "famille": "deviation rachis",
    "detail": "déviation du rachis dorsal",
    "cotation": "DRA 8.08",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "deviation rachis dorsal",
        "déviation rachis dorsal",
        "scoliose dorsale"
    ],
    "required_fields": []
},
{
    "id": "deviation_rachis_cervical",
    "acte": "Rééducation pour déviation du rachis cervical chez le patient de moins de 18 ans",
    "famille": "deviation rachis",
    "detail": "déviation du rachis cervical, moins de 18 ans",
    "cotation": "DRA 8.11",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "deviation rachis cervical moins de 18 ans",
        "deviation rachis cervical enfant",
        "deviation rachis cervical adolescent",
        "deviation rachis cervical mineur",
        "déviation rachis cervical moins de 18 ans",
        "déviation rachis cervical enfant",
        "déviation rachis cervical adolescent",
        "scoliose cervicale enfant",
        "scoliose cervicale adolescent"
    ],
    "required_fields": []
},
{
    "id": "deviation_rachis_plusieurs_segments",
    "acte": "Rééducation pour déviation portant sur au moins deux segments du rachis",
    "famille": "deviation rachis",
    "detail": "déviation sur plusieurs segments du rachis",
    "cotation": "DRA 8.10",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "deviation plusieurs segments rachis",
        "déviation plusieurs segments rachis",
        "deviation du rachis plusieurs segments",
        "scoliose plusieurs segments",
        "scoliose thoraco lombaire",
        "scoliose thoraco-lombaire"
    ],
    "required_fields": []
},
    {
        "id": "membre_inf_lca",
        "acte": "Rééducation après reconstruction du ligament croisé antérieur du genou",
        "famille": "membre inferieur",
        "detail": "ligament croisé antérieur du genou",
        "cotation": "RIC 8.08",
        "seances_max": 40,
        "referentiel": "oui",
        "keywords_any": [
            "ligament croisé antérieur",
            "ligament croise anterieur",
            "ligament croisé du genou",
            "ligament croise du genou",
            "croisé du genou",
            "croise du genou",
            "lca",
            "reconstruction lca",
            "plastie lca",
            "ligamentoplastie",
            "ligamentoplastie genou",
            "genou opéré lca",
            "genou opere lca",
            "patient opéré du ligament croisé",
            "patient opere du ligament croise"
        ],
        "required_fields": []
    },
    {
        "id": "membre_inf_ptg",
        "acte": "Rééducation après arthroplastie du genou par prothèse totale ou uni-compartimentaire",
        "famille": "membre inferieur",
        "detail": "arthroplastie du genou",
        "cotation": "RIC 8.12",
        "seances_max": 25,
        "referentiel": "oui",
        "keywords_any": [
            "prothese totale de genou",
            "prothèse totale de genou",
            "ptg",
            "arthroplastie genou",
            "prothese genou",
            "prothèse genou",
            "prothese totale",
            "prothèse totale"
        ],
        "required_fields": []
    },
    {
        "id": "membre_inf_meniscectomie",
        "acte": "Rééducation après méniscectomie isolée, totale ou subtotale, par arthroscopie",
        "famille": "membre inferieur",
        "detail": "méniscectomie",
        "cotation": "RIC 8.09",
        "seances_max": 15,
        "referentiel": "oui",
        "keywords_any": [
            "méniscectomie",
            "meniscectomie",
            "arthroscopie menisque",
            "arthroscopie ménisque",
            "menisque opéré",
            "ménisque opéré"
        ],
        "required_fields": []
    },
{
    "id": "membre_inf_entorse_cheville_non_operee",
    "acte": "Rééducation des conséquences d'une entorse externe récente de cheville-pied non opérée",
    "famille": "membre inferieur",
    "detail": "entorse externe récente cheville-pied non opérée",
    "cotation": "RIM 8.10",
    "seances_max": 10,
    "referentiel": "oui",
    "keywords_any": [
        "entorse cheville",
        "entorse de cheville",
        "entorse externe cheville",
        "entorse cheville pied",
        "cheville entorse",
        "entorse",
        "entorse recente",
        "entorse récente"
    ],
    "required_fields": []
},
{
    "id": "membre_inf_entorse_cheville_operee",
    "acte": "Rééducation des conséquences d'une entorse externe récente de cheville-pied opérée",
    "famille": "membre inferieur",
    "detail": "entorse externe récente cheville-pied opérée",
    "cotation": "RIC 8.11",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "entorse cheville operee",
        "entorse cheville opérée",
        "entorse externe cheville operee",
        "entorse externe cheville opérée",
        "entorse cheville chirurgie",
        "entorse pied operee",
        "entorse pied opérée"
    ],
    "required_fields": []
},
{
    "id": "membre_inf_cheville_pied_non_opere",
    "acte": "Rééducation des conséquences d'une affection de la cheville ou du pied non opérée",
    "famille": "membre inferieur",
    "detail": "cheville-pied non opérée",
    "cotation": "VIM 8.10",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "cheville non opere",
        "cheville non operee",
        "cheville non opérée",
        "pied non opere",
        "pied non operee",
        "pied non opérée",
        "cheville pied non opere",
        "cheville pied non opérée",
        "affection cheville non operee",
        "affection pied non operee",
        "fracture cheville non operee",
        "fracture cheville non opérée",
        "fracture pied non operee",
        "fracture pied non opérée"
    ],
    "required_fields": []
},
{
    "id": "membre_inf_cheville_pied_opere",
    "acte": "Rééducation des conséquences d'une affection de la cheville ou du pied opérée",
    "famille": "membre inferieur",
    "detail": "cheville-pied opérée",
    "cotation": "VIC 8.11",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "cheville operee",
        "cheville opérée",
        "cheville opere",
        "pied opere",
        "pied operee",
        "pied opérée",
        "cheville pied operee",
        "cheville pied opérée",
        "affection cheville operee",
        "affection pied operee",
        "fracture cheville operee",
        "fracture cheville opérée",
        "fracture pied operee",
        "fracture pied opérée"
    ],
    "required_fields": []
},{
    "id": "membre_inf_genou_jambe_non_opere",
    "acte": "Rééducation des conséquences d'une affection du genou ou de la jambe non opérée",
    "famille": "membre inferieur",
    "detail": "genou ou jambe non opérée",
    "cotation": "VIM 8.11",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "genou non opere",
        "genou non opéré",
        "jambe non operee",
        "jambe non opérée",
        "affection genou non operee",
        "affection genou non opérée"
    ],
    "required_fields": []
},
{
    "id": "membre_inf_genou_jambe_opere",
    "acte": "Rééducation des conséquences d'une affection du genou ou de la jambe opérée hors référentiel",
    "famille": "membre inferieur",
    "detail": "genou ou jambe opérée",
    "cotation": "VIC 8.10",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "genou opere",
        "genou opéré",
        "jambe operee",
        "jambe opérée",
        "affection genou operee",
        "affection genou opérée"
    ],
    "required_fields": []
},
{
    "id": "membre_inf_hanche_cuisse_non_operee",
    "acte": "Rééducation des conséquences d'une affection de la hanche ou de la cuisse non opérée",
    "famille": "membre inferieur",
    "detail": "hanche ou cuisse non opérée",
    "cotation": "VIM 8.09",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "hanche non operee",
        "hanche non opérée",
        "cuisse non operee",
        "cuisse non opérée",
        "affection hanche non operee",
        "affection hanche non opérée"
    ],
    "required_fields": []
},
{
    "id": "membre_inf_hanche_cuisse_operee",
    "acte": "Rééducation des conséquences d'une affection de la hanche ou de la cuisse opérée hors référentiel",
    "famille": "membre inferieur",
    "detail": "hanche ou cuisse opérée",
    "cotation": "VIC 8.09",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "hanche operee",
        "hanche opérée",
        "cuisse operee",
        "cuisse opérée",
        "affection hanche operee",
        "affection hanche opérée"
    ],
    "required_fields": []
},
{
    "id": "membre_inf_pth",
    "acte": "Rééducation après arthroplastie de la hanche",
    "famille": "membre inferieur",
    "detail": "arthroplastie de hanche",
    "cotation": "RIC 8.10",
    "seances_max": 15,
    "referentiel": "oui",
    "keywords_any": [
        "prothese de hanche",
        "prothèse de hanche",
        "prothese totale de hanche",
        "prothèse totale de hanche",
        "arthroplastie hanche",
        "arthroplastie de hanche",
        "prothese hanche",
        "prothèse hanche",
        "prothese hanche chirurgie",
        "prothèse hanche chirurgie"
    ],
    "required_fields": []
},
{
    "id": "membre_inf_plusieurs_segments_non_operes",
    "acte": "Rééducation secondaire à l'affection d'au moins deux segments du même membre inférieur non opérés",
    "famille": "membre inferieur",
    "detail": "plusieurs segments du membre inférieur non opérés",
    "cotation": "VIM 8.12",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "deux segments membre inferieur",
        "2 segments membre inferieur",
        "plusieurs segments membre inferieur",
        "deux membres inferieurs non operes",
        "deux membres inferieurs non opérés"
    ],
    "required_fields": []
},
{
    "id": "membre_inf_plusieurs_segments_operes",
    "acte": "Rééducation secondaire à l'affection d'au moins deux segments du même membre inférieur avec chirurgie sur au moins un segment",
    "famille": "membre inferieur",
    "detail": "plusieurs segments du membre inférieur avec chirurgie",
    "cotation": "VIC 8.12",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "deux segments membre inferieur operes",
        "2 segments membre inferieur operes",
        "plusieurs segments membre inferieur operes",
        "deux membres inferieurs operes",
        "deux membres inferieurs opérés"
    ],
    "required_fields": []
},
    {
        "id": "membre_sup_canal_carpien",
        "acte": "Rééducation après libération du nerf médian au canal carpien",
        "famille": "membre superieur",
        "detail": "canal carpien",
        "cotation": "RSC 8.09",
        "seances_max": 0,
        "referentiel": "oui",
        "keywords_any": [
            "canal carpien",
            "tunnel carpien",
            "syndrome du tunnel carpien",
            "liberation canal carpien",
            "libération canal carpien",
            "nerf médian",
            "nerf median"
        ],
        "required_fields": []
    },
    {
        "id": "membre_sup_coiffe_non_operee",
        "acte": "Rééducation dans le cadre d'une tendinopathie de la coiffe des rotateurs non opérée",
        "famille": "membre superieur",
        "detail": "tendinopathie coiffe des rotateurs non opérée",
        "cotation": "RSM 8.09",
        "seances_max": 25,
        "referentiel": "oui",
        "keywords_any": [
            "coiffe des rotateurs",
            "tendinopathie coiffe",
            "tendinopathie de l epaule",
            "tendinopathie epaule",
            "epaule tendinopathie",
            "epaule tendinopathie non operee",
            "coiffe non opérée",
            "coiffe non operee",
            "épaule tendinopathie"
        ],
        "required_fields": []
    },{
    "id": "membre_sup_epaule_bras_non_opere",
    "acte": "Rééducation des conséquences d'une affection de l'épaule ou du bras non opérée",
    "famille": "membre superieur",
    "detail": "épaule ou bras non opérée",
    "cotation": "VSM 8.08",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "epaule non operee",
        "épaule non opérée",
        "bras non opere",
        "bras non opéré",
        "affection epaule non operee",
        "affection épaule non opérée"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_epaule_bras_opere",
    "acte": "Rééducation des conséquences d'une affection de l'épaule ou du bras opérée",
    "famille": "membre superieur",
    "detail": "épaule ou bras opérée",
    "cotation": "VSC 8.10",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "epaule operee",
        "épaule opérée",
        "bras opere",
        "bras opéré",
        "affection epaule operee",
        "affection épaule opérée"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_coiffe_operee",
    "acte": "Rééducation après chirurgie de la coiffe des rotateurs",
    "famille": "membre superieur",
    "detail": "coiffe des rotateurs opérée",
    "cotation": "RSC 8.11",
    "seances_max": 50,
    "referentiel": "oui",
    "keywords_any": [
        "coiffe operee",
        "coiffe opérée",
        "coiffe chirurgie",
        "chirurgie coiffe",
        "coiffe post op",
        "coiffe post-op",
        "suture de coiffe",
        "reparation des tendons de l epaule",
        "réparation des tendons de l épaule",
        "acromioplastie"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_coude_avant_bras_non_opere",
    "acte": "Rééducation des conséquences d'une affection du coude ou de l'avant-bras non opérée",
    "famille": "membre superieur",
    "detail": "coude ou avant-bras non opéré",
    "cotation": "VSM 8.09",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "coude non opere",
        "coude non opéré",
        "avant bras non opere",
        "avant-bras non opéré"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_fracture_avant_bras_distale_non_operee",
    "acte": "Rééducation après fracture non opérée de l'extrémité distale des deux os de l'avant-bras",
    "famille": "membre superieur",
    "detail": "fracture distale de l'avant-bras non opérée",
    "cotation": "RSM 8.11",
    "seances_max": 25,
    "referentiel": "oui",
    "keywords_any": [
        "fracture avant bras non operee",
        "fracture avant-bras non operee",
        "fracture avant bras non opérée",
        "fracture avant-bras non opérée",
        "fracture distale avant bras non operee",
        "fracture distale avant-bras non opérée",
        "fracture des deux os de l avant bras non operee",
        "fracture distale des deux os de l avant bras"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_coude_avant_bras_opere",
    "acte": "Rééducation des conséquences d'une affection du coude ou de l'avant-bras opérée",
    "famille": "membre superieur",
    "detail": "coude ou avant-bras opéré",
    "cotation": "VSC 8.09",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "coude opere",
        "coude opéré",
        "avant bras opere",
        "avant-bras opéré"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_fracture_avant_bras_distale_operee",
    "acte": "Rééducation après fracture opérée de l'extrémité distale des deux os de l'avant-bras",
    "famille": "membre superieur",
    "detail": "fracture distale de l'avant-bras opérée",
    "cotation": "RSC 8.10",
    "seances_max": 25,
    "referentiel": "oui",
    "keywords_any": [
        "fracture avant bras operee",
        "fracture avant-bras operee",
        "fracture avant bras opérée",
        "fracture avant-bras opérée",
        "fracture distale avant bras operee",
        "fracture distale avant-bras opérée",
        "fracture des deux os de l avant bras operee"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_fracture_coude_adulte_non_operee",
    "acte": "Rééducation après fracture avec ou sans luxation du coude chez l'adulte non opérée",
    "famille": "membre superieur",
    "detail": "fracture du coude adulte non opérée",
    "cotation": "RSM 8.12",
    "seances_max": 30,
    "referentiel": "oui",
    "keywords_any": [
        "fracture coude non operee",
        "fracture coude non opérée",
        "coude fracture non operee",
        "coude fracture non opérée",
        "fracture du coude non operee",
        "fracture du coude non opérée",
        "luxation coude non operee",
        "luxation coude non opérée",
        "luxation du coude non operee",
        "luxation du coude non opérée",
        "fracture ou luxation du coude non operee",
        "fracture du coude adulte non operee"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_fracture_coude_adulte_operee",
    "acte": "Rééducation après fracture avec ou sans luxation du coude chez l'adulte opérée",
    "famille": "membre superieur",
    "detail": "fracture du coude adulte opérée",
    "cotation": "RSC 8.12",
    "seances_max": 30,
    "referentiel": "oui",
    "keywords_any": [
        "fracture coude operee",
        "fracture coude opérée",
        "coude fracture operee",
        "coude fracture opérée",
        "fracture du coude operee",
        "fracture du coude opérée",
        "luxation coude operee",
        "luxation coude opérée",
        "luxation du coude operee",
        "luxation du coude opérée",
        "fracture ou luxation du coude operee",
        "fracture du coude adulte operee"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_poignet_main_non_opere",
    "acte": "Rééducation des conséquences d'une affection du poignet ou de la main non opérée",
    "famille": "membre superieur",
    "detail": "poignet ou main non opérée",
    "cotation": "VSM 8.10",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "poignet non opere",
        "poignet non opéré",
        "main non operee",
        "main non opérée"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_poignet_main_opere",
    "acte": "Rééducation des conséquences d'une affection du poignet ou de la main opérée",
    "famille": "membre superieur",
    "detail": "poignet ou main opérée",
    "cotation": "VSC 8.11",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "poignet opere",
        "poignet opéré",
        "main operee",
        "main opérée"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_fracture_humerus_prox_non_operee",
    "acte": "Rééducation après fracture non opérée de l'extrémité proximale de l'humérus",
    "famille": "membre superieur",
    "detail": "fracture proximale de l'humérus non opérée",
    "cotation": "RSM 8.10",
    "seances_max": 30,
    "referentiel": "oui",
    "keywords_any": [
        "fracture humerus non operee",
        "fracture humerus non opérée",
        "fracture proximale humerus non operee",
        "fracture proximale humerus non opérée",
        "fracture humerus proximal non operee",
        "fracture humerus proximal non opérée",
        "fracture proximale de l humerus",
        "fracture de l extremite proximale de l humerus",
        "fracture extremite proximale humerus",
        "fracture epaule non operee humerus"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_plusieurs_segments_non_operes",
    "acte": "Rééducation secondaire à l'affection d'au moins deux segments du même membre supérieur non opérés",
    "famille": "membre superieur",
    "detail": "plusieurs segments du membre supérieur non opérés",
    "cotation": "VSM 8.11",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "deux segments membre superieur",
        "2 segments membre superieur",
        "plusieurs segments membre superieur",
        "deux membres superieurs non operes",
        "deux membres superieurs non opérés"
    ],
    "required_fields": []
},
{
    "id": "membre_sup_plusieurs_segments_operes",
    "acte": "Rééducation secondaire à l'affection d'au moins deux segments du même membre supérieur avec chirurgie sur au moins un segment",
    "famille": "membre superieur",
    "detail": "plusieurs segments du membre supérieur avec chirurgie",
    "cotation": "VSC 8.12",
    "seances_max": None,
    "referentiel": "non",
    "keywords_any": [
        "deux segments membre superieur operes",
        "2 segments membre superieur operes",
        "plusieurs segments membre superieur operes",
        "deux membres superieurs operes",
        "deux membres superieurs opérés"
    ],
    "required_fields": []
},
    {
        "id": "respiratoire_desencombrement_urgent",
        "acte": "Rééducation des maladies respiratoires avec désencombrement urgent",
        "famille": "respiratoire",
        "detail": "désencombrement urgent",
        "cotation": "ARL 8.49",
        "seances_max": None,
        "referentiel": "non",
        "keywords": [
            "desencombrement urgent",
            "désencombrement urgent",
            "bronchiolite",
            "encombrement respiratoire aigu"
        ],
        "keywords_any": [
            "bronchiolite",
            "désencombrement urgent",
            "desencombrement urgent",
            "encombrement respiratoire aigu",
            "poussée aiguë respiratoire",
            "poussee aigue respiratoire"
        ],
        "required_fields": []
    },
    {
        "id": "respiratoire_obstructive_restrictive_mixte",
        "acte": "Rééducation des maladies respiratoires obstructives, restrictives ou mixtes",
        "famille": "respiratoire",
        "detail": "maladies respiratoires obstructives, restrictives ou mixtes",
        "cotation": "ARL 8.5",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "respiratoire obstructive",
            "respiratoire restrictive",
            "respiratoire mixte",
            "insuffisance respiratoire"
        ],
        "keywords_any": [
            "respiratoire obstructive",
            "respiratoire restrictive",
            "respiratoire mixte",
            "insuffisance respiratoire"
        ],
        "required_fields": []
    },
    {
        "id": "respiratoire_preop_postop",
        "acte": "Rééducation respiratoire préopératoire ou post-opératoire",
        "famille": "respiratoire",
        "detail": "rééducation préopératoire ou post-opératoire",
        "cotation": "ARL 8.51",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "respiratoire preoperatoire",
            "respiratoire préopératoire",
            "respiratoire post operatoire",
            "respiratoire post-opératoire"
        ],
        "keywords_any": [
            "respiratoire preoperatoire",
            "respiratoire préopératoire",
            "respiratoire post operatoire",
            "respiratoire post-opératoire"
        ],
        "required_fields": []
    },
    {
        "id": "respiratoire_mucoviscidose",
        "acte": "Rééducation respiratoire dans le cadre de la mucoviscidose",
        "famille": "respiratoire",
        "detail": "mucoviscidose",
        "cotation": "ARL 10",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "mucoviscidose",
            "mukoviscidose"
        ],
        "keywords_any": [
            "mucoviscidose",
            "mukoviscidose"
        ],
        "required_fields": []
    },
    {
        "id": "respiratoire_handicap_chronique_individuel",
        "acte": "Rééducation du handicap respiratoire chronique en individuel",
        "famille": "respiratoire",
        "detail": "handicap respiratoire chronique individuel",
        "cotation": "ARL 28",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "handicap respiratoire chronique individuel",
            "respiratoire chronique individuel",
            "bpco individuel",
            "individuel"
        ],
        "keywords_any": [
            "handicap respiratoire chronique individuel",
            "respiratoire chronique individuel",
            "bpco individuel",
            "individuel"
        ],
        "required_fields": []
    },
    {
        "id": "respiratoire_handicap_chronique_groupe",
        "acte": "Rééducation du handicap respiratoire chronique en groupe",
        "famille": "respiratoire",
        "detail": "handicap respiratoire chronique groupe",
        "cotation": "ARL 20",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "handicap respiratoire chronique groupe",
            "respiratoire chronique groupe",
            "bpco groupe",
            "groupe"
        ],
        "keywords_any": [
            "handicap respiratoire chronique groupe",
            "respiratoire chronique groupe",
            "bpco groupe",
            "groupe"
        ],
        "required_fields": []
    },
    {
        "id": "neurologie_hemiplegie",
        "acte": "Rééducation de l'hémiplégie",
        "famille": "neurologie",
        "detail": "hémiplégie",
        "cotation": "NMI 9",
        "seances_max": None,
        "referentiel": "non",
        "keywords": [
            "hemiplegie",
            "hémiplégie",
            "hemi"
        ],
        "keywords_any": [
            "hémiplégie",
            "hemiplegie",
            "hémi",
            "hemi"
        ],
        "required_fields": []
    },
    {
        "id": "neurologie_atteintes_peripheriques_radiculaires_tronculaires_un_membre",
        "acte": "Rééducation des atteintes périphériques radiculaires ou tronculaires localisées à un membre",
        "famille": "neurologie",
        "detail": "atteintes périphériques radiculaires ou tronculaires un membre",
        "cotation": "NMI 8.5",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "radiculaire un membre",
            "tronculaire un membre",
            "atteinte peripherique un membre"
        ],
        "keywords_any": [
            "radiculaire un membre",
            "tronculaire un membre",
            "atteinte peripherique un membre"
        ],
        "required_fields": []
    },
    {
        "id": "neurologie_atteintes_peripheriques_radiculaires_tronculaires_plusieurs_membres",
        "acte": "Rééducation des atteintes périphériques radiculaires ou tronculaires concernant plusieurs membres",
        "famille": "neurologie",
        "detail": "atteintes périphériques radiculaires ou tronculaires plusieurs membres",
        "cotation": "NMI 10.01",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "radiculaire plusieurs membres",
            "tronculaire plusieurs membres",
            "atteinte peripherique plusieurs membres"
        ],
        "keywords_any": [
            "radiculaire plusieurs membres",
            "tronculaire plusieurs membres",
            "atteinte peripherique plusieurs membres"
        ],
        "required_fields": []
    },
    {
        "id": "neurologie_paraplegie_tetraplegie",
        "acte": "Rééducation de la paraplégie et de la tétraplégie",
        "famille": "neurologie",
        "detail": "paraplégie et tétraplégie",
        "cotation": "NMI 11.01",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "paraplegie",
            "paraplégie",
            "tetraplegie",
            "tétraplégie"
        ],
        "keywords_any": [
            "paraplegie",
            "paraplégie",
            "tetraplegie",
            "tétraplégie"
        ],
        "required_fields": []
    },
    {
        "id": "neurologie_affection_stable_un_membre",
        "acte": "Rééducation d'une affection neurologique stable localisée à un membre",
        "famille": "neurologie",
        "detail": "affection neurologique stable un membre",
        "cotation": "NMI 8.51",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "neurologique stable un membre",
            "affection stable un membre"
        ],
        "keywords_any": [
            "neurologique stable un membre",
            "affection stable un membre"
        ],
        "required_fields": []
    },
    {
        "id": "neurologie_affection_stable_plusieurs",
        "acte": "Rééducation d'une affection neurologique stable concernant plusieurs membres",
        "famille": "neurologie",
        "detail": "affection neurologique stable plusieurs membres",
        "cotation": "NMI 10",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "neurologique stable plusieurs",
            "affection stable plusieurs membres"
        ],
        "keywords_any": [
            "neurologique stable plusieurs",
            "affection stable plusieurs membres"
        ],
        "required_fields": []
    },
    {
        "id": "neurologie_myopathie",
        "acte": "Rééducation de la myopathie",
        "famille": "neurologie",
        "detail": "myopathie",
        "cotation": "NMI 10.99",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "myopathie",
            "myopathies"
        ],
        "keywords_any": [
            "myopathie",
            "myopathies"
        ],
        "required_fields": []
    },
    {
        "id": "neurologie_encephalopathie_infantile",
        "acte": "Rééducation de l'encéphalopathie infantile",
        "famille": "neurologie",
        "detail": "encéphalopathie infantile",
        "cotation": "NMI 11",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "encephalopathie infantile",
            "encéphalopathie infantile"
        ],
        "keywords_any": [
            "encephalopathie infantile",
            "encéphalopathie infantile"
        ],
        "required_fields": []
    },
    {
        "id": "neurologie_paralysie_cerebrale_polyhandicap",
        "acte": "Rééducation des enfants présentant une paralysie cérébrale ou un polyhandicap",
        "famille": "neurologie",
        "detail": "rééducation des enfants présentant une paralysie cérébrale ou un polyhandicap",
        "cotation": "TER 16",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "paralysie cerebrale",
            "paralysie cérébrale",
            "polyhandicap",
            "enfant neurologique"
        ],
        "keywords_any": [
            "paralysie cerebrale",
            "paralysie cérébrale",
            "polyhandicap",
            "enfant neurologique"
        ],
        "required_fields": []
    },
    {
        "id": "maxillo_facial_hors_paralysie_faciale",
        "acte": "Rééducation maxillo-faciale en dehors de la paralysie faciale",
        "famille": "maxillo-facial / vestibulaire / ORL",
        "detail": "rééducation maxillo-faciale en dehors de la paralysie faciale",
        "cotation": "ARL 7.99",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "maxillo-facial",
            "maxillo facial",
            "temporo mandibulaire",
            "atm"
        ],
        "keywords_any": [
            "maxillo-facial",
            "maxillo facial",
            "temporo mandibulaire",
            "atm"
        ],
        "required_fields": []
    },
    {
        "id": "vestibulaire_troubles_equilibre",
        "acte": "Rééducation vestibulaire et des troubles de l'équilibre",
        "famille": "maxillo-facial / vestibulaire / ORL",
        "detail": "rééducation vestibulaire et des troubles de l'équilibre",
        "cotation": "ARL 8",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "vestibulaire",
            "troubles de l'equilibre",
            "troubles de l équilibre",
            "vertiges"
        ],
        "keywords_any": [
            "vestibulaire",
            "troubles de l'equilibre",
            "troubles de l équilibre",
            "vertiges"
        ],
        "required_fields": []
    },
    {
        "id": "orl_troubles_deglutition_isoles",
        "acte": "Rééducation des troubles de la déglutition isolés",
        "famille": "maxillo-facial / vestibulaire / ORL",
        "detail": "rééducation des troubles de la déglutition isolés",
        "cotation": "ARL 8.01",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "deglutition isolee",
            "déglutition isolée",
            "trouble de la deglutition",
            "trouble de la déglutition"
        ],
        "keywords_any": [
            "deglutition isolee",
            "déglutition isolée",
            "trouble de la deglutition",
            "trouble de la déglutition"
        ],
        "required_fields": []
    },
    {
        "id": "vasculaire_arteriopathie_membres_inferieurs",
        "acte": "Rééducation de l'artériopathie des membres inférieurs",
        "famille": "vasculaire",
        "detail": "artériopathie des membres inférieurs",
        "cotation": "RAV 8.01",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "arteriopathie membres inferieurs",
            "artériopathie membres inférieurs",
            "arteriopathie"
        ],
        "keywords_any": [
            "arteriopathie membres inferieurs",
            "artériopathie membres inférieurs",
            "arteriopathie"
        ],
        "required_fields": []
    },
    {
        "id": "vasculaire_insuffisance_veineuse",
        "acte": "Rééducation de l'insuffisance veineuse des membres inférieurs avec retentissement articulaire et/ou troubles trophiques",
        "famille": "vasculaire",
        "detail": "insuffisance veineuse des membres inférieurs avec retentissement articulaire et/ou troubles trophiques",
        "cotation": "RAV 7.99",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "insuffisance veineuse membres inferieurs",
            "insuffisance veineuse membres inférieurs",
            "troubles trophiques"
        ],
        "keywords_any": [
            "insuffisance veineuse membres inferieurs",
            "insuffisance veineuse membres inférieurs",
            "troubles trophiques"
        ],
        "required_fields": []
    },
    {
        "id": "vasculaire_lymphoedeme_un_membre",
        "acte": "Rééducation des lymphœdèmes vrais par drainage manuel, un membre",
        "famille": "vasculaire",
        "detail": "lymphœdèmes vrais par drainage manuel un membre",
        "cotation": "RAV 8",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "lymphoedeme vrai un membre",
            "lymphœdème vrai un membre",
            "drainage manuel un membre"
        ],
        "keywords_any": [
            "lymphoedeme vrai un membre",
            "lymphœdème vrai un membre",
            "drainage manuel un membre"
        ],
        "required_fields": []
    },
    {
        "id": "vasculaire_lymphoedeme_deux_membres",
        "acte": "Rééducation des lymphœdèmes vrais par drainage manuel, deux membres",
        "famille": "vasculaire",
        "detail": "lymphœdèmes vrais par drainage manuel deux membres",
        "cotation": "RAV 9",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "lymphoedeme vrai deux membres",
            "lymphœdème vrai deux membres",
            "drainage manuel deux membres"
        ],
        "keywords_any": [
            "lymphoedeme vrai deux membres",
            "lymphœdème vrai deux membres",
            "drainage manuel deux membres"
        ],
        "required_fields": []
    },
    {
        "id": "vasculaire_lymphoedeme_sein",
        "acte": "Rééducation pour lymphœdème du membre supérieur après traitement d'un cancer du sein, associée à une rééducation de l'épaule homolatérale à la phase intensive du traitement du lymphœdème",
        "famille": "vasculaire",
        "detail": "lymphœdème membre supérieur post-cancer du sein",
        "cotation": "RAV 15.5",
        "seances_max": None,
        "referentiel": "non",
        "keywords": [
            "lymphoedeme membre superieur cancer du sein",
            "lymphœdème membre supérieur cancer du sein",
            "drainage lymphatique cancer du sein"
        ],
        "keywords_any": [
            "lymphoedeme membre supérieur cancer du sein",
            "lymphœdème membre supérieur cancer du sein",
            "drainage lymphatique cancer du sein",
            "lymphoedeme post cancer du sein",
            "lymphœdème post cancer du sein"
        ],
        "required_fields": []
    },
    {
        "id": "vasculaire_bandage_un_membre",
        "acte": "Supplément pour bandage multicouche, un membre",
        "famille": "vasculaire",
        "detail": "supplément pour bandage multicouche un membre",
        "cotation": "RAV 1",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "bandage multicouche un membre",
            "supplement bandage multicouche un membre"
        ],
        "keywords_any": [
            "bandage multicouche un membre",
            "supplement bandage multicouche un membre"
        ],
        "required_fields": []
    },
    {
        "id": "vasculaire_bandage_deux_membres",
        "acte": "Supplément pour bandage multicouche, deux membres",
        "famille": "vasculaire",
        "detail": "supplément pour bandage multicouche deux membres",
        "cotation": "RAV 2",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "bandage multicouche deux membres",
            "supplement bandage multicouche deux membres"
        ],
        "keywords_any": [
            "bandage multicouche deux membres",
            "supplement bandage multicouche deux membres"
        ],
        "required_fields": []
    },
    {
        "id": "abdominal_preop_postop",
        "acte": "Rééducation abdominale pré-opératoire ou post-opératoire",
        "famille": "abdominal",
        "detail": "rééducation abdominale pré-opératoire ou post-opératoire",
        "cotation": "RAB 8.01",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "abdominal preoperatoire",
            "abdominal préopératoire",
            "abdominal post operatoire",
            "abdominal post-opératoire"
        ],
        "keywords_any": [
            "abdominal preoperatoire",
            "abdominal préopératoire",
            "abdominal post operatoire",
            "abdominal post-opératoire"
        ],
        "required_fields": []
    },
    {
        "id": "abdominal_post_partum",
        "acte": "Rééducation abdominale du post-partum",
        "famille": "abdominal",
        "detail": "rééducation abdominale du post-partum",
        "cotation": "RAB 8",
        "seances_max": None,
        "referentiel": "non",
        "keywords": [
            "post partum",
            "post-partum",
            "reeducation abdominale post partum"
        ],
        "keywords_any": [
            "post partum",
            "post-partum",
            "rééducation abdominale post partum",
            "reeducation abdominale post partum"
        ],
        "required_fields": []
    },
    {
        "id": "perinee_active",
        "acte": "Rééducation périnéale active sous contrôle manuel et/ou électrostimulation et/ou biofeedback",
        "famille": "perinee",
        "detail": "rééducation périnéale active",
        "cotation": "RAB 8.5",
        "seances_max": None,
        "referentiel": "non",
        "keywords": [
            "perinee",
            "périnée",
            "reeducation perineale",
            "biofeedback perineal"
        ],
        "keywords_any": [
            "périnée",
            "perinee",
            "rééducation périnéale",
            "reeducation perineale",
            "biofeedback périnéal",
            "biofeedback perineal"
        ],
        "required_fields": []
    },
    {
        "id": "sujet_age_deambulation",
        "acte": "Rééducation analytique et globale, musculo-articulaire des deux membres inférieurs, de la posture, de l'équilibre et de la coordination chez le sujet âgé",
        "famille": "sujet age",
        "detail": "rééducation analytique et globale, musculo-articulaire chez le sujet âgé",
        "cotation": "RPE 8.5",
        "seances_max": None,
        "referentiel": "non",
        "keywords": [
            "deambulation sujet age",
            "déambulation sujet âgé",
            "equilibre sujet age",
            "prévention chute sujet âgé"
        ],
        "keywords_any": [
            "déambulation sujet âgé",
            "deambulation sujet age",
            "equilibre sujet age",
            "équilibre sujet âgé",
            "prévention chute sujet âgé",
            "prevention chute sujet age"
        ],
        "required_fields": []
    },
    {
        "id": "brulure_un_membre",
        "acte": "Rééducation d'un patient atteint de brûlures localisées à un membre ou à un segment de membre",
        "famille": "brulures",
        "detail": "brûlures localisées à un membre ou à un segment de membre",
        "cotation": "RPB 8",
        "seances_max": None,
        "referentiel": "non",
        "keywords": [
            "brulure membre",
            "brûlure membre",
            "brulure localisee",
            "brûlure localisée",
            "localisee membre",
            "localisee segment"
        ],
        "keywords_any": [
            "brulure membre",
            "brûlure membre",
            "brulure localisée",
            "brûlure localisée",
            "localisee membre",
            "localisee segment"
        ],
        "required_fields": []
    },
    {
        "id": "brulure_plusieurs_membres_tronc",
        "acte": "Rééducation d'un patient atteint de brûlures étendues à plusieurs membres et/ou au tronc",
        "famille": "brulures",
        "detail": "brûlures étendues à plusieurs membres et/ou au tronc",
        "cotation": "RPB 9",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "brulure etendue",
            "brûlure étendue",
            "plusieurs membres",
            "brulure tronc",
            "brûlure tronc",
            "etendues tronc",
            "etendues plusieurs membres"
        ],
        "keywords_any": [
            "brulure etendue",
            "brûlure étendue",
            "plusieurs membres",
            "brulure tronc",
            "brûlure tronc",
            "etendues tronc",
            "etendues plusieurs membres"
        ],
        "required_fields": []
    },
    {
        "id": "soins_palliatifs",
        "acte": "Prise en charge, dans le cadre des soins palliatifs, comportant les actes nécessaires en fonction de situations cliniques",
        "famille": "soins palliatifs",
        "detail": "cotation journalière forfaitaire quel que soit le nombre d'interventions",
        "cotation": "PLL 12",
        "seances_max": None,
        "referentiel": "non",
        "keywords": [
            "soins palliatifs",
            "palliatif",
            "fin de vie",
            "cotation journaliere forfaitaire"
        ],
        "keywords_any": [
            "soins palliatifs",
            "palliatif",
            "fin de vie"
        ],
        "required_fields": []
    },
    {
        "id": "rhumatismales_atteinte_localisee",
        "acte": "Rééducation des maladies rhumatismales inflammatoires avec atteinte localisée à un membre ou le tronc",
        "famille": "maladies rhumatismales inflammatoires",
        "detail": "atteinte localisée à un membre ou le tronc",
        "cotation": "NMI 8",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "polyarthrite rhumatoide",
            "polyarthrite rhumatoïde",
            "rhumatismal inflammatoire",
            "rhumatisme inflammatoire",
            "atteinte localisee"
        ],
        "keywords_any": [
            "polyarthrite rhumatoide",
            "polyarthrite rhumatoïde",
            "rhumatismal inflammatoire",
            "rhumatisme inflammatoire",
            "atteinte localisee"
        ],
        "required_fields": []
    },
    {
        "id": "rhumatismales_atteinte_plusieurs_membres",
        "acte": "Rééducation des maladies rhumatismales inflammatoires avec atteinte de plusieurs membres, ou du tronc et d'un ou plusieurs membres",
        "famille": "maladies rhumatismales inflammatoires",
        "detail": "atteinte de plusieurs membres, ou du tronc et d'un ou plusieurs membres",
        "cotation": "NMI 9.01",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "polyarthrite",
            "plusieurs membres",
            "tronc et membre",
            "atteinte pluriterritoriale rhumatismale"
        ],
        "keywords_any": [
            "polyarthrite",
            "plusieurs membres",
            "tronc et membre",
            "atteinte pluriterritoriale rhumatismale"
        ],
        "required_fields": []
    },
    {
        "id": "plusieurs_territoires_sans_chirurgie",
        "acte": "Rééducation de plusieurs territoires sans chirurgie, avec au moins 2 territoires lésés",
        "famille": "plusieurs territoires",
        "detail": "sans chirurgie, au moins 2 territoires lésés",
        "cotation": "TER 9.49",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "plusieurs territoires",
            "deux territoires",
            "sans chirurgie",
            "multi territoires sans chirurgie"
        ],
        "keywords_any": [
            "plusieurs territoires",
            "deux territoires",
            "sans chirurgie",
            "multi territoires sans chirurgie"
        ],
        "required_fields": []
    },
    {
        "id": "plusieurs_territoires_avec_chirurgie",
        "acte": "Rééducation de plusieurs territoires avec chirurgie sur au moins un des territoires, avec au moins 2 territoires lésés",
        "famille": "plusieurs territoires",
        "detail": "avec chirurgie sur au moins un des territoires, au moins 2 territoires lésés",
        "cotation": "TER 9.51",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "plusieurs territoires",
            "deux territoires",
            "avec chirurgie",
            "multi territoires operes",
            "multi territoires opérés"
        ],
        "keywords_any": [
            "plusieurs territoires",
            "deux territoires",
            "avec chirurgie",
            "multi territoires operes",
            "multi territoires opérés"
        ],
        "required_fields": []
    },
    {
        "id": "amputation_un_membre_superieur",
        "acte": "Rééducation après amputation d'un membre supérieur",
        "famille": "amputations",
        "detail": "un membre supérieur",
        "cotation": "APM 8.11",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "amputation un membre superieur",
            "amputation un membre supérieur",
            "amputation membre superieur",
            "amputation membre supérieur",
            "ampute membre superieur",
            "amputé membre supérieur"
        ],
        "keywords_any": [
            "amputation un membre superieur",
            "amputation un membre supérieur",
            "amputation membre superieur",
            "amputation membre supérieur",
            "ampute membre superieur",
            "amputé membre supérieur"
        ],
        "required_fields": []
    },
    {
        "id": "amputation_un_membre_inferieur",
        "acte": "Rééducation après amputation d'un membre inférieur",
        "famille": "amputations",
        "detail": "un membre inférieur",
        "cotation": "APM 8.10",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "amputation un membre inferieur",
            "amputation un membre inférieur",
            "amputation membre inferieur",
            "amputation membre inférieur",
            "ampute membre inferieur",
            "amputé membre inférieur"
        ],
        "keywords_any": [
            "amputation un membre inferieur",
            "amputation un membre inférieur",
            "amputation membre inferieur",
            "amputation membre inférieur",
            "ampute membre inferieur",
            "amputé membre inférieur"
        ],
        "required_fields": []
    },
    {
        "id": "amputation_au_moins_deux_membres",
        "acte": "Rééducation après amputation d'au moins 2 membres",
        "famille": "amputations",
        "detail": "au moins 2 membres",
        "cotation": "APM 9.50",
        "seances_max": None,
        "referentiel": "non documente",
        "keywords": [
            "amputation au moins 2 membres",
            "amputation deux membres",
            "amputation 2 membres",
            "amputation plusieurs membres",
            "double amputation"
        ],
        "keywords_any": [
            "amputation au moins 2 membres",
            "amputation deux membres",
            "amputation 2 membres",
            "amputation plusieurs membres",
            "double amputation"
        ],
        "required_fields": []
    }
]
