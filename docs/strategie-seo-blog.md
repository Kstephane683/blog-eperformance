# Stratégie SEO du blog ePerformance

## 1. Le constat qui commande tout

L'analyse Search Console (`docs/analyse-search-console.md`) établit un fait : **le site n'a aucune requête métier**. Les 73 requêtes de l'export sont toutes des variantes orthographiques de « eperformance ». Zéro occurrence de `créer site web`, `facebook ads`, `calculer cac`, `seo local`.

Il n'y a donc rien à optimiser — il y a tout à construire. Les 78 articles ne capitalisent pas sur un acquis : ils créent la présence.

## 2. Séparation site / blog

| Le site cible | Le blog cible |
|---|---|
| Transactionnel : « création site web Abidjan » | Informationnel : « comment calculer », « pourquoi », « combien » |
| L'offre, le prix, le contact | La méthode, l'explication, la comparaison |

**Règle appliquée** : un titre de blog ne commence jamais par « Création de » et ne contient jamais de prix dans la balise.

Trois têtes sont déjà occupées par les articles existants et ne sont pas redoublées : `calculer cac côte d'ivoire`, `site web professionnel abidjan`, `seo local abidjan`.

## 3. Les six piliers

| Pilier | Articles | Rôle |
|---|---|---|
| ① Acquisition rentable | 20 | Le socle méthodologique — les 4 ratios |
| ② Site web | 14 | Choisir, budgéter, optimiser |
| ③ SEO & visibilité | 14 | Local, technique, AEO |
| ④ Business | 12 | Prix, trésorerie, modèle |
| ⑤ IA générative | 9 | Différenciation — aucune concurrence locale |
| ⑥ Automatisation | 9 | Différenciation — aucune concurrence locale |

Les piliers ⑤ et ⑥ correspondent aux pages de service `ia.html` et `automatisation.html`. Ils ouvrent le plan : ce sont les seuls territoires éditoriaux libres.

## 4. Ce que les données GSC changent

**Rien sur les priorités.** Il n'existe aucune requête à capter, donc aucune repriorisation n'est possible. La colonne Priorité du plan ordonne la production selon la difficulté et la valeur du sujet, pas selon un volume mesuré.

**Trois ajustements documentés :**

1. Le mobile performe 4× mieux que l'ordinateur (position 6,35 contre 25,35). Le contenu doit être conçu pour un téléphone d'entrée de gamme : paragraphes courts, pas de tableau large.
2. Les positions africaines sont excellentes (1,7 à 2,9) sur peu d'impressions. Trois articles transposables y sont renforcés : `pack local Ouagadougou`, `annuaires ivoiriens`, `vendre à la diaspora`.
3. Un article ajouté : « Comment se former à la publicité Meta quand on débute », qui comble l'absence de contenu sur les formations — `/formation.html` affiche 329 impressions et 0 clic.

## 5. AEO — être cité par les moteurs IA

| Pratique | Où |
|---|---|
| `robots.txt` autorisant 9 crawlers IA | `robots.txt` |
| FAQ en `<details>` avec réponses autoportantes | chaque article |
| `FAQPage` JSON-LD aligné sur le visible | chaque article |
| `llms.txt` | racine du blog |
| Entité cohérente (Organization + Person reliés par `@id`) | chaque page |

## 6. Indicateurs à suivre

| Indicateur | Où | Fréquence |
|---|---|---|
| Impressions par article | Search Console | mensuelle |
| Position moyenne sur le mot-clé principal | Search Console | mensuelle |
| Requêtes métier apparues (vs marque) | Search Console | mensuelle |
| Leads du diagnostic attribués au blog | GA4 | mensuelle |

**L'indicateur qui compte** : l'apparition de requêtes métier dans Search Console. Tant que l'export ne contient que des variantes de « eperformance », le blog n'a pas encore produit son effet.
