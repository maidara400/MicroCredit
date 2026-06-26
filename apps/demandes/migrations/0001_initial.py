import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DemandePret',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('montant', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(10000), django.core.validators.MaxValueValidator(5000000)])),
                ('duree_mois', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(36)])),
                ('motif', models.TextField()),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('approuve', 'Approuvée'), ('refuse', 'Refusée')], default='en_attente', max_length=15)),
                ('date_soumission', models.DateTimeField(auto_now_add=True)),
                ('date_traitement', models.DateTimeField(blank=True, null=True)),
                ('motif_refus', models.TextField(blank=True)),
                ('agent', models.ForeignKey(blank=True, limit_choices_to={'role': 'agent'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dossiers_traites', to=settings.AUTH_USER_MODEL)),
                ('client', models.ForeignKey(limit_choices_to={'role': 'client'}, on_delete=django.db.models.deletion.CASCADE, related_name='demandes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Demande de prêt',
                'verbose_name_plural': 'Demandes de prêt',
                'ordering': ['-date_soumission'],
            },
        ),
    ]
