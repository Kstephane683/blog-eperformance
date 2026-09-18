#!/usr/bin/env python3
"""Vérifie que chaque page publiée contient tous les blocs critiques.

Né d'un incident : le 18 septembre 2026, un commit a recomposé les pages depuis
un générateur qui n'émettait pas le bloc SDK du chatbot, puis les a copiées vers
la racine. Le chatbot a disparu d'eperformance.pro en production.

La leçon : **recomposer ne met pas à jour les pages, il les régénère.** Tout ce
qui n'est pas émis par le générateur disparaît, y compris ce qui avait été
ajouté à la main dans les fichiers HTML.

Ce contrôle s'exécute sur les fichiers de la racine — ceux qui partent en
production — et non sur le preview. Il doit tourner AVANT toute copie vers la
racine, et il tourne en CI à chaque push.

Usage :
    python3 scripts/verifier-blocs-critiques.py          # contrôle
    python3 scripts/verifier-blocs-critiques.py --strict # code de sortie 1 si échec
"""
import argparse
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

# Chaque bloc : (nom, motif à trouver, pourquoi il compte)
BLOCS = [
    ("SDK chatbot",
     r"eperformance-sdk\.js",
     "sans lui le widget ne se charge pas — incident du 18/09/2026"),
    ("Configuration chatbot",
     r"ePerformanceConfig",
     "le SDK lit sa configuration dans cet objet"),
    ("Tracking",
     r"assets/js/tracking\.js",
     "sans lui aucune conversion ne remonte à GA4"),
    ("Consentement",
     r"assets/js/consent\.js",
     "sans lui les traceurs ne se chargent pas du tout"),
    ("Comportement",
     r"assets/js/eperf\.js",
     "thème et interactions"),
    ("Feuille de style",
     r"assets/css/eperf\.css",
     "sans elle la page n'est pas stylée"),
]

# Blocs attendus sur toutes les pages, mais qui peuvent manquer sur certaines
BLOCS_SOUPLES = [
    ("Bouton WhatsApp", r'data-cta="whatsapp"', "les pages sans CTA n'en ont pas"),
]


def pages_publiees():
    """Les pages de la racine, hors dossiers techniques et preview."""
    ignorees = {"preview", "_build", "_content", "_templates", "scripts",
                "docs", "assets", "node_modules", ".git", ".github"}
    pages = []
    for f in sorted(RACINE.rglob("*.html")):
        parties = set(f.relative_to(RACINE).parts[:-1])
        if parties & ignorees:
            continue
        # Les pages de redirection (dossier/index.html renvoyant vers la page
        # racine homonyme) ne portent ni feuille de style ni script : ce sont
        # des coquilles de réécriture d'URL, pas des pages.
        texte = f.read_text(encoding="utf-8")
        if len(texte) < 1200 and "http-equiv=\"refresh\"" in texte:
            continue
        pages.append(f)
    return pages


def controler():
    pages = pages_publiees()
    if not pages:
        return ["aucune page trouvée à la racine"], []

    manquants, souples = [], []
    for f in pages:
        s = f.read_text(encoding="utf-8")
        for nom, motif, raison in BLOCS:
            if not re.search(motif, s):
                manquants.append((str(f.relative_to(RACINE)), nom, raison))
        for nom, motif, _ in BLOCS_SOUPLES:
            if not re.search(motif, s):
                souples.append(str(f.relative_to(RACINE)))
    return manquants, souples


def controler_generateur():
    """Le générateur émet-il les blocs ? C'est la cause racine de l'incident."""
    compose = RACINE / "preview" / "_build" / "compose.py"
    if not compose.exists():
        return ["preview/_build/compose.py introuvable"]
    s = compose.read_text(encoding="utf-8")
    absents = []
    for nom, motif, _ in BLOCS:
        if not re.search(motif, s):
            absents.append(nom)
    return absents


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true",
                    help="code de sortie 1 si un bloc manque")
    args = ap.parse_args()

    manquants, souples = controler()
    gen = controler_generateur()
    pages = pages_publiees()

    print(f"  {len(pages)} page(s) publiée(s) contrôlée(s)")

    if gen:
        print(f"  ✗ GÉNÉRATEUR : bloc(s) non émis → {', '.join(gen)}")
        print("      Recommposer effacerait ces blocs des pages.")
    else:
        print("  ✓ générateur : émet tous les blocs critiques")

    # Deux pages ne passent pas par le composeur : merci-ebook.html et
    # merci-candidature.html. Elles datent d'avant la refonte, gardent leurs
    # propres styles, et — plus grave — chargent GA4 en dur sans passer par
    # consent.js. Elles ne sont donc pas une régression : ce sont des pages
    # à migrer. Les isoler évite de crier au loup à chaque contrôle.
    LEGACY = {"merci-ebook.html", "merci-candidature.html"}
    regression = [m for m in manquants if m[0] not in LEGACY]
    heritage = [m for m in manquants if m[0] in LEGACY]

    if regression:
        print(f"  ✗ {len(regression)} bloc(s) manquant(s) — RÉGRESSION :")
        for nom_page, bloc, raison in regression[:12]:
            print(f"      {nom_page} : {bloc} — {raison}")
    if heritage:
        pages_legacy = sorted({m[0] for m in heritage})
        print(f"  ⚠ {len(pages_legacy)} page(s) hors composeur, à migrer : {', '.join(pages_legacy)}")
        print("      Elles chargent GA4 en dur, sans consentement — défaut de conformité.")
    else:
        print(f"  ✓ pages : les {len(BLOCS)} blocs critiques sont présents partout")

    if souples:
        print(f"  · {len(souples)} page(s) sans bouton WhatsApp (normal hors CTA)")

    echec = bool(regression or gen)
    if echec:
        print()
        print("  NE PAS COPIER VERS LA RACINE. Corriger le générateur d'abord,")
        print("  puis recomposer et relancer ce contrôle.")
    else:
        print()
        print("  Publication sûre : les pages contiennent tous les blocs.")

    return 1 if (echec and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
