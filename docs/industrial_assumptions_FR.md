# Hypothèses industrielles

## 1. Statut et usage prévu

Ce registre définit le monde industriel synthétique du premier jet Asteria. Les valeurs sont des paramètres plausibles pour démonstrations logicielles, non des mesures d’une usine composites identifiée. Elles doivent être remplacées ou étalonnées avant usage opérationnel. Chaque expérience consigne la version du jeu d’hypothèses et toute surcharge.

La confiance d’une hypothèse vaut :

- **A — confirmée :** étayée par une source approuvée ;
- **B — provisoire :** plausible et à confirmer ;
- **C — synthétique :** inventée pour exercer le comportement.

Sauf promotion explicite, toutes les valeurs du premier jet sont **C — synthétiques**.

## 2. Installation et calendrier d’exploitation

Le modèle représente un flux de production composites avec préparation matière première, découpe, deux postes de drapage parallèles, tampon pré-autoclave fini, un autoclave, finition, contrôle qualité et retouche. C’est un flux logique, non une implantation spatiale.

Le calendrier de référence est de cinq jours par semaine, deux équipes de 8 heures par jour. Pauses planifiées et fenêtres de maintenance préventive réduisent la disponibilité. Les libérations s’arrêtent hors calendrier ; un cycle autoclave ininterrompu déjà engagé peut se terminer. Les heures supplémentaires sont désactivées sauf si un scénario les active et les chiffre.

## 3. Produits, demande et routage

La référence utilise deux familles synthétiques : `PANEL_STD` et `PANEL_COMPLEX`. Elles suivent la même route ; `PANEL_COMPLEX` a des durées de drapage/finition plus longues et une probabilité de défaut supérieure. La demande est constituée d’ordres datés ou d’un processus d’arrivée ensemencé. Les priorités sont normale et urgente ; FIFO s’applique par défaut dans chaque classe.

Aucune entité ne saute le CQ. Un défaut récupérable retourne en finition, puis au CQ. Chaque pièce accepte au plus deux boucles de retouche ; l’échec suivant devient rebut. Le mélange de produits dans un lot autoclave n’est permis que si la compatibilité de famille de recette est déclarée.

## 4. Hypothèses de référence des postes

| Étape | Capacité | Hypothèse de durée de référence | Règle importante |
|---|---:|---|---|
| MP | 1 | Triangulaire 20/30/45 min par kit | Matière disponible avant découpe |
| Découpe | 1 | Triangulaire 25/40/60 min par kit | Un kit par machine |
| Drapage A | 1 | Durée positive de type lognormale, médiane 180 min standard | Éligible aux deux familles |
| Drapage B | 1 | Même distribution avec tirages indépendants | Éligible aux deux familles |
| Tampon | 6 pièces | Aucun temps de traitement | Blocage lorsque plein |
| Autoclave | 1 ressource par lot, jusqu’à 4 pièces compatibles | 360 min fixes plus 30 min chargement/déchargement | Démarre plein ou après attente max de 120 min |
| Finition | 2 | Triangulaire 45/70/110 min par pièce | La retouche consomme la même capacité |
| CQ | 1 | Triangulaire 20/30/50 min par pièce | Oriente vers conforme, retouche ou rebut |

Ces chiffres sont des valeurs de scénario, non des temps de cycle acceptés. Les durées sont échantillonnées une fois par activité depuis une distribution nommée ensemencée et ne peuvent être négatives. Les réglages/changements de série valent zéro dans la référence simple et sont explicites dans les scénarios avancés.

## 5. Hypothèses de qualité et retouche

La probabilité de défaut au premier passage est de 6 % pour `PANEL_STD` et 10 % pour `PANEL_COMPLEX`. Conditionnellement à un défaut, 80 % sont supposés récupérables et 20 % rebutés. Une première retouche multiplie le temps de finition par 0,6 ; une seconde par 0,8. Dans le modèle le plus simple, les résultats CQ sont indépendants hors famille produit et nombre de retouches.

Cette indépendance est une simplification connue. Un étalonnage futur devrait conditionner la qualité sur lot matière, opérateur/équipe, état équipement, attente, compatibilité recette et retouches antérieures. Rendement et rebut restent synthétiques jusqu’à cet étalonnage.

## 6. Hypothèses de fiabilité et maintenance

Découpe, drapage, autoclave et finition peuvent tomber en panne. La référence tire temps avant panne et réparation depuis des distributions positives ensemencées ; la maintenance planifiée restaure la fraction d’âge virtuel déclarée. Les pannes interrompent ou retardent le travail selon la politique explicite du poste. Une interruption autoclave invalide par défaut le lot et impose une revue CQ ; cette règle prudente est configurable.

Les variables synthétiques de maintenance prédictive sont corrélées à un état latent de dégradation. Valeurs capteur, étiquettes de panne et actions sont générées dans l’ordre causal. Aucun score n’est traité comme une mesure physique de durée de vie résiduelle. Techniciens et fenêtres de maintenance sont des ressources finies dans les scénarios d’affectation.

## 7. Hypothèses de personnel et d’affectation

Les travailleurs ont des compétences nommées telles que préparation matière, découpe, drapage, conduite autoclave, finition, inspection qualité et maintenance. Une personne ne couvre pas des tâches qui se chevauchent et n’est disponible que sur ses équipes. La référence considère la compétence uniforme et omet fatigue, ergonomie et apprentissage.

Les contraintes fortes incluent éligibilité de compétence, disponibilité, couverture de tâche, capacité du poste et maximum légal d’heures déclaré par le scénario. Préférences, équité et heures supplémentaires ne sont des objectifs souples que si elles sont quantifiées. L’optimiseur peut laisser du travail non affecté plutôt que d’inventer de la capacité.

## 8. Hypothèses commerciales et marketing

Les scénarios marketing sont séparés de la demande usine observée. Ils utilisent segments, canaux, courbes de réponse, marges unitaires, dépenses minimales/maximales et une devise déclarée synthétiques. La réponse présente des rendements décroissants et peut être bornée par la capacité faisable du scénario d’affectation.

Aucune réponse de canal ne constitue une preuve causale. Les effets de campagne sont des valeurs attendues de scénario et ne créent pas automatiquement d’ordres usine. Une expérience intégrée applique une correspondance explicite et rapporte la demande au-delà de la capacité comme non satisfaite ou différée, jamais comme chiffre d’affaires livré.

## 9. Hypothèses de portefeuille R&D

Les projets candidats sont synthétiques avec coût, durée, probabilité de succès, valeur attendue, scores stratégiques, dépendances, exclusions et besoin en ressources. Coûts et capacité partagent un horizon de planification. La valeur attendue n’est ajustée du risque que si la formule est déclarée ; les poids stratégiques restent visibles.

La sélection ne prouve pas la valeur d’innovation. Elle produit un scénario contraint et explicable selon les entrées. Projets obligatoires, planchers de diversification et prérequis sont des contraintes fortes ; les scores subjectifs exigent propriétaire et date de revue.

## 10. Hypothèses de données et intégration

Le premier jet lit des artefacts locaux YAML/JSON/CSV/Parquet versionnés et s’exécute hors ligne dans un processus Python par expérience. Il ne suppose aucun MES, ERP, historien, OPC UA, MQTT, base cloud ou ordonnanceur distribué. Les horodatages absolus sont UTC ; la DES utilise des minutes simulées non négatives.

Les identifiants synthétiques ne contiennent aucune donnée personnelle ni confidentielle d’usine. Les entrées brutes sont immuables, les dérivés portent les hachages sources, et les valeurs manquantes ne sont pas remplies silencieusement. Les échanges inter-modules passent uniquement par `asteria_contracts`.

## 11. Sécurité, sûreté et limites de décision

Asteria n’a aucune interface actionneur et ne peut commander l’équipement, libérer des pièces, planifier de vraies personnes, déclencher une maintenance, dépenser un budget marketing ni approuver un investissement R&D. Les sorties sont des artefacts expérimentaux consultatifs. Un usage production imposerait authentification, autorisation, audit, segmentation réseau, classification des données, conservation, analyse de dangers et approbation humaine.

Aucun jeu généré ne doit inclure de données personnelles réelles ou de détails opérationnels confidentiels sans gouvernance approuvée. Journaux et erreurs de validation évitent les charges complètes.

## 12. Protocole de changement des hypothèses

Chaque hypothèse possède ID, propriétaire, valeur/plage, unité, confiance, source, période de validité et modules affectés. Un changement :

1. crée une nouvelle version du jeu d’hypothèses ;
2. identifie contrats, fixtures et références affectés ;
3. rejoue vérification et cas de sensibilité ;
4. consigne écarts KPI et notes de migration ;
5. exige une revue métier avant promotion de confiance.

Changer une référence n’écrase jamais les manifestes précédents.

## 13. Arriéré d’étalonnage industriel

Avant toute allégation étalonnée, obtenir et gouverner :

- routage, calendriers, capacités, règles tampon et politique de lots autoclave réels ;
- distributions de durée et changements de série par famille ;
- arrivées de commandes, échéances et priorités ;
- historiques pannes, réparations, maintenance préventive et capteurs ;
- définitions qualité, retouche et rebut reliées à des causes traçables ;
- compétences/disponibilités du personnel avec protection de la vie privée ;
- preuves de réponse commerciale et lien à la capacité production ;
- coûts R&D, contraintes de ressources, gouvernance des scores et historique de résultats.

L’étalonnage sépare données d’estimation et périodes de validation indépendantes et documente les biais de sélection connus.

## 14. Critères d’acceptation

Le registre est adéquat pour le premier jet lorsque chaque valeur de scénario est reliée à une entrée versionnée, tous les paramètres par défaut sont visiblement synthétiques, les plages empêchent les états impossibles, les correspondances intégrées déclarent leurs limites, et les tests de sensibilité montrent quelles conclusions changent avec les hypothèses influentes. Aucun rapport ne peut omettre le niveau de preuve ni suggérer une validation usine.
