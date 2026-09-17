# Rapport de vérification — articles

**Contrôle :** `scripts/verify-articles.py`, exécuté sur chaque fragment avant composition.

## Ce que le script vérifie

| Contrôle | Seuil | Origine du seuil |
|---|---|---|
| Longueur du corps | 1 900 à 2 600 mots | Calibré sur les 3 articles en ligne (2 056 à 2 497) |
| Sections `h2` | 9 à 16 | Idem (9 à 15) |
| Questions FAQ | 5 à 8 | Idem (6 à 7) |
| Chapô `.lead` | 25 à 60 mots | Idem (31 à 41) |
| Schémas `Article`, `BreadcrumbList`, `FAQPage` | présents | Structure des articles existants |
| Validité JSON-LD | `json.loads` | — |
| Liens relatifs | aucun dans `href`, `src`, **`srcset`** | Bug réel : les `srcset` relatifs ont cassé les logos sur 9 pages |
| Formulations interdites | 13 motifs | Conformité Google Ads + anti-slop |
| CTA | présent | Diagnostic, WhatsApp ou page de service |

## Pourquoi les seuils sont calibrés et non estimés

La première version du script rejetait **les 3 articles en ligne**. Elle exigeait 4 à 8 sections `h2` et un chapô de 120 mots — des valeurs inventées. Un script qui rejette le standard existant a des seuils faux, pas le standard.

Après calibration : **3/3 articles de référence conformes**.

## Deux faux positifs corrigés

**« garanti » captait « la garantie ».** Le nom commun décrit une politique commerciale et est légitime dans une liste de questions fréquentes ; l'adjectif est une promesse interdite. Motif corrigé en `\bgarantis?\b` — le `\b` échoue entre « i » et « e », donc « garantie » n'est plus capté.

**`../` était signalé comme lien relatif.** Dans le fil d'Ariane des articles, `../` remonte de `/articles/xxx/` vers `/articles/` — il résout correctement. Exception ajoutée, comme dans les 3 articles en ligne.

## Résultats

| Passe | Résultat |
|---|---|
| Articles de référence (3) | **3/3 conformes** |
| Pilote : IA générative pour une PME africaine | **OK** — 2 391 mots, 14 H2, 6 FAQ |

## Ce que le script ne vérifie pas

**La qualité rédactionnelle.** Il contrôle la structure, la conformité et les liens ; il ne juge ni la pertinence de l'angle, ni la justesse des affirmations, ni le ton. Ces trois points demandent une relecture humaine.

**Le rendu visuel.** À contrôler dans le navigateur (`python3 -m http.server 8011`) : lisibilité en thème clair et sombre, comportement du sommaire, de la progression et des révélations.
