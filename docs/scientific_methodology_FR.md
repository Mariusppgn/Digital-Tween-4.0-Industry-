# SylvaPapers — Méthodologie scientifique

## 1. Positionnement

SylvaPapers est une expérience logicielle reproductible, pas un modèle étalonné d'une papèterie. Le
Module A teste un système de production synthétique ; le Module B teste des méthodes de maintenance
interprétables sur ses preuves synthétiques.

## 2. Reproductibilité

Chaque exécution déclare version de schéma, provenance, configuration, graine, horizon et chemin de
sortie. Des entrées A validées et une graine identiques reproduisent événements, états et capteurs.
Le Module B est déterministe pour un même paquet persisté et une même configuration de maintenance.

## 3. Expérience procédé du Module A

Le graphe représente transformations en série, recettes de pâte alternatives et machines redondantes.
Un produit peut déclarer sa gamme ou laisser le simulateur la déduire des conditions. Les routes
actives finissent en rouleaux acceptés ou pertes mesurées. Files et encours exposent l'accumulation,
tandis qu'un bilan continu en tonnes sèches reste hors de la baseline.

## 4. Expérience fiabilité du Module A

La famille Weibull à deux paramètres fait varier forme et échelle par type. La probabilité est
conditionnée par l'âge et la durée de l'intervalle. Dégradation, réparation et récupération de
maintenance sont des choix d'ingénierie synthétiques explicites. Les comparaisons font d'abord varier
un facteur avant les plans factoriels ou sensibilités.

## 5. Instrumentation du Module A

Les capteurs synthétiques dérivés des états couvrent charge, température, vibration, pression,
puissance, âge et dégradation. Chaque relevé possède unités et qualité. Une série constitue une preuve
sur l'état latent du simulateur, pas que la même relation existe sur une machine à papier réelle.

## 6. Expérience anomalie du Module B

EWMA pondère les observations récentes en gardant le contexte historique. Position et échelle robustes
réduisent l'influence des extrêmes isolés, et l'importance explique les canaux pilotant le score
récent. La validation doit employer des baselines chronologiques sans ajuster les seuils sur le futur.

## 7. Fiabilité et incertitude du Module B

Le risque Weibull conditionnel estime la probabilité entre l'âge courant et l'horizon choisi. La RUL
est en heures de marche avec intervalle d'incertitude. La validation utile inclut discrimination
temporelle, calibration probabiliste et couverture ; une petite démonstration synthétique ne suffit
pas à les revendiquer.

## 8. Expérience des politiques de maintenance

Les politiques corrective, préventive et prédictive sont comparées sous une configuration économique
synthétique explicite. La comparaison rapporte coût attendu, arrêt et probabilité d'intervention. Elle
n'optimise pas un planning réel et ne prouve aucune économie.

## 9. KPI et preuves visuelles

Le Module A rapporte production, service, cycle, utilisation, défauts, pertes, arrêts, coût, énergie,
OEE simplifié et retard. Le Module B rapporte anomalie, risque, RUL, recommandation et économie des
politiques. Les figures doivent être régénérées depuis les entrées sauvegardées et ne remplacent
jamais la validation contractuelle ou numérique.

## 10. Hiérarchie de validation

1. valider contrats, unités, références et provenance ;
2. valider accessibilité du graphe, activation produit et complétude des sorties ;
3. tester événements, états, capteurs déterministes et bornes KPI du Module A ;
4. tester formules anomalie, risque, RUL et politiques du Module B contre des baselines simples ;
5. tester aller-retour fichiers, rejet des entrées invalides et parité documentaire bilingue ;
6. mesurer séparément `fast`, `standard` et `research` ;
7. comparer les scénarios synthétiques après réussite des niveaux précédents ;
8. exiger un backtesting historique approuvé avant toute interprétation opérationnelle.

## 11. Porte des méthodes avancées

CUSUM, Cox, forêts d'isolation, espace-état, prédiction conforme et modèles RUL légers sont candidats,
pas des exigences de baseline. Une extension doit améliorer une métrique temporelle ou décision
économique déclarée, respecter le budget, préserver des preuves interprétables et conserver la
baseline simple pour comparaison.

## 12. Chemin d'étalonnage

Un usage opérationnel exige historiques procédé approuvés, pannes censurées, capteurs et maintenance
synchronisés, étiquettes qualité, comptage énergie et bilans matière. L'étalonnage doit conserver une
baseline synthétique distincte et documenter dérive des données, manquants, censure, incertitude et
règles de suivi du modèle.
