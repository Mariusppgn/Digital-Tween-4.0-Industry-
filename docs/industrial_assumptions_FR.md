# SylvaPapers — Hypothèses industrielles

## 1. Statut des preuves

Chaque valeur de la baseline est une hypothèse d'ingénierie synthétique. Aucune valeur ne provient
d'une papèterie, GMAO, historien ou campagne de laboratoire identifiée. Un étalonnage est obligatoire
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

Chaque nœud liste ses entrées et sorties matière. Le simulateur léger suit des équivalents-rouleaux
plutôt qu'un bilan massique continu. Les rejets qualité éligibles entrent dans une boucle contrôlée
vers la préparation de pâte : chaque passage utilise une probabilité de récupération de Bernoulli
avec graine de 0,75 et la politique de référence autorise au plus deux passages. Les récupérations
échouées et les boucles épuisées deviennent des pertes finales. Cette hypothèse unitaire n'est pas un
bilan massique des fibres, de l'humidité ou des cassés ni la description d'une pratique recommandée.

## 5. Machines et capacité

Les listes de machines parallèles représentent des alternatives redondantes pour une opération. Les
branches conditionnelles représentent les recettes. Temps, capacités, énergie et coûts sont
synthétiques et emploient les unités déclarées dans la configuration.

## 6. Densité de panne

Tous les types de machine utilisent un modèle Weibull à deux paramètres :

| Paramètre | Signification | Unité |
|---|---|---|
| `shape` β | profil du taux de panne | sans dimension |
| `scale_hours` η | âge de fonctionnement caractéristique | heures de fonctionnement |

L'âge avance pendant le traitement. Le risque conditionnel suppose que forme et échelle configurées
restent valides sur l'horizon. La maintenance applique une récupération partielle d'âge virtuel. La
durée de réparation reste un paramètre synthétique.

## 7. Dégradation et capteurs

L'indice de dégradation est un état latent synthétique piloté par l'usage et la maintenance. Charge,
température, vibration, pression et puissance sont générées comme corrélats interprétables de cet état
et du contexte. Bruit, coefficients et échantillonnage ne représentent aucun capteur, fournisseur ou
programme de mesure particulier.

`operating_age_hours` et `degradation_index` sont des états du modèle, pas des mesures physiques
indépendantes. La qualité d'un relevé décrit la donnée générée, pas une métrologie certifiée.

## 8. Baseline de maintenance prédictive

EWMA détecte les décalages persistants et la mise à l'échelle robuste réduit la sensibilité aux valeurs
isolées. Weibull conditionnel estime risque sur l'horizon et vie restante en fonctionnement. Les deux
supposent une baseline représentative et un alignement temporel correct ; aucun ne prouve une cause.

L'urgence combine des preuves synthétiques d'anomalie, risque et criticité. Elle reste consultative et
ne doit jamais créer automatiquement un ordre de maintenance.

## 9. Économie de maintenance

Les politiques corrective, préventive et prédictive sont comparées avec coût d'intervention, coût
d'arrêt, durées planifiée et corrective, efficacité prédictive et récupération d'âge. Les valeurs de
`configs/maintenance/baseline.yaml` sont marquées synthétiques. Les coûts attendus comparent le
logiciel et ne sont pas des prévisions financières.

## 10. Qualité et calendriers

La probabilité qualité est synthétique. Un rejet crée des événements qualité et perte matière et ne
devient pas production acceptée. Les calendriers sont contractuels, mais l'application complète du
personnel, des arrêts planifiés et fenêtres de maintenance reste future.

## 11. Frontière de sécurité

SylvaPapers ne possède aucune interface actionneur et ne peut commander un équipement réel. Un usage
production exigerait gouvernance des données, identité, autorisation, audit, segmentation réseau,
analyse de dangers, suivi du modèle et approbation humaine.

## 12. Liste d'étalonnage

- confirmer topologie réelle, grades, capacités et unités matière ;
- remplacer paramètres synthétiques procédé, qualité, énergie, dégradation et coûts ;
- estimer Weibull sur des historiques censurés en heures de marche ;
- aligner horodatages capteurs, états, pannes et maintenances ;
- backtester anomalie et risque avec des découpages temporels ;
- valider couverture RUL, calibration probabiliste et économie de maintenance ;
- réconcilier rouleaux, tonnes sèches et bilans d'humidité ;
- définir les taxonomies approuvées des pertes, modes de panne et interventions.
