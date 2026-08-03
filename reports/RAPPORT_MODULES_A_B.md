# Rapport de livraison — Modules A et B de SylvaPapers

Date de validation initiale : 2 août 2026
Extension longue durée et recyclage : 3 août 2026
Version : `0.4.0`
Branche : `feature/sylvapapers-modules-a-b`

## Répartition des travaux

| Chantier | Responsabilité | Résultat |
|---|---|---|
| Module A | compléter la simulation, les états, les capteurs, les pannes, la maintenance et les exports | terminé pour la baseline synthétique |
| Module B | construire l'analyse prédictive interprétable et l'interface A vers B | terminé pour la baseline synthétique |
| Documentation | aligner les guides anglais/français, la feuille de route et les limites | terminé |
| Intégration | ajouter la CLI, les contrats, les tests de bout en bout et vérifier les artefacts | terminé |

## Résultat exécutif

Les modules A et B forment maintenant une chaîne locale reproductible. Le Module A simule la
papeterie configurable SylvaPapers et produit un paquet de données versionné. Le Module B lit ce
paquet sans dépendre des détails internes du simulateur, estime les anomalies et le risque de panne,
calcule une durée de vie résiduelle, compare trois politiques de maintenance et produit des
recommandations explicables.

Cette livraison termine la **baseline synthétique exécutable sur ordinateur portable**. Elle ne
constitue pas une validation sur données industrielles et ne commande aucune machine réelle.

## Module A — éléments implémentés

- graphe orienté configurable du bois brut aux rouleaux de papier ;
- étapes en série, branches de recettes et machines physiques en parallèle ;
- trois produits activables et validation des produits désactivés ;
- édition web locale du graphe avec glisser-déposer, duplication, annuler/rétablir, auto-layout,
  validation et écriture explicite ;
- simulation à événements discrets avec graine reproductible ;
- âge de fonctionnement individuel des machines en heures ;
- densité de panne Weibull à deux paramètres par type de machine ;
- pannes, maintenance corrective et maintenance préventive configurable ;
- états machine et capteurs synthétiques horodatés ;
- mesure des files, encours, pertes terminales, énergie et coûts ;
- boucle qualité contrôlée vers la préparation de pâte, rendement Bernoulli synthétique 0,75 et deux passages maximum ;
- campagne 30 × 1 000 jobs, 15 KPI avec quantiles et IC95, et exports plats pour les futurs dépôts D/E ;
- état final et métadonnées décrivant explicitement les limites du modèle ;
- graphiques de débit, utilisation, KPI, Gantt, files et énergie.

Principaux artefacts produits :

- `events.csv`, `jobs.csv`, `machine_states.csv`, `sensors.csv` ;
- `failures.csv`, `maintenance.csv`, `recycling.csv`, `queues.csv`, `work_in_progress.csv` ;
- `kpis.json`, `summary.json`, `final_state.json` ;
- six figures PNG reproductibles.

## Module B — éléments implémentés

- chargement validé des fichiers finaux du Module A ;
- usage des capteurs, états machine, pannes et interventions de maintenance ;
- détection d'anomalie par EWMA et CUSUM bilatéral avec seuils robustes ;
- importance relative des variables pour chaque alerte ;
- probabilité conditionnelle de panne Weibull sur un horizon configurable ;
- RUL Weibull avec intervalle d'incertitude paramétrique ;
- recommandation par machine : politique, urgence, confiance, action et fenêtre d'intervention ;
- comparaison économique des politiques corrective, préventive et prédictive ;
- garde-fou conservateur lorsqu'une anomalie ou un risque élevé est détecté ;
- backtest à origine glissante sans fuite, censure à droite, confusion temporelle et calibration ;
- résultats JSON/CSV, cinq graphiques en français et manifeste pour consommateurs externes ;
- séparation nette des packages `sylvapapers_digital_twin` et `sylvapapers_maintenance`.

Interfaces publiques stables :

```python
from sylvapapers_maintenance import analyze_maintenance_bundle, save_maintenance_analysis
```

## Continuité entre A et B

```text
configuration validée
        ↓
Module A : simulation
        ↓ fichiers versionnés et validés
Module B : anomalie + Weibull + économie
        ↓
recommandation consultative soumise à validation humaine
```

Le Module B ne modifie ni les sorties du Module A, ni la configuration de l'usine. Cette frontière
prépare l'ajout du Module C : celui-ci pourra consommer les recommandations et fenêtres
d'intervention, puis proposer un planning qui sera rejoué dans le Module A.

## Validation effectuée

| Contrôle | Résultat |
|---|---|
| Tests automatisés complets | 49 réussis |
| Ruff | réussi |
| Format Ruff | réussi |
| mypy strict | réussi sur 22 modules source |
| Validation de la configuration | graphe valide, 20 nœuds, 22 relations, aucun cycle |
| Intégration réelle A vers B | réussie |
| Parité documentaire anglais/français | réussie |
| Contrôle visuel des figures principales | réussi |

Exécution de référence :

- 10 ordres produits, taux de service de 100 % ;
- 384 événements, 337 états machine et 150 relevés capteurs ;
- durée simulée de 671,06 minutes ;
- temps de calcul Module A d'environ 0,02 seconde sur l'environnement de validation ;
- 20 machines physiques évaluées par le Module B ;
- 9 alertes EWMA sur les données synthétiques.

Les neuf alertes ne mesurent pas une précision industrielle. Elles signalent surtout que le seuil
EWMA doit être ajusté sur un historique sain et représentatif avant toute interprétation métier.

## Commandes de test utilisateur

Depuis PowerShell, à la racine du dépôt :

```powershell
.\.venv_sylvapapers\Scripts\python.exe -m sylvapapers_digital_twin validate-config --config configs/scenarios/baseline.yaml
.\.venv_sylvapapers\Scripts\python.exe -m sylvapapers_digital_twin simulate --config configs/scenarios/baseline.yaml --output outputs/baseline
.\.venv_sylvapapers\Scripts\python.exe -m sylvapapers_digital_twin maintenance --input outputs/baseline --output outputs/maintenance --config configs/maintenance/baseline.yaml
.\.venv_sylvapapers\Scripts\python.exe -m sylvapapers_digital_twin report --input outputs/baseline --output reports/generated
```

Pour la suite complète de qualité :

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

## Éléments non implémentés

### Module A

- bilan massique continu en tonnes sèches, humidité et rendement matière ;
- application réelle des calendriers, équipes, compétences et capacités humaines ;
- contraintes de capacité des stocks ;
- tarification énergétique variable ;
- panne au milieu d'une opération avec politiques reprendre, recommencer ou rebuter ;
- durée de réparation probabiliste ;
- étalonnage des durées et coefficients sur une usine réelle.

### Module B

- estimation des paramètres Weibull à partir d'historiques censurés ;
- backtesting temporel, matrice de confusion temporelle et courbes de calibration ;
- comparaison CUSUM, Cox, espace d'état, forêt d'isolation ou méthodes conformes ;
- apprentissage à partir de l'historique de maintenance ;
- calibration industrielle des seuils, probabilités, coûts et fenêtres ;
- intégration GMAO, automate ou boucle de commande — volontairement hors périmètre actuel.

### Modules suivants

- Module C : allocation des ressources et co-planification production/maintenance ;
- Module D : marketing contraint par la capacité ;
- Module E : portefeuille R&D sous incertitude.

Les contrats de recommandations, de planning, de demande et de portefeuille existent déjà pour
préparer ces extensions sans coupler leurs implémentations aux modules A et B.

## Décision de livraison

Les Modules A et B sont acceptables comme démonstrateur scientifique synthétique, local et
reproductible. La prochaine étape recommandée est le Module C, après ajout des contraintes de
calendrier et de personnel dans le Module A. L'autre priorité est de constituer un historique sain et
documenté afin de calibrer le Module B avant d'ajouter des modèles plus complexes.
