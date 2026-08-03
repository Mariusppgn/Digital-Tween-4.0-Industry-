# SylvaPapers — Rapport de livraison Usine

## Répartition des tâches

| Responsable | Mission | Résultat |
|---|---|---|
| Agent audit | Architecture existante, impacts de migration et risques | écarts du graphe déclaratif et inventaire de renommage identifiés |
| Agent modèle | Contrats, procédé papetier, trois produits et Weibull | configuration et tests métier livrés |
| Agent éditeur | Interface locale, interactions, validation et sécurité | éditeur web et tests livrés |
| Agent principal | Moteur, pertes, routage, migration, intégration, QA et Git | incréments consolidés et validés |

## Décisions confirmées

- entreprise fictive : **SylvaPapers** ;
- migration complète des packages, de la CLI, de la documentation et des rapports ;
- trois produits configurables, dont le carton désactivé par défaut ;
- branches de recette et machines redondantes ;
- entrées/sorties matière explicites ;
- boucle de recyclage qualité ajoutée ultérieurement : retour vers la préparation de pâte, rendement synthétique 0,75 et deux passages maximum ;
- pertes qualité mesurées ;
- densité Weibull à deux paramètres par type de machine ;
- âge exprimé en heures de fonctionnement ;
- éditeur web local français ;
- export et validation avant écriture explicite ;
- annuler/rétablir, duplication et auto-agencement.

## Usine livrée

Le graphe couvre le bois brut, l'écorçage, le déchiquetage, le stockage des copeaux, trois branches de
production de pâte, le lavage, l'épuration, le blanchiment facultatif, la préparation, le raffinage,
la formation, le pressage, le séchage, le calandrage, le bobinage, le contrôle qualité, les rouleaux
conformes et les pertes mesurées.

Chaque étape expose ses matières d'entrée et de sortie. Les branches `kraft`, `printing` et `board`
peuvent être sélectionnées par produit. Les positions de l'éditeur sont persistées dans le contrat.

## Fiabilité livrée

Chaque type de machine définit `shape` et `scale_hours`. Le simulateur suit l'âge de fonctionnement et
calcule la probabilité conditionnelle de panne sur chaque intervalle d'opération. Les événements restent
reproductibles à graine fixe. Les valeurs livrées sont explicitement synthétiques et non étalonnées.

## Éditeur livré

L'éditeur permet d'ajouter, déplacer, modifier, dupliquer et supprimer étapes et machines, de créer ou
supprimer des relations matière, de modifier les coefficients Weibull, d'annuler/rétablir, d'appliquer
un agencement simple et d'importer/exporter le contrat JSON. Le fichier source n'est écrit qu'après
validation locale et confirmation explicite.

## Validation effectuée

- tests unitaires et bout en bout ;
- Ruff ;
- mypy strict ;
- validation des structures documentaires EN/FR ;
- QA navigateur de l'éditeur ;
- contrôle responsive à 360 px ;
- contrôle de la console navigateur ;
- simulation de référence et génération des sorties.

## Reste hors du périmètre Usine actuel

La partie Usine demandée est fonctionnelle dans le périmètre du simulateur léger. Les extensions
suivantes restent des approfondissements, pas des défauts bloquants de cette livraison :

- bilans massiques continus en tonnes sèches et humidité ;
- application effective des calendriers ;
- panne au milieu d'une opération avec politique reprise/recommencement ;
- état de fiabilité totalement indépendant pour chaque instance d'un groupe parallèle ;
- calibration sur historiques industriels réels ;
- renommage du dépôt GitHub distant, qui demande une décision et une action externe séparées.

## Lancement

```bash
uv run sylvapapers validate-config --config configs/scenarios/baseline.yaml
uv run sylvapapers simulate --config configs/scenarios/baseline.yaml --output outputs/baseline
uv run sylvapapers factory-editor --factory configs/factory.yaml
```
