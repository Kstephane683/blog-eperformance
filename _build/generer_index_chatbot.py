#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère `chatbot-index.json` — source de vérité publique pour l'onglet Aide et
l'onglet Actualités du widget ePerformance.

POURQUOI CE FICHIER
-------------------
Le widget (iframe, dépôt eperformance-widget) doit lister les collections et
les articles du blog sans scraper le site à l'exécution (CORS, poids, fragilité).
Il récupère `https://blog.eperformance.pro/chatbot-index.json` (fetch) et, si
le fetch échoue, une copie embarquée dans son bundle. L'index est donc un
artefact PUBLIC, versionné avec le blog, régénéré à chaque composition.

RÈGLE ABSOLUE : LES ARTICLES NON PUBLIÉS NE FUIRENT PAS
-------------------------------------------------------
Un article est retenu si et seulement si :
  1. `_schedule.json` le marque `published: true` ;
  2. sa page ne porte pas `noindex` dans `<meta name="robots">`.
Les articles en avant-première (composés mais pas encore publiés) sont donc
exclus, même s'ils existent physiquement dans `articles/<slug>/`.

UTILISATION
-----------
    python3 _build/generer_index_chatbot.py                  # écrit chatbot-index.json
    python3 _build/generer_index_chatbot.py --copie-widget /chemin/vers/eperformance-widget
    python3 _build/generer_index_chatbot.py --check          # code 1 si l'index est périmé

--copie-widget écrit la même charge utile dans
`<widget>/src/data/chatbot-index.json` : c'est le repli embarqué du bundle
(le widget n'a aucune dépendance à ce dépôt, il embarque une copie figée).

DONNÉES LUES (aucune invention)
-------------------------------
- `_schedule.json`            → quels articles sont publiés (drapeau `published`)
- `articles/<slug>/index.html`→ `<title>`, `<meta name="description">`,
                                JSON-LD Article (`headline`, `datePublished`,
                                `articleSection`, `keywords`), `og:image`
- `acquisition|seo|site-web|business/index.html` → titre de la page de tête
  de collection (`<h1>`), quand elle existe

DATE RETENUE
------------
`datePublished` du JSON-LD de l'article (c'est la date que le blog affiche sur
ses propres cartes et sur la page de l'article), avec repli sur la date/heure
de `_schedule.json` si la page n'en déclare pas.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

RACINE = Path(__file__).resolve().parent.parent
BASE_URL = "https://blog.eperformance.pro/"

# Pages de tête de collection (les seules qui existent aujourd'hui).
# Le slug de collection d'un article est dérivé de sa section déclarée
# (JSON-LD `articleSection`) ; on rattache la page de tête quand son slug
# correspond. « Automatisation » et « IA générative » n'ont pas de page de
# tête : la collection existe quand même (section déclarée par l'article),
# simplement sans URL de collection.
PAGES_DE_TETE = {
    "acquisition": "Acquisition",
    "seo": "SEO",
    "site-web": "Site Web",
    "business": "Business",
}

# Image générique du blog : partagée par toutes les pages, elle n'est PAS
# l'aperçu d'un article → on ne la met pas dans `image` (l'onglet Actualités
# retombe alors sur l'icône SVG de la collection, comme les cartes du blog).
OG_GENERIQUE = "og-image.jpg"

RE_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
RE_DESC = re.compile(r'<meta\s+name="description"\s+content="(.*?)"', re.S | re.I)
RE_ROBOTS = re.compile(r'<meta\s+name="robots"\s+content="(.*?)"', re.S | re.I)
RE_OG_IMAGE = re.compile(r'<meta\s+property="og:image"\s+content="(.*?)"', re.S | re.I)
RE_CATEGORIE_CHIP = re.compile(r'class="article-category">(.*?)<', re.S)
RE_H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I)
RE_LD = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>', re.S | re.I
)
RE_TAGS_HTML = re.compile(r"<[^>]+>")


def lire(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


def texte_brut(fragment: str) -> str:
    """Retire les balises et décode les entités HTML."""
    return html.unescape(RE_TAGS_HTML.sub("", fragment)).strip()


def slugifier(valeur: str) -> str:
    """« IA générative » → « ia-generative » (mêmes slugs que les URL du blog)."""
    sans_accent = unicodedata.normalize("NFKD", valeur)
    sans_accent = "".join(c for c in sans_accent if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", sans_accent.lower()).strip("-")


def titre_propre(valeur: str) -> str:
    """Le `<title>` porte souvent un suffixe de marque : on le retire."""
    titre = texte_brut(valeur)
    for suffixe in (" | ePerformance", " — ePerformance", " - ePerformance"):
        if titre.endswith(suffixe):
            titre = titre[: -len(suffixe)]
    return titre.strip()


def bloc_article_jsonld(source: str) -> dict:
    """Renvoie le nœud JSON-LD `Article` de la page, ou {} s'il est absent."""
    for brut in RE_LD.findall(source):
        try:
            donnees = json.loads(brut)
        except json.JSONDecodeError:
            continue
        noeuds = donnees if isinstance(donnees, list) else [donnees]
        if isinstance(donnees, dict) and "@graph" in donnees:
            noeuds = donnees["@graph"]
        for noeud in noeuds:
            if isinstance(noeud, dict) and noeud.get("@type") == "Article":
                return noeud
    return {}


def lire_schedule() -> dict[str, dict]:
    """{slug: entrée de _schedule.json}"""
    donnees = json.loads(lire(RACINE / "_schedule.json"))
    return {article["slug"]: article for article in donnees.get("articles", [])}


def lire_collections() -> dict[str, dict]:
    """Titres des pages de tête existantes (jamais inventés)."""
    collections: dict[str, dict] = {}
    for slug, defaut in PAGES_DE_TETE.items():
        page = RACINE / slug / "index.html"
        if not page.exists():
            continue
        source = lire(page)
        trouve = RE_H1.search(source)
        titre = texte_brut(trouve.group(1)) if trouve else defaut
        collections[slug] = {
            "slug": slug,
            "titre": defaut,
            # Le <h1> des pages de tête est un slogan (« Ce que nous faisons ») :
            # on garde le libellé du blog (nav) et on expose l'URL de la page.
            "slogan": titre or None,
            "url": urljoin(BASE_URL, f"{slug}/"),
            "nombre": 0,
        }
    return collections


def lire_article(slug: str, schedule: dict[str, dict]) -> dict | None:
    """Construit l'entrée d'index d'un article publié, ou None s'il est exclu."""
    page = RACINE / "articles" / slug / "index.html"
    if not page.exists():
        return None

    source = lire(page)
    trouve_robots = RE_ROBOTS.search(source)
    robots = trouve_robots.group(1) if trouve_robots else ""
    if "noindex" in robots.lower():
        # Article en avant-première : jamais exposé au chatbot.
        return None

    jsonld = bloc_article_jsonld(source)
    section = jsonld.get("articleSection") or ""
    if not section:
        chip = RE_CATEGORIE_CHIP.search(source)
        section = texte_brut(chip.group(1)) if chip else ""

    titre = (
        jsonld.get("headline")
        or titre_propre((RE_TITLE.search(source) or [None, ""])[1])
        or slug.replace("-", " ").capitalize()
    )
    description = jsonld.get("description") or html.unescape(
        (RE_DESC.search(source) or [None, ""])[1]
    )

    # Date : celle que le blog affiche (JSON-LD), repli sur _schedule.json
    date = jsonld.get("datePublished") or ""
    if not date:
        entree = schedule.get(slug, {})
        date = f"{entree.get('date', '')}T{entree.get('heure', '00:00')}:00+00:00"
    date = date.strip()

    og = html.unescape((RE_OG_IMAGE.search(source) or [None, ""])[1] or "")
    image = og if og and OG_GENERIQUE not in og else None

    mots_cles = jsonld.get("keywords") or []
    if isinstance(mots_cles, str):
        mots_cles = [m.strip() for m in mots_cles.split(",") if m.strip()]

    return {
        "slug": slug,
        "titre": titre.strip(),
        "description": description.strip(),
        "collection": slugifier(section) if section else None,
        "collection_titre": section or None,
        "date": date,
        "url": urljoin(BASE_URL, f"articles/{slug}/"),
        "tags": [str(m) for m in mots_cles][:3],
        "image": image,
    }


def construire_index() -> dict:
    schedule = lire_schedule()
    articles = []
    for slug, entree in schedule.items():
        if not entree.get("published"):
            continue
        article = lire_article(slug, schedule)
        if article:
            articles.append(article)

    # Plus récentes d'abord (tri stable : la date, puis le slug)
    articles.sort(key=lambda a: (a["date"] or "", a["slug"]), reverse=True)

    collections = lire_collections()
    for article in articles:
        slug_collection = article["collection"]
        if not slug_collection:
            continue
        if slug_collection not in collections:
            # Section déclarée sans page de tête (ex. « IA générative ») :
            # la collection existe par les articles, sans URL de collection.
            collections[slug_collection] = {
                "slug": slug_collection,
                "titre": article["collection_titre"] or slug_collection,
                "slogan": None,
                "url": None,
                "nombre": 0,
            }
        collections[slug_collection]["nombre"] += 1

    liste_collections = [c for c in collections.values() if c["nombre"] > 0]
    liste_collections.sort(key=lambda c: (-c["nombre"], c["titre"]))

    return {
        "genere_le": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": BASE_URL,
        "collections": liste_collections,
        "articles": articles,
    }


def serialiser(index: dict) -> str:
    """JSON stable : `genere_le` en tête, reste indenté et trié."""
    return json.dumps(index, ensure_ascii=False, indent=2) + "\n"


def ecrire(chemin: Path, contenu: str) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8")
    print(f"  écrit : {chemin} ({chemin.stat().st_size} octets)")


def main() -> int:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument(
        "--copie-widget",
        type=Path,
        default=None,
        help="Dépôt du widget : y écrit src/data/chatbot-index.json (repli embarqué)",
    )
    parseur.add_argument(
        "--check",
        action="store_true",
        help="Ne rien écrire : échoue si chatbot-index.json est absent ou périmé",
    )
    args = parseur.parse_args()

    index = construire_index()
    # `genere_le` change à chaque exécution : on le neutralise pour comparer
    contenu = serialiser(index)
    cible = RACINE / "chatbot-index.json"

    if args.check:
        if not cible.exists():
            print("chatbot-index.json absent — lancer le script", file=sys.stderr)
            return 1
        existant = json.loads(lire(cible))
        existant.pop("genere_le", None)
        attendu = json.loads(contenu)
        attendu.pop("genere_le", None)
        if existant != attendu:
            print("chatbot-index.json périmé — relancer le script", file=sys.stderr)
            return 1
        print("chatbot-index.json à jour")
        return 0

    print(f"Articles publiés indexés : {len(index['articles'])}")
    for collection in index["collections"]:
        print(f"  - {collection['titre']} ({collection['nombre']})")
    ecrire(cible, contenu)

    if args.copie_widget:
        ecrire(args.copie_widget / "src" / "data" / "chatbot-index.json", contenu)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
