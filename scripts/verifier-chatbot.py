#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Garde-fou : le bloc SDK du chatbot Mia doit être présent
  1. dans le layout du générateur `_build/compose.py` (source de vérité) ;
  2. dans CHAQUE page HTML déployée à la racine.

POURQUOI : le 18/09/2026, un commit a retiré le bloc SDK de 14 pages sur 16
(le générateur ne l'émettait pas) — le chatbot a disparu du site en production
sans qu'aucun contrôle ne le signale. Ce script est ce contrôle.

USAGE : python3 scripts/verifier-chatbot.py   → code 0 si conforme, 1 sinon.
Il est exécuté par le workflow .github/workflows/verifier-chatbot.yml à chaque
push, et disponible en pre-commit local.
"""
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
GENERATEUR = RACINE / "_build" / "compose.py"
MARQUEUR_SDK = "eperformance-sdk.js"
MARQUEUR_CONFIG = "window.ePerformanceConfig"

# Pages exclues du contrôle (gabarits, redirections)
EXCLUES = {"_content", "_templates", "assets", "scripts", "docs", "logs", ".github"}


def pages_deployees():
    """Toutes les pages du blog : racine + catégories/ + articles/<slug>/."""
    pages = [p for p in RACINE.rglob("*.html")]
    return sorted(
        p for p in pages
        if not any(part in EXCLUES or part.startswith(".") for part in p.parts)
    )



def main() -> int:
    erreurs = []

    # 1. Le générateur doit émettre le bloc (sinon toute regénération l'efface)
    if not GENERATEUR.exists():
        erreurs.append(f"générateur introuvable : {GENERATEUR}")
    else:
        source = GENERATEUR.read_text(encoding="utf-8")
        if MARQUEUR_SDK not in source:
            erreurs.append(
                "le layout du GÉNÉRATEUR (_build/compose.py) n'émet pas "
                "le bloc SDK → toute regénération effacera le chatbot"
            )
        # Les accolades doivent être échappées ({{ }}) dans le f-string
        if re.search(r"window\.ePerformanceConfig = \{(\s|\n)", source):
            erreurs.append(
                "accolades NON échappées dans le layout : utiliser {{ }} "
                "(le layout est un f-string)"
            )

    # 2. Chaque page déployée doit porter le bloc
    manquantes = []
    for page in pages_deployees():
        contenu = page.read_text(encoding="utf-8")
        if MARQUEUR_SDK not in contenu or MARQUEUR_CONFIG not in contenu:
            manquantes.append(page.name)

    if manquantes:
        erreurs.append(
            f"{len(manquantes)} page(s) sans bloc SDK : {', '.join(manquantes)}"
        )

    total = len(pages_deployees())
    if erreurs:
        print("❌ CONTRÔLE CHATBOT EN ÉCHEC")
        for e in erreurs:
            print(f"   • {e}")
        print("\n   → Le bloc est injecté par _build/compose.py : "
              "régénérez (python3 _build/compose.py) au lieu de "
              "retirer le bloc des pages.")
        return 1

    print(f"✅ Contrôle chatbot : {total}/{total} page(s) avec SDK "
          f"+ générateur conforme")
    print()
    print("📋 RAPPEL DE COORDINATION")
    print("   Ce dépôt partage le design system et le chatbot du site.")
    print("   Le document de coordination canonique est dans le dépôt du site :")
    print("   OX6A/site-eperformance/COORDINATION-AGENTS.md")
    print("   → le lire avant toute tâche touchant le layout ou les jetons.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
