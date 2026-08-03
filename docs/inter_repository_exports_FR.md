# SylvaPapers — Exports inter-dépôts

## 1. Objectif et responsabilités

Ce document définit la transmission stable par fichiers du dépôt SylvaPapers Modules A/B vers les
futurs dépôts séparés du Module D marketing et du Module E R&D. Le code aval doit dépendre de ces
fichiers et métadonnées, jamais de `sylvapapers_digital_twin`, `sylvapapers_maintenance` ou d'objets
d'exécution privés.

Le producteur est responsable des schémas, définitions et générations rétrocompatibles. Chaque
consommateur est responsable d'un validateur d'entrée strict, d'une zone brute immuable et de ses
tables analytiques dérivées.

## 2. Paquets d'export

| Fichier | Grain | Consommateur requis | Preuve décisionnelle principale |
|---|---|---|---|
| `campaign_runs.csv` | campagne × réplication | D et E | les 21 KPI, comptes, graine, horizon et durée d'exécution |
| `kpi_statistics.csv` | campagne × KPI | D et E | moyenne, dispersion, quantiles empiriques et IC95 de la moyenne |
| `module_d_product_statistics.csv` | campagne × réplication × produit | D | capacité de service, débit, retard, rejets, recyclage et perte finale |
| `module_e_machine_statistics.csv` | campagne × réplication × machine | E | charge, pannes, arrêts, maintenance, énergie, émissions et coût synthétique |
| `machine_decision_features.csv` | analyse × machine | D et E | risque de panne, RUL, politique, arrêt, coût et impact capacité |
| `maintenance_policy_costs.csv` | analyse × machine × politique | E facultatif | alternatives économiques corrective, préventive et prédictive |
| `machine_economic_priorities.csv` | modèle × machine | D et E | perte prédite, rang et bénéfice net attendu |
| `economic_model_feature_importance.csv` | modèle × variable | E | importance par permutation sur holdout |

Le paquet de campagne inclut aussi `campaign_metadata.json` et `column_dictionary.json`. Celui du
Module B inclut `module_b_manifest.json`. Ces fichiers JSON adjacents sont des preuves de contrôle
obligatoires même lorsque le modèle récepteur ne lit que les CSV.

Le paquet compact ajoute `handoff_manifest.json`, qui consigne chaque fichier copié, ses
consommateurs, sa taille, ses lignes et en-têtes CSV, ainsi que son empreinte SHA-256.

## 3. Identité, provenance et versions

| Champ ou document | Règle |
|---|---|
| `schema_version` | version sémantique d'échange ; valeur actuelle `1.0.0` |
| `producer_version` | version du générateur SylvaPapers ; valeur campagne actuelle `0.5.0` |
| `data_classification` | la baseline actuelle est `synthetic_hypothesis_not_calibrated` |
| `provenance` | identifie la simulation, le backtest temporel ou l'étape de variables décisionnelles |
| `campaign_id`, `scenario_id` | identité stable d'expérience ; ne jamais la déduire des noms de fichier |
| `replication`, `seed` | identité d'échantillon stochastique des tables de campagne |
| `source_schema_version`, `source_code_version` | filiation du Module B vers son paquet du Module A |
| `generated_at` | horodatage de génération dans les métadonnées ou le manifeste JSON adjacent |
| `analysis_reference_at` | date simulée à laquelle l'évaluation du Module B a été réalisée |

Un consommateur doit préserver ces champs sans modification dans sa couche brute. Les valeurs
synthétiques ne doivent jamais être renommées comme données observées ou étalonnées. Les sorties D/E
doivent conserver l'identité de campagne ou d'analyse source afin de relier une décision à un paquet
de simulation exact.

## 4. Unités et interprétation statistique

| Domaine | Unité ou interprétation canonique |
|---|---|
| quantité produite | `roll` ou `roll_equivalent` explicitement nommé |
| débit | `roll/hour` |
| durées simulées | `minute` ; la RUL utilise `operating_hour` ; le préavis utilise `calendar_hour` |
| probabilités, taux et impact capacité | ratio dans `[0, 1]`, jamais points de pourcentage |
| énergie | `kWh` |
| émissions | `kgCO2e`, estimation synthétique issue des facteurs configurés |
| coût machine, CA et manque à gagner | `EUR`, hypothèses synthétiques explicites et non données comptables |
| coût de politique Module B | devise déclarée par ligne et dans `module_b_manifest.json` |
| intervalle de confiance à 95 % | intervalle percentile bootstrap non paramétrique à graine fixe |

`column_dictionary.json` fait foi pour les types, unités et descriptions des colonnes de campagne. Un
intervalle de confiance à 95 % décrit l'incertitude de la moyenne des réplications simulées pour une
usine et un scénario fixes ; ce n'est pas une garantie de performance industrielle. La campagne de
référence contient 100 réplications de 2 000 jobs avec les graines 1000–1099.

## 5. Politique de compatibilité

| Changement | Action du consommateur |
|---|---|
| même version majeure, colonne ajoutée | accepter et ignorer ou mapper le champ additif inconnu |
| même version majeure, colonnes réordonnées | accepter par nom d'en-tête, jamais par position |
| même version majeure, colonne requise absente | rejeter le paquet avec une erreur de validation claire |
| unité, grain ou sens d'un champ modifié | exiger une nouvelle version de schéma et une migration explicite |
| version majeure différente | rejeter jusqu'à implémentation d'un adaptateur revu |
| dictionnaire, manifeste ou provenance absent | rejeter ; ne pas inventer les métadonnées |

Les CSV sont en UTF-8, avec une ligne d'en-tête et des cellules scalaires. Le producteur neutralise
les préfixes de formule tableur dans le texte, mais le consommateur doit traiter tout fichier copié
comme une entrée non fiable : borner taille et lignes, analyser strictement nombres et dates, rejeter
les clés logiques dupliquées et ne jamais exécuter le contenu d'une cellule.

## 6. Procédure de génération et copie

Exécuter d'abord la campagne, puis analyser l'échantillon du Module A délibérément sélectionné parce
qu'il contient des pannes. Cet échantillon sert à valider le Module B mais n'est pas statistiquement
représentatif.

```powershell
uv run sylvapapers campaign --config configs/campaigns/long_run.yaml --output outputs/long-run-statistics
uv run sylvapapers maintenance --input outputs/long-run-statistics/representative_module_a --output outputs/long-run-maintenance --config configs/maintenance/baseline.yaml
uv run sylvapapers economic-model --input outputs/long-run-statistics/module_e_machine_statistics.csv --output outputs/economic-model
uv run sylvapapers prepare-exchange --campaign outputs/long-run-statistics --maintenance outputs/long-run-maintenance --economic-model outputs/economic-model --output exports/sylvapapers-handoff-v2

$sylvaHandoff = Resolve-Path "exports/sylvapapers-handoff-v2"
$moduleDRepo = Resolve-Path "..\SylvaPapers-Module-D"
$moduleERepo = Resolve-Path "..\SylvaPapers-Module-E"

Copy-Item -LiteralPath "$sylvaHandoff\module_d_product_statistics.csv","$sylvaHandoff\kpi_statistics.csv","$sylvaHandoff\campaign_metadata.json","$sylvaHandoff\column_dictionary.json","$sylvaHandoff\machine_decision_features.csv","$sylvaHandoff\module_b_manifest.json","$sylvaHandoff\handoff_manifest.json" -Destination "$moduleDRepo\data\raw"
Copy-Item -LiteralPath "$sylvaHandoff\module_e_machine_statistics.csv","$sylvaHandoff\kpi_statistics.csv","$sylvaHandoff\campaign_metadata.json","$sylvaHandoff\column_dictionary.json","$sylvaHandoff\machine_decision_features.csv","$sylvaHandoff\maintenance_policy_costs.csv","$sylvaHandoff\temporal_validation_metrics.csv","$sylvaHandoff\probability_calibration.csv","$sylvaHandoff\module_b_manifest.json","$sylvaHandoff\handoff_manifest.json" -Destination "$moduleERepo\data\raw"
```

Créer les dossiers `data/raw` de destination dans leurs propres dépôts avant la copie. Ne pas
modifier les fichiers bruts après transfert. Consigner le commit Git source et l'heure de copie dans
le reçu d'import de chaque consommateur ; les métadonnées du producteur consignent déjà les empreintes
de configuration et l'environnement d'exécution.
La commande vérifie aussi les versions majeures, classifications et en-têtes CSV, puis consigne les
empreintes ; les validateurs aval doivent néanmoins revérifier les fichiers copiés.

## 7. Validation requise côté consommateur

1. Vérifier la présence de chaque fichier requis du paquet choisi.
2. Lire le dictionnaire ou manifeste adjacent avant d'analyser les lignes métier.
3. N'accepter que les versions majeures de `schema_version` prises en charge, consigner `producer_version` et vérifier la compatibilité CSV UTF-8 déclarée.
4. Contrôler colonnes requises, unités, bornes, clés logiques uniques et identités référentielles.
5. Confirmer l'accord de tous les fichiers sur l'identité source et la classification des données.
6. Persister une copie brute immuable et un reçu d'import avant de dériver des variables.
7. Séparer les hypothèses synthétiques de tout futur jeu observé ou étalonné.

Le Module D doit joindre statistiques produit et KPI par campagne/scénario/réplication et n'utiliser
les variables décisionnelles machine que comme contexte de risque capacité. Le Module E doit agréger
les preuves machine entre réplications avant de comparer les projets R&D et ne pas considérer une
politique de maintenance recommandée comme une intervention déjà exécutée.

## 8. Limites actuelles

- Le recyclage est une récupération de Bernoulli par `roll_equivalent`, de rendement 0,75 et limitée
  à deux boucles ; ce n'est pas un bilan continu de fibres, humidité ou cassés.
- La campagne ne change que les graines ; topologie d'usine et hypothèses de scénario sont communes.
- L'intervalle de confiance à 95 % utilise un bootstrap percentile à graine fixe sur 100 réplications synthétiques.
- Les fenêtres temporelles du Module B se chevauchent ; les fenêtres censurées à droite sont exclues
  de la confusion et de l'étalonnage, et les métriques à peu d'événements restent descriptives.
- Coûts, émissions, pannes, capteurs et paramètres économiques sont synthétiques et non étalonnés.
- Les dépôts séparés des Modules D et E et leurs validateurs d'entrée ne sont pas créés dans ce dépôt.
