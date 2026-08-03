# SylvaPapers — Contrats de données

## 1. Règles des contrats

`sylvapapers_contracts` utilise des modèles Pydantic v2 stricts. Les champs inconnus sont rejetés, les
versions suivent le format sémantique, la provenance distingue hypothèses synthétiques et preuves, et
les collections et nombres bornés réduisent les entrées mal formées ou excessives.

## 2. Contrats usine

| Contrat | Objectif | Validation principale |
|---|---|---|
| `FactoryConfig` | identité, types, machines, graphe et calendriers | IDs uniques et références valides |
| `MachineTypeConfig` | fiabilité partagée des équipements | type unique et densité Weibull |
| `FailureDensityConfig` | famille Weibull à deux paramètres | forme et échelle positives |
| `MachineConfig` | capacité et métadonnées d'un équipement | capacité positive et type déclaré |
| `ProcessGraph` | topologie éditable | nœuds uniques et arêtes non pendantes |
| `ProcessNode` | étape, matières et position | opération référençant des machines déclarées |
| `ProcessEdge` | relation matière orientée | source/cible valides et probabilité bornée |
| `RecyclingConfig` | rétroaction qualité contrôlée | une source QC, une opération amont cible, rendement et boucles bornées |

Les arêtes directes restent acycliques. Une seule arête explicitement typée `recycle` peut fermer la
boucle qualité contrôlée lorsque son `RecyclingConfig` est présent. Le rendement de référence est une
probabilité de Bernoulli par `roll_equivalent`, pas un coefficient de rendement massique continu.

## 3. Contrats scénario

| Contrat | Objectif | Validation principale |
|---|---|---|
| `ProductDefinition` | activation, recette, temps et nomenclature | valeurs positives ; gamme dérivable |
| `ProductionOrder` | demande datée de rouleaux | quantité positive bornée et dates valides |
| `SimulationScenario` | produits, commandes, graine et horizon | produits connus et actifs uniquement |

## 4. Contrats opérationnels du Module A

| Contrat | Objectif | Validation principale |
|---|---|---|
| `SimulationEvent` | journal unifié des événements | horodatage, identité et durée positive |
| `MachineState` | instantané d'état et utilisation | utilisation bornée et âge de marche positif |
| `SensorRecord` | observation machine multivariée | clés des valeurs et unités identiques et bornées |
| `FailureEvent` | résultat de panne et arrêt | gravité 1–5 et contexte capteur borné |
| `KPIReport` | métriques agrégées versionnées | noms, valeurs et unités explicites |

Le Module A persiste ces contrats dans `machine_states.csv`, `sensors.csv` et `failures.csv`, avec
maintenance, recyclage, files, encours, événements, jobs, KPI, résumé et état final dans le même
paquet.

## 5. Contrats d'échange de campagne du Module A

| Artefact | Grain | Rôle de compatibilité |
|---|---|---|
| `campaign_runs.csv` | réplication | valeurs des 15 KPI, comptes, graine, horizon et durée d'exécution |
| `kpi_statistics.csv` | KPI | n, moyenne, écart-type, quantiles et IC95 de la moyenne |
| `module_d_product_statistics.csv` | produit × réplication | preuves portables de capacité, service, perte et recyclage |
| `module_e_machine_statistics.csv` | machine × réplication | preuves portables d'utilisation, fiabilité, énergie, émissions et coût |
| `column_dictionary.json` | table et colonne | type, unité, description et déclaration de compatibilité CSV plat |

Ces CSV d'échange utilisent le schéma `1.0.0`, la version producteur `0.4.0`, UTF-8, une ligne
d'en-tête et des cellules scalaires. Chaque ligne porte `schema_version`, `producer_version`,
`data_classification`, `provenance`, `campaign_id` et `scenario_id` ; les tables répliquées portent
aussi `replication` et `seed`.

## 6. Contrats de configuration du Module B

| Contrat | Objectif | Validation principale |
|---|---|---|
| `MaintenanceAnalysisConfig` | horizon, seuils EWMA/CUSUM, classes d'étalonnage, confiance et densités | valeurs finies bornées et défauts Weibull explicites |
| `MaintenanceEconomicConfig` | hypothèses de coût corrective, préventive et prédictive | coûts/arrêts positifs et efficacité bornée |

La configuration de baseline est explicitement marquée `synthetic_example`. Devise, coûts et
paramètres d'efficacité ne peuvent pas être interprétés comme économie observée en papèterie.

## 7. Contrats de résultat du Module B

| Contrat | Objectif | Validation principale |
|---|---|---|
| `AnomalyResult` | anomalie EWMA ou CUSUM robuste et importance des variables | score positif et importance dans [0, 1] |
| `ReliabilityEstimate` | risque Weibull conditionnel et intervalle RUL | probabilités bornées et intervalle contenant l'estimation |
| `MaintenancePolicyCost` | coût et arrêt attendus d'une politique | politique nommée exactement et résultats positifs |
| `MaintenanceRecommendation` | action, urgence, fenêtre, confiance et raisons | fenêtre complète ordonnée et importance bornée |
| `MaintenanceAssessment` | agrégat décisionnel par machine | ID machine cohérent et trois politiques uniques |
| `TemporalPrediction` | prédiction à origine glissante, résultat et état de censure | cohérence résultat/censure et unités explicites à l'export |
| `TemporalValidationMetrics` | confusion temporelle, score de Brier et délai événementiel | comptes positifs et scores optionnels bornés |
| `ProbabilityCalibrationBin` | risque prédit face à la fréquence observée | bornes probabilistes ordonnées et classe non vide |

Le Module B persiste aussi les fichiers plats versionnés `temporal_predictions.csv`,
`temporal_validation_metrics.csv`, `probability_calibration.csv` et
`machine_decision_features.csv`. `module_b_manifest.json` consigne les versions sources, la
provenance, la classification, les unités, les fichiers et les limites pour les consommateurs situés
dans des dépôts séparés.

## 8. Contrats des futurs modules

`ProductionSchedule`, `MarketingPlan`, `DemandForecast`, `RDProject` et `RDPortfolio` restent
des frontières publiques versionnées pour les Modules C–E. Leur présence ne signifie pas que les
optimiseurs correspondants sont implémentés.

## 9. Règle d'interopérabilité

Les modules échangent des fichiers validés et modèles contractuels, pas des classes privées ou un état
mutable. Les identifiants techniques restent en anglais ; documentation et descriptions peuvent être
en français. Chaque champ numérique exige une unité explicite ou définie sans ambiguïté par le contrat.

Les Modules D et E seront des dépôts séparés. Ils doivent consommer les fichiers d'échange copiés
avec leur dictionnaire ou manifeste adjacent, rejeter les versions majeures incompatibles et ne
jamais importer les modules Python privés de ce dépôt. La transmission complète est définie dans
`inter_repository_exports_FR.md`.

## 10. Génération des schémas

```bash
uv run python -c "from sylvapapers_contracts import export_json_schemas; export_json_schemas('schemas')"
```

Les schémas générés sont des artefacts déterministes à régénérer après toute évolution de contrat.
