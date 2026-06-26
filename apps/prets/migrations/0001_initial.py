import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('demandes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pret',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('montant_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('mensualite', models.DecimalField(decimal_places=2, max_digits=12)),
                ('duree_mois', models.IntegerField()),
                ('statut', models.CharField(choices=[('actif', 'Actif'), ('solde', 'Soldé')], default='actif', max_length=10)),
                ('date_debut', models.DateField()),
                ('date_fin_prevue', models.DateField()),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prets', to=settings.AUTH_USER_MODEL)),
                ('demande', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='pret', to='demandes.demandepret')),
            ],
            options={
                'verbose_name': 'Prêt',
                'verbose_name_plural': 'Prêts',
                'ordering': ['-date_debut'],
            },
        ),
        migrations.CreateModel(
            name='Echeance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.IntegerField()),
                ('montant_du', models.DecimalField(decimal_places=2, max_digits=12)),
                ('date_echeance', models.DateField()),
                ('date_paiement', models.DateTimeField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('paye', 'Payée'), ('en_retard', 'En retard')], default='en_attente', max_length=15)),
                ('pret', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='echeances', to='prets.pret')),
            ],
            options={
                'verbose_name': 'Échéance',
                'verbose_name_plural': 'Échéances',
                'ordering': ['numero'],
                'unique_together': {('pret', 'numero')},
            },
        ),
    ]
