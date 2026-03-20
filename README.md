# Application de comptabilite des depenses

Application web de suivi financier personnel construite avec Django.

Le projet permet d'enregistrer des depenses et des gains, de les organiser dans des feuilles de suivi, de preparer des entrees planifiees, puis d'analyser l'evolution du solde dans le temps.

## Objectif du projet

L'application doit permettre de :

- creer une feuille de suivi de depenses, avec ou sans compte utilisateur ;
- enregistrer des depenses et des gains ;
- definir un solde initial et calculer le solde courant apres chaque entree validee ;
- preparer des depenses a l'avance ;
- gerer des modeles recurrents pour eviter les saisies repetitives ;
- visualiser les mouvements financiers au fil du temps ;
- analyser les depenses et les gains par categorie ;
- exporter les donnees en CSV et en Excel.

## Regles metier

### Types d'entree

- `gain`
- `depense`

### Statuts d'entree

- `brouillon`
- `planifiee`
- `validee`

### Categories prises en charge

- `food`
- `cagnote`
- `pret`
- `utilities`
- `transport`
- `extras`
- `autre`

## Fonctionnalites deja en place

- initialisation du projet Django ;
- creation de feuilles de depenses ;
- creation d'entrees de type gain ou depense ;
- prise en charge des statuts `brouillon`, `planifiee` et `validee` ;
- page d'accueil avec indicateurs de base ;
- liste dediee des mouvements ;
- filtres par feuille, type, categorie, statut et plage de dates ;
- premiers indicateurs analytiques sur les revenus, depenses et soldes ;
- gestion de modeles recurrents ;
- generation d'entrees planifiees depuis les modeles recurrents ;
- interface d'administration Django ;
- base de tests automatises.

## Fonctionnalites restantes

- export CSV des mouvements ;
- export Excel des mouvements ;
- visualisations graphiques plus avancees ;
- edition et suppression des feuilles, entrees et modeles ;
- validation automatique ou manuelle des entrees planifiees a leur date d'effet ;
- gestion complete des comptes utilisateurs si necessaire.

## Stack technique

- Python
- Django
- HTML
- CSS
- JavaScript
- SQLite en developpement

## Installation locale

### 1. Cloner le depot

```bash
git clone <url-du-repo>
cd comptable-depenses
```

### 2. Creer et activer l'environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Installer les dependances

```bash
pip install -r requirements.txt
```

### 4. Appliquer les migrations

```bash
python manage.py migrate
```

### 5. Lancer le serveur de developpement

```bash
python manage.py runserver
```

L'application est alors accessible a l'adresse `http://127.0.0.1:8000/`.

## Commandes utiles

### Verifier la configuration Django

```bash
python manage.py check
```

### Lancer les tests

```bash
python manage.py test
```

### Creer un superutilisateur

```bash
python manage.py createsuperuser
```

## Structure actuelle du projet

```text
config/      Configuration Django
expenses/    Application metier principale
manage.py    Point d'entree Django
README.md    Documentation du projet
```

## Strategie de branches proposee

- `main` : branche stable ;
- `develop` : integration des fonctionnalites en cours ;
- `feature/export-csv-excel` : export des donnees ;
- `feature/charts-dashboard` : visualisations et tableaux de bord ;
- `feature/planned-entry-workflow` : cycle de vie des entrees planifiees ;
- `feature/crud-management` : edition et suppression des donnees.

## Vision produit

Le projet vise une application simple a deployer, lisible et evolutive, capable de servir d'outil de suivi budgetaire personnel ou familial.
