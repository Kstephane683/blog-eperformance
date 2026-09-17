#!/usr/bin/env python3
"""
ePerformance — Bibliothèque d'illustrations SVG
preview/_build/illustrations.py

Direction artistique : docs/adr/ADR-0003-direction-artistique-illustrations.md

Une illustration ePerformance est un instrument de mesure, pas un dessin :
chaque trait est une graduation, une mesure ou une trajectoire.

Sept primitives, rien d'autre : cercle concentrique, arc gradué, barres
verticales, grille de points, segment en escalier, rectangle imbriqué,
diagonale.

Cinq règles, contrôlées par controler() :
  1. un seul accent or par illustration ;
  2. aucune couleur littérale — uniquement les jetons du thème ;
  3. grille de 4 px dans un viewBox 0 0 120 72 ;
  4. deux épaisseurs de trait : 1 (trame) et 1.5 (forme structurante) ;
  5. la trame est toujours partielle (jamais une grille pleine).

Trois tons, et trois seulement :
  - currentColor       → les formes et les trajectoires (le trait fort) ;
  - var(--border)      → la trame : grilles de points, graduations, axes,
                         liaisons et flèches — toujours discrète ;
  - currentColor/var(--gold-border) rempli sur UN SEUL élément : l'accent or.

`.card-figure` pose `color: var(--gold)` : currentColor suit donc le thème
clair/sombre sans qu'aucune valeur ne soit écrite en dur. L'accent est le seul
élément *rempli* de la composition — les autres sont des traits, jamais des
aplats (voir ADR, « pas de remplissage plein »).

Usage :
    from illustrations import ILLUSTRATIONS, controler
    for cle, svg in ILLUSTRATIONS.items():
        controler(svg, cle)
"""

import re


# ---------------------------------------------------------------------------
# JETONS ET RÈGLES
# ---------------------------------------------------------------------------

VIEWBOX = "0 0 120 72"
PAS = 4                       # pas de la grille, en unités du viewBox
EPAISSEURS = {"1", "1.5"}     # trame, forme structurante — jamais trois
JETONS = {"none", "currentColor", "var(--border)", "var(--gold-border)", "var(--gold-bg)"}
ACCENT_FILLS = {"currentColor", "var(--gold-border)"}
TAG_RACINE = "svg"

# Attributs porteurs de coordonnées, contrôlés un par un.
ATTRS_COORD = ("x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry",
               "width", "height", "points", "d")

# Commandes de tracé autorisées dans un attribut d, et leur arité.
ARITE_PATH = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Q": 4, "A": 7, "Z": 0}

INTERDITS = ("<style", "<defs", "<animate", "<use", "<image", "url(", "@keyframes")


class IllustrationInvalide(ValueError):
    """Une illustration viole la direction artistique."""


COULEUR_LITTERALE = re.compile(r"#[0-9a-fA-F]{3,6}")
BALISE = re.compile(r"<([a-zA-Z][a-zA-Z0-9-]*)\b([^>]*)>")
# Le nom d'attribut peut porter un chiffre : x1, y1, x2, y2 — sans quoi la
# grille de 4 ne serait jamais contrôlée sur les extrémités de trait.
ATTR = re.compile(r"([a-zA-Z][a-zA-Z0-9-]*)\s*=\s*\"([^\"]*)\"")
NOMBRE = re.compile(r"-?\d+(?:\.\d+)?")


# ---------------------------------------------------------------------------
# OUTILS DE LECTURE
# ---------------------------------------------------------------------------

def _elements(svg):
    """Rend [(nom, attributs)] pour chaque balise du document."""
    for m in BALISE.finditer(svg):
        nom = m.group(1).lower()
        attributs = dict(ATTR.findall(m.group(2)))
        yield nom, attributs


def _nombres(valeur):
    """Tous les nombres d'une valeur d'attribut."""
    return [float(n) for n in NOMBRE.findall(valeur)]


def _nombres_path(d):
    """Nombres d'un attribut `d`, drapeaux d'arc exclus.

    Les drapeaux (large-arc, sweep) valent 0 ou 1 : ce ne sont pas des
    coordonnées, les soumettre à la grille de 4 n'aurait pas de sens. Ils sont
    donc contrôlés séparément, et strictement.
    """
    jetons = re.findall(r"[A-Za-z]|-?\d+(?:\.\d+)?", d)
    nombres, commande, i = [], None, 0
    while i < len(jetons):
        jeton = jetons[i]
        if jeton.isalpha():
            commande = jeton.upper()
            if commande not in ARITE_PATH:
                raise IllustrationInvalide(f"commande de tracé interdite : {jeton}")
            i += 1
            continue
        if commande is None:
            raise IllustrationInvalide("attribut d sans commande de tracé")
        arite = ARITE_PATH[commande]
        if arite == 0:
            raise IllustrationInvalide(f"coordonnée après la commande {commande}")
        groupe = jetons[i:i + arite]
        if len(groupe) != arite:
            raise IllustrationInvalide("attribut d tronqué")
        for rang, valeur in enumerate(groupe):
            if not NOMBRE.fullmatch(valeur):
                raise IllustrationInvalide(f"attribut d illisible : {valeur}")
            if commande == "A" and rang in (3, 4):
                if valeur not in ("0", "1"):
                    raise IllustrationInvalide(f"drapeau d'arc hors 0/1 : {valeur}")
                continue
            nombres.append(float(valeur))
        i += arite
    return nombres


def _est_multiple(valeur):
    return abs(valeur / PAS - round(valeur / PAS)) < 1e-9


# ---------------------------------------------------------------------------
# CONTRÔLE
# ---------------------------------------------------------------------------

def controler(svg, cle="?"):
    """Vérifie les cinq règles. Lève IllustrationInvalide sinon.

    Ce contrôle n'est pas permissif : c'est lui qui garantit que vingt-cinq
    illustrations écrites à la main restent un seul et même langage.
    """
    def faute(message):
        raise IllustrationInvalide(f"[{cle}] {message}")

    if not isinstance(svg, str) or not svg.strip():
        faute("illustration vide")

    # --- Règle 2 : aucune couleur littérale --------------------------------
    litterale = COULEUR_LITTERALE.search(svg)
    if litterale:
        faute(f"couleur littérale interdite : {litterale.group(0)}")

    elements = list(_elements(svg))
    if not elements:
        faute("aucune balise")

    # --- Interdits absolus -------------------------------------------------
    for interdit in INTERDITS:
        if interdit in svg:
            faute(f"construction interdite : {interdit}")
    if re.search(r"stroke-dasharray\s*:", svg):
        faute("animation par tracé interdite")

    # --- Racine : viewBox, aria-hidden -------------------------------------
    nom_racine, attrs_racine = elements[0]
    if nom_racine != TAG_RACINE:
        faute("la racine doit être une balise <svg>")
    if attrs_racine.get("viewbox", attrs_racine.get("viewBox")) != VIEWBOX:
        faute(f'viewBox attendu "{VIEWBOX}"')
    if attrs_racine.get("aria-hidden") != "true":
        faute('aria-hidden="true" absent de la racine')
    if attrs_racine.get("class") != "card-figure-svg":
        faute('class="card-figure-svg" attendue sur la racine')

    # --- Règle 4 : deux épaisseurs, jamais trois ---------------------------
    epaisseurs = {a["stroke-width"] for _, a in elements if "stroke-width" in a}
    hors = epaisseurs - EPAISSEURS
    if hors:
        faute(f"épaisseur(s) hors barème : {', '.join(sorted(hors))}")
    if len(epaisseurs) > 2:
        faute(f"plus de deux épaisseurs de trait : {sorted(epaisseurs)}")

    # --- Accent or : un seul élément rempli --------------------------------
    accents = [a for nom, a in elements
               if nom != TAG_RACINE and a.get("fill", "none") in ACCENT_FILLS]
    if len(accents) != 1:
        faute(f"{len(accents)} accent(s) or — il en faut exactement un")

    # --- Règle 3 : grille de 4 px -----------------------------------------
    for nom, attrs in elements:
        for attribut in ATTRS_COORD:
            if attribut not in attrs:
                continue
            valeur = attrs[attribut]
            nombres = _nombres_path(valeur) if attribut == "d" else _nombres(valeur)
            if not nombres:
                faute(f"{nom} : attribut {attribut} sans coordonnée")
            for n in nombres:
                if not _est_multiple(n):
                    faute(f"{nom} : {attribut}=\"{valeur}\" — {n:g} hors grille de 4")

    # --- Jetons de couleur uniquement --------------------------------------
    for nom, attrs in elements:
        for attribut in ("stroke", "fill"):
            if attribut not in attrs:
                continue
            valeur = attrs[attribut]
            if valeur not in JETONS:
                faute(f"{nom} : {attribut}=\"{valeur}\" hors jetons du thème")

    # --- Règle 5 : la trame reste partielle --------------------------------
    # Une grille de points qui couvre toute la surface devient un aplat.
    points = [a for nom, a in elements
              if nom == "circle" and a.get("fill") == "var(--border)"]
    if len(points) > 12:
        faute(f"trame trop dense : {len(points)} points de grille")
    return True


# ---------------------------------------------------------------------------
# LES ILLUSTRATIONS
#   Clé = identifiant, valeur = SVG complet, prêt à insérer.
#   Toutes les coordonnées sont des multiples de 4 dans un viewBox 120 × 72.
# ---------------------------------------------------------------------------

ILLUSTRATIONS = {

    # -----------------------------------------------------------------------
    # ACCUEIL — LES 4 RATIOS
    # -----------------------------------------------------------------------

    # Barres décroissantes, la plus courte en or : le coût qu'on réduit.
    "ratio_cac": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="12" y1="56" x2="108" y2="56" stroke="var(--border)" stroke-width="1"/>
  <rect x="20" y="16" width="8" height="40" stroke="currentColor" stroke-width="1.5"/>
  <rect x="36" y="24" width="8" height="32" stroke="currentColor" stroke-width="1.5"/>
  <rect x="52" y="32" width="8" height="24" stroke="currentColor" stroke-width="1.5"/>
  <rect x="68" y="40" width="8" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="84" y="48" width="8" height="8" fill="currentColor"/>
</svg>''',

    # Barres ascendantes cumulées, la dernière en or : la valeur dans le temps.
    "ratio_ltv": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="12" y1="56" x2="108" y2="56" stroke="var(--border)" stroke-width="1"/>
  <polyline points="20 48 28 48 28 40 44 40 44 32 60 32 60 24 76 24 76 16 84 16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="20" y="48" width="8" height="8" stroke="currentColor" stroke-width="1.5"/>
  <rect x="36" y="40" width="8" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="52" y="32" width="8" height="24" stroke="currentColor" stroke-width="1.5"/>
  <rect x="68" y="24" width="8" height="32" stroke="currentColor" stroke-width="1.5"/>
  <rect x="84" y="16" width="8" height="40" fill="currentColor"/>
</svg>''',

    # Arc gradué, repère or à 60 % : le franchissement du seuil.
    "ratio_payback": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <path d="M 20 56 A 40 40 0 0 1 100 56" stroke="currentColor" stroke-width="1.5"/>
  <line x1="12" y1="56" x2="108" y2="56" stroke="var(--border)" stroke-width="1"/>
  <line x1="28" y1="32" x2="20" y2="32" stroke="var(--border)" stroke-width="1"/>
  <line x1="60" y1="16" x2="60" y2="8" stroke="var(--border)" stroke-width="1"/>
  <line x1="92" y1="32" x2="100" y2="32" stroke="var(--border)" stroke-width="1"/>
  <circle cx="72" cy="20" r="4" fill="currentColor"/>
</svg>''',

    # Deux rectangles imbriqués, la bande d'écart en or : ce qui reste.
    "ratio_marge": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <rect x="24" y="12" width="72" height="48" stroke="currentColor" stroke-width="1.5"/>
  <rect x="36" y="20" width="48" height="24" stroke="currentColor" stroke-width="1.5"/>
  <rect x="36" y="44" width="48" height="16" fill="var(--gold-border)" stroke="currentColor" stroke-width="1.5"/>
</svg>''',

    # -----------------------------------------------------------------------
    # ACCUEIL — LES 4 PILIERS
    # -----------------------------------------------------------------------

    # Cercles concentriques et un point hors de l'axe : l'écart à la cible.
    "pilier_strategie": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <circle cx="60" cy="36" r="28" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="60" cy="36" r="20" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="60" cy="36" r="12" stroke="currentColor" stroke-width="1.5"/>
  <line x1="56" y1="36" x2="64" y2="36" stroke="var(--border)" stroke-width="1"/>
  <line x1="60" y1="32" x2="60" y2="40" stroke="var(--border)" stroke-width="1"/>
  <line x1="60" y1="36" x2="88" y2="20" stroke="var(--border)" stroke-width="1"/>
  <circle cx="88" cy="20" r="4" fill="currentColor"/>
</svg>''',

    # Nœuds reliés, un seul en or, plus dense : la génération depuis un corpus.
    "pilier_ia": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <polyline points="24 24 48 12 72 20 96 28" stroke="var(--border)" stroke-width="1"/>
  <polyline points="24 24 36 48 60 60" stroke="var(--border)" stroke-width="1"/>
  <polyline points="48 12 60 36 96 28" stroke="var(--border)" stroke-width="1"/>
  <polyline points="36 48 60 36 88 48 72 20" stroke="var(--border)" stroke-width="1"/>
  <circle cx="24" cy="24" r="4" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="48" cy="12" r="4" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="72" cy="20" r="4" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="96" cy="28" r="4" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="36" cy="48" r="4" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="60" cy="60" r="4" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="88" cy="48" r="4" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="60" cy="36" r="4" fill="currentColor"/>
</svg>''',

    # Rectangles chaînés en cycle, un maillon en or : le cycle sans intervention.
    "pilier_automatisation": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="48" y1="20" x2="64" y2="20" stroke="var(--border)" stroke-width="1"/>
  <polyline points="64 16 72 20 64 24" stroke="var(--border)" stroke-width="1"/>
  <line x1="88" y1="28" x2="88" y2="36" stroke="var(--border)" stroke-width="1"/>
  <polyline points="84 36 88 44 92 36" stroke="var(--border)" stroke-width="1"/>
  <line x1="72" y1="52" x2="56" y2="52" stroke="var(--border)" stroke-width="1"/>
  <polyline points="56 48 48 52 56 56" stroke="var(--border)" stroke-width="1"/>
  <line x1="32" y1="44" x2="32" y2="36" stroke="var(--border)" stroke-width="1"/>
  <polyline points="28 36 32 28 36 36" stroke="var(--border)" stroke-width="1"/>
  <rect x="16" y="12" width="32" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="72" y="12" width="32" height="16" fill="currentColor"/>
  <rect x="72" y="44" width="32" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="16" y="44" width="32" height="16" stroke="currentColor" stroke-width="1.5"/>
</svg>''',

    # Grille modulaire, un module en or décalé vers le haut : la hiérarchie.
    "pilier_web": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="12" y1="68" x2="108" y2="68" stroke="var(--border)" stroke-width="1"/>
  <rect x="16" y="20" width="24" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="44" y="12" width="24" height="16" fill="currentColor"/>
  <rect x="72" y="20" width="24" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="16" y="44" width="24" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="44" y="44" width="24" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="72" y="44" width="24" height="16" stroke="currentColor" stroke-width="1.5"/>
</svg>''',

    # -----------------------------------------------------------------------
    # ACCUEIL — LA MÉTHODE (complexité croissante)
    # -----------------------------------------------------------------------

    # Une barre et un point : le plus simple.
    "methode_1": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="12" y1="56" x2="108" y2="56" stroke="var(--border)" stroke-width="1"/>
  <rect x="28" y="28" width="16" height="28" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="36" cy="20" r="4" fill="currentColor"/>
</svg>''',

    # Deux barres et une diagonale.
    "methode_2": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="12" y1="56" x2="108" y2="56" stroke="var(--border)" stroke-width="1"/>
  <rect x="20" y="36" width="16" height="20" stroke="currentColor" stroke-width="1.5"/>
  <rect x="44" y="24" width="16" height="32" stroke="currentColor" stroke-width="1.5"/>
  <line x1="68" y1="52" x2="96" y2="24" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="100" cy="20" r="4" fill="currentColor"/>
</svg>''',

    # Trois barres et une grille de points partielle.
    "methode_3": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="12" y1="56" x2="108" y2="56" stroke="var(--border)" stroke-width="1"/>
  <rect x="16" y="40" width="16" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="40" y="28" width="16" height="28" stroke="currentColor" stroke-width="1.5"/>
  <rect x="64" y="16" width="16" height="40" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="92" cy="16" r="4" fill="var(--border)"/>
  <circle cx="92" cy="36" r="4" fill="var(--border)"/>
  <circle cx="92" cy="56" r="4" fill="var(--border)"/>
  <circle cx="108" cy="36" r="4" fill="var(--border)"/>
  <circle cx="108" cy="56" r="4" fill="var(--border)"/>
  <circle cx="108" cy="16" r="4" fill="currentColor"/>
</svg>''',

    # Quatre barres, une diagonale et un escalier : l'accent sur la trajectoire.
    "methode_4": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="12" y1="56" x2="108" y2="56" stroke="var(--border)" stroke-width="1"/>
  <line x1="12" y1="52" x2="72" y2="12" stroke="var(--border)" stroke-width="1"/>
  <rect x="12" y="44" width="12" height="12" stroke="currentColor" stroke-width="1.5"/>
  <rect x="28" y="36" width="12" height="20" stroke="currentColor" stroke-width="1.5"/>
  <rect x="44" y="28" width="12" height="28" stroke="currentColor" stroke-width="1.5"/>
  <rect x="60" y="16" width="12" height="40" stroke="currentColor" stroke-width="1.5"/>
  <polyline points="80 48 88 48 88 40 96 40 96 32 104 32 104 24" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="104" cy="24" r="4" fill="currentColor"/>
</svg>''',

    # -----------------------------------------------------------------------
    # ACCUEIL — LES 3 FORMULES (modules empilés)
    # -----------------------------------------------------------------------

    "formule_1": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="24" y1="28" x2="24" y2="40" stroke="var(--border)" stroke-width="1"/>
  <rect x="36" y="28" width="48" height="12" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="24" cy="28" r="4" fill="currentColor"/>
</svg>''',

    "formule_2": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="24" y1="20" x2="24" y2="48" stroke="var(--border)" stroke-width="1"/>
  <rect x="36" y="20" width="48" height="12" stroke="currentColor" stroke-width="1.5"/>
  <rect x="36" y="36" width="48" height="12" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="24" cy="20" r="4" fill="currentColor"/>
</svg>''',

    "formule_3": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="24" y1="12" x2="24" y2="56" stroke="var(--border)" stroke-width="1"/>
  <rect x="36" y="12" width="48" height="12" fill="currentColor"/>
  <rect x="36" y="28" width="48" height="12" stroke="currentColor" stroke-width="1.5"/>
  <rect x="36" y="44" width="48" height="12" stroke="currentColor" stroke-width="1.5"/>
</svg>''',

    # -----------------------------------------------------------------------
    # LE CAS CLIENT — le résultat mesuré
    # -----------------------------------------------------------------------

    "cas_client": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="12" y1="56" x2="108" y2="56" stroke="var(--border)" stroke-width="1"/>
  <rect x="16" y="44" width="12" height="12" stroke="currentColor" stroke-width="1.5"/>
  <rect x="32" y="36" width="12" height="20" stroke="currentColor" stroke-width="1.5"/>
  <rect x="48" y="28" width="12" height="28" stroke="currentColor" stroke-width="1.5"/>
  <rect x="64" y="20" width="12" height="36" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="96" cy="20" r="4" fill="currentColor"/>
</svg>''',

    # -----------------------------------------------------------------------
    # AUTOMATISATION — 4 CAS D'USAGE
    # -----------------------------------------------------------------------

    # Une barre large en haut, trois barres fines qui convergent vers un point.
    "auto_capture": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <rect x="24" y="8" width="72" height="12" stroke="currentColor" stroke-width="1.5"/>
  <rect x="24" y="32" width="8" height="12" stroke="currentColor" stroke-width="1.5"/>
  <rect x="56" y="32" width="8" height="12" stroke="currentColor" stroke-width="1.5"/>
  <rect x="88" y="32" width="8" height="12" stroke="currentColor" stroke-width="1.5"/>
  <line x1="28" y1="44" x2="60" y2="60" stroke="var(--border)" stroke-width="1"/>
  <line x1="60" y1="44" x2="60" y2="60" stroke="var(--border)" stroke-width="1"/>
  <line x1="92" y1="44" x2="60" y2="60" stroke="var(--border)" stroke-width="1"/>
  <circle cx="60" cy="60" r="4" fill="currentColor"/>
</svg>''',

    # Trois rectangles en file, reliés par des flèches, le dernier en or.
    "auto_relance": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="36" y1="36" x2="40" y2="36" stroke="var(--border)" stroke-width="1"/>
  <polyline points="40 32 44 36 40 40" stroke="var(--border)" stroke-width="1"/>
  <line x1="72" y1="36" x2="76" y2="36" stroke="var(--border)" stroke-width="1"/>
  <polyline points="76 32 80 36 76 40" stroke="var(--border)" stroke-width="1"/>
  <rect x="8" y="24" width="28" height="24" stroke="currentColor" stroke-width="1.5"/>
  <rect x="44" y="24" width="28" height="24" stroke="currentColor" stroke-width="1.5"/>
  <rect x="80" y="24" width="28" height="24" fill="currentColor"/>
</svg>''',

    # Grille partielle de points sous un arc gradué, l'accent sur la fin.
    "auto_reporting": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <path d="M 16 32 A 68 68 0 0 1 104 32" stroke="currentColor" stroke-width="1.5"/>
  <line x1="36" y1="20" x2="32" y2="12" stroke="var(--border)" stroke-width="1"/>
  <line x1="60" y1="16" x2="60" y2="8" stroke="var(--border)" stroke-width="1"/>
  <line x1="84" y1="20" x2="88" y2="12" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="92" cy="12" r="4" fill="currentColor"/>
  <circle cx="24" cy="52" r="4" fill="var(--border)"/>
  <circle cx="40" cy="52" r="4" fill="var(--border)"/>
  <circle cx="56" cy="52" r="4" fill="var(--border)"/>
  <circle cx="72" cy="52" r="4" fill="var(--border)"/>
  <circle cx="24" cy="64" r="4" fill="var(--border)"/>
  <circle cx="40" cy="64" r="4" fill="var(--border)"/>
  <circle cx="56" cy="64" r="4" fill="var(--border)"/>
  <circle cx="72" cy="64" r="4" fill="var(--border)"/>
</svg>''',

    # Deux colonnes reliées par des diagonales croisées, jonction en or.
    "auto_sync": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="36" y1="16" x2="84" y2="56" stroke="var(--border)" stroke-width="1"/>
  <line x1="36" y1="56" x2="84" y2="16" stroke="var(--border)" stroke-width="1"/>
  <rect x="12" y="8" width="24" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="12" y="48" width="24" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="84" y="8" width="24" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="84" y="48" width="24" height="16" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="60" cy="36" r="4" fill="currentColor"/>
</svg>''',

    # -----------------------------------------------------------------------
    # IA — 4 CAS D'USAGE
    # -----------------------------------------------------------------------

    # Le corpus, trois lignes, trois sorties : la dernière en or.
    "ia_contenu": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="52" y1="28" x2="84" y2="16" stroke="var(--border)" stroke-width="1"/>
  <line x1="52" y1="36" x2="84" y2="36" stroke="var(--border)" stroke-width="1"/>
  <line x1="52" y1="44" x2="84" y2="56" stroke="var(--border)" stroke-width="1"/>
  <rect x="12" y="20" width="40" height="32" stroke="currentColor" stroke-width="1.5"/>
  <rect x="84" y="8" width="24" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="84" y="28" width="24" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="84" y="48" width="24" height="16" fill="currentColor"/>
</svg>''',

    # Cercle ouvert en arc, un point or à l'intérieur, grille partielle dehors.
    "ia_service": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <path d="M 72 20 A 20 20 0 1 0 80 36" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="16" cy="20" r="4" fill="var(--border)"/>
  <circle cx="16" cy="36" r="4" fill="var(--border)"/>
  <circle cx="16" cy="52" r="4" fill="var(--border)"/>
  <circle cx="104" cy="20" r="4" fill="var(--border)"/>
  <circle cx="104" cy="36" r="4" fill="var(--border)"/>
  <circle cx="104" cy="52" r="4" fill="var(--border)"/>
  <circle cx="60" cy="36" r="4" fill="currentColor"/>
</svg>''',

    # Barres surmontées d'une diagonale de tendance, point or à l'inflexion.
    "ia_analyse": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <line x1="12" y1="56" x2="108" y2="56" stroke="var(--border)" stroke-width="1"/>
  <line x1="16" y1="24" x2="104" y2="8" stroke="currentColor" stroke-width="1.5"/>
  <rect x="20" y="24" width="8" height="32" stroke="currentColor" stroke-width="1.5"/>
  <rect x="36" y="32" width="8" height="24" stroke="currentColor" stroke-width="1.5"/>
  <rect x="52" y="40" width="8" height="16" stroke="currentColor" stroke-width="1.5"/>
  <rect x="68" y="32" width="8" height="24" stroke="currentColor" stroke-width="1.5"/>
  <rect x="84" y="16" width="8" height="40" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="56" cy="36" r="4" fill="currentColor"/>
</svg>''',

    # Grille modulaire dont un module est remplacé par un escalier en or.
    "ia_prepa": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <rect x="20" y="8" width="24" height="24" stroke="currentColor" stroke-width="1.5"/>
  <rect x="76" y="8" width="24" height="24" stroke="currentColor" stroke-width="1.5"/>
  <rect x="20" y="36" width="24" height="24" stroke="currentColor" stroke-width="1.5"/>
  <rect x="48" y="36" width="24" height="24" stroke="currentColor" stroke-width="1.5"/>
  <rect x="76" y="36" width="24" height="24" stroke="currentColor" stroke-width="1.5"/>
  <polyline points="48 32 56 32 56 24 64 24 64 16 72 16" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="72" cy="16" r="4" fill="currentColor"/>
</svg>''',

    # -----------------------------------------------------------------------
    # BLOG — LE 4e PILIER ET LE REPÈRE D'ARTICLE
    # -----------------------------------------------------------------------

    # Grille de points partielle et diagonale descendante : le modèle économique.
    "pilier_business": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <circle cx="16" cy="16" r="4" fill="var(--border)"/>
  <circle cx="32" cy="16" r="4" fill="var(--border)"/>
  <circle cx="48" cy="16" r="4" fill="var(--border)"/>
  <circle cx="16" cy="32" r="4" fill="var(--border)"/>
  <circle cx="32" cy="32" r="4" fill="var(--border)"/>
  <circle cx="48" cy="32" r="4" fill="var(--border)"/>
  <circle cx="16" cy="48" r="4" fill="var(--border)"/>
  <circle cx="32" cy="48" r="4" fill="var(--border)"/>
  <circle cx="48" cy="48" r="4" fill="var(--border)"/>
  <line x1="36" y1="12" x2="104" y2="56" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="104" cy="56" r="4" fill="currentColor"/>
</svg>''',

    # Repère de lecture : trois marches, identique sur toutes les cartes.
    "article_repere": '''<svg class="card-figure-svg" viewBox="0 0 120 72" fill="none" aria-hidden="true" focusable="false">
  <polyline points="44 44 56 44 56 36 68 36 68 28 80 28" stroke="currentColor" stroke-width="1"/>
  <circle cx="84" cy="28" r="4" fill="currentColor"/>
</svg>''',
}


# ---------------------------------------------------------------------------
# VÉRIFICATION DE LA BIBLIOTHÈQUE
# ---------------------------------------------------------------------------

def verifier_tout():
    """Contrôle la bibliothèque entière. Rend la liste des identifiants."""
    for cle, svg in ILLUSTRATIONS.items():
        controler(svg, cle)
    return sorted(ILLUSTRATIONS)


if __name__ == "__main__":
    cles = verifier_tout()
    poids = sum(len(v) for v in ILLUSTRATIONS.values())
    print(f"  {len(cles)} illustrations conformes — {poids} octets au total")
