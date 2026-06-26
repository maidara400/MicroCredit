from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from dateutil.relativedelta import relativedelta

User = get_user_model()

SCENARIOS = [
    # (client_email, montant, duree, statut_pret)
    ('aminata.sow@gmail.com',       500000,  12, 'actif'),
    ('ibrahima.diallo@gmail.com',   200000,  6,  'actif'),
    ('fatou.ndiaye@yahoo.fr',       1000000, 24, 'solde'),
    ('moussa.gueye@gmail.com',      350000,  18, 'actif'),
    ('mariama.ba@hotmail.com',      150000,  6,  'solde'),
    ('ousmane.fall@gmail.com',      750000,  12, 'actif'),
    ('rokhaya.mbaye@gmail.com',     2000000, 36, 'actif'),
    ('cheikh.diouf@gmail.com',      100000,  3,  'solde'),
    ('aissatou.sarr@gmail.com',     600000,  24, 'actif'),
    ('pape.diop@yahoo.fr',          450000,  18, 'actif'),
]


class Command(BaseCommand):
    help = 'Génère des demandes et prêts de démo pour tous les clients'

    def handle(self, *args, **options):
        from apps.demandes.models import DemandePret
        from apps.prets.models import Pret, Echeance, ParametresPret, TranchePret

        # Créer les tranches de taux si elles n'existent pas
        if not TranchePret.objects.exists():
            TranchePret.objects.bulk_create([
                TranchePret(montant_min=10000, montant_max=199999, taux_annuel=8, libelle='Petits montants'),
                TranchePret(montant_min=200000, montant_max=999999, taux_annuel=6, libelle='Montants moyens'),
                TranchePret(montant_min=1000000, montant_max=None, taux_annuel=5, libelle='Grands montants'),
            ])
            self.stdout.write(self.style.SUCCESS('Tranches de taux créées.'))

        # Récupérer un agent pour l'approbation
        agent = User.objects.filter(role='agent').first()
        if not agent:
            self.stdout.write(self.style.ERROR('Aucun agent trouvé. Lancez seed_demo d\'abord.'))
            return

        created = 0
        for email, montant, duree, statut_pret in SCENARIOS:
            try:
                client = User.objects.get(email=email)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Client introuvable : {email}'))
                continue

            if Pret.objects.filter(client=client).exists():
                self.stdout.write(self.style.WARNING(f'[SKIP] {email} a déjà un prêt'))
                continue

            montant_d = Decimal(str(montant))

            # Créer la demande
            demande = DemandePret.objects.create(
                client=client,
                montant=montant_d,
                duree_mois=duree,
                motif='Demande générée par seed_prets',
                statut='approuve',
                agent=agent,
                date_traitement=timezone.now(),
            )

            # Déterminer le taux
            from django.db.models import Q
            tranche = TranchePret.objects.filter(montant_min__lte=montant_d).filter(
                Q(montant_max__isnull=True) | Q(montant_max__gte=montant_d)
            ).order_by('-montant_min').first()
            taux_annuel = Decimal(str(tranche.taux_annuel)) if tranche else Decimal('5')

            # Calculer les échéances
            date_debut = date.today() - relativedelta(months=duree // 2 if statut_pret == 'solde' else 1)
            date_fin = date_debut + relativedelta(months=duree)
            r = taux_annuel / Decimal('12') / Decimal('100')

            if r == 0:
                mensualite = (montant_d / duree).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                echeances_data = [{'capital': mensualite, 'interet': Decimal('0'), 'total': mensualite}] * duree
                montant_interets = Decimal('0')
            else:
                facteur = (1 + r) ** duree
                mensualite = (montant_d * r * facteur / (facteur - 1)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                capital_restant = montant_d
                montant_interets = Decimal('0')
                echeances_data = []
                for i in range(1, duree + 1):
                    interet = (capital_restant * r).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    capital = (mensualite - interet).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    if i == duree:
                        capital = capital_restant
                    montant_interets += interet
                    echeances_data.append({'capital': capital, 'interet': interet, 'total': capital + interet})
                    capital_restant -= capital

            pret = Pret.objects.create(
                demande=demande, client=client,
                montant_total=montant_d, mensualite=mensualite, duree_mois=duree,
                taux_annuel=taux_annuel, montant_interets=montant_interets,
                date_debut=date_debut, date_fin_prevue=date_fin,
                statut=statut_pret,
            )

            echeances_objs = []
            for i, ed in enumerate(echeances_data, 1):
                statut_ech = 'paye' if statut_pret == 'solde' else ('paye' if i <= duree // 3 else 'en_attente')
                date_ech = date_debut + relativedelta(months=i)
                echeances_objs.append(Echeance(
                    pret=pret, numero=i,
                    montant_capital=ed['capital'], montant_interet=ed['interet'], montant_du=ed['total'],
                    date_echeance=date_ech,
                    date_paiement=timezone.now() if statut_ech == 'paye' else None,
                    statut=statut_ech,
                ))
            Echeance.objects.bulk_create(echeances_objs)

            created += 1
            self.stdout.write(self.style.SUCCESS(
                f'[OK] {client.get_full_name()} — {montant_d} FCFA / {duree}mois @ {taux_annuel}% ({statut_pret})'
            ))

        self.stdout.write(self.style.SUCCESS(f'\nTerminé : {created} prêts créés.'))
