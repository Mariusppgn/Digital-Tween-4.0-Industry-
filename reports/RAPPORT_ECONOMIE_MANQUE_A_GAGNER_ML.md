# Rapport — économie, manque à gagner et ML

Date : 3 août 2026  
Version : `0.5.0`  
Classification : `synthetic_hypothesis_not_calibrated`

## 1. Périmètre livré

Le Module A calcule maintenant le coût machine, le chiffre d'affaires instantané et cumulé, la
marge brute d'exploitation synthétique et un CA contrefactuel sans panne. Chaque panne porte une
exposition commerciale calculée à partir du graphe : totalité du flux pour une étape commune en
série, part des produits affectés pour une dérivation, puis part de capacité nominale pour plusieurs
machines parallèles. Les ressources restantes conservent leur vitesse nominale ; aucun rattrapage
n'est crédité. Les pertes simultanées sont plafonnées au flux nominal total afin d'éviter un double
comptage au niveau usine.

Le Module B reçoit ces variables dans les tables machine. Un modèle `ExtraTreesRegressor` prédit le
manque à gagner attendu et classe les machines. L'apprentissage utilise les réplications 1 à 80 et
le holdout temporel les réplications 81 à 100. Les variables de conséquence (`failure_count`, temps
d'arrêt et cible) ne sont pas utilisées en entrée.

## 2. Hypothèses économiques

| Paramètre | Valeur de référence | Statut |
|---|---:|---|
| Électricité non résidentielle | 0,1837 EUR/kWh | benchmark Eurostat UE, bande 500–2 000 MWh, S2 2025 |
| Coût horaire du travail industriel | 47,7 EUR/h | benchmark Insee France 2025 ; contexte, non additionné directement |
| Coût direct des 21 machines | 68 à 520 EUR/h | hypothèses synthétiques par type, hors électricité |
| Coût d'immobilisation | 20 % du coût direct par défaut | hypothèse synthétique |
| Prix kraft | 950 EUR/rouleau | hypothèse synthétique |
| Prix impression | 990 EUR/rouleau | hypothèse synthétique |
| Prix linerboard | 1 020 EUR/rouleau | hypothèse synthétique, produit désactivé |

Les références externes cadrent les catégories et ordres de grandeur ; elles ne constituent pas un
devis papetier. Les prix produit et coûts machine doivent être remplacés par la comptabilité et les
contrats énergétiques réels avant toute décision industrielle.

## 3. Campagne statistique longue

La campagne `sylvapapers-economic-long-run-v2` comprend 100 réplications de 2 000 rouleaux, soit
200 000 rouleaux planifiés, avec les graines 1000 à 1099. Elle a été exécutée en 311,47 s. Les IC95
sont des intervalles percentiles obtenus par 2 000 rééchantillonnages bootstrap avec graine fixe.

| KPI | Moyenne | IC95 bootstrap | Erreur standard relative |
|---|---:|---:|---:|
| Rouleaux acceptés | 1 957,18 | [1 955,99 ; 1 958,34] | 0,030 % |
| CA reconnu | 1 890 618,60 EUR | [1 889 559,26 ; 1 891 675,59] | 0,030 % |
| Manque à gagner panne | 2 982,37 EUR | [2 504,80 ; 3 472,61] | 8,219 % |
| Taux de manque à gagner | 0,1573 % | [0,1317 % ; 0,1842 %] | 8,192 % |
| Coût total | 3 319 245,13 EUR | [3 316 764,86 ; 3 321 532,91] | 0,036 % |
| Marge brute synthétique | -1 428 626,53 EUR | [-1 431 026,36 ; -1 425 890,32] | 0,092 % |

86 réplications sur 100 contiennent un manque à gagner non nul. Les statistiques de production et
de CA sont précises dans ce scénario fixe. Le manque à gagner demeure plus incertain ; son erreur
standard relative de 8,2 % justifie de conserver au moins 100 réplications.

La marge négative n'est pas un diagnostic économique de SylvaPapers : elle révèle que les coûts et
prix synthétiques ne sont pas étalonnés entre eux.

## 4. Résultats du modèle ML

| Mesure holdout | Résultat |
|---|---:|
| Lignes apprentissage / validation | 2 000 / 500 |
| Lignes positives apprentissage / validation | 117 / 30 |
| MAE | 215,61 EUR |
| MAE pondérée par la gravité | 328,79 EUR |
| RMSE | 532,74 EUR |
| R² | 0,077 |
| Perte réelle totale du holdout | 65 276 EUR |
| Interventions rentables au seuil de 3 000 EUR | 0 |

Le signal hors échantillon est positif mais faible et les pertes sont très clairsemées. Le modèle
est donc une baseline de classement, pas un prédicteur déployable. Avec une efficacité supposée de
75 % et un coût de 3 000 EUR, il est rationnel qu'il ne déclenche aucune intervention dans ce jeu
synthétique. Les premières priorités de classement sont `digester-01`, `bleach-01`,
`tmp-refiner-01`, `press-01` et `pulp-refiner-01`.

## 5. Exports et graphiques

Le paquet `exports/sylvapapers-handoff-v2` contient 15 fichiers sources validés plus
`handoff_manifest.json`, avec nombre de lignes, en-têtes et SHA-256. Il inclut notamment :

- `campaign_runs.csv`, `kpi_statistics.csv` et les tables produit/machine pour D/E ;
- les variables et résultats temporels du Module B ;
- `machine_economic_priorities.csv`, les importances, métriques et manifeste du modèle.

35 anciens PNG ont été supprimés. Les 14 figures canoniques ont été régénérées avec
`plt.style.use("ggplot")` dans les sorties Module A, campagne, Module B et modèle économique. Les
anciens répertoires de démonstration n'ont pas été repeuplés.

## 6. Validation

- environnement verrouillé : `uv sync --frozen --system-certs --extra dev` ;
- 70 tests collectés et réussis ;
- Ruff check et format : réussis ;
- mypy strict : réussi ;
- parité structurelle README anglais/français : réussie ;
- inspection visuelle de `revenue.png`, `kpi_distributions.png` et
  `economic_model_validation.png` : réussie ;
- handoff v2 : schémas, classifications, CSV et sommes SHA-256 validés.

## 7. Ce qui reste à faire

1. Remplacer les coûts, prix, MTTR et coefficients Weibull synthétiques par des données réelles
   approuvées, avec dates d'effet et centres de coût.
2. Définir le CA au niveau tonne/format/qualité si l'unité `roll` devient insuffisante.
3. Ajouter davantage d'historiques positifs avant d'évaluer un modèle de survie ou un modèle en deux
   étages probabilité × sévérité.
4. Recalibrer le coût et l'efficacité d'une intervention ; le seuil actuel ne justifie aucune action.
5. Créer les dépôts séparés des Modules D et E et leurs validateurs d'entrée à partir du handoff v2.

## 8. Sources de cadrage

- Eurostat, prix de l'électricité non résidentielle au second semestre 2025 :
  <https://ec.europa.eu/eurostat/web/products-eurostat-news/w/ddn-20260508-2>
- Insee, coût horaire du travail selon l'activité en 2025 :
  <https://www.insee.fr/fr/statistiques/2381340>
- Commission européenne JRC, BREF production de pâte, papier et carton :
  <https://joint-research-centre.ec.europa.eu/reports-and-technical-documentation/best-available-techniques-bat-reference-document-production-pulp-paper-and-board-industrial_en>
- Eurostat, métadonnées PRODCOM sur les valeurs et volumes produits :
  <https://ec.europa.eu/eurostat/cache/metadata/en/prom_esms.htm>
- scikit-learn, documentation `ExtraTreesRegressor` :
  <https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesRegressor.html>
