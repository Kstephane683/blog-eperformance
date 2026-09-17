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
</div>"""


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

def main():
    ap = argparse.ArgumentParser(description="Compose les pages statiques ePerformance.")
    ap.add_argument("--check", action="store_true", help="vérifie sans écrire")
    ap.add_argument("--only", help="ne composer qu'une page (nom de fichier)")
    args = ap.parse_args()

    os.makedirs(PREVIEW, exist_ok=True)

    written, skipped, errors = 0, [], []

    for page_key, meta in PAGES.items():
        if args.only and page_key != args.only:
            continue
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
