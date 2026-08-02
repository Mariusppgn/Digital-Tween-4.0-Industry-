# SylvaPapers — Hypothèses industrielles

## 1. Statut des preuves

Chaque valeur de la baseline est une hypothèse d'ingénierie synthétique. Aucune valeur ne provient
d'une papèterie, d'une GMAO ou d'une campagne de laboratoire identifiée. Un étalonnage est obligatoire
avant tout usage opérationnel.

## 2. Frontière du procédé

Le modèle intégré commence au bois brut et se termine par des rouleaux finis acceptés ou des pertes
qualité mesurées. Il couvre écorçage, déchiquetage, production de pâte, lavage, épuration,
blanchiment facultatif, préparation, raffinage, formation, pressage, séchage, calandrage, bobinage et CQ.

## 3. Produits

| Produit | État initial | Branche de recette | Unité nominale |
|---|---|---|---|
| Rouleau kraft | actif | cuisson kraft | rouleau |
| Rouleau impression | actif | pâte thermomécanique | rouleau |
| Rouleau carton | désactivé | cuisson pâte carton | rouleau |

L'activation est explicite. Une commande visant un produit désactivé est invalide.

## 4. Matières et pertes

Chaque nœud liste ses entrées et sorties matière en langage lisible. Le simulateur léger suit des
entités rouleau plutôt qu'un bilan massique continu. Les rejets CQ sont comptés comme pertes et
quittent le procédé ; recyclage, reprise et récupération des cassés sont volontairement exclus.

## 5. Machines et capacité

Les listes de machines parallèles représentent des alternatives redondantes pour une même opération.
Les branches conditionnelles représentent des recettes produit différentes. Temps, capacités,
énergie et coûts sont synthétiques et utilisent les unités déclarées dans la configuration.

## 6. Densité de panne

Tous les types de machine utilisent un modèle Weibull à deux paramètres :

| Paramètre | Signification | Unité |
|---|---|---|
| `shape` β | profil du taux de panne | sans dimension |
| `scale_hours` η | âge de fonctionnement caractéristique | heures de fonctionnement |

L'âge n'avance que pendant le traitement. La maintenance applique la récupération partielle d'âge
virtuel configurée. Le temps de réparation reste déterministe et synthétique dans cet incrément.

## 7. Qualité

La probabilité CQ est synthétique. Un rouleau rejeté crée des événements `qc_fail` et `material_loss`
et n'entre pas dans la production acceptée. `material_loss_rate` rapporte les rouleaux perdus aux
rouleaux libérés.

## 8. Calendriers

Les horaires sont des données contractuelles des équipes production et maintenance. Le simulateur
léger actuel ne les applique pas ; cette limite doit accompagner toute interprétation.

## 9. Frontière de sécurité

SylvaPapers ne possède aucune interface actionneur et ne peut commander un équipement réel. Un usage
production exigerait identité, autorisation, audit, segmentation réseau, analyse de dangers et validation humaine.

## 10. Liste d'étalonnage

- confirmer la topologie réelle et les grades actifs ;
- remplacer temps, capacités, rendements, énergie et coûts synthétiques ;
- estimer Weibull sur des historiques censurés en heures de marche ;
- valider réparation et récupération d'âge ;
- réconcilier comptes de rouleaux et bilans en tonnes sèches ;
- définir les taxonomies qualité et pertes approuvées.
