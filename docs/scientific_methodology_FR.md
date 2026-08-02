# SylvaPapers — Méthodologie scientifique

## 1. Positionnement

SylvaPapers est une expérience logicielle reproductible, pas un modèle étalonné d'une papèterie
particulière. Les résultats testent uniquement l'implémentation et des hypothèses synthétiques.

## 2. Reproductibilité

Chaque simulation déclare version, provenance, graine, horizon, produits et commandes. Des entrées
validées identiques et une même graine doivent produire les mêmes événements et jobs.

## 3. Expérience procédé

Le graphe représente transformations en série, recettes de pâte alternatives et machines redondantes.
Un produit peut déclarer sa gamme ou laisser le simulateur la déduire des conditions d'arête. Toutes
les routes actives doivent finir en rouleaux acceptés ou pertes mesurées.

## 4. Expérience fiabilité

La famille Weibull commune ne change que forme et échelle selon le type de machine. La probabilité de
panne est conditionnée par l'âge de fonctionnement et la durée de l'opération. Les comparaisons font
d'abord varier un coefficient à la fois avant les plans factoriels.

## 5. Qualité et pertes

Dans le modèle léger, les résultats qualité sont des événements Bernoulli avec graine. Les rouleaux
rejetés sont des pertes terminales. Aucun résultat ne peut compter un rejet comme production acceptée.

## 6. KPI

Les sorties principales incluent quantité acceptée, service, cycle, utilisation, défauts, pertes
matière, arrêts, coût, énergie, OEE simplifié et retard.

## 7. Hiérarchie de validation

1. valider contrats et références ;
2. valider accessibilité du graphe et activation produit ;
3. tester événements déterministes et bornes KPI ;
4. tester aller-retour et frontières de sécurité de l'éditeur ;
5. comparer les résultats synthétiques après réussite des quatre niveaux.

## 8. Chemin d'étalonnage

Un usage opérationnel exige historiques procédé approuvés, pannes censurées, maintenance, étiquettes
qualité, comptage énergie et bilans matière. L'étalonnage doit conserver une baseline synthétique
séparée pour les tests de régression.
