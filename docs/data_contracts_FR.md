# SylvaPapers — Contrats de données

## 1. Règles des contrats

`sylvapapers_contracts` utilise des modèles Pydantic v2 stricts. Les champs inconnus sont rejetés, les
versions suivent le format sémantique et la provenance distingue hypothèses synthétiques et preuves.

## 2. Contrats usine

| Contrat | Objectif | Validation principale |
|---|---|---|
| `FactoryConfig` | Identité, types, machines, graphe et calendriers | IDs uniques et références valides |
| `MachineTypeConfig` | Fiabilité partagée par type | type unique et densité Weibull |
| `FailureDensityConfig` | Famille Weibull à deux paramètres | forme et échelle positives |
| `MachineConfig` | Capacité et métadonnées d'un équipement | capacité positive et type déclaré |
| `ProcessGraph` | Topologie éditable | nœuds uniques et arêtes non pendantes |
| `ProcessNode` | Étape, matières et position | une opération référence des machines |
| `ProcessEdge` | Relation matière orientée | source/cible valides et probabilité bornée |

## 3. Contrats scénario

| Contrat | Objectif | Validation principale |
|---|---|---|
| `ProductDefinition` | Activation, recette, temps et nomenclature | valeurs positives ; gamme dérivable |
| `ProductionOrder` | Demande datée de rouleaux | quantité positive et échéance après libération |
| `SimulationScenario` | Produits, commandes, graine et horizon | produits connus et actifs uniquement |

## 4. Contrats opérationnels

Événements, états machine, capteurs, pannes, recommandations, plannings et rapports KPI restent des
contrats publics versionnés pour les futurs modules.

## 5. Interopérabilité de l'éditeur

L'éditeur importe et exporte la représentation JSON de `FactoryConfig`. Les coordonnées sont dans
`ProcessNode.position` ; les entrées et sorties sont des listes d'identifiants matière. Le serveur
n'écrit qu'après validation complète du contrat.

## 6. Génération des schémas

```bash
uv run python -c "from sylvapapers_contracts import export_json_schemas; export_json_schemas('schemas')"
```

Les schémas générés sont des artefacts déterministes à régénérer après toute évolution de contrat.
