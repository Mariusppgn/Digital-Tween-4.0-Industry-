# Méthodologie scientifique

## 1. Objectif et niveau de preuve

Asteria Composites Lab est un environnement expérimental reproductible, non une représentation étalonnée d’une usine particulière. Il étudie comment flux de production, fiabilité des actifs, affectation des ressources, choix marketing et portefeuilles R&D interagissent sous des hypothèses synthétiques explicites. Les résultats servent à vérifier le logiciel et explorer des hypothèses jusqu’à comparaison avec des données industrielles approuvées.

Chaque sortie porte un niveau de preuve :

- **synthétique :** entièrement produite à partir d’hypothèses documentées ;
- **étalonnée :** certains paramètres ajustés sur un jeu traçable ;
- **validée :** évaluée sur des données indépendantes selon des critères prédéclarés.

Le premier jet est **synthétique**.

## 2. Questions de recherche et hypothèses

| Projet | Question de recherche | Hypothèse testable du premier jet |
|---|---|---|
| Jumeau numérique | Où files et variabilité limitent-elles le débit ? | Mise en lots autoclave, tampon fini et retouches créent des goulots mesurables |
| Maintenance prédictive | L’historique d’un actif permet-il de prioriser les interventions ? | Un modèle ensemencé de dégradation/panne classe les actifs à risque devant les témoins sains |
| Affectation des ressources | Peut-on affecter personnes et machines rares de façon faisable ? | Une affectation contrainte améliore l’objectif déclaré face à une référence simple sans violer la capacité |
| Optimisation marketing | Comment répartir un budget de campagne borné ? | L’optimisation améliore la contribution attendue face à une répartition uniforme, sous les mêmes hypothèses |
| Portefeuille R&D | Quels projets respectent budget et contraintes stratégiques ? | Une sélection contrainte surpasse une référence gloutonne par score sur la valeur attendue |
| Scénario intégré | Les recommandations inter-domaines sont-elles cohérentes ? | Des instantanés contractuels propagent de façon reproductible capacité et demande sans couplage des paquets |

Hypothèses, métriques et critères de rejet sont figés avant la comparaison.

## 3. Protocole expérimental commun

1. Définir référence, question, plages de facteurs, contraintes et métriques d’acceptation.
2. Valider les entrées avec `asteria_contracts` et figer un manifeste.
3. Dériver une graine aléatoire indépendante par module depuis une graine maître.
4. Exécuter référence et variantes avec les mêmes conditions exogènes.
5. Contrôler les invariants métier avant de calculer les KPI.
6. Répéter les cas stochastiques sur un ensemble de graines déclaré.
7. Rapporter taille d’effet, dispersion, échecs et limites.
8. Conserver configuration, résultats, versions et hachages comme artefacts immuables.

Changer l’hypothèse, la métrique ou une règle d’exclusion après observation des résultats crée une nouvelle expérience.

## 4. Méthode du jumeau numérique

### 4.1 Type de modèle

L’usine est une simulation à événements discrets terminante. Un calendrier avance le temps simulé jusqu’au prochain événement ; aucune attente réelle n’est utilisée. Les entités suivent :

`MP → découpe → l’un des deux postes de drapage parallèles → tampon fini → autoclave par lots → finition → CQ → conforme, retouche bornée ou rebut`.

Les ressources ont capacité, calendrier, réglages et état de panne. Les durées sont des distributions non négatives ensemencées. La discipline de file par défaut est FIFO avec départage déterministe. L’autoclave démarre selon capacité de lot et politique de libération déclarées. Le nombre de retouches a une limite forte.

### 4.2 Invariants et KPI

Pour chaque exécution terminée :

- la conservation des entités tient : libérées = en-cours + terminées + rebutées ;
- le temps des événements est monotone et aucune durée n’est négative ;
- l’occupation d’une ressource ne dépasse jamais sa capacité ;
- une entité n’occupe au plus qu’une ressource de traitement ;
- retouches et longueurs de file restent dans les bornes configurées.

Les KPI principaux sont débit, délai, encours, attente par poste, utilisation, remplissage autoclave, ponctualité, rendement premier passage, retouche et rebut. Périodes de chauffe et d’observation sont déclarées pour toute métrique de régime établi.

## 5. Méthode de maintenance prédictive

Le jeu synthétique d’actifs combine âge, heures de fonctionnement, charge, indicateurs de température/vibration, historique de maintenance et pannes ensemencées. Une référence transparente — règles à seuil ou classification régularisée — précède tout modèle complexe. Les séparations sont chronologiques ou par groupes d’actifs pour empêcher les observations d’un même épisode de panne de fuir entre apprentissage et test.

L’évaluation comprend précision, rappel, PR-AUC, calibration, préavis avant panne, fausses alertes par période et capacité de maintenance consommée. Le déséquilibre des classes est publié. Un score de risque ne garantit pas une durée de vie résiduelle et ne déclenche jamais automatiquement une commande équipement.

## 6. Méthode d’affectation des ressources

Le modèle déclare ressources, compétences, disponibilités, tâches, durées, priorités et compatibilités. Les contraintes fortes couvrent capacité, absence de chevauchement, éligibilité et couverture requise. L’objectif est une combinaison pondérée documentée telle que retard, déséquilibre d’utilisation, changements de série et demande non satisfaite.

Chaque optimiseur est comparé à une référence déterministe et renvoie faisabilité, composantes de l’objectif, contraintes actives et travail non affecté. Si aucune solution faisable n’existe, le système fournit un diagnostic minimal au lieu de relâcher silencieusement les contraintes.

## 7. Méthode d’optimisation marketing

Segments et canaux synthétiques portent bornes budgétaires, réponse attendue, marge unitaire, saturation et incertitude. L’expérience compare une référence uniforme ou de style historique à une affectation contrainte. Les résultats incluent contribution attendue, volume d’acquisition, dépense, rendement marginal et concentration par canal/segment.

Les fonctions de réponse sont des hypothèses de scénario, non des estimations causales. Aucun résultat n’est interprété comme preuve de marché sans expérience contrôlée ou méthode observationnelle approuvée. La sensibilité aux hypothèses de réponse et de marge est obligatoire.

## 8. Méthode de portefeuille R&D

Chaque projet candidat comporte coût, durée, valeur attendue, probabilité de succès, score stratégique, besoins en ressources, dépendances et exclusions. La sélection respecte contraintes de budget, capacité, prérequis et diversification. Les sorties séparent valeur attendue brute et pondération stratégique, et listent les projets rejetés avec leurs raisons actives.

La référence est une politique gloutonne ou par classement transparente. Coûts, valeurs et succès incertains sont propagés par scénarios ; le modèle ne masque pas les jugements de valeur dans un score unique inexpliqué.

## 9. Génération des données synthétiques

La génération suit un ordre causal : hypothèses de scénario → entités/événements latents → observations bruitées → valeurs manquantes/défauts → variables dérivées. Graines maître et dérivées sont conservées. Distributions, plages et corrélations par défaut résident dans une configuration versionnée. L’injection de défaut est optionnelle et consigne cible, début, durée et amplitude.

Les données synthétiques doivent contenir :

- identifiants stables et relations de clés étrangères valides ;
- unités, horodatages/temps simulé et provenance explicites ;
- déséquilibre réaliste des classes et bruit borné si pertinent ;
- cas limites de demande nulle, pleine capacité, arrêt, infaisabilité et retouche ;
- marqueur visible `source = synthetic`.

Les valeurs manquantes le restent dans les données brutes. L’imputation crée un jeu dérivé avec méthode et version.

## 10. Vérification et validation

La vérification logicielle précède la validation empirique :

- tests unitaires des calculs déterministes et cas frontières ;
- tests par propriétés pour conservation, bornes, temps monotone et faisabilité ;
- rejeu à graine fixe et hachages de résultats stables lorsque la sérialisation le permet ;
- micro-scénarios calculables à la main pour chaque module ;
- tests de sensibilité montrant la réponse directionnelle attendue ;
- tests d’intégration de tous les contrats échangés ;
- tests de terminaison des files, retouches et limites de temps d’optimisation.

La validation utilise des données séparées par temps, actif, lot ou campagne, jamais une division aléatoire de lignes adjacentes lorsqu’une fuite est possible. Métriques et seuils sont déclarés avant l’évaluation. Un tableau de bord plausible n’est pas une preuve de validation.

## 11. Plan d’expériences et incertitude

Les scénarios « un facteur à la fois » expliquent le comportement local ; les plans factoriels ou hypercubes latins explorent les interactions. Les facteurs intégrés minimaux incluent demande, variabilité des durées, intensité de panne, effectif de drapage, politique de lot autoclave, probabilité de défaut CQ, capacité maintenance, budget campagne et budget R&D.

Les sorties stochastiques sont rapportées sur plusieurs graines avec médiane, quantiles et intervalles de confiance lorsque justifiés. La sensibilité classe les hypothèses influentes sans revendiquer de causalité. Incertitudes de mesure, paramètres, forme du modèle et scénario sont distinguées. Les échecs sont comptés, non écartés sans explication.

## 12. Reproductibilité et provenance

Chaque exécution consigne identifiant d’expérience, entrées canoniques immuables, graines maître/dérivées, versions paquets et contrats, révision du code, empreinte dépendances/runtime, hachages des données, heures début/fin, avertissements, résultats des invariants, hachages de sortie et niveau de preuve. Les exports incluent un manifeste lisible par machine et une section de limites lisible.

L’identité exacte des flottants entre plateformes n’est pas promise. Les comparaisons utilisent tolérances documentées, équivalence de faisabilité et invariants distributionnels.

## 13. Limites et règles de promotion

Le premier jet exclut physique détaillée de cuisson, implantation spatiale de l’usine, facteurs humains, ruptures fournisseurs, inférence marketing causale, action automatique de maintenance et commande usine temps réel. Les optima synthétiques peuvent exploiter des hypothèses absentes du réel. La promotion de **synthétique** à **étalonné**, puis **validé**, exige données sources gouvernées, revue des fuites, évaluation indépendante, seuils prédéfinis et approbation du responsable industriel concerné. Toute modification significative des équations, contraintes, distributions ou définitions de KPI déclenche une nouvelle version du modèle et une revue d’impact de validation.
