#!/usr/bin/env python3
"""
ePerformance — Composeur de pages statiques
preview/_build/compose.py

Assemble les pages du site à partir d'un layout unique et de fragments de
contenu. Produit du HTML statique, prêt pour GitHub Pages.

Pourquoi un script plutôt qu'un framework : voir docs/adr/ADR-0002. Le
générateur agent-ia-web émet du HTML/CSS vanilla via un moteur de template
maison ; ce script joue le même rôle, sans ajouter de dépendance à
l'exécution ni de workflow de build.

Usage :
    python3 preview/_build/compose.py            # génère dans preview/
    python3 preview/_build/compose.py --check     # vérifie sans écrire

Le HTML produit est versionné. Le script n'est PAS nécessaire au
déploiement — GitHub Pages publie les fichiers déjà composés.
"""

import argparse
import html
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# CHEMINS
# ---------------------------------------------------------------------------

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
PREVIEW = os.path.dirname(BUILD_DIR)
CONTENT = os.path.join(PREVIEW, "_content")
ROOT = os.path.dirname(PREVIEW)

BASE_URL = "https://blog.eperformance.pro"
SITE_URL = "https://eperformance.pro"
SITE_NAME = "ePerformance"
SITE_DESC = ("Stratégie d'acquisition, IA générative, automatisation et "
             "développement web premium. Basé en Côte d'Ivoire, 100 % en ligne.")
WHATSAPP = "https://wa.me/2250151170666"
WHATSAPP_LABEL = "+225 01 51 17 06 66"
EMAIL = "bonjour@eperformance.pro"

YEAR = "2026"

# ---------------------------------------------------------------------------
# NAVIGATION — une seule définition, utilisée par toutes les pages
# ---------------------------------------------------------------------------

NAV = [
    ("Accueil",        "/",            "accueil"),
    ("Acquisition",    "/acquisition/", "acquisition"),
    ("Site web",       "/site-web/",   "site-web"),
    ("SEO",            "/seo/",        "seo"),
    ("Business",       "/business/",   "business"),
    ("IA",             "/articles/ia-generative-pme-africaine/", "ia"),
    ("Automatisation", "/articles/automatisation-marketing-debuter/", "automatisation"),
    ("À propos",       "/a-propos/",   "a-propos"),
    ("Site principal", SITE_URL,       "site"),
]

FOOTER_COLS = [
    ("Services", [
        ("stratégie d'acquisition", SITE_URL + "/index.html#methode"),
        ("IA générative",           SITE_URL + "/ia.html"),
        ("Automatisation",          SITE_URL + "/automatisation.html"),
        ("Création de site web",    SITE_URL + "/site-web.html"),
    ]),
    ("Ressources", [
        ("Diagnostic gratuit", SITE_URL + "/diagnostic_eperformance.html"),
        ("Formations",         SITE_URL + "/formation.html"),
        ("Ebooks",             SITE_URL + "/ebook.html"),
        ("Blog",               BASE_URL + "/"),
    ]),
    ("Contact", [
        (WHATSAPP_LABEL,        WHATSAPP),
        (EMAIL,                 "mailto:" + EMAIL),
        ("Espace client",       "https://api.eperformance.pro/connexion.php"),
    ]),
]

LEGAL_LINKS = [
    ("Mentions légales", SITE_URL + "/mentions-legales.html"),
    ("Confidentialité",  SITE_URL + "/politique-confidentialite.html"),
    ("Cookies",          SITE_URL + "/cookies.html"),
    ("CGV",              SITE_URL + "/cgv.html"),
]

# ---------------------------------------------------------------------------
# MÉTADONNÉES PAR PAGE
#   title / description : mesurés, ≤ 60 et ≤ 160 caractères
#   schema : blocs JSON-LD supplémentaires, injectés après le graphe de site
# ---------------------------------------------------------------------------

PAGES = {
    # ── Les 7 pages qui utilisent le hero du layout ──────────────────────
    # Titre, sur-titre et chapô viennent d'ici ; les fragments ne portent
    # aucun <h1>.
    "index.html": {
        "title": "Blog ePerformance — acquisition, web & SEO en Côte d'Ivoire",
        "description": "Méthodes concrètes sur le CAC, la création de sites web professionnels et le SEO local à Abidjan. Par K. Stéphane, fondateur d'ePerformance.",
        "h1": 'Piloter l\'acquisition <em>sans piloter à l\'aveugle.</em>',
        "lead": "Articles concrets sur le calcul du vrai CAC, la création de sites web professionnels en Côte d'Ivoire, le SEO local à Abidjan et la stratégie d'acquisition rentable. Que des méthodes appliquées, chiffres à l'appui.",
        "cta": ("Voir le pilier Acquisition", "/acquisition/"),
        "cta2": ("Site principal", SITE_URL),
        "fragment": "index.html",
        "nav_active": "accueil",
    },
    "acquisition/index.html": {
        "title": "Acquisition rentable — CAC, LTV, Payback | Blog ePerformance",
        "description": "Comment piloter votre acquisition par les chiffres réels plutôt qu'à l'aveugle : CAC, LTV, Payback et marge nette expliqués en pratique.",
        "h1": 'Piloter par les chiffres réels, <em>pas par les impressions.</em>',
        "eyebrow": "Pilier 01 · Acquisition",
        "lead": "Le ROAS affiché ne reflète pas votre marge nette. Ici, on parle de CAC, LTV, Payback et marge réelle — les quatre ratios qui décident vraiment.",
        "cta": ("Faire mon diagnostic gratuit", SITE_URL + "/diagnostic_eperformance.html"),
        "fragment": "acquisition.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/")],
    },
    "site-web/index.html": {
        "title": "Site web professionnel en Côte d'Ivoire | Blog ePerformance",
        "description": "Choisir, faire créer et optimiser un site web professionnel en Côte d'Ivoire : critères de choix, prix réels et erreurs à éviter.",
        "h1": 'Un site web <em>qui travaille pour vous.</em>',
        "eyebrow": "Pilier 02 · Site web",
        "lead": "Pas un site vitrine qui dort. Un site optimisé mobile, rapide, indexable par Google, qui capte les contacts pendant que vous dormez.",
        "cta": ("Voir les formules", SITE_URL + "/site-web.html"),
        "fragment": "site-web.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/")],
    },
    "seo/index.html": {
        "title": "SEO local à Abidjan et référencement | Blog ePerformance",
        "description": "Apparaître sur Google quand vos clients vous cherchent : SEO local à Abidjan, référencement technique, contenu et optimisation pour les moteurs IA.",
        "h1": 'Apparaître <em>quand vos clients vous cherchent.</em>',
        "eyebrow": "Pilier 03 · SEO",
        "lead": "Le SEO n'est pas un luxe d'agence. C'est le canal le moins cher pour ramener des clients qualifiés, mois après mois, sans budget publicitaire.",
        "cta": ("Guide SEO local à Abidjan", "/articles/seo-local-abidjan-guide/"),
        "fragment": "seo.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/")],
    },
    "business/index.html": {
        "title": "Business et modèle économique | Blog ePerformance",
        "description": "Prix, trésorerie et modèle économique : ce qui décide de votre rentabilité avant même la première campagne publicitaire.",
        "h1": 'Le modèle économique <em>avant la tactique.</em>',
        "eyebrow": "Pilier 04 · Business",
        "lead": "On peut pirouetter sur Meta Ads : si le modèle économique est mauvais, vous perdrez. Ces articles traitent de ce qui se décide avant la publicité.",
        "fragment": "business.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/")],
    },
    "a-propos/index.html": {
        "title": "À propos — K. Stéphane, fondateur d'ePerformance",
        "description": "K. Stéphane accompagne les entrepreneurs de Côte d'Ivoire sur leur acquisition depuis 2017. Parcours, méthode et raison d'être de ce blog.",
        "h1": 'K. Stéphane, <em>fondateur d\'ePerformance.</em>',
        "lead": "J'accompagne des entrepreneurs qui vendent déjà et qui veulent savoir ce que chaque client leur coûte vraiment. Basé en Côte d'Ivoire, 100 % en ligne.",
        "cta": ("Me contacter", "/contact/"),
        "fragment": "a-propos.html",
        "nav_active": "a-propos",
        "breadcrumb": [("À propos", "/a-propos/")],
    },
    "contact/index.html": {
        "title": "Contact — Blog ePerformance",
        "description": "Contactez K. Stéphane, fondateur d'ePerformance : WhatsApp, diagnostic gratuit en ligne, ou site principal.",
        "h1": 'Parlons de <em>votre acquisition.</em>',
        "lead": "Le plus simple et le plus rapide : WhatsApp. Réponse en général sous 24 h ouvrées.",
        "fragment": "contact.html",
        "nav_active": "contact",
        "breadcrumb": [("Contact", "/contact/")],
    },

    # ── Les 3 articles ───────────────────────────────────────────────────
    # Pas de hero : le fragment porte son propre en-tête éditorial
    # (.article-hero avec catégorie, <h1>, date, temps de lecture).
    "articles/site-trop-lent/index.html": {
        "title": 'Site trop lent : les cinq causes réelles',
        "description": "Serveur, images, scripts, polices, services tiers : les cinq causes d'un site lent, comment les repérer avec un outil, et dans quel ordre les corriger.",
        "fragment": "articles-site-trop-lent.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Site trop lent", "/articles/site-trop-lent/")],
    },
    "articles/images-site-webp/index.html": {
        "title": 'Images de site : le format qui divise le poids par dix',
        "description": "Convertir en WebP, redimensionner à la taille d'affichage, différer le chargement : la méthode pour alléger les images sans casser la mise en page.",
        "fragment": "articles-images-site-webp.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Images et WebP", "/articles/images-site-webp/")],
    },
    "articles/site-mobile-entree-de-gamme/index.html": {
        "title": 'Rendre son site utilisable sur un téléphone modeste',
        "description": 'Polices lourdes, animations, formulaires, images, menus : ce qui casse en premier sur un appareil modeste, et comment tester son site sur un vrai téléphone.',
        "fragment": "articles-site-mobile-entree-de-gamme.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Site sur mobile", "/articles/site-mobile-entree-de-gamme/")],
    },
    "articles/formulaire-contact-efficace/index.html": {
        "title": 'Formulaire de contact : pourquoi le vôtre ne reçoit rien',
        "description": 'Trop de champs, libellés flous, formulaire cassé, notifications en spam : les six causes qui vident une boîte de réception, et comment tester la vôtre.',
        "fragment": "articles-formulaire-contact-efficace.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Formulaire de contact", "/articles/formulaire-contact-efficace/")],
    },
    "articles/bouton-whatsapp-site/index.html": {
        "title": "Bouton WhatsApp : bien le placer pour qu'on clique",
        "description": "Placement, libellé, message pré-rempli, taille et moment d'apparition : les cinq réglages qui décident des clics sur un bouton WhatsApp.",
        "fragment": "articles-bouton-whatsapp-site.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Bouton WhatsApp", "/articles/bouton-whatsapp-site/")],
    },
    "articles/erreurs-qui-font-fuir/index.html": {
        "title": 'Les erreurs qui font fuir un visiteur en dix secondes',
        "description": 'Page lente, message incompréhensible, absence de preuve, navigation introuvable, contact invisible : repérer ces cinq défauts, et les corriger.',
        "fragment": "articles-erreurs-qui-font-fuir.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Erreurs qui font fuir", "/articles/erreurs-qui-font-fuir/")],
    },
    "articles/monetiser-sans-ecommerce/index.html": {
        "title": 'Monétiser un site sans e-commerce',
        "description": "Rendez-vous, devis, réservation, abonnement, mise en relation, vente sur WhatsApp : six modèles pour faire entrer de l'argent sans boutique.",
        "fragment": "articles-monetiser-sans-ecommerce.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Monétiser sans boutique", "/articles/monetiser-sans-ecommerce/")],
    },
    "articles/refonte-site-quand/index.html": {
        "title": "Refonte de site : nécessaire, ou du luxe ?",
        "description": 'Les signaux qui justifient une refonte, ceux qui ne la justifient pas, et les cinq chiffres à relever avant de décider entre réparer et tout refaire.',
        "fragment": "articles-refonte-site-quand.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Faut-il refaire son site", "/articles/refonte-site-quand/")],
    },
    "articles/reprendre-controle-site/index.html": {
        "title": 'Reprendre le contrôle de son site après un prestataire',
        "description": 'Domaine, hébergement, administration, mesure, contenus : quoi récupérer, comment le demander par écrit, et les étapes quand le prestataire ne répond plus.',
        "fragment": "articles-reprendre-controle-site.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Reprendre son site", "/articles/reprendre-controle-site/")],
    },
    "articles/fiche-google-business-profile/index.html": {
        "title": 'Fiche Google Business Profile : la configuration qui compte',
        "description": "Nom, catégories, description, horaires, zone, photos, attributs, questions, publications, messagerie : ce qu'il faut mettre dans chaque champ.",
        "fragment": "articles-fiche-google-business-profile.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("Fiche Google Business Profile", "/articles/fiche-google-business-profile/")],
    },
    "articles/avis-google-sans-forcer/index.html": {
        "title": 'Avis Google : comment en obtenir sans forcer',
        "description": 'Quand demander un avis, quel lien envoyer, quoi écrire, comment répondre à un avis négatif et ce qui fait suspendre une fiche.',
        "fragment": "articles-avis-google-sans-forcer.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("Avis Google : comment en obtenir sans forcer", "/articles/avis-google-sans-forcer/")],
    },
    "articles/pack-local-ouagadougou/index.html": {
        "title": 'Être visible dans le pack local Google à Ouagadougou',
        "description": 'Secteurs, quartiers, repères et point sur la carte : comment configurer sa fiche Google et suivre ce qui amène des appels à Ouagadougou.',
        "fragment": "articles-pack-local-ouagadougou.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("Être visible dans le pack local Google à Ouagadougou", "/articles/pack-local-ouagadougou/")],
    },
    "articles/annuaires-citations-cote-ivoire/index.html": {
        "title": "Citations, annuaires ivoiriens : où inscrire son entreprise",
        "description": "Les plateformes à tenir, les familles d'annuaires à couvrir en Côte d'Ivoire, et sept vérifications pour écarter un annuaire sans audience.",
        "fragment": "articles-annuaires-citations-cote-ivoire.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("Citations, annuaires ivoiriens : où inscrire son entreprise", "/articles/annuaires-citations-cote-ivoire/")],
    },
    "articles/seo-local-sans-site-web/index.html": {
        "title": "SEO local pour un commerce sans site web",
        "description": "Une fiche Google bien tenue ramène des appels et des visites, sans site. Voici ce qu'elle permet vraiment, et le point exact où elle plafonne.",
        "fragment": "articles-seo-local-sans-site-web.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("SEO local pour un commerce sans site web", "/articles/seo-local-sans-site-web/")],
    },
    "articles/balises-title-description/index.html": {
        "title": 'Title et description : réécrire pour gagner des clics',
        "description": 'Balise title et meta description : la méthode de réécriture en quatre questions, trois exemples avant/après, et comment vérifier ce que Google affiche.',
        "fragment": "articles-balises-title-description.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("Title et description : réécrire pour gagner des clics", "/articles/balises-title-description/")],
    },
    "articles/donnees-structurees-schema-org/index.html": {
        "title": 'Données structurées : ce que Google comprend de votre site',
        "description": 'Données structurées : à quoi servent LocalBusiness, Organization, Product, Article, BreadcrumbList ou FAQPage, avec un exemple JSON-LD.',
        "fragment": "articles-donnees-structurees-schema-org.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("Données structurées : ce que Google comprend de votre site", "/articles/donnees-structurees-schema-org/")],
    },
    "articles/sitemap-robots-txt/index.html": {
        "title": "Sitemap et robots.txt : les deux fichiers qu'on oublie",
        "description": "Vérifier en cinq minutes que sitemap.xml et robots.txt sont en place : adresses à tester, commandes curl, erreurs classiques et corrections.",
        "fragment": "articles-sitemap-robots-txt.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("Sitemap et robots.txt : les deux fichiers qu'on oublie", "/articles/sitemap-robots-txt/")],
    },
    "articles/erreurs-indexation-google/index.html": {
        "title": "Erreurs d'indexation : pourquoi votre page n'apparaît pas",
        "description": "Diagnostiquer une page absente de Google avec Search Console : les sept causes par ordre de fréquence, le symptôme exact et la correction.",
        "fragment": "articles-erreurs-indexation-google.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("Erreurs d'indexation : pourquoi votre page n'apparaît pas", "/articles/erreurs-indexation-google/")],
    },
    "articles/etre-cite-par-chatgpt/index.html": {
        "title": 'Être cité par ChatGPT, Claude et Perplexity : la méthode',
        "description": 'Structure de réponse, faits datés et vérifiables, entité cohérente : les conditions pour être cité par ChatGPT, Claude et Perplexity, et comment mesurer.',
        "fragment": "articles-etre-cite-par-chatgpt.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("Être cité par ChatGPT, Claude et Perplexity", "/articles/etre-cite-par-chatgpt/")],
    },
    "articles/llms-txt/index.html": {
        "title": "llms.txt : à quoi ça sert, et si ça sert vraiment",
        "description": "Le llms.txt se pose à la racine d'un site. Ce qu'il contient, ce qu'il ne fait pas encore, et pourquoi il ne remplace ni robots.txt ni vos pages.",
        "fragment": "articles-llms-txt.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("llms.txt : à quoi ça sert, et si ça sert vraiment", "/articles/llms-txt/")],
    },
    "articles/contenu-duplique/index.html": {
        "title": "Contenu dupliqué : les cas qui pénalisent vraiment",
        "description": "Vendre le même produit dans dix villes n'est pas un problème. Les quatre cas qui en posent un, ce que Google fait vraiment, et comment poser un canonical.",
        "fragment": "articles-contenu-duplique.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("Contenu dupliqué : les cas qui pénalisent vraiment", "/articles/contenu-duplique/")],
    },
    "articles/netlinking-local/index.html": {
        "title": "Netlinking local : quels liens comptent vraiment",
        "description": "Partenariats, presse locale, annuaires, associations : les sources de liens classées par rendement réel pour un commerce en Afrique de l'Ouest.",
        "fragment": "articles-netlinking-local.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("Netlinking local : quels liens comptent vraiment", "/articles/netlinking-local/")],
    },
    "articles/mesurer-son-seo/index.html": {
        "title": 'Mesurer son SEO sans y passer ses journées',
        "description": 'Quatre indicateurs, une lecture par mois, quinze minutes : impressions, clics, position sur les requêtes qui comptent, pages indexées.',
        "fragment": "articles-mesurer-son-seo.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("Mesurer son SEO sans y passer ses journées", "/articles/mesurer-son-seo/")],
    },
    "articles/fixer-ses-prix/index.html": {
        "title": "Fixer ses prix quand on vend en ligne en Afrique de l'Ouest",
        "description": "Coût de revient réel, marge visée, puis prix affiché : la méthode dans l'ordre, les coûts oubliés du e-commerce et deux exemples chiffrés en FCFA.",
        "fragment": "articles-fixer-ses-prix.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Fixer ses prix quand on vend en ligne en Afrique de l'Ouest", "/articles/fixer-ses-prix/")],
    },
    "articles/vendre-a-la-diaspora/index.html": {
        "title": "Vendre à la diaspora : ce qui change dans l'achat",
        "description": "Confiance, paiement en euros, livraison à un tiers, calendrier des fêtes et service après : le parcours d'achat d'un client de la diaspora, étape par étape.",
        "fragment": "articles-vendre-a-la-diaspora.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Vendre à la diaspora : ce qui change dans l'achat", "/articles/vendre-a-la-diaspora/")],
    },
    "articles/paiement-mobile-money/index.html": {
        "title": "Paiement mobile money : Orange, Wave, MTN et Moov",
        "description": "Ce qu'un site peut accepter en mobile money : lien de paiement, QR code, formulaire avec confirmation manuelle ou passerelle. Les frictions qui restent.",
        "fragment": "articles-paiement-mobile-money.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Paiement mobile money : Orange, Wave, MTN et Moov", "/articles/paiement-mobile-money/")],
    },
    "articles/tableau-tresorerie/index.html": {
        "title": 'Trésorerie : le tableau qui évite le blocage',
        "description": 'Trois colonnes, une ligne par semaine, quinze minutes le lundi : le tableau de trésorerie minimal, avec un exemple chiffré en FCFA sur huit semaines.',
        "fragment": "articles-tableau-tresorerie.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Trésorerie : le tableau qui évite le blocage", "/articles/tableau-tresorerie/")],
    },
    "articles/delai-paiement-client/index.html": {
        "title": "Délai de paiement client : comment ne plus le subir",
        "description": "Conditions écrites, acompte, facturation immédiate, relance programmée : l'ordre des défenses contre les retards de paiement, avec les textes à copier.",
        "fragment": "articles-delai-paiement-client.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Délai de paiement client : comment ne plus le subir", "/articles/delai-paiement-client/")],
    },
    "articles/emprunter-ou-autofinancer/index.html": {
        "title": "Emprunter ou autofinancer sa croissance",
        "description": "L'autofinancement coûte la lenteur, l'emprunt coûte les intérêts et la date fixe. Comparaison des deux coûts réels, fonds de roulement compris.",
        "fragment": "articles-emprunter-ou-autofinancer.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Emprunter ou autofinancer sa croissance", "/articles/emprunter-ou-autofinancer/")],
    },
    "articles/choisir-statut-entreprise/index.html": {
        "title": "Choisir son statut d'entreprise en Côte d'Ivoire",
        "description": "Ce que le statut change pour la publicité, les paiements et la séparation du patrimoine — et ce qu'il ne change pas, pour décider sur des faits.",
        "fragment": "articles-choisir-statut-entreprise.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Choisir son statut d'entreprise en Côte d'Ivoire", "/articles/choisir-statut-entreprise/")],
    },
    "articles/se-lancer-au-burkina-faso/index.html": {
        "title": "Se lancer au Burkina Faso : ce qui change",
        "description": "Ouagadougou et Bobo ne se ressemblent pas, les portefeuilles mobiles ne sont pas les mêmes, la route fixe le délai : ce qui change quand on arrive d'Abidjan.",
        "fragment": "articles-se-lancer-au-burkina-faso.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Se lancer au Burkina Faso : ce qui change", "/articles/se-lancer-au-burkina-faso/")],
    },
    "articles/structure-de-couts/index.html": {
        "title": "Structure de coûts : où part votre argent",
        "description": "Coûts fixes, coûts variables, cas ambigus, seuil de rentabilité et décisions : la carte des charges d'une petite structure, avec un exemple chiffré.",
        "fragment": "articles-structure-de-couts.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Structure de coûts : où part votre argent", "/articles/structure-de-couts/")],
    },
    "articles/externaliser-ou-recruter/index.html": {
        "title": 'Externaliser ou recruter : décider avec des chiffres',
        "description": 'Salaire demandé contre facture : ce que chaque option coûte vraiment sur douze mois, et pourquoi le volume décide du résultat.',
        "fragment": "articles-externaliser-ou-recruter.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Externaliser ou recruter : décider avec des chiffres", "/articles/externaliser-ou-recruter/")],
    },
    "articles/deleguer-sans-perdre-le-controle/index.html": {
        "title": 'Déléguer sans perdre le contrôle',
        "description": 'Ce qui se délègue, ce qui ne se délègue pas, la procédure écrite en cinq questions et le contrôle par échantillon qui laisse travailler.',
        "fragment": "articles-deleguer-sans-perdre-le-controle.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Déléguer sans perdre le contrôle", "/articles/deleguer-sans-perdre-le-controle/")],
    },
    "articles/decider-avec-des-chiffres/index.html": {
        "title": "Décider avec des chiffres plutôt qu'au ressenti",
        "description": "La boucle mesure, décision, action : pourquoi le chiffre manque au moment de décider, et la routine d'une heure par mois qui rend les décisions défendables.",
        "fragment": "articles-decider-avec-des-chiffres.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Décider avec des chiffres plutôt qu'au ressenti", "/articles/decider-avec-des-chiffres/")],
    },
    "articles/se-lancer-au-burkina-faso/index.html": {
        "title": "Se lancer au Burkina Faso : ce qui change",
        "description": "Ouagadougou et Bobo ne se ressemblent pas, les portefeuilles mobiles ne sont pas les mêmes, la route fixe le délai : ce qui change quand on arrive d'Abidjan.",
        "fragment": "articles-se-lancer-au-burkina-faso.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Se lancer au Burkina Faso : ce qui change", "/articles/se-lancer-au-burkina-faso/")],
    },
    "articles/structure-de-couts/index.html": {
        "title": "Structure de coûts : où part votre argent",
        "description": "Coûts fixes, coûts variables, cas ambigus, seuil de rentabilité et décisions : la carte des charges d'une petite structure, avec un exemple chiffré.",
        "fragment": "articles-structure-de-couts.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Structure de coûts : où part votre argent", "/articles/structure-de-couts/")],
    },
    "articles/externaliser-ou-recruter/index.html": {
        "title": 'Externaliser ou recruter : décider avec des chiffres',
        "description": 'Salaire demandé contre facture : ce que chaque option coûte vraiment sur douze mois, et pourquoi le volume décide du résultat.',
        "fragment": "articles-externaliser-ou-recruter.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Externaliser ou recruter : décider avec des chiffres", "/articles/externaliser-ou-recruter/")],
    },
    "articles/deleguer-sans-perdre-le-controle/index.html": {
        "title": 'Déléguer sans perdre le contrôle',
        "description": 'Ce qui se délègue, ce qui ne se délègue pas, la procédure écrite en cinq questions et le contrôle par échantillon qui laisse travailler.',
        "fragment": "articles-deleguer-sans-perdre-le-controle.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Déléguer sans perdre le contrôle", "/articles/deleguer-sans-perdre-le-controle/")],
    },
    "articles/decider-avec-des-chiffres/index.html": {
        "title": "Décider avec des chiffres plutôt qu'au ressenti",
        "description": "La boucle mesure, décision, action : pourquoi le chiffre manque au moment de décider, et la routine d'une heure par mois qui rend les décisions défendables.",
        "fragment": "articles-decider-avec-des-chiffres.html",
        "nav_active": "business",
        "breadcrumb": [("Business", "/business/"), ("Décider avec des chiffres plutôt qu'au ressenti", "/articles/decider-avec-des-chiffres/")],
    },
    "articles/marge-nette-acquisition/index.html": {
        "title": "Marge nette d'acquisition : le chiffre qui dit vrai",
        "description": "Publicité, marchandise, emballage, livraison, commission et retours déduits un par un : ce qui reste vraiment sur chaque vente, exemple chiffré en FCFA.",
        "fragment": "articles-marge-nette-acquisition.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Marge nette d'acquisition : le chiffre qui dit vrai", "/articles/marge-nette-acquisition/")],
    },
    "articles/boost-publication/index.html": {
        "title": "Le boost de publication est-il encore utile",
        "description": "Ce que le boost d'une publication fait, ce qu'il ne mesure pas, les cas où il rend service et le test simple pour savoir s'il a rapporté quelque chose.",
        "fragment": "articles-boost-publication.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Le boost de publication est-il encore utile", "/articles/boost-publication/")],
    },
    "articles/ameliorer-taux-conversion/index.html": {
        "title": 'Améliorer le taux de conversion sans toucher au budget pub',
        "description": 'Cinq fuites du parcours client, du clic à la relance, avec la méthode pour repérer chacune et la correction à appliquer, sans un franc de budget en plus.',
        "fragment": "articles-ameliorer-taux-conversion.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Améliorer sa conversion", "/articles/ameliorer-taux-conversion/")],
    },
    "articles/cac-par-segment/index.html": {
        "title": 'Segments clients : arrêter de calculer un CAC moyen',
        "description": 'Segmenter par canal, produit, type de client et zone. La méthode de calcul du CAC par segment, avec un exemple où un segment en finance un autre.',
        "fragment": "articles-cac-par-segment.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("CAC par segment", "/articles/cac-par-segment/")],
    },
    "articles/test-ab-methode/index.html": {
        "title": 'Test A/B : la méthode minimale pour décider',
        "description": 'Ce qui se teste en une semaine, ce qui ne se teste pas sans volume, comment fixer la durée et lire un résultat. La version minimale, sans outil payant.',
        "fragment": "articles-test-ab-methode.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Test A/B", "/articles/test-ab-methode/")],
    },
    "articles/fidelisation-ltv/index.html": {
        "title": 'Fidélisation : le levier de LTV le plus rentable',
        "description": "Faire revenir un client coûte moins cher que d'en acquérir un nouveau. Quatre mécaniques de fidélisation testables, et ce qu'elles déplacent sur votre LTV.",
        "fragment": "articles-fidelisation-ltv.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Fidélisation", "/articles/fidelisation-ltv/")],
    },
    "articles/upsell-vente-complementaire/index.html": {
        "title": 'Upsell et vente complémentaire : la méthode simple',
        "description": 'Le complément à la commande, la montée en gamme, le réassort programmé : trois mécaniques testables pour faire monter le panier moyen.',
        "fragment": "articles-upsell-vente-complementaire.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Upsell", "/articles/upsell-vente-complementaire/")],
    },
    "articles/prix-site-web-cote-ivoire/index.html": {
        "title": "Combien coûte un site web professionnel en Côte d'Ivoire",
        "description": 'Fourchettes observées sur le marché ivoirien, sept éléments qui font monter un devis, et comment lire une proposition de site web avant de signer.',
        "fragment": "articles-prix-site-web-cote-ivoire.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Prix d'un site web", "/articles/prix-site-web-cote-ivoire/")],
    },
    "articles/vitrine-ou-ecommerce/index.html": {
        "title": 'Site vitrine, e-commerce ou les deux : comment décider',
        "description": "Vos clients achètent-ils après avoir vu, ou après avoir demandé ? Grille de décision par activité, et coût caché d'un e-commerce qu'on n'utilise pas.",
        "fragment": "articles-vitrine-ou-ecommerce.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Vitrine ou e-commerce", "/articles/vitrine-ou-ecommerce/")],
    },
    "articles/wordpress-shopify-sur-mesure/index.html": {
        "title": 'WordPress, Shopify ou sur-mesure : lequel choisir',
        "description": 'Paiement mobile money, connexion, maintenance, liberté de changer : quatre critères locaux pour trancher, et pour qui chaque option est un mauvais choix.',
        "fragment": "articles-wordpress-shopify-sur-mesure.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Quelle technologie", "/articles/wordpress-shopify-sur-mesure/")],
    },
    "articles/questions-prestataire-site-web/index.html": {
        "title": 'Les questions à poser avant de confier son site',
        "description": "Douze questions à poser avant de signer, et ce qu'une bonne réponse contient : propriété, délai écrit, support, sauvegardes, sortie de collaboration.",
        "fragment": "articles-questions-prestataire-site-web.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Questions au prestataire", "/articles/questions-prestataire-site-web/")],
    },
    "articles/domaine-hebergement-propriete/index.html": {
        "title": 'Nom de domaine et hébergement : ce que vous devez posséder',
        "description": "Le domaine, l'hébergement, les comptes et les accès de mesure doivent être à votre nom. Vérifier ce que vous possédez, et reprendre la main si besoin.",
        "fragment": "articles-domaine-hebergement-propriete.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Propriété du site", "/articles/domaine-hebergement-propriete/")],
    },
    "articles/cinq-couts-cac-oublies/index.html": {
        "title": 'Les cinq coûts que votre CAC oublie',
        "description": 'Les cinq coûts absents de votre CAC : temps de traitement, frais mobile money, colis refusés, livraison, outils. Comment les repérer et les chiffrer.',
        "fragment": "articles-cinq-couts-cac-oublies.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Les coûts oubliés du CAC", "/articles/cinq-couts-cac-oublies/")],
    },
    "articles/lire-statistiques-meta-ads/index.html": {
        "title": 'Lire ses statistiques Meta sans se noyer',
        "description": 'Six chiffres suffisent pour lire un gestionnaire de publicités : dépense, résultats, coût par résultat, CTR, CPM, fréquence. Ceux à ignorer, et pourquoi.',
        "fragment": "articles-lire-statistiques-meta-ads.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Lire ses statistiques Meta", "/articles/lire-statistiques-meta-ads/")],
    },
    "articles/roas-trompeur/index.html": {
        "title": 'Pourquoi le ROAS affiché ment sur votre rentabilité',
        "description": "Un ROAS de 4 peut cacher un mois déficitaire : marchandise, livraison, frais mobile money, colis refusés et temps déduits, chiffres à l'appui.",
        "fragment": "articles-roas-trompeur.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Le ROAS qui trompe", "/articles/roas-trompeur/")],
    },
    "articles/ciblage-meta-2026/index.html": {
        "title": "Cibler ou laisser l'algorithme travailler en 2026",
        "description": 'Andromeda change la donne : le ciblage manuel fin perd son intérêt. Structure de campagne, rôle de la créa, qualité du signal, habitudes à abandonner.',
        "fragment": "articles-ciblage-meta-2026.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Ciblage Meta en 2026", "/articles/ciblage-meta-2026/")],
    },
    "articles/creas-publicitaires-afrique/index.html": {
        "title": "Créas publicitaires qui fonctionnent en Afrique de l'Ouest",
        "description": 'Trois formats efficaces localement, ce qui échoue, et les critères de production : format, durée, taille du texte, poids du fichier, lisibilité sur petit écran.',
        "fragment": "articles-creas-publicitaires-afrique.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Créas qui fonctionnent", "/articles/creas-publicitaires-afrique/")],
    },
    "articles/whatsapp-business-conversion/index.html": {
        "title": 'WhatsApp Business : le canal de conversion sous-estimé',
        "description": "Catalogue, réponses rapides, message d'accueil, étiquettes : la structure qui transforme une conversation WhatsApp en commande, et ses limites.",
        "fragment": "articles-whatsapp-business-conversion.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("WhatsApp Business", "/articles/whatsapp-business-conversion/")],
    },
    "articles/pixel-meta-capi/index.html": {
        "title": 'Pixel Meta et CAPI : un tracking qui survit à iOS',
        "description": 'Pourquoi le Pixel seul perd des conversions depuis iOS, ce que le CAPI envoie côté serveur, et ce que vous devez commander et vérifier vous-même.',
        "fragment": "articles-pixel-meta-capi.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Pixel et CAPI", "/articles/pixel-meta-capi/")],
    },
    "articles/meta-ads-ou-google-ads/index.html": {
        "title": 'Meta Ads ou Google Ads : lequel choisir',
        "description": "Meta interrompt, Google répond. Grille de décision par activité, ordre d'ouverture des deux canaux et vérifications avant d'engager un budget.",
        "fragment": "articles-meta-ads-ou-google-ads.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Meta ou Google Ads", "/articles/meta-ads-ou-google-ads/")],
    },
    "articles/google-ads-quand/index.html": {
        "title": 'Google Ads : quand cela vaut vraiment la peine',
        "description": "Trois conditions à réunir avant de dépenser sur Google Ads : une demande de recherche existante, une page qui convertit, un budget qui sort de l'apprentissage.",
        "fragment": "articles-google-ads-quand.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Google Ads : quand", "/articles/google-ads-quand/")],
    },
    "articles/budget-publicitaire-debuter/index.html": {
        "title": 'Budget publicitaire : combien prévoir pour commencer',
        "description": "Partir du CAC cible plutôt que d'un budget arbitraire : méthode en quatre lignes, seuil minimum pour tester, budget de test et budget d'échelle.",
        "fragment": "articles-budget-publicitaire-debuter.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Budget publicitaire", "/articles/budget-publicitaire-debuter/")],
    },
    "articles/capturer-qualifier-demandes/index.html": {
        "title": 'Capturer et qualifier ses demandes entrantes',
        "description": "Le parcours d'une demande entrante, étape par étape : accusé de réception, trois questions de qualification, fiche créée, bonne personne prévenue.",
        "fragment": "articles-capturer-qualifier-demandes.html",
        "nav_active": "automatisation",
        "breadcrumb": [("Automatisation", "/articles/automatisation-marketing-debuter/"), ("Capturer ses demandes entrantes", "/articles/capturer-qualifier-demandes/")],
    },
    "articles/relance-client-automatique/index.html": {
        "title": 'Relance automatique : la séquence J+1, J+3, J+7',
        "description": "J+1, J+3, J+7, puis l'arrêt immédiat dès que la personne répond : comment régler une séquence de relance et écrire un message qui donne envie de répondre.",
        "fragment": "articles-relance-client-automatique.html",
        "nav_active": "automatisation",
        "breadcrumb": [("Automatisation", "/articles/automatisation-marketing-debuter/"), ("Relance automatique", "/articles/relance-client-automatique/")],
    },
    "articles/reporting-automatise/index.html": {
        "title": 'Un reporting qui se remplit tout seul chaque mois',
        "description": "Quelles données collecter, d'où elles viennent, à quelle fréquence, et les contrôles qui empêchent un rapport faux d'arriver à l'heure.",
        "fragment": "articles-reporting-automatise.html",
        "nav_active": "automatisation",
        "breadcrumb": [("Automatisation", "/articles/automatisation-marketing-debuter/"), ("Reporting automatisé", "/articles/reporting-automatise/")],
    },
    "articles/synchroniser-outils-commerciaux/index.html": {
        "title": 'Synchroniser site, WhatsApp et suivi commercial',
        "description": 'Un seul statut par contact, partagé entre site, WhatsApp et suivi : la mécanique de synchronisation, les règles à écrire et les pièges du numéro.',
        "fragment": "articles-synchroniser-outils-commerciaux.html",
        "nav_active": "automatisation",
        "breadcrumb": [("Automatisation", "/articles/automatisation-marketing-debuter/"), ("Synchroniser ses outils", "/articles/synchroniser-outils-commerciaux/")],
    },
    "articles/cout-automatisation/index.html": {
        "title": 'Combien coûte une automatisation, et que rapporte-t-elle',
        "description": "Les cinq postes de coût, la mise en place comptée en jours de travail et la division qui donne le seuil de rentabilité d'une automatisation.",
        "fragment": "articles-cout-automatisation.html",
        "nav_active": "automatisation",
        "breadcrumb": [("Automatisation", "/articles/automatisation-marketing-debuter/"), ("Coût d'une automatisation", "/articles/cout-automatisation/")],
    },
    "articles/automatisation-dependance/index.html": {
        "title": "Automatiser sans dépendre d'un prestataire",
        "description": "Accès à votre nom, propriété des workflows, documentation, réversibilité : ce qui doit rester chez vous et ce qu'il faut exiger par écrit.",
        "fragment": "articles-automatisation-dependance.html",
        "nav_active": "automatisation",
        "breadcrumb": [("Automatisation", "/articles/automatisation-marketing-debuter/"), ("Garder la main", "/articles/automatisation-dependance/")],
    },
    "articles/erreurs-automatisation/index.html": {
        "title": 'Trois automatisations à ne pas faire',
        "description": 'Relancer des prospects mal qualifiés, automatiser sans volume, automatiser une réclamation : trois chantiers à refuser, et pourquoi.',
        "fragment": "articles-erreurs-automatisation.html",
        "nav_active": "automatisation",
        "breadcrumb": [("Automatisation", "/articles/automatisation-marketing-debuter/"), ("Ce qu'il ne faut pas automatiser", "/articles/erreurs-automatisation/")],
    },
    "articles/calculer-ltv/index.html": {
        "title": "Calculer sa LTV sans se raconter d'histoires",
        "description": 'La LTV se calcule sur des achats réels : méthode par cohorte, taux de rachat, erreurs qui gonflent le chiffre et décisions publicitaires.',
        "fragment": "articles-calculer-ltv.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Calculer sa LTV", "/articles/calculer-ltv/")],
    },
    "articles/payback-period/index.html": {
        "title": 'Payback period : le ratio qui tue les trésoreries',
        "description": 'Le payback mesure le délai de récupération du CAC. Calcul, cible des 90 jours, exemple chiffré et cinq leviers pour le raccourcir.',
        "fragment": "articles-payback-period.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Payback period", "/articles/payback-period/")],
    },
    "articles/ratio-ltv-cac/index.html": {
        "title": 'Ratio LTV:CAC : quel seuil viser vraiment',
        "description": 'Le 3:1 est un point de départ, pas une loi. Calcul en marge, lecture par zone, seuils de décision et alerte du ratio trop élevé.',
        "fragment": "articles-ratio-ltv-cac.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Ratio LTV:CAC", "/articles/ratio-ltv-cac/")],
    },
    "articles/cinq-taches-ia-entreprise/index.html": {
        "title": "Cinq tâches que l'IA fait mieux que vous | ePerformance",
        "description": "Cinq tâches que l'IA générative fait mieux que vous, classées par temps gagné mesurable. Ce que chacune remplace, ce qu'elle produit, comment la traiter.",
        "fragment": "articles-cinq-taches-ia-entreprise.html",
        "nav_active": "ia",
        "breadcrumb": [("IA générative", "/"), ("Cinq tâches que l'IA fait mieux que vous", "/articles/cinq-taches-ia-entreprise/")],
    },
    "articles/chatbot-ia-repondre-site/index.html": {
        "title": "IA conversationnelle : ce qu'elle répond vraiment",
        "description": "Ce qu'un agent conversationnel peut répondre depuis vos données réelles, et ce qu'il ne peut pas. La mécanique, les limites, le passage à un humain.",
        "fragment": "articles-chatbot-ia-repondre-site.html",
        "nav_active": "ia",
        "breadcrumb": [("IA générative", "/"), ("IA conversationnelle sur votre site", "/articles/chatbot-ia-repondre-site/")],
    },
    "articles/rediger-fiches-produits-ia/index.html": {
        "title": "Rédiger ses fiches produits avec l'IA | ePerformance",
        "description": "La méthode en quatre étapes pour produire ses fiches produits avec l'IA sans perdre la voix de la marque. Sans informations brutes, le résultat est générique.",
        "fragment": "articles-rediger-fiches-produits-ia.html",
        "nav_active": "ia",
        "breadcrumb": [("IA générative", "/"), ("Rédiger ses fiches produits avec l'IA", "/articles/rediger-fiches-produits-ia/")],
    },
    "articles/ia-service-client-nuit/index.html": {
        "title": 'IA et service client : répondre la nuit | ePerformance',
        "description": "Trois niveaux d'automatisation du service client comparés : réponse préparée, agent sur le site, agent sur WhatsApp. Ce que chacun couvre et ce qu'il exige.",
        "fragment": "articles-ia-service-client-nuit.html",
        "nav_active": "ia",
        "breadcrumb": [("IA générative", "/"), ("IA et service client", "/articles/ia-service-client-nuit/")],
    },
    "articles/ia-analyse-rapports-publicitaires/index.html": {
        "title": "Analyser ses rapports publicitaires avec l'IA | ePerformance",
        "description": "Comment faire lire un export publicitaire à un outil d'IA : ce qui a bougé d'un mois sur l'autre, et pourquoi un résumé de données fausses est pire qu'aucun.",
        "fragment": "articles-ia-analyse-rapports-publicitaires.html",
        "nav_active": "ia",
        "breadcrumb": [("IA générative", "/"), ("Analyser ses rapports publicitaires", "/articles/ia-analyse-rapports-publicitaires/")],
    },
    "articles/ia-preparation-commerciale/index.html": {
        "title": "Structurer une offre commerciale avec l'IA | ePerformance",
        "description": "Structurer une proposition commerciale en une heure : problème, périmètre, livrables, délais. Ce que l'IA rédige et ce qui doit rester de votre main.",
        "fragment": "articles-ia-preparation-commerciale.html",
        "nav_active": "ia",
        "breadcrumb": [("IA générative", "/"), ("Structurer une offre avec l'IA", "/articles/ia-preparation-commerciale/")],
    },
    "articles/ia-limites-business/index.html": {
        "title": "Ce que l'IA ne sait pas faire dans votre business",
        "description": "L'IA ignore votre marge, votre trésorerie et votre capacité de production. Elle amplifie ce que vous faites mal autant que ce que vous faites bien.",
        "fragment": "articles-ia-limites-business.html",
        "nav_active": "ia",
        "breadcrumb": [("IA générative", "/"), ("Ce que l'IA ne sait pas faire", "/articles/ia-limites-business/")],
    },
    "articles/ia-donnees-confidentialite/index.html": {
        "title": "Vos données et l'IA : ce qui sort, ce qui reste",
        "description": "Le trajet d'une donnée quand vous l'utilisez dans un outil en ligne : ce qui quitte votre entreprise, ce qui reste local, ce qu'il faut vérifier avant.",
        "fragment": "articles-ia-donnees-confidentialite.html",
        "nav_active": "ia",
        "breadcrumb": [("IA générative", "/"), ("Vos données et l'IA", "/articles/ia-donnees-confidentialite/")],
    },
    "articles/automatisation-marketing-debuter/index.html": {
        "title": 'Automatisation marketing : par où commencer | ePerformance',
        "description": "Commencer par la tâche qui coûte le plus d'heures, pas la plus spectaculaire. Comment la repérer, la mesurer et la traiter sans y passer plus de temps.",
        "fragment": "articles-automatisation-marketing-debuter.html",
        "nav_active": "automatisation",
        "breadcrumb": [("Automatisation", "/articles/automatisation-marketing-debuter/"), ("Par où commencer", "/articles/automatisation-marketing-debuter/")],
    },
    "articles/n8n-afrique-ouest/index.html": {
        "title": "n8n en Afrique de l'Ouest : pourquoi cet outil",
        "description": "n8n auto-hébergeable, connecteurs WhatsApp Business, réversibilité des workflows : ce que cela change localement, et pour qui ce n'est pas le bon choix.",
        "fragment": "articles-n8n-afrique-ouest.html",
        "nav_active": "automatisation",
        "breadcrumb": [("Automatisation", "/articles/automatisation-marketing-debuter/"), ("n8n en Afrique de l'Ouest", "/articles/n8n-afrique-ouest/")],
    },
    "articles/ia-generative-pme-africaine/index.html": {
        "title": "IA générative pour une PME africaine : trois tâches",
        "description": "Ce que l'IA générative fait vraiment pour une PME : trois tâches qu'elle fait mieux que vous, trois qu'elle ne fera jamais. Guide pratique.",
        "fragment": "articles-ia-generative-pme-africaine.html",
        "nav_active": "ia",
        "breadcrumb": [("IA générative", "/"), ("Qu'est-ce que l'IA générative pour une PME africaine", "/articles/ia-generative-pme-africaine/")],
    },
    "articles/calculer-cac-cote-ivoire/index.html": {
        "title": "Calculer son vrai CAC en Côte d'Ivoire (guide 2026)",
        "description": "Le CAC réel inclut la pub, les outils et votre temps. Méthode de calcul, exemple chiffré et 5 leviers pour le réduire.",
        "fragment": "articles-calculer-cac-cote-ivoire.html",
        "nav_active": "acquisition",
        "breadcrumb": [("Acquisition", "/acquisition/"), ("Calculer son vrai CAC", "/articles/calculer-cac-cote-ivoire/")],
    },
    "articles/site-web-professionnel-abidjan-guide/index.html": {
        "title": "Site web professionnel à Abidjan : 7 critères (2026)",
        "description": "Les 7 critères qui séparent un site rentable d'une carte de visite : vitesse, mobile, schema, capture de leads et SEO local.",
        "fragment": "articles-site-web-professionnel-abidjan-guide.html",
        "nav_active": "site-web",
        "breadcrumb": [("Site web", "/site-web/"), ("Site web professionnel à Abidjan", "/articles/site-web-professionnel-abidjan-guide/")],
    },
    "articles/seo-local-abidjan-guide/index.html": {
        "title": "SEO local à Abidjan : apparaître sur Google (guide 2026)",
        "description": "Les 7 étapes pour sortir dans le pack local Google à Abidjan : fiche, avis, citations ivoiriennes et contenu local.",
        "fragment": "articles-seo-local-abidjan-guide.html",
        "nav_active": "seo",
        "breadcrumb": [("SEO", "/seo/"), ("SEO local à Abidjan", "/articles/seo-local-abidjan-guide/")],
    },
}

# ---------------------------------------------------------------------------
# GABARIT — <head>
# ---------------------------------------------------------------------------

# Le thème est appliqué AVANT le premier rendu : aucun FOUC.
THEME_SCRIPT = """<script>
(function(){try{var t=localStorage.getItem('eperf-theme');
if(t!=='dark'&&t!=='light'){t='light';}
document.documentElement.setAttribute('data-theme',t);}catch(e){}})();
</script>"""


# Polices peintes au premier écran, auto-hébergées dans assets/fonts/.
# Les précharger garantit que le texte est peint dans la bonne police dès le
# premier rendu : sans cela le navigateur affiche d'abord le repli puis
# recompose — c'est ce qui produisait un CLS de 0,13 à la première visite.
FONT_PRELOADS = [
    'assets/fonts/cormorant-garamond-700.woff2',
    'assets/fonts/dm-sans-400.woff2',
]

# Les polices sont servies localement (assets/fonts/) : plus de requête tierce.


def head(page_key, meta):
    """Construit le <head> complet pour une page."""
    title = html.escape(meta["title"])
    desc = html.escape(meta.get("description", SITE_DESC), quote=True)
    canonical = f"{BASE_URL}/{page_key}" if page_key != "index.html" else f"{BASE_URL}/"
    og_type = "website"

    robots = ('<meta name="robots" content="noindex,follow">'
              if meta.get("noindex") else
              '<meta name="robots" content="index,follow,max-image-preview:large">')

    parts = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        THEME_SCRIPT,
        f"<title>{title}</title>",
        f'<meta name="description" content="{desc}">',
        robots,
        f'<link rel="canonical" href="{canonical}">',
        '<meta name="theme-color" content="#fdfcfa">',
        f'<meta name="author" content="K. Stéphane">',
        "",
        '<!-- Icônes -->',
        '<link rel="icon" href="/assets/img/favicon-32.png" sizes="32x32">',
        '<link rel="icon" href="/assets/img/favicon-16.png" sizes="16x16">',
        '<link rel="apple-touch-icon" href="/assets/img/icon-192.png">',
        "",
        '<!-- Open Graph -->',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        f'<meta property="og:locale" content="fr_CI">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{desc}">',
        f'<meta property="og:url" content="{canonical}">',
        f'<meta property="og:image" content="{BASE_URL}/assets/img/og-image.jpg">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="ePerformance — {html.escape(SITE_NAME)}">',
        "",
        '<!-- Twitter -->',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{title}">',
        f'<meta name="twitter:description" content="{desc}">',
        f'<meta name="twitter:image" content="{BASE_URL}/assets/img/og-image.jpg">',
        f'<meta name="twitter:creator" content="@eperformancepro">',
        "",
        '<!-- Polices : préconnexion, préchargement des deux polices critiques,',
        '     puis chargement non bloquant de la feuille complète -->',
        '<!-- Polices : auto-hébergées, déclarées dans eperf.css.',
        '     On précharge les deux graisses du premier écran pour que le',
        '     texte soit peint dans la bonne police dès le premier rendu. -->',
    ] + [
        f'<link rel="preload" as="font" type="font/woff2" crossorigin href="/{u}">'
        for u in FONT_PRELOADS
    ] + [
        '',
        "<!-- Design system : la MEME feuille que le site, a l'identique. -->",
        '<link rel="stylesheet" href="/assets/css/eperf.css">',
        "<!-- Composants editoriaux du blog : corps d'article, largeur de",
        "     lecture, cartes d'article. Ils consomment les jetons d'eperf.css",
        "     et ne redefinissent aucune couleur. -->",
        '<link rel="stylesheet" href="/assets/css/blog.css">',
    ]

    return "\n".join("  " + p if p else "" for p in parts)


# ---------------------------------------------------------------------------
# EN-TÊTE — une seule définition pour tout le site
#   (remplace les 7 variantes divergentes de l'ancien site)
# ---------------------------------------------------------------------------

def header(active=""):
    links = []
    for label, href, key in NAV:
        attrs = []
        if key == active:
            attrs.append('aria-current="page"')
        if href.startswith("http"):
            attrs.append('rel="noopener"')
        a = " ".join(attrs)
        cls = ' class="text-gold"' if key == "blog" else ""
        links.append(f'      <a href="{href}"{cls}{(" " + a) if a else ""}>{label}</a>'.replace('" >', '">'))
    nav = "\n".join(links)

    return f"""<a class="skip-link" href="#main">Aller au contenu</a>

<header class="site-header">
  <div class="container header-inner">

    <a class="logo" href="/" aria-label="ePerformance — accueil">
      <img class="logo-img-light" src="/assets/img/logo-light.webp"
           srcset="/assets/img/logo-light.webp 1x, /assets/img/logo-light@2x.webp 2x"
           width="182" height="30" alt="ePerformance" fetchpriority="high">
      <img class="logo-img-dark" src="/assets/img/logo-dark.webp"
           srcset="/assets/img/logo-dark.webp 1x, /assets/img/logo-dark@2x.webp 2x"
           width="188" height="30" alt="" aria-hidden="true">
    </a>

    <nav class="nav" id="primary-nav" aria-label="Navigation principale">
{nav}
    </nav>

    <div class="header-actions">
      <button class="theme-toggle" type="button" data-theme-toggle
              aria-pressed="false" aria-label="Activer le thème sombre">
        <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" aria-hidden="true">
          <circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>
        </svg>
        <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>
        </svg>
      </button>

      <a class="btn btn-outline btn-desktop" href="https://wa.me/2250151170666" data-cta="whatsapp"
         target="_blank" rel="noopener" aria-label="Écrire sur WhatsApp"><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.4 11.6a8.4 8.4 0 0 1-12.5 7.4L3.6 20.4l1.4-4.3A8.4 8.4 0 1 1 20.4 11.6z"/><path d="M9.4 9.2a4.6 4.6 0 0 0 5.4 5.4"/></svg> WhatsApp</a>

      <a class="btn btn-gold btn-desktop" href="https://eperformance.pro/diagnostic_eperformance.html">Diagnostic gratuit</a>

      <button class="nav-toggle" type="button" aria-expanded="false"
              aria-controls="primary-nav" aria-label="Ouvrir le menu">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" aria-hidden="true">
          <path d="M3 6h18M3 12h18M3 18h18"/>
        </svg>
      </button>
    </div>

  </div>
</header>"""


# ---------------------------------------------------------------------------
# PIED DE PAGE — une seule définition
# ---------------------------------------------------------------------------

def footer():
    cols = []
    for title, links in FOOTER_COLS:
        items = "\n".join(
            f'          <li><a href="{href}"{" rel=\"noopener\"" if href.startswith("http") else ""}>{html.escape(label)}</a></li>'
            for label, href in links
        )
        cols.append(f"""      <div class="footer-col">
        <h2>{title}</h2>
        <ul>
{items}
        </ul>
      </div>""")

    legal = " · ".join(
        f'<a href="{href}">{label}</a>' for label, href in LEGAL_LINKS
    )

    return f"""<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">

      <div class="footer-col">
        <img class="footer-logo logo-img-light" src="/assets/img/logo-light.webp"
             srcset="/assets/img/logo-light.webp 1x, /assets/img/logo-light@2x.webp 2x"
             width="152" height="25" alt="ePerformance" loading="lazy">
        <img class="footer-logo logo-img-dark" src="/assets/img/logo-dark.webp"
             srcset="/assets/img/logo-dark.webp 1x, /assets/img/logo-dark@2x.webp 2x"
             width="157" height="25" alt="" aria-hidden="true" loading="lazy">
        <p class="card-text mt-3" style="max-width:34ch">{html.escape(SITE_DESC)}</p>
      </div>

{chr(10).join(cols)}

    </div>

    <div class="footer-bottom">
      <p>© {YEAR} ePerformance — par K. Stéphane. Tous droits réservés.</p>
      <p>{legal}</p>
    </div>
  </div>
</footer>

<div class="sticky-cta">
  <a class="btn btn-gold" href="https://eperformance.pro/diagnostic_eperformance.html">Diagnostic gratuit</a>
  <a class="btn btn-wa" href="{WHATSAPP}" style="flex:0 0 auto" rel="noopener">WhatsApp</a>
</div>

<!-- Bouton WhatsApp flottant — desktop uniquement. Sur mobile la barre
     ci-dessus fait le travail, et le bas à droite est réservé au chatbot. -->
<a class="wa-float" href="https://wa.me/2250151170666" data-cta="whatsapp" target="_blank" rel="noopener"
   aria-label="Écrire sur WhatsApp">
  <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.4 11.6a8.4 8.4 0 0 1-12.5 7.4L3.6 20.4l1.4-4.3A8.4 8.4 0 1 1 20.4 11.6z"/><path d="M9.4 9.2a4.6 4.6 0 0 0 5.4 5.4"/></svg>
</a>"""


# ---------------------------------------------------------------------------
# BANDEAU DE CONSENTEMENT
#   Les traceurs ne se chargent QU'APRÈS consentement explicite.
# ---------------------------------------------------------------------------

CONSENT_BANNER = """<div class="consent" id="consent-banner" hidden>
  <div class="consent-inner">
    <div class="consent-text">
      <p><strong>Vous choisissez ce que nous mesurons.</strong></p>
      <p>Nous utilisons des traceurs pour comprendre comment le site est utilisé et pour
         mesurer nos campagnes. Aucun ne se déclenche avant votre accord.
         <a href="https://eperformance.pro/politique-confidentialite.html">Politique de confidentialité</a> ·
         <a href="https://eperformance.pro/cookies.html">En savoir plus</a></p>
    </div>
    <div class="consent-actions">
      <button type="button" class="btn btn-ghost" data-consent="refuse">Tout refuser</button>
      <button type="button" class="btn btn-outline" data-consent="customize">Paramétrer</button>
      <button type="button" class="btn btn-gold" data-consent="accept">Tout accepter</button>
    </div>
  </div>

  <div class="consent-detail" id="consent-detail" hidden>
    <fieldset class="fieldset">
      <legend>Vos préférences</legend>

      <label class="consent-row consent-row-locked">
        <input type="checkbox" checked disabled>
        <span>
          <strong>Nécessaires</strong>
          <span class="field-hint">Mémorisation de votre choix de thème et de vos préférences.
            Toujours actifs : le site ne peut pas fonctionner sans.</span>
        </span>
      </label>

      <label class="consent-row">
        <input type="checkbox" id="consent-analytics">
        <span>
          <strong>Mesure d'audience</strong>
          <span class="field-hint">Google Analytics 4 et Microsoft Clarity. Nous aide à voir
            quelles pages sont utiles et où les visiteurs abandonnent.</span>
        </span>
      </label>

      <label class="consent-row">
        <input type="checkbox" id="consent-ads">
        <span>
          <strong>Publicité</strong>
          <span class="field-hint">Meta Pixel. Mesure l'efficacité de nos campagnes
            Facebook et Instagram.</span>
        </span>
      </label>
    </fieldset>

    <div class="consent-actions">
      <button type="button" class="btn btn-outline" data-consent="back">Retour</button>
      <button type="button" class="btn btn-gold" data-consent="save">Enregistrer mes choix</button>
    </div>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# GRAPHE DE DONNÉES STRUCTURÉES — Organization + WebSite, une fois par page
#   Les entités sont reliées par @id pour que Google et les moteurs IA
#   comprennent qu'il s'agit de la même organisation.
# ---------------------------------------------------------------------------

def site_graph(page_key, meta):
    canonical = f"{BASE_URL}/{page_key}" if page_key != "index.html" else f"{BASE_URL}/"

    org = {
        "@type": "Organization",
        "@id": f"{BASE_URL}/#organization",
        "name": "ePerformance",
        "alternateName": "ePerformance par K. Stéphane",
        "url": BASE_URL,
        "email": EMAIL,
        "telephone": "+2250151170666",
        "founder": {
            "@type": "Person",
            "@id": f"{BASE_URL}/#founder",
            "name": "K. Stéphane",
            "jobTitle": "Fondateur, stratège acquisition",
            "url": f"{BASE_URL}/kstephane.html",
        },
        "areaServed": [
            {"@type": "Country", "name": "Côte d'Ivoire"},
            {"@type": "Country", "name": "Burkina Faso"},
            {"@type": "Place", "name": "Afrique de l'Ouest"},
        ],
        "knowsLanguage": "fr",
        "sameAs": ["https://blog.eperformance.pro/"],
    }

    # LocalBusiness : le ciblage Abidjan est explicite dans le contenu, il
    # manquait totalement du balisage. Il porte l'adresse de service.
    local = {
        "@type": "ProfessionalService",
        "@id": f"{BASE_URL}/#localbusiness",
        "name": "ePerformance",
        "description": SITE_DESC,
        "url": BASE_URL,
        "email": EMAIL,
        "telephone": "+2250151170666",
        "parentOrganization": {"@id": f"{BASE_URL}/#organization"},
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Abidjan",
            "addressCountry": "CI",
        },
        "areaServed": {"@type": "Country", "name": "Côte d'Ivoire"},
        "priceRange": "100000-350000 XOF",
        "currenciesAccepted": "XOF",
        "paymentAccepted": "Orange Money, Wave, MTN MoMo, Moov Money, Visa, Mastercard",
        "availableLanguage": "fr",
    }

    website = {
        "@type": "WebSite",
        "@id": f"{BASE_URL}/#website",
        "url": BASE_URL,
        "name": "ePerformance",
        "description": SITE_DESC,
        "publisher": {"@id": f"{BASE_URL}/#organization"},
        "inLanguage": "fr-CI",
    }

    page = {
        "@type": "WebPage",
        "@id": f"{canonical}#webpage",
        "url": canonical,
        "name": meta["title"],
        "description": meta.get("description", SITE_DESC),
        "isPartOf": {"@id": f"{BASE_URL}/#website"},
        "about": {"@id": f"{BASE_URL}/#organization"},
        "inLanguage": "fr-CI",
    }

    graph = [org, local, website, page]

    if meta.get("breadcrumb"):
        items = [{"@type": "ListItem", "position": 1, "name": "Accueil", "item": f"{BASE_URL}/"}]
        for i, (name, href) in enumerate(meta["breadcrumb"], start=2):
            items.append({"@type": "ListItem", "position": i, "name": name,
                          "item": f"{BASE_URL}{href if href.startswith(chr(47)) else chr(47) + href}"})
        graph.append({
            "@type": "BreadcrumbList",
            "@id": f"{canonical}#breadcrumb",
            "itemListElement": items,
        })

    return {"@context": "https://schema.org", "@graph": graph}


def page_schema_blocks(page_key, meta):
    """Blocs JSON-LD additionnels fournis par le fragment de contenu."""
    frag_path = os.path.join(CONTENT, meta["fragment"])
    if not os.path.exists(frag_path):
        return [], ""
    raw = open(frag_path, encoding="utf-8").read()
    blocks = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.S
    )
    return blocks, raw


def strip_schema(raw):
    """Retire les blocs JSON-LD du fragment : ils sont remontés dans le <head>."""
    return re.sub(
        r'\s*<script[^>]*type="application/ld\+json"[^>]*>.*?</script>\s*', "\n", raw, flags=re.S
    ).strip()


# ---------------------------------------------------------------------------
# BREADCRUMB VISIBLE
# ---------------------------------------------------------------------------

def breadcrumb_html(meta):
    if not meta.get("breadcrumb"):
        return ""
    items = ['<li><a href="/">Accueil</a></li>']
    for i, (name, href) in enumerate(meta["breadcrumb"]):
        last = i == len(meta["breadcrumb"]) - 1
        if last:
            items.append(f'<li aria-current="page">{html.escape(name)}</li>')
        else:
            items.append(f'<li><a href="{href}">{html.escape(name)}</a></li>')
    return ('<nav class="breadcrumb container" aria-label="Fil d\'Ariane">\n'
            '  <ol>\n    ' + "\n    ".join(items) + "\n  </ol>\n</nav>")


# ---------------------------------------------------------------------------
# HÉROS DE PAGE — titre + chapô + CTA
# ---------------------------------------------------------------------------

def hero(meta):
    if not meta.get("h1"):
        return ""

    eyebrow = (f'      <span class="eyebrow">{html.escape(meta["eyebrow"])}</span>\n'
               if meta.get("eyebrow") else "")
    lead = (f'      <p class="lead mt-3">{html.escape(meta["lead"])}</p>\n'
            if meta.get("lead") else "")

    ctas = []
    if meta.get("cta"):
        label, href = meta["cta"]
        ctas.append(f'        <a class="btn btn-gold" href="{href}">{html.escape(label)}\n'
                    '          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" '
                    'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
                    'stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>\n'
                    '        </a>')
    if meta.get("cta2"):
        label, href = meta["cta2"]
        ctas.append(f'        <a class="btn btn-outline" href="{href}">{html.escape(label)}</a>')

    cta_block = ""
    if ctas:
        cta_block = ('      <div class="row mt-4" style="gap:12px;flex-wrap:wrap">\n'
                     + "\n".join(ctas) + "\n      </div>\n")

    return f"""  <section class="hero">
    <div class="container">
{eyebrow}      <h1 class="mt-3">{meta["h1"]}</h1>
{lead}{cta_block}    </div>
  </section>"""


# ---------------------------------------------------------------------------
# ASSEMBLAGE D'UNE PAGE
# ---------------------------------------------------------------------------

def compose_page(page_key, meta):
    # Les fragments peuvent référencer https://eperformance.pro : ils sont rendus ici.
    meta = dict(meta)
    frag_path = os.path.join(CONTENT, meta["fragment"])
    if not os.path.exists(frag_path):
        raise FileNotFoundError(f"fragment manquant : {frag_path}")

    schema_blocks, raw = page_schema_blocks(page_key, meta)
    body = strip_schema(raw)

    # JSON-LD : graphe de site + blocs propres à la page
    ld = [json.dumps(site_graph(page_key, meta), ensure_ascii=False, indent=2)]
    for b in schema_blocks:
        try:
            json.loads(b)                      # validation
            ld.append(b.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON-LD invalide dans {meta['fragment']} : {e}")

    ld_html = "\n".join(
        f'  <script type="application/ld+json">\n{b}\n  </script>' for b in ld
    )

    return f"""<!DOCTYPE html>
<html lang="fr" class="no-js" data-theme="light">
<head>
{head(page_key, meta)}
{ld_html}
</head>
<body>

{header(meta.get("nav_active", ""))}

{breadcrumb_html(meta)}

<main id="main">
{hero(meta)}

{body}
</main>

{footer()}

{CONSENT_BANNER}

<script src="/assets/js/consent.js" defer></script>
<script src="/assets/js/eperf.js" defer></script>
<script src="/assets/js/blog.js" defer></script>
</body>
</html>
"""



# ---------------------------------------------------------------------------
# CONTRÔLE DE COMPOSITION
#   Ce contrôle existe à cause d'un bug réel : la balise
#   <link rel="stylesheet" href="/assets/css/eperf.css"> a disparu du gabarit
#   lors d'une réécriture du <head>, et les 14 pages ont été régénérées sans
#   design system. Aucun test ne l'a vu, parce qu'aucun test ne vérifiait que
#   la page produite contenait réellement ses ressources.
#   Une page sans feuille de style reste du HTML parfaitement valide : seule
#   une vérification explicite peut l'attraper.
# ---------------------------------------------------------------------------

RESSOURCES_CRITIQUES = [
    ('assets/css/eperf.css',
     'la feuille du design system — sans elle la page n\'est pas stylée',
     '<link rel="stylesheet" href="/assets/css/eperf.css">'),
    ('/assets/js/consent.js',
     'le consentement — sans lui les traceurs ne se chargent pas du tout',
     '/assets/js/consent.js'),
    ('/assets/js/eperf.js',
     'le thème et les interactions',
     '/assets/js/eperf.js'),
    ('/assets/css/blog.css',
     "les composants éditoriaux du blog",
     'assets/css/blog.css'),
    ('assets/js/blog.js',
     "le partage d'article, seul script propre au blog",
     'assets/js/blog.js'),
]


def controler(page_key, html_produit):
    """Vérifie qu'une page contient bien ses ressources. Renvoie une liste
    de problèmes, vide si tout va bien."""
    problemes = []
    for chemin, role, motif in RESSOURCES_CRITIQUES:
        if motif not in html_produit:
            problemes.append(f"balise absente du HTML : {role}")
        if not os.path.exists(os.path.join(PREVIEW, chemin.lstrip("/"))):
            problemes.append(f"fichier introuvable sur disque : {chemin}")
    for police in FONT_PRELOADS:
        if police not in html_produit:
            problemes.append(f"police non préchargée : {police}")
        if not os.path.exists(os.path.join(PREVIEW, police)):
            problemes.append(f"fichier de police introuvable : {police}")
    if '<link rel="stylesheet"' not in html_produit:
        problemes.append("aucune feuille de style liée dans le <head>")
    return problemes


# ---------------------------------------------------------------------------
# PROGRAMME
# ---------------------------------------------------------------------------

def articles_differe():
    """Slugs des articles planifiés qui ne sont pas encore publiés.

    Lit _schedule.json : un article dont le drapeau published est faux n'est
    pas encore en ligne. Sa page est composée quand même — sinon les liens des
    articles déjà publiés vers lui casseraient — mais elle porte
    « noindex,follow » et reste hors du sitemap et de l'index. Un lien qui
    résout vers une page noindex vaut mieux qu'un lien vers une 404.
    """
    chemin = os.path.join(PREVIEW, "_schedule.json")
    if not os.path.exists(chemin):
        return set()
    with open(chemin, encoding="utf-8") as f:
        sched = json.load(f)
    return {a["slug"] for a in sched.get("articles", []) if not a.get("published")}


def main():
    ap = argparse.ArgumentParser(description="Compose les pages statiques ePerformance.")
    ap.add_argument("--check", action="store_true", help="vérifie sans écrire")
    ap.add_argument("--only", help="ne composer qu'une page (nom de fichier)")
    args = ap.parse_args()

    os.makedirs(PREVIEW, exist_ok=True)

    written, skipped, errors = 0, [], []
    differes = articles_differe()
    noindexes = 0

    for page_key, meta in PAGES.items():
        if args.only and page_key != args.only:
            continue
        meta = dict(meta)
        if page_key.startswith("articles/") and page_key.split("/")[1] in differes:
            meta["noindex"] = True
            noindexes += 1
        frag = os.path.join(CONTENT, meta["fragment"])
        if not os.path.exists(frag):
            skipped.append((page_key, meta["fragment"]))
            continue
        try:
            out = compose_page(page_key, meta)
        except Exception as e:
            errors.append((page_key, str(e)))
            continue
        problemes = controler(page_key, out)
        if problemes:
            errors.append((page_key, " ; ".join(problemes)))
            continue

        if not args.check:
            dest = os.path.join(PREVIEW, page_key)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(out)
        written += 1

    label = "vérifiées" if args.check else "écrites"
    print(f"  {written} page(s) {label}")
    if noindexes:
        print(f"  dont {noindexes} article(s) planifié(s) en noindex — hors sitemap, hors index")
    if written and not errors:
        print(f"  ressources vérifiées : feuille de style, JS, polices")

    if skipped:
        print(f"\n  Fragments absents ({len(skipped)}) :")
        for k, f in skipped:
            print(f"    {k:34} ← _content/{f}")

    if errors:
        print(f"\n  ERREURS ({len(errors)}) :")
        for k, e in errors:
            print(f"    {k} : {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
