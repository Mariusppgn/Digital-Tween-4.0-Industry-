# SylvaPapers — Budget de calcul

## 1. Objectif

Conserver édition, validation et simulation rapide de l'usine sur un ordinateur développeur. Ces
budgets sont des garde-fous d'ingénierie, pas des engagements de service de production.

## 2. Profil rapide

| Activité | Budget |
|---|---:|
| Validation contrats et graphe | < 2 s |
| Simulation de dix rouleaux sans figures | < 30 s |
| Chargement initial de l'éditeur | < 3 s |
| Suite locale complète | < 30 s |

## 3. Mémoire et sorties

La configuration reste lisible. Les événements sont compacts ; figures et résultats sont écrits hors
des sources. L'éditeur limite les charges de sauvegarde à 2 Mo.

## 4. Gardes de terminaison

Les gammes produit doivent atteindre un puits. Le modèle SylvaPapers ne contient aucun cycle de
recyclage ou reprise ; les rejets qualité quittent le procédé comme pertes mesurées.

## 5. Mesure

Chaque résumé consigne version Python, plateforme, graine, scénario, durée et comptes de résultats.
