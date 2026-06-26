from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée les comptes de démonstration (admin, agent, client)'

    def handle(self, *args, **options):
        comptes = [
            {
                'email': 'admin@microcredit.sn',
                'username': 'admin_mc',
                'first_name': 'Super',
                'last_name': 'Admin',
                'role': 'admin',
                'password': 'Admin1234!',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'email': 'agent@microcredit.sn',
                'username': 'agent_mc',
                'first_name': 'Moussa',
                'last_name': 'Diallo',
                'role': 'agent',
                'password': 'Agent1234!',
            },
            {
                'email': 'client@microcredit.sn',
                'username': 'client_mc',
                'first_name': 'Aminata',
                'last_name': 'Sow',
                'role': 'client',
                'telephone': '77 123 45 67',
                'password': 'Client1234!',
            },
        ]

        for data in comptes:
            password = data.pop('password')
            email = data['email']
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f'  [SKIP] {email} existe déjà'))
                continue
            user = User(**data)
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'  [OK] {email} créé ({data["role"]})'))

        self.stdout.write(self.style.SUCCESS('\nComptes de démo prêts !'))
        self.stdout.write('  admin@microcredit.sn   / Admin1234!')
        self.stdout.write('  agent@microcredit.sn   / Agent1234!')
        self.stdout.write('  client@microcredit.sn  / Client1234!')
