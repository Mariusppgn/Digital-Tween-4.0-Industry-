# SylvaPapers — Budget de calcul

## 1. Objectif

Conserver édition, simulation du Module A et analyse de maintenance du Module B sur un ordinateur
développeur standard sans GPU. Ces budgets sont des garde-fous d'ingénierie, pas des engagements de
service mesurés.

## 2. Profils

| Profil | Charge prévue | Garde-fou de bout en bout |
|---|---|---:|
| `fast` | scénario de vérification, tests et une passe maintenance | < 30 s par exécution simple |
| `standard` | un mois industriel, plusieurs réplications et comparaison des politiques | < 2 min |
| `research` | sensibilité facultative ou comparaison de méthode avancée | < 5 min par configuration par défaut |

Un benchmark nommé doit consigner matériel, version Python, scénario, graine, répétitions, comptes
d'artefacts et temps avant de présenter un garde-fou comme résultat observé.

## 3. Budgets des modules

| Activité | Cible `fast` | Contrôle de dimension |
|---|---:|---|
| Validation contrats et graphe | < 2 s | taille du graphe et nombre de schémas |
| Chargement initial de l'éditeur | < 3 s | nœuds, arêtes et sauvegarde limitée à 2 Mo |
| Simulation simple Module A | < 30 s | commandes, horizon et figures facultatives |
| Analyse baseline Module B | < 30 s | machines, relevés, horizon et figures |
| Suite locale complète | < 60 s | hors installation des dépendances |

## 4. Mémoire et sorties

Les configurations restent lisibles. Les observations tabulaires sont compactes, tandis que figures
et résultats sont écrits hors des sources. Les sorties A et B utilisent des dossiers séparés pour que
l'analyse de maintenance ne puisse écraser ses preuves sources.

## 5. Politique algorithmique

EWMA, seuils robustes et calculs Weibull fermés sont les baselines pour portable. Les méthodes CUSUM,
survie, espace-état ou apprentissage facultatives doivent partager les mêmes contrats, exposer leur
coût et rester désactivées en `fast`.

## 6. Gardes de terminaison

Les gammes doivent atteindre un puits. L'usine ne contient aucun recyclage ou reprise. Horizon,
commandes et taille de sortie sont bornés par la configuration validée ; l'entrée maintenance doit
être un paquet fini et complet.

## 7. Mesure

Chaque résumé consigne versions Python, plateforme, schéma et code, graine, profil, scénario, durée,
chemins d'entrée et de sortie et comptes de résultats.
