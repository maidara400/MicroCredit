# MicroCredit

Plateforme de gestion de microcrédit. Les clients soumettent des demandes de prêt, les agents de crédit instruisent et valident les dossiers, et le système génère automatiquement le plan de remboursement avec calcul des intérêts par amortissement constant.

## Stack technique

| Couche | Technologies |
|--------|-------------|
| **Backend** | Python 3.11 / Django 4.2 / Django REST Framework 3.15 |
| **Authentification** | JWT via `djangorestframework-simplejwt` (access 2h, refresh 7j) |
| **Documentation API** | Swagger UI via `drf-spectacular` |
| **Base de données** | SQLite (développement) |
| **Frontend** | HTML / CSS / JavaScript Vanilla (SPA) / Chart.js 4.4 |

## Installation

```bash
# 1. Cloner le repo
git clone https://github.com/maidara400/MicroCredit.git
cd MicroCredit

# 2. Créer et activer le virtualenv
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows (PowerShell)

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et renseigner SECRET_KEY

# 5. Appliquer les migrations
python manage.py migrate

# 6. Créer les comptes de démo
python manage.py seed_demo

# 7. Créer les prêts et tranches de taux de démo
python manage.py seed_prets

# 8. Lancer le serveur
python manage.py runserver 8080
```

## Variables d'environnement

| Variable | Description | Exemple |
|----------|-------------|---------|
| `SECRET_KEY` | Clé secrète Django | `django-insecure-xxx...` |
| `DEBUG` | Mode debug | `True` |
| `ALLOWED_HOSTS` | Hôtes autorisés | `localhost,127.0.0.1` |

## Endpoints API

### Authentification & Utilisateurs

| Méthode | URL | Rôle requis | Description |
|---------|-----|-------------|-------------|
| POST | `/api/auth/register/` | Public | Inscription client |
| POST | `/api/auth/login/` | Public | Connexion → JWT |
| POST | `/api/auth/token/refresh/` | Public | Rafraîchir le token |
| GET | `/api/auth/me/` | Tous | Profil connecté |
| PATCH | `/api/auth/me/` | Tous | Modifier son profil |
| GET | `/api/auth/admin/stats/` | Admin | KPIs et statistiques globales |
| GET | `/api/auth/admin/users/` | Admin | Liste de tous les utilisateurs |
| POST | `/api/auth/admin/users/` | Admin | Créer un utilisateur |
| PATCH | `/api/auth/admin/users/{id}/` | Admin | Modifier / activer un utilisateur |

### Demandes de prêt

| Méthode | URL | Rôle requis | Description |
|---------|-----|-------------|-------------|
| GET | `/api/demandes/` | Client / Agent / Admin | Lister les demandes |
| POST | `/api/demandes/` | Client | Soumettre une demande |
| GET | `/api/demandes/{id}/` | Client / Agent / Admin | Détail d'une demande |
| POST | `/api/demandes/{id}/approuver/` | Agent / Admin | Approuver → génère le prêt |
| POST | `/api/demandes/{id}/refuser/` | Agent / Admin | Refuser avec motif |

### Prêts & Échéances

| Méthode | URL | Rôle requis | Description |
|---------|-----|-------------|-------------|
| GET | `/api/prets/` | Agent / Admin | Liste tous les prêts |
| GET | `/api/prets/dashboard/` | Client | Dashboard du client |
| GET | `/api/prets/{id}/echeances/` | Tous | Plan de remboursement |
| POST | `/api/prets/echeances/{id}/payer/` | Client | Enregistrer un paiement |
| GET | `/api/prets/echeances/en-retard/` | Agent / Admin | Échéances en retard |

### Configuration (Admin uniquement)

| Méthode | URL | Description |
|---------|-----|-------------|
| GET / PATCH | `/api/prets/config/parametres/` | Paramètres globaux (montant min/max, durée, taux défaut) |
| GET / POST | `/api/prets/config/tranches/` | Tranches de taux d'intérêt |
| GET / PATCH / DELETE | `/api/prets/config/tranches/{id}/` | Modifier ou supprimer une tranche |

Documentation interactive : `http://localhost:8080/api/docs/`

## Règles métier

| Règle | Description |
|-------|-------------|
| R1 | Un client ne peut avoir qu'un seul prêt actif à la fois |
| R2 | Un client ne peut avoir qu'une seule demande en attente |
| R3 | Le montant doit être dans la plage définie par l'admin |
| R4 | La durée doit être dans la plage définie par l'admin |
| R5 | L'approbation génère automatiquement toutes les échéances |
| R6 | Mensualité calculée par amortissement constant : `M = P × r(1+r)ⁿ / ((1+r)ⁿ - 1)` |
| R7 | Le taux est déterminé par la tranche correspondant au montant |
| R8 | Quand toutes les échéances sont payées, le prêt passe automatiquement à "soldé" |

## Comptes de démonstration

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Administrateur | admin@microcredit.sn | Admin1234! |
| Agent de crédit | agent@microcredit.sn | Agent1234! |
| Client | client@microcredit.sn | Client1234! |

## Auteur

**Mouhamed Aidara**  
Licence 3 Informatique — ISI — Année académique 2025-2026  
Projet Réserve 1 — Professeur Robert DIASSE
