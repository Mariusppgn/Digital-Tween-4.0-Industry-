# Audit de cybersécurité — SylvaPapers

Date : 2026-08-02

Périmètre : code Python, éditeur web local, contrats et fichiers de configuration, exports, dépendances, chaîne CI, secrets et installation Windows.

## Synthèse

Aucun secret manifeste, aucune désérialisation Python dangereuse et aucun appel de commande système n'ont été détectés. Les fichiers YAML utilisent `safe_load`, les ressources web sont servies par liste blanche, les valeurs affichées utilisent `textContent`, et le serveur écoute par défaut sur l'interface locale.

Deux risques élevés restent à corriger avant de traiter des fichiers non fiables ou d'exposer l'éditeur au-delà de la machine locale : l'écriture HTTP n'est pas protégée contre les requêtes externes, et une quantité de production non bornée peut épuiser la mémoire ou le processeur.

## Constats prioritaires

### Élevé — écriture web sans authentification ni protection CSRF

`POST /factory.json` écrase le fichier de configuration sans jeton, sans validation stricte de `Host`, `Origin` ou `Content-Type`. La confirmation affichée par le navigateur ne protège pas l'endpoint direct. L'option `--host` permet aussi une écoute non locale sans authentification ni TLS.

Correctifs recommandés : limiter le serveur aux adresses loopback, valider `Host` et `Origin`, exiger `application/json`, générer un jeton aléatoire par démarrage et refuser toute exposition distante sans authentification et TLS.

### Élevé — simulation sans plafond de ressources

Une commande accepte une quantité positive sans maximum, puis le simulateur matérialise un job par unité. Un petit scénario peut donc demander des milliards de jobs et saturer la mémoire ou le processeur.

Correctifs recommandés : plafonner quantités, ordres, nœuds et arêtes ; ajouter `max_jobs`, `max_events`, `max_runtime_seconds` et un horizon maximal ; générer les jobs de manière paresseuse.

### Moyen — chaîne CI partiellement mutable

Les actions GitHub et hooks pre-commit sont référencés par tags, et le backend de build accepte toute version future de Setuptools au-dessus de 69.

Correctifs recommandés : épingler les actions et hooks à des SHA complets, désactiver la persistance des identifiants de checkout, fixer un délai maximal de job et automatiser les mises à jour avec Dependabot ou Renovate.

### Moyen — injection de formules dans les CSV

Les identifiants provenant des scénarios sont écrits tels quels dans les CSV. Une cellule commençant par `=`, `+`, `-` ou `@` peut être interprétée comme une formule par un tableur.

Correctif recommandé : neutraliser ces préfixes dans les exports destinés aux tableurs et conserver le JSON comme export fidèle.

### Moyen — nombres extrêmes ou non finis

Plusieurs valeurs numériques n'ont pas de borne supérieure globale. Des paramètres extrêmes peuvent produire `Infinity` ou `NaN`, puis un JSON non standard.

Correctifs recommandés : interdire `inf` et `nan`, ajouter des bornes métier, vérifier `math.isfinite` et sérialiser avec `allow_nan=False`.

### Moyen — écriture concurrente et déni de service HTTP

Le serveur multithread utilise un même fichier temporaire prévisible et ne fixe pas de délai de lecture. Des écritures simultanées peuvent entrer en concurrence et des connexions lentes peuvent immobiliser des threads.

Correctifs recommandés : verrou d'écriture, fichier temporaire unique, `fsync` puis `os.replace`, délais socket et limite de concurrence.

## Constats faibles

- Les chargeurs locaux lisent entièrement les fichiers JSON/YAML avant validation, sans limite de taille ou de profondeur.
- Les références d'un manifeste peuvent sortir de son dossier ; prévoir un mode sûr et une option explicite pour les chemins externes.
- Certaines erreurs HTTP et certains rapports exposent des chemins ou détails d'environnement locaux.
- La bannière HTTP hérite d'informations de version du serveur Python.
- `simpy` semble inutilisé dans `src`; toute dépendance inutile augmente la surface de chaîne logistique.
- La CI ne lance pas encore d'audit CVE, de détection de secrets ni de SAST.

## Mesures satisfaisantes

- `yaml.safe_load` et validation Pydantic avec champs supplémentaires interdits.
- Aucun `pickle`, `eval`, `exec`, `subprocess`, `os.system` ou `shell=True` détecté.
- Ressources web servies par liste blanche ; pas de traversée de chemin HTTP.
- Limite HTTP de 2 Mo, CSP stricte, `nosniff`, `no-store` et interdiction d'intégration en iframe.
- Rendu DOM avec `textContent`, sans `innerHTML`.
- Dépendances verrouillées avec empreintes dans `uv.lock`.
- Permissions GitHub Actions limitées à `contents: read`.
- Aucun secret ou fichier de clé manifeste dans les fichiers suivis.

## Vérifications exécutées

- Recherche statique de secrets et primitives dangereuses.
- Inspection manuelle du serveur, de l'éditeur, des chargeurs, du simulateur, des exports et de la CI.
- Validation de la configuration : 20 nœuds, 22 arêtes, aucun cycle.
- Suite de tests : 41 tests réussis.
- Export exact des versions de production depuis `uv.lock`.

La tentative d'audit CVE en ligne avec `pip-audit` n'a pas produit de résultat exploitable dans l'environnement contrôlé. Il ne faut donc pas interpréter ce rapport comme une attestation d'absence de CVE. Ajouter `pip-audit --strict` ou `osv-scanner` en CI reste requis.

## Ordre de correction recommandé

1. Sécuriser l'API locale et interdire l'exposition réseau implicite.
2. Ajouter les plafonds de simulation et interdire les nombres non finis.
3. Neutraliser les formules dans les CSV.
4. Durcir les écritures atomiques et les limites HTTP.
5. Épingler la chaîne CI et ajouter audit CVE, SAST et détection de secrets.
6. Durcir les chargeurs, chemins et informations exportées.
