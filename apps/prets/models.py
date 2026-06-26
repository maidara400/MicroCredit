from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class ParametresPret(models.Model):
    """Singleton — paramètres globaux modifiables par l'admin."""
    montant_min = models.DecimalField(max_digits=14, decimal_places=2, default=10000)
    montant_max = models.DecimalField(max_digits=14, decimal_places=2, default=5000000)
    duree_min   = models.IntegerField(default=1)
    duree_max   = models.IntegerField(default=36)
    taux_defaut = models.DecimalField(max_digits=5, decimal_places=2, default=5.00,
                                      help_text="Taux annuel par défaut (%) si aucune tranche ne correspond")
    date_modification = models.DateTimeField(auto_now=True)
    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='parametres_modifies'
    )

    class Meta:
        verbose_name = 'Paramètres de prêt'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Paramètres — max {self.montant_max} FCFA / {self.duree_max} mois"


class TranchePret(models.Model):
    """Plage de montant avec taux d'intérêt annuel associé."""
    montant_min  = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    montant_max  = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                       help_text="Laisser vide pour 'et plus'")
    taux_annuel  = models.DecimalField(max_digits=5, decimal_places=2,
                                       help_text="Taux d'intérêt annuel en %")
    libelle      = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Tranche de prêt'
        verbose_name_plural = 'Tranches de prêt'
        ordering = ['montant_min']

    def __str__(self):
        plafond = f"{self.montant_max} FCFA" if self.montant_max else "+"
        return f"{self.montant_min}–{plafond} → {self.taux_annuel}%/an"


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
    montant_total    = models.DecimalField(max_digits=14, decimal_places=2)
    mensualite       = models.DecimalField(max_digits=14, decimal_places=2)
    duree_mois       = models.IntegerField()
    taux_annuel      = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    montant_interets = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    statut           = models.CharField(max_length=10, choices=STATUT_CHOICES, default=STATUT_ACTIF)
    date_debut       = models.DateField()
    date_fin_prevue  = models.DateField()

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

    pret             = models.ForeignKey(Pret, on_delete=models.CASCADE, related_name='echeances')
    numero           = models.IntegerField()
    montant_capital  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_interet  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    montant_du       = models.DecimalField(max_digits=14, decimal_places=2)
    date_echeance    = models.DateField()
    date_paiement    = models.DateTimeField(null=True, blank=True)
    statut           = models.CharField(max_length=15, choices=STATUT_CHOICES, default=STATUT_EN_ATTENTE)

    class Meta:
        verbose_name = 'Échéance'
        verbose_name_plural = 'Échéances'
        ordering = ['numero']
        unique_together = ['pret', 'numero']

    def __str__(self):
        return f"Échéance #{self.numero} — Prêt #{self.pret_id} — {self.statut}"
