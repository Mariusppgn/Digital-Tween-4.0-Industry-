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
maintenance, files, encours, événements, jobs, KPI, résumé et état final dans le même paquet.

## 5. Contrats de configuration du Module B

| Contrat | Objectif | Validation principale |
|---|---|---|
| `MaintenanceAnalysisConfig` | horizon, EWMA, seuil robuste, confiance et densités | valeurs finies bornées et défauts Weibull explicites |
| `MaintenanceEconomicConfig` | hypothèses de coût corrective, préventive et prédictive | coûts/arrêts positifs et efficacité bornée |

La configuration de baseline est explicitement marquée `synthetic_example`. Devise, coûts et
paramètres d'efficacité ne peuvent pas être interprétés comme économie observée en papèterie.

## 6. Contrats de résultat du Module B

| Contrat | Objectif | Validation principale |
|---|---|---|
| `AnomalyResult` | anomalie EWMA robuste et importance des variables | score positif et importance dans [0, 1] |
| `ReliabilityEstimate` | risque Weibull conditionnel et intervalle RUL | probabilités bornées et intervalle contenant l'estimation |
| `MaintenancePolicyCost` | coût et arrêt attendus d'une politique | politique nommée exactement et résultats positifs |
| `MaintenanceRecommendation` | action, urgence, fenêtre, confiance et raisons | fenêtre complète ordonnée et importance bornée |
| `MaintenanceAssessment` | agrégat décisionnel par machine | ID machine cohérent et trois politiques uniques |

Le Module B persiste `maintenance_assessments.json`, `maintenance_policy_costs.csv`,
`sensor_anomalies.png`, `failure_risk_rul.png` et `maintenance_policy_costs.png`.

## 7. Contrats des futurs modules

`ProductionSchedule`, `MarketingPlan`, `DemandForecast`, `RDProject` et `RDPortfolio` restent
des frontières publiques versionnées pour les Modules C–E. Leur présence ne signifie pas que les
optimiseurs correspondants sont implémentés.

## 8. Règle d'interopérabilité

Les modules échangent des fichiers validés et modèles contractuels, pas des classes privées ou un état
mutable. Les identifiants techniques restent en anglais ; documentation et descriptions peuvent être
en français. Chaque champ numérique exige une unité explicite ou définie sans ambiguïté par le contrat.

## 9. Génération des schémas

```bash
uv run python -c "from sylvapapers_contracts import export_json_schemas; export_json_schemas('schemas')"
```

Les schémas générés sont des artefacts déterministes à régénérer après toute évolution de contrat.
