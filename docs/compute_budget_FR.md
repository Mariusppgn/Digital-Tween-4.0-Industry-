# Budget de calcul

## 1. Objectif et périmètre

Ce budget conserve le premier jet Asteria rapide, reproductible et utilisable sur un ordinateur développeur courant. C’est un garde-fou d’ingénierie, non un SLA de production. L’architecture reste un monorepo Python local ; dépasser un budget déclenche d’abord profilage, amélioration algorithme/format et réduction du périmètre expérimental — non un passage par défaut aux microservices ou au calcul distribué.

## 2. Environnement de référence

Les budgets sont mesurés sur une classe de machine, non un modèle constructeur :

- 4 cœurs logiques disponibles pour l’expérience ;
- 8 Gio de RAM disponibles, plafond souple de 2 Gio par exécution ;
- SSD local ;
- CPython 64 bits supporté ;
- aucun GPU requis ;
- cache de dépendances chaud et aucun accès réseau pendant l’exécution.

Les benchmarks consignent CPU, RAM, versions Python/OS et état froid/chaud. La CI peut utiliser un profil déterministe plus petit ; les assertions de temps absolu incluent une marge documentée.

## 3. Classes de charge

| Classe | Usage prévu | Temps cible | Mémoire | Artefacts générés |
|---|---|---:|---:|---:|
| Unitaire | Une fonction ou micro-scénario | ≤ 1 s | ≤ 256 Mio | ≤ 1 Mio |
| Fumée | Une petite exécution bout en bout | ≤ 10 s | ≤ 512 Mio | ≤ 10 Mio |
| Standard | Un scénario analyste | ≤ 60 s | ≤ 1 Gio | ≤ 100 Mio |
| Intégré | Scénario cinq modules du premier jet | ≤ 180 s | ≤ 2 Gio | ≤ 250 Mio |
| Lot recherche | Campagne locale explicite | ≤ 30 min | ≤ 4 Gio avec accord | ≤ 2 Gio avec politique de conservation |

Les commandes par défaut exécutent des charges fumée ou standard. Les lots recherche exigent des limites explicites et ne s’exécutent pas dans les tests ordinaires.

## 4. Budgets par module

| Module | Enveloppe d’entrée standard | Cible | Garde-fou fort du premier jet |
|---|---|---:|---:|
| Jumeau numérique | ≤ 10 000 pièces libérées, ≤ 1 000 000 événements | 60 s / 1 Gio | 2 000 000 événements ou 120 s |
| Maintenance prédictive | ≤ 100 000 observations, ≤ 200 variables, ≤ 1 000 actifs | 60 s / 1 Gio | 500 000 lignes ou 120 s |
| Affectation ressources | ≤ 500 tâches, ≤ 100 ressources, ≤ 50 000 affectations candidates | 60 s / 1 Gio | timeout solveur 120 s |
| Optimisation marketing | ≤ 100 segments × 30 canaux × 20 scénarios | 30 s / 512 Mio | 120 s et itérations bornées |
| Portefeuille R&D | ≤ 500 projets, ≤ 2 000 arêtes de dépendance/contrainte | 60 s / 1 Gio | timeout solveur 120 s |

Le franchissement renvoie un diagnostic structuré avant ou pendant l’exécution. Les résultats partiels sont marqués incomplets et ne sont jamais comparés comme expériences réussies.

## 5. Modèle de coût du jumeau numérique

Avec un calendrier d’événements en file de priorité, le temps doit croître approximativement en \(O(E \log E)\), où \(E\) est le nombre d’événements émis ; la mémoire est \(O(E)\) seulement si le journal complet est retenu. L’agrégation KPI en flux conserve un état proportionnel aux entités actives, files et ressources.

Par défaut, les événements compacts nécessaires à l’audit sont conservés et écrits par blocs. Les instantanés de toutes les files à chaque événement sont interdits ; on utilise des instantanés périodiques ou sur changement. La sélection des lots autoclave emploie des parcours candidats bornés. Les gardes de terminaison couvrent horizon, nombre d’événements, retouches maximales et boucles d’événements à durée nulle.

## 6. Modèle de coût analytique et optimisation

Le prétraitement de maintenance est linéaire en lignes × variables si possible. Les calculs toutes paires denses sont interdits sauf taille déclarée faible. Les modèles de référence précèdent la recherche coûteuse, et plis de validation × candidats doivent tenir dans le budget standard.

Les problèmes d’affectation, marketing et portefeuille peuvent être combinatoires. Chaque solveur reçoit limite de temps/itérations, graine déterministe si supportée, écart d’optimalité acceptable et politique de retour de la meilleure solution. Le résultat indique `optimal`, `feasible`, `infeasible`, `timeout` ou `error` ; une solution à l’expiration n’est pas dite optimale.

## 7. Budget du scénario intégré

L’orchestrateur exécute les modules séquentiellement par défaut pour simplifier la provenance et borner le pic mémoire. Il affecte des graines dérivées stables et libère les gros intermédiaires après écriture des artefacts validés. Le budget standard intégré est :

- validation et préparation : 10 s ;
- jumeau numérique : 60 s ;
- maintenance prédictive : 30 s ;
- affectation ressources : 30 s ;
- optimisation marketing : 20 s ;
- portefeuille R&D : 20 s ;
- contrôles croisés, sérialisation et données rapport : 10 s.

La cible totale est 180 secondes et 2 Gio de pic. Les budgets module sont des plafonds, non des réservations ; le temps inutilisé n’est pas automatiquement redistribué.

## 8. Budget des expériences stochastiques

Les tests fumée utilisent une graine fixe. Une comparaison d’incertitude standard utilise 10 graines ; une étude synthétique publiable doit en justifier au moins 30 ou démontrer la convergence. Avant campagne :

\[
\text{coût estimé} = \text{scénarios} \times \text{graines} \times \text{durée de référence mesurée}
\]

L’orchestrateur affiche l’estimation et exige un accord explicite au-delà de 30 minutes ou 2 Gio de sorties prévues. L’arrêt anticipé n’est permis que par une règle de convergence prédéclarée et consigne les répétitions omises.

## 9. Budget de stockage et sérialisation

Les artefacts générés ne vont pas dans le contrôle de source sauf petites fixtures relues. Chaque exécution possède manifeste, résultat KPI compact et tables détaillées optionnelles. Limites recommandées :

- manifeste et configuration : ≤ 1 Mio ;
- résumés KPI/résultats : ≤ 10 Mio ;
- tables détaillées événements/observations : ≤ 200 Mio par exécution intégrée ;
- journaux : ≤ 10 Mio, rotation ou troncature avec marqueur ;
- exécutions standard conservées : 20 par famille de scénario par défaut.

JSON sert aux contrats et petits enregistrements ; CSV aux échanges simples ; Parquet est préféré pour les grandes tables si la dépendance optionnelle est installée. Compression et sous-échantillonnage ne remplacent jamais le hachage source immuable.

## 10. Budget des tests et de la CI

La suite locale/CI ordinaire cible :

- tests unitaires : ≤ 60 secondes ;
- tests contrats et architecture : ≤ 30 secondes ;
- scénario d’intégration fumée : ≤ 60 secondes ;
- suite totale par défaut : ≤ 3 minutes sur la classe de référence.

Tests stochastiques longs, benchmarks solveur et recherche sont marqués et exécutés séparément. Aucun test ne dépend d’attentes réelles, de services réseau ou d’aléatoire non ensemencé. Les tests de performance comparent tendances et plafonds généreux pour éviter les échecs dus au bruit matériel.

## 11. Instrumentation

Toute exécution standard ou supérieure consigne temps réel, temps CPU processus, pic mémoire résident, nombres de lignes/entités, événements DES, itérations/état solveur, octets d’artefacts et alertes/limites. Les durées des modules entourent les points d’entrée publics avec un outil standard léger.

Les rapports comparent des configurations identiques et donnent médiane et dispersion sur plusieurs exécutions. Les artefacts de profilage ne sont générés qu’à la demande car ils peuvent être volumineux et contenir des valeurs dérivées des entrées.

## 12. Garde-fous et comportement d’échec

- Valider les tailles avant d’allouer de grands tableaux ou matrices.
- Traiter en flux/blocs les grandes tables et sorties d’événements.
- Contrôler entiers/comptages et nombres finis aux frontières.
- Appliquer limites d’événements, itérations, récursion, retouches, horizon et temps solveur.
- Écrire dans un répertoire temporaire d’exécution, puis finaliser le manifeste après validation.
- Sur annulation/limite, préserver un manifeste diagnostic et ne supprimer aucune exécution réussie antérieure.
- Ne jamais retenter automatiquement une entrée déterministe invalide.

Des alertes à 80 % d’une limite aident à redimensionner avant échec.

## 13. Politique de parallélisme

Le premier jet exécute les modules séquentiellement et peut paralléliser les répétitions indépendantes avec un petit nombre explicite de processus. Le code bibliothèque ne crée pas de pools non bornés et ne change pas les réglages globaux des threads. Les exécutions parallèles ont graines dérivées et répertoires séparés. L’estimation mémoire agrégée, non le seul nombre de CPU, limite la concurrence.

Aucun GPU, cluster, file, base distribuée ou orchestration de services n’est requis. Le parallélisme optionnel doit produire des résultats statistiquement équivalents au séquentiel dans les tolérances déclarées.

## 14. Déclencheurs de changement d’échelle et critères d’acceptation

Réexaminer l’architecture seulement lorsque des charges représentatives profilées dépassent régulièrement un garde-fou après amélioration des algorithmes/formats, ou lorsqu’un cas validé exige isolation/concurrence indisponible localement. Les preuves candidates incluent plus de 2 millions d’événements DES par exécution requise, plus de 4 Gio de mémoire, campagnes de plus de 30 minutes irréductibles, ou plusieurs utilisateurs gouvernés devant exécuter en concurrence.

Le budget est accepté lorsque chaque orchestrateur public applique limites d’entrée/exécution, les scénarios standard atteignent la cible sur l’environnement consigné, la suite par défaut respecte son budget, les rejeux ensemencés sont reproductibles, et les dépassements produisent des diagnostics valides sans corrompre les artefacts terminés.
