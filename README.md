# MicroCredit

## Description
Plateforme de gestion de microcredit. Les clients soumettent des demandes de pret, les agents de credit instruisent et valident les dossiers, et le systeme suit les remboursements mensuels avec les echeances restantes.

## Stack technique
- **Backend :** Python 3.11 / Django 4.2 / Django REST Framework
- **Auth :** JWT via `djangorestframework-simplejwt`
- **Docs API :** Swagger UI via `drf-spectacular`
- **Base de donnees :** SQLite (dev)
- **Frontend :** HTML / CSS / JavaScript (Fetch API)

## Installation

```bash
# 1. Cloner le repo
git clone https://github.com/maidara400/MicroCredit.git
cd MicroCredit

# 2. Créer et activer le virtualenv
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Editer .env et renseigner SECRET_KEY

# 5. Appliquer les migrations
python manage.py migrate

# 6. Créer les comptes de demo
python manage.py seed_demo

# 7. Lancer le serveur
python manage.py runserver
```

## Variables d'environnement

| Variable | Description | Exemple |
|----------|-------------|---------|
| `SECRET_KEY` | Clé secrète Django | `django-insecure-xxx...` |
| `DEBUG` | Mode debug | `True` |
| `ALLOWED_HOSTS` | Hôtes autorisés | `localhost,127.0.0.1` |

## Endpoints API

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/auth/register/` | Inscription client |
| POST | `/api/auth/login/` | Connexion → JWT |
| POST | `/api/auth/token/refresh/` | Rafraîchir token |
| GET | `/api/auth/me/` | Profil connecté |
| POST | `/api/demandes/` | Soumettre une demande |
| GET | `/api/demandes/` | Lister les demandes |
| POST | `/api/demandes/{id}/approuver/` | Approuver un dossier |
| POST | `/api/demandes/{id}/refuser/` | Refuser un dossier |
| GET | `/api/prets/` | Lister les prêts |
| GET | `/api/prets/{id}/echeances/` | Plan de remboursement |
| POST | `/api/echeances/{id}/payer/` | Enregistrer un paiement |
| GET | `/api/admin/stats/` | Statistiques globales |

Documentation interactive : `http://localhost:8000/api/docs/`

## Comptes de demonstration

| Role | Email | Mot de passe |
|------|-------|--------------|
| Administrateur | admin@microcredit.sn | Admin1234! |
| Agent de crédit | agent@microcredit.sn | Agent1234! |
| Client | client@microcredit.sn | Client1234! |

## Auteur

**Mouhamed Aidara**  
Licence 3 Informatique — ISI — Année académique 2025-2026  
Projet Réserve 1 — Professeur Robert DIASSE
