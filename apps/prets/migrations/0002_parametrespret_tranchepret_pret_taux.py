from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('prets', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ParametresPret',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('montant_min', models.DecimalField(decimal_places=2, default=10000, max_digits=14)),
                ('montant_max', models.DecimalField(decimal_places=2, default=5000000, max_digits=14)),
                ('duree_min', models.IntegerField(default=1)),
                ('duree_max', models.IntegerField(default=36)),
                ('taux_defaut', models.DecimalField(decimal_places=2, default=5.0, help_text='Taux annuel par défaut (%) si aucune tranche ne correspond', max_digits=5)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('modifie_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parametres_modifies', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Paramètres de prêt',
            },
        ),
        migrations.CreateModel(
            name='TranchePret',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('montant_min', models.DecimalField(decimal_places=2, max_digits=14, validators=[django.core.validators.MinValueValidator(0)])),
                ('montant_max', models.DecimalField(blank=True, decimal_places=2, help_text="Laisser vide pour 'et plus'", max_digits=14, null=True)),
                ('taux_annuel', models.DecimalField(decimal_places=2, help_text="Taux d'intérêt annuel en %", max_digits=5)),
                ('libelle', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'verbose_name': 'Tranche de prêt',
                'verbose_name_plural': 'Tranches de prêt',
                'ordering': ['montant_min'],
            },
        ),
        migrations.AddField(
            model_name='pret',
            name='taux_annuel',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='pret',
            name='montant_interets',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='echeance',
            name='montant_capital',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='echeance',
            name='montant_interet',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AlterField(
            model_name='pret',
            name='montant_total',
            field=models.DecimalField(decimal_places=2, max_digits=14),
        ),
        migrations.AlterField(
            model_name='pret',
            name='mensualite',
            field=models.DecimalField(decimal_places=2, max_digits=14),
        ),
        migrations.AlterField(
            model_name='echeance',
            name='montant_du',
            field=models.DecimalField(decimal_places=2, max_digits=14),
        ),
    ]
