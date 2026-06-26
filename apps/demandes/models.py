from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class DemandePret(models.Model):
    STATUT_EN_ATTENTE = 'en_attente'
    STATUT_APPROUVE = 'approuve'
    STATUT_REFUSE = 'refuse'

    STATUT_CHOICES = [
        (STATUT_EN_ATTENTE, 'En attente'),
        (STATUT_APPROUVE, 'Approuvée'),
        (STATUT_REFUSE, 'Refusée'),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='demandes',
        limit_choices_to={'role': 'client'}
    )
    montant = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(10000), MaxValueValidator(5000000)]
    )
    duree_mois = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(36)]
    )
    motif = models.TextField()
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default=STATUT_EN_ATTENTE)
    date_soumission = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dossiers_traites',
        limit_choices_to={'role': 'agent'}
    )
    motif_refus = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Demande de prêt'
        verbose_name_plural = 'Demandes de prêt'
        ordering = ['-date_soumission']

    def __str__(self):
        return f"Demande #{self.pk} — {self.client} — {self.montant} FCFA ({self.statut})"
