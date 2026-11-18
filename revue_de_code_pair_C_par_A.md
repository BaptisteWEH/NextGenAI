# Revue de Code - Branche `Pair_C`

Cette revue est basée sur la structure et les métadonnées de l'archive `NextGenAI-Pair_C.zip`.

## 1. Architecture et Structure du Dépôt

L'architecture est globalement orientée vers un environnement d'apprentissage ou d'évaluation (TDs, lectures, évaluations).

### ✅ Points forts
* **Organisation logique :** La séparation entre `kit-td1`, `lectures`, `reports`, et `templates` est claire.
* **Documentation abondante :** La présence de nombreux fichiers d'énoncés et de rapports (`.md`, `.html`, `.pdf`) est excellente pour le contexte pédagogique.
* **Données structurées :** Les données (fichiers SQLite, CSV) sont bien circonscrites dans `kit-td1/data/`.

### ⚠️ Points d'attention et Améliorations
* **Redondance des formats :** De nombreux documents (ex: `enonce-td1-en`, `syllabus-en`) existent en triple format (Markdown, HTML, PDF). Il est recommandé de ne versionner que le Markdown et de générer les PDF/HTML via une CI/CD (GitHub Actions).
* **Nommage et hiérarchie `kit-td1` :** Le dossier `kit-td1` contient de manière surprenante les sous-dossiers `TD1`, `TD2`, et `TD3`. Il devrait être renommé en `labs` ou `tds` pour être cohérent avec son contenu.
* **Racine encombrée :** Des fichiers comme `assessment-en.*`, `before-td1-en.*`, et `submission-en.*` pourraient être regroupés dans un dossier `docs/` ou `course_info/`.

## 2. Code Python et Bonnes Pratiques

Le dépôt contient plusieurs scripts Python, principalement dans l'espace des TDs.

### 🔍 Éléments à vérifier (Analyse statique recommandée)
* **Modularité :** Le script `skeleton-multi-llm-en.py` est très volumineux (~41 Ko). Il devrait probablement être divisé en modules plus petits (API calls, data processing).
* **Gestion des dépendances :** Le fichier `requirements.txt` ne pèse que 17 octets. C'est anormalement petit pour un projet utilisant des LLMs et SQLite. Il manque fort probablement des dépendances critiques (ex: `openai`, `pandas`, etc.).
* **Sécurité SQL :** `sandbox_sqlite.py` interagit avec `boutique.sqlite`. Vérifier qu'il n'y a pas de risque d'injection SQL si des LLMs génèrent des requêtes exécutées automatiquement.
* **Sécurité des clés API :** S'assurer qu'aucune clé API n'est hardcodée dans les scripts, en particulier dans `skeleton-multi-llm-en.py`, et qu'un `.env` est bien utilisé (et listé dans `.gitignore`).

## 3. Données et Fichiers de Traces

### ✅ Points forts
* **Conservation des traces :** La sauvegarde des logs d'exécution (`traces-A.csv`, `state-X.jsonl`) est très utile pour analyser et comparer le comportement des modèles IA.

### ⚠️ Points d'attention
* **Volume et Git History :** Les fichiers générés (`traces-td1.jsonl` de 115 Ko, multiples CSV) risquent d'alourdir l'historique Git si les étudiants relancent souvent les scripts. Il est souvent préférable de les ajouter au `.gitignore` et de ne versionner que les jeux de données de *référence*.
* **Vérification du `.gitignore` :** S'assurer qu'il exclut bien les environnements virtuels (`venv/`, `.venv/`), le cache (`__pycache__/`) et les fichiers de variables d'environnement (`.env`).

---

## 🎯 Plan d'action recommandé
1. **Restructurer les dossiers :** Renommer `kit-td1` et nettoyer la racine.
2. **Revoir le `requirements.txt` :** Générer un fichier complet avec `pip freeze > requirements.txt` ou utiliser un gestionnaire comme `poetry`.
3. **Mettre en place un `.gitignore` robuste :** Exclure les logs d'exécution de grande taille non essentiels.
4. **Refactoriser le code :** Découper `skeleton-multi-llm-en.py` pour une meilleure maintenabilité.