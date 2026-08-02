# SylvaPapers — Catalogue des modules

## 1. Contrats partagés

| Champ | Valeur |
|---|---|
| Objectif | Valider les échanges usine, production, fiabilité, maintenance et futurs modules. |
| Entrées | Configuration YAML/JSON et relevés de résultats persistés. |
| Sorties | Modèles typés stricts et schémas JSON. |
| Règle de dépendance | Aucun import depuis un module métier. |
| État | Implémenté et testé ; extensions préparées pour les Modules C–E. |

## 2. Module A — jumeau numérique

| Champ | Valeur |
|---|---|
| Objectif | Simuler la papèterie et produire des preuves opérationnelles et de condition auditables. |
| Entrées | Graphe, produits, commandes, graine, horizon et paramètres synthétiques. |
| Méthodes | Simulation à événements discrets, gammes NetworkX et fiabilité Weibull à deux paramètres. |
| Sorties | Événements, jobs, états, capteurs, pannes, maintenance, files, encours, KPI, figures et état final. |
| Budget | `fast` < 30 s pour une exécution simple ; `standard` < 2 min pour une étude mensuelle. |
| État | Baseline synthétique implémentée et testée. |

## 3. Module B — maintenance prédictive

| Champ | Valeur |
|---|---|
| Objectif | Classer le risque machine et comparer les politiques grâce aux preuves du Module A. |
| Entrées | États, capteurs, pannes, interventions, types de machine, horizon et coûts. |
| Méthodes | EWMA, seuil robuste, risque Weibull conditionnel, RUL et baselines économiques. |
| Sorties | Scores, alertes, risque, incertitude RUL, recommandations, coûts et figures. |
| Budget | `fast` < 30 s ; comparaisons research facultatives < 5 min par configuration par défaut. |
| État | Baseline synthétique interprétable implémentée et testée. |

## 4. Éditeur d'usine

| Champ | Valeur |
|---|---|
| Objectif | Éditer visuellement étapes, matières, machines, relations et coefficients Weibull. |
| Interface | Application web locale française avec support clavier. |
| Persistance | Import/export JSON validé et écriture YAML/JSON atomique explicite. |
| État | Implémenté et validé dans le navigateur. |

## 5. Module C — allocation des ressources

| Champ | Valeur |
|---|---|
| Objectif | Planifier production, opérateurs, techniciens et fenêtres de maintenance. |
| Entrées préparées | Commandes, états machine, capacités et recommandations du Module B. |
| Baseline prévue | Référence gloutonne puis comparaison CP-SAT ou MILP. |
| État | Contrats publics et relais A/B préparés ; optimiseur non implémenté. |

## 6. Module D — optimisation marketing

| Champ | Valeur |
|---|---|
| Objectif | Optimiser la demande sans dépasser la capacité réalisable de l'usine. |
| Entrées préparées | Demande, marges, service, coûts et capacité issus du Module A. |
| Baseline prévue | Modèle contribution saturation/adstock et allocation contrainte. |
| État | Contrats publics préparés ; modèle non implémenté. |

## 7. Module E — portefeuille R&D

| Champ | Valeur |
|---|---|
| Objectif | Sélectionner des améliorations de paramètres sous budget, ressources et incertitude. |
| Entrées préparées | Goulots et risques du Module A plus valeur marché du Module D. |
| Baseline prévue | Référence en valeur attendue, Monte Carlo et sélection multiobjectif. |
| État | Contrats publics préparés ; modèle non implémenté. |

## 8. Règle de séparation

Chaque module possède un problème métier, des entrées et sorties déclarées, des exemples, tests et
figures. Le monorepo est un choix de livraison, pas une permission d'import croisé incontrôlé. Une
future extraction préservera versions de schéma, unités, provenance et identifiants anglais techniques.
