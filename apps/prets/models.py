from django.db import models
from django.conf import settings


class Pret(models.Model):
    STATUT_ACTIF = 'actif'
    STATUT_SOLDE = 'solde'

    STATUT_CHOICES = [
        (STATUT_ACTIF, 'Actif'),
        (STATUT_SOLDE, 'Soldé'),
    ]

    demande = models.OneToOneField(
        'demandes.DemandePret',
        on_delete=models.CASCADE,
        related_name='pret'
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prets'
    )
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    mensualite = models.DecimalField(max_digits=12, decimal_places=2)
    duree_mois = models.IntegerField()
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default=STATUT_ACTIF)
    date_debut = models.DateField()
    date_fin_prevue = models.DateField()

    class Meta:
        verbose_name = 'Prêt'
        verbose_name_plural = 'Prêts'
        ordering = ['-date_debut']

    def __str__(self):
        return f"Prêt #{self.pk} — {self.client} — {self.montant_total} FCFA ({self.statut})"

    @property
    def echeances_payees(self):
        return self.echeances.filter(statut='paye').count()

    @property
    def echeances_restantes(self):
        return self.echeances.exclude(statut='paye').count()

    @property
    def montant_rembourse(self):
        from django.db.models import Sum
        return self.echeances.filter(statut='paye').aggregate(total=Sum('montant_du'))['total'] or 0

    @property
    def montant_restant(self):
        return float(self.montant_total) - float(self.montant_rembourse)


class Echeance(models.Model):
    STATUT_EN_ATTENTE = 'en_attente'
    STATUT_PAYE = 'paye'
    STATUT_EN_RETARD = 'en_retard'

    STATUT_CHOICES = [
        (STATUT_EN_ATTENTE, 'En attente'),
        (STATUT_PAYE, 'Payée'),
        (STATUT_EN_RETARD, 'En retard'),
    ]

    pret = models.ForeignKey(Pret, on_delete=models.CASCADE, related_name='echeances')
    numero = models.IntegerField()
    montant_du = models.DecimalField(max_digits=12, decimal_places=2)
    date_echeance = models.DateField()
    date_paiement = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default=STATUT_EN_ATTENTE)

    class Meta:
        verbose_name = 'Échéance'
        verbose_name_plural = 'Échéances'
        ordering = ['numero']
        unique_together = ['pret', 'numero']

    def __str__(self):
        return f"Échéance #{self.numero} — Prêt #{self.pret_id} — {self.statut}"
