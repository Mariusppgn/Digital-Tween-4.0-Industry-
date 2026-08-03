# Rapport de complétude — Modules A et B longue durée

Date d'exécution de référence : 3 août 2026
Périmètre : SylvaPapers, baseline synthétique non étalonnée

## Répartition des agents

| Responsable | Mission | Résultat consolidé |
|---|---|---|
| Agent Module A | boucle qualité, conservation et instrumentation | rétroaction QC → préparation de pâte, recyclage borné et export détaillé |
| Agent campagne et interopérabilité | réplications longues, statistiques et tables D/E | campagne 30 × 1 000, 15 KPI, IC95 et CSV plats versionnés |
| Agent Module B | détection, validation temporelle et sorties décisionnelles | EWMA/CUSUM, censure, calibration, manifeste et variables machine |
| Agent documentation | contrats bilingues, transmission inter-dépôts et rapport | README/docs EN-FR alignés et procédure D/E documentée |
| Agent principal | continuité A → B, arbitrages et validation finale | consolidation du dépôt, campagne réelle et contrôles qualité |

## Conclusion

Les Modules A et B sont complets pour leur objectif actuel : produire, sur ordinateur portable, une
simulation papetière synthétique longue et reproductible, puis une analyse de maintenance
interprétable avec des fichiers d'échange stables. Cette complétude est logicielle et expérimentale ;
elle ne constitue ni une validation industrielle ni un étalonnage sur des mesures de papèterie.

La livraison prépare explicitement deux futurs dépôts indépendants : Module D marketing et Module E
R&D. Ceux-ci pourront consommer les CSV sans installer ni importer les packages Python internes de
SylvaPapers A/B.

## Fonctionnalités implémentées

### Module A — usine et recyclage

- graphe éditable bois brut → rouleaux, avec opérations en série, machines en parallèle et trois
  produits activables ;
- états physiques propres aux machines, densités de panne Weibull à deux paramètres et âge en heures
  de fonctionnement ;
- production à événements discrets avec graine, files, encours, capteurs synthétiques, pannes,
  maintenance, énergie, émissions estimées et coûts synthétiques ;
- boucle contrôlée de `quality-control` vers `stock-preparation` ;
- rendement de récupération configuré à `0.75`, appliqué comme Bernoulli avec graine par
  `roll_equivalent`, avec au plus deux boucles ;
- retraversée des opérations aval après récupération, perte finale après échec ou limite atteinte ;
- compteurs séparés de rejets qualité, tentatives, unités récupérées, débit recyclé interne et pertes
  finales, avec journal `recycling.csv` ;
- validation du graphe : arêtes directes acycliques et unique arête `recycle` explicitement bornée.

### Module A — campagne statistique

- commande `sylvapapers campaign` et configuration `configs/campaigns/long_run.yaml` ;
- 30 réplications déterministes, graines 1000 à 1029, 1 000 jobs par réplication ;
- arrivées espacées de 45 minutes et horizon du scénario étendu de 90 jours ;
- 15 KPI par réplication ;
- moyenne, écart-type échantillonnal, minimum, maximum, quantiles P05/P25/P50/P75/P95 ;
- intervalle de confiance à 95 % de la moyenne par approximation normale ;
- paquet détaillé du Module A conservé pour une réplication sélectionnée ;
- protection contre l'injection de formules dans les CSV.

### Module B — maintenance interprétable

- EWMA robuste et CUSUM bilatéral robuste ;
- risque de panne conditionnel Weibull et RUL en heures de fonctionnement avec intervalle ;
- recommandations par machine, justification, importance des variables et comparaison économique
  corrective/préventive/prédictive ;
- backtest à origine glissante : chaque prédiction n'utilise que le préfixe disponible à son heure ;
- recherche des pannes futures réservée à l'évaluation, sans fuite dans les variables ;
- marquage des fenêtres censurées à droite et exclusion de ces fenêtres des métriques de confusion et
  d'étalonnage ;
- TP, FP, TN, FN, précision, rappel, F1, Brier, rappel par événement et préavis d'alerte ;
- classes d'étalonnage comparant risque Weibull prédit et fréquence de panne observée ;
- export des prédictions, métriques, étalonnage et variables décisionnelles machine.

## Résultats mesurés de la campagne de référence

Environnement consigné par le paquet : Windows 11, Python 3.13.14. Les temps sont indicatifs de cette
exécution et ne sont pas un engagement de performance sur une autre machine.

| Mesure | Résultat |
|---|---:|
| Réplications | 30 |
| Jobs planifiés | 30 000 |
| Durée cumulée déclarée par les simulations | 49,75 s |
| Durée mur observée de la commande complète | environ 72 s |
| Réplications comportant au moins une panne | 8 sur 30 |
| Production acceptée moyenne | 978,733 rouleaux par réplication |
| Taux de service moyen | 97,8733 % |
| Perte matière finale moyenne | 2,1267 % |
| Tentatives de recyclage moyennes | 83,433 par réplication |
| Quantité récupérée moyenne | 62,3 `roll_equivalent` par réplication |
| Rendement de récupération réalisé moyen | 74,6511 % |
| Arrêt moyen | 36 min par réplication |
| Utilisation moyenne | 24,4351 % |
| OEE simplifié moyen | 22,5136 % |
| Énergie synthétique moyenne | 2 797 766,869 kWh par réplication |
| Coût synthétique moyen | 1 144 097,943 unités monétaires par réplication |

Le rendement réalisé est proche du paramètre 75 % sans lui être égal, comme attendu pour des tirages
de Bernoulli finis. L'IC95 de sa moyenne est `[72,9459 % ; 76,3563 %]`. L'IC95 de la production
acceptée moyenne est `[977,103 ; 980,364]` rouleaux et celui du taux de perte finale est
`[1,9636 % ; 2,2897 %]`.

La réplication 4, graine 1003, contient deux pannes et est conservée comme échantillon pour la
validation du Module B. Elle est sélectionnée précisément parce qu'elle porte des événements de
panne ; elle ne doit donc pas être décrite comme statistiquement représentative de la campagne.

## Résultats du backtest temporel du Module B

L'analyse de l'échantillon à deux pannes a produit 28 780 prédictions temporelles : 14 390 par
méthode, dont 12 942 évaluées et 1 448 censurées à droite. Son exécution murale locale a duré environ
144 secondes. Les résultats ci-dessous démontrent le fonctionnement du protocole sans fuite ; ils
montrent aussi qu'un étalonnage est indispensable avant tout usage décisionnel.

| Méthode | TP | FP | TN | FN | Précision | Rappel | F1 | Pannes détectées | Préavis moyen |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EWMA robuste | 115 | 2 316 | 10 399 | 112 | 4,7306 % | 50,6608 % | 8,6531 % | 1 sur 2 | 71,8579 h |
| CUSUM robuste | 227 | 12 679 | 36 | 0 | 1,7589 % | 100 % | 3,4569 % | 2 sur 2 | 71,5057 h |

CUSUM retrouve les deux événements mais déclenche presque continuellement dans cet échantillon ; sa
précision de 1,76 % est très insuffisante. EWMA réduit fortement les faux positifs mais manque une
panne et reste peu précis. Il ne faut donc pas choisir CUSUM sur son seul rappel ni EWMA sur son seul
nombre d'alertes : les seuils et la fonction de coût doivent être recalibrés sur des historiques plus
riches et séparés en apprentissage/validation.

L'étalonnage Weibull disponible ne contient qu'une classe non vide : probabilité moyenne prédite de
2,0720 % contre fréquence observée de 1,7540 %, avec score de Brier `0.01732146`. Ce point unique ne
permet pas de conclure à une bonne calibration sur toute l'échelle des risques.

## Fichiers prêts pour les futurs dépôts D et E

| Fichier | Destination | Usage principal |
|---|---|---|
| `campaign_runs.csv` | D et E | échantillons des 15 KPI par réplication |
| `kpi_statistics.csv` | D et E | agrégats, quantiles et IC95 |
| `module_d_product_statistics.csv` | D | capacité, service, débit, retard, rejet, recyclage et perte par produit |
| `module_e_machine_statistics.csv` | E | utilisation, pannes, maintenance, énergie, émissions et coût par machine |
| `machine_decision_features.csv` | D et E | risque, RUL, politique, arrêt, coût et disponibilité de capacité |
| `maintenance_policy_costs.csv` | E facultatif | comparaison économique détaillée par politique |
| `handoff_manifest.json` | D et E | inventaire compact, lignes, en-têtes et empreintes SHA-256 |

Les CSV sont plats, UTF-8, avec `schema_version=1.0.0` et `producer_version=0.4.0` pour la campagne.
Chaque ligne porte classification et provenance. Le
dictionnaire `column_dictionary.json`, les métadonnées `campaign_metadata.json` et le manifeste
`module_b_manifest.json` doivent accompagner toute copie. Le contrat et la procédure de consommation
sont détaillés dans `docs/inter_repository_exports_FR.md`.

La commande `prepare-exchange` rassemble ces fichiers dans `exports/sylvapapers-handoff-v1`, vérifie
la compatibilité des versions majeures et classifications, puis produit un manifeste de transfert.
Les sorties détaillées de diagnostic, notamment les 28 780 prédictions temporelles, restent dans les
répertoires de travail et ne gonflent pas inutilement le paquet destiné aux dépôts D/E.

## Ce qui n'est pas implémenté

- bilan massique continu en tonnes sèches, humidité, rendement fibre et conservation des cassés ;
- calibration des paramètres sur un historique industriel approuvé ;
- estimation Weibull statistique sur données multi-modes censurées ;
- pannes interrompant une opération avec politiques reprise/redémarrage/rebut ;
- contraintes complètes de calendriers, compétences, équipes et capacité de stock ;
- causalité des anomalies, modèles Cox, espace-état, conformes ou apprentissage automatique ;
- correction de dépendance statistique entre fenêtres temporelles chevauchantes ;
- validation hors échantillon sur une autre usine, une autre période ou des capteurs réels ;
- interfaces vers automate, GMAO, ERP ou actionneurs ;
- dépôts et moteurs d'optimisation des Modules D et E.

## Limites d'utilisation

Les valeurs de procédé, capteurs, pannes, maintenance, émissions et coûts sont des hypothèses
synthétiques non étalonnées. Les 30 réplications varient uniquement les graines : elles partagent la
même topologie et le même scénario. Les intervalles de confiance quantifient la variabilité du modèle
dans ce cadre fixe, pas l'incertitude totale d'une vraie papèterie.

Le Module B reste une aide à la décision. Ses métriques temporelles peuvent être descriptives lorsque
le nombre de pannes est faible, et ses fenêtres se chevauchent. Aucune recommandation n'est écrite
vers un équipement ou transformée automatiquement en ordre de maintenance.

## Commandes de reproduction

```powershell
uv sync --extra dev
uv run sylvapapers validate-config --config configs/scenarios/baseline.yaml
uv run sylvapapers campaign --config configs/campaigns/long_run.yaml --output outputs/long-run-statistics
uv run sylvapapers maintenance --input outputs/long-run-statistics/representative_module_a --output outputs/long-run-maintenance --config configs/maintenance/baseline.yaml
uv run sylvapapers prepare-exchange --campaign outputs/long-run-statistics --maintenance outputs/long-run-maintenance --output exports/sylvapapers-handoff-v1
uv run pytest
uv run ruff check .
uv run mypy
```

## Critère de passage vers les Modules D et E

Avant de commencer les nouveaux dépôts, figer les fichiers d'une campagne approuvée, enregistrer le
commit source et copier chaque CSV avec son dictionnaire ou manifeste. Chaque dépôt aval doit d'abord
implémenter et tester son validateur d'entrée `schema_version 1.x`, puis conserver les fichiers bruts
immuables. Aucun import de package interne A/B n'est autorisé à travers cette frontière.
