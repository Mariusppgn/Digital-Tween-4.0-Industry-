# Catalogue des modules

## 1. `asteria-contracts`

| Dimension | Définition de la première livraison |
|---|---|
| Objectif | Fournir des contrats d’échange versionnés avec unités et provenance. |
| Entrées | Dictionnaires Python et documents YAML ou JSON. |
| Sorties | Objets Pydantic validés et schémas JSON. |
| Algorithmes de base | Validation Pydantic v2 et sérialisation déterministe. |
| Extensions avancées | Migration de compatibilité et validation sémantique entre versions de schéma. |
| Visualisations | Diagramme des relations entre contrats et matrice de couverture des schémas. |
| Dépendances | Pydantic et PyYAML uniquement ; aucune dépendance vers un package métier. |
| Critères de validation | Exemples positifs et négatifs, références, unités et export des 19 schémas. |
| Budget de calcul | Moins d’une seconde pour la configuration de référence. |

## 2. `asteria-digital-twin`

| Dimension | Définition de la première livraison |
|---|---|
| Objectif | Simuler l’usine de panneaux composites et produire les preuves opérationnelles partagées. |
| Entrées | Graphe usine, produits, commandes, calendriers, qualité, pannes, énergie et graine. |
| Sorties | Journal d’événements, historique des lots, KPI, métadonnées de reproductibilité et figures. |
| Algorithmes de base | Ordonnancement événementiel léger avec graine, capacités finies et reprise bornée. |
| Extensions avancées | Moteur SimPy, ensembles de scénarios, politiques robustes et dégradation calibrée. |
| Visualisations | Graphe, Gantt, files, production cumulée, utilisation, énergie et tableau de KPI. |
| Dépendances | `asteria-contracts`, NetworkX et Matplotlib ; SimPy est réservé au moteur enrichi. |
| Critères de validation | Déterminisme, topologie série/parallèle/reprise, capacités, valeurs non négatives et dix KPI. |
| Budget de calcul | Exécution fast sous 30 secondes ; réplications mensuelles standard sous 2 minutes. |

## 3. `asteria-predictive-maintenance`

| Dimension | Définition de la première livraison |
|---|---|
| Objectif | Estimer le risque de panne et comparer les politiques corrective, préventive et prédictive. |
| Entrées | Capteurs, cycles, charge, états machine, pannes, historique de maintenance et coûts. |
| Sorties | Scores d’anomalie, probabilités de panne, intervalles de RUL et recommandations. |
| Algorithmes de base | Seuils physiques, EWMA, CUSUM et survie Weibull. |
| Extensions avancées | Modèles de Cox, espace-état, prédiction conforme et boosting calibré. |
| Visualisations | Signaux annotés, survie/calibration, précision-rappel et comparaison des coûts de politiques. |
| Dépendances | `asteria-contracts` ; consomme les artefacts du jumeau sans importer ses composants internes. |
| Critères de validation | Découpage temporel, calibration, absence de fuite et gain de coût face aux politiques simples. |
| Budget de calcul | Apprentissage et évaluation standard sous 60 secondes ; recherche sous 5 minutes. |

## 4. `asteria-resource-allocation`

| Dimension | Définition de la première livraison |
|---|---|
| Objectif | Affecter de manière faisable opérateurs, techniciens, machines et fenêtres de maintenance. |
| Entrées | Commandes, gammes, compétences, calendriers, capacité, pannes prévues, priorités et énergie. |
| Sorties | Planning, affectations, créneaux de maintenance, retards, coût et indicateurs de robustesse. |
| Algorithmes de base | Ordonnanceur glouton faisable puis comparaison CP-SAT. |
| Extensions avancées | Optimisation robuste/par scénarios et recherche locale. |
| Visualisations | Gantt, heatmap des ressources, capacité-demande et frontière coût-retard. |
| Dépendances | `asteria-contracts` et OR-Tools ; le planning versionné est réinjecté dans le jumeau. |
| Critères de validation | Aucune violation dure et comparaison explicite avec la baseline gloutonne. |
| Budget de calcul | Baseline fast sous 10 secondes ; CP-SAT par défaut sous 2 minutes. |

## 5. `asteria-marketing-optimization`

| Dimension | Définition de la première livraison |
|---|---|
| Objectif | Allouer les dépenses marketing sans dépasser la capacité industrielle réalisable. |
| Entrées | Dépenses canal, demande, prix, saisonnalité, marge, budget, service et scénarios de capacité. |
| Sorties | Contribution, saturation, ROI, prévision de demande et recommandation budgétaire contrainte. |
| Algorithmes de base | Adstock, courbes de saturation et allocation non linéaire sous contraintes. |
| Extensions avancées | MMM bayésien, causalité, bandits contextuels et optimisation bayésienne. |
| Visualisations | Contributions, saturation/adstock, ROI et frontière revenu-capacité. |
| Dépendances | `asteria-contracts` ; consomme les KPI de capacité et émet des contrats de demande. |
| Critères de validation | Backtest, incertitude explicite et aucune recommandation hors garde-fous service/capacité. |
| Budget de calcul | Baseline standard sous 60 secondes ; exécution bayésienne facultative sous 5 minutes. |

## 6. `asteria-rd-portfolio`

| Dimension | Définition de la première livraison |
|---|---|
| Objectif | Sélectionner les projets R&D sous contraintes de budget, compétences, calendrier et risque. |
| Entrées | Projets, dépendances, compétences, probabilités, corrélations, KPI industriels et marché. |
| Sorties | Portefeuille, allocations, calendrier, valeur, risque, Pareto et coût d’opportunité. |
| Algorithmes de base | Programmation entière et simulation Monte-Carlo de VAN avec graine. |
| Extensions avancées | Optimisation multiobjectif robuste, options réelles et valeur de l’information. |
| Visualisations | Risque-rendement, Pareto, allocations budget/compétences, chronologie et tornado chart. |
| Dépendances | `asteria-contracts` ; consomme les artefacts jumeau et marketing sans imports directs. |
| Critères de validation | Dépendances et budgets faisables, stabilité par scénarios et comparaison au classement par valeur. |
| Budget de calcul | Portefeuille standard sous 60 secondes ; étude d’incertitude sous 5 minutes. |

## 7. Acceptation intermodules

- Chaque module reste exécutable indépendamment avec un petit exemple synthétique.
- Chaque artefact émis valide une version de schéma déclarée.
- Les méthodes avancées restent facultatives et sont comparées à la baseline documentée.
- Les exécutions intégrées enregistrent configuration, graines, versions, durée, métriques et sorties.

