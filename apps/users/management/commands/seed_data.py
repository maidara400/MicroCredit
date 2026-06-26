from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

CLIENTS = [
    {'first_name': 'Aminata',    'last_name': 'Sow',      'username': 'aminata_sow',    'email': 'aminata.sow@gmail.com',    'telephone': '77 123 45 67', 'adresse': 'Dakar, Plateau'},
    {'first_name': 'Ibrahima',   'last_name': 'Diallo',   'username': 'ibrahima_d',     'email': 'ibrahima.diallo@gmail.com','telephone': '78 234 56 78', 'adresse': 'Dakar, Parcelles Assainies'},
    {'first_name': 'Fatou',      'last_name': 'Ndiaye',   'username': 'fatou_ndiaye',   'email': 'fatou.ndiaye@yahoo.fr',    'telephone': '76 345 67 89', 'adresse': 'Thiès, Centre'},
    {'first_name': 'Moussa',     'last_name': 'Gueye',    'username': 'moussa_gueye',   'email': 'moussa.gueye@gmail.com',   'telephone': '70 456 78 90', 'adresse': 'Saint-Louis'},
    {'first_name': 'Mariama',    'last_name': 'Ba',       'username': 'mariama_ba',     'email': 'mariama.ba@hotmail.com',   'telephone': '77 567 89 01', 'adresse': 'Dakar, Almadies'},
    {'first_name': 'Ousmane',    'last_name': 'Fall',     'username': 'ousmane_fall',   'email': 'ousmane.fall@gmail.com',   'telephone': '78 678 90 12', 'adresse': 'Ziguinchor'},
    {'first_name': 'Rokhaya',    'last_name': 'Mbaye',    'username': 'rokhaya_mbaye',  'email': 'rokhaya.mbaye@gmail.com',  'telephone': '76 789 01 23', 'adresse': 'Kaolack'},
    {'first_name': 'Cheikh',     'last_name': 'Diouf',    'username': 'cheikh_diouf',   'email': 'cheikh.diouf@gmail.com',   'telephone': '70 890 12 34', 'adresse': 'Dakar, Medina'},
    {'first_name': 'Aissatou',   'last_name': 'Sarr',     'username': 'aissatou_sarr',  'email': 'aissatou.sarr@gmail.com',  'telephone': '77 901 23 45', 'adresse': 'Rufisque'},
    {'first_name': 'Pape',       'last_name': 'Diop',     'username': 'pape_diop',      'email': 'pape.diop@yahoo.fr',       'telephone': '78 012 34 56', 'adresse': 'Dakar, Grand Yoff'},
]

AGENTS = [
    {'first_name': 'Seydou',     'last_name': 'Camara',   'username': 'agent_camara',   'email': 'seydou.camara@microcredit.sn',   'telephone': '77 100 00 01'},
    {'first_name': 'Ndèye',      'last_name': 'Toure',    'username': 'agent_toure',    'email': 'ndeye.toure@microcredit.sn',    'telephone': '77 100 00 02'},
    {'first_name': 'Babacar',    'last_name': 'Kane',     'username': 'agent_kane',     'email': 'babacar.kane@microcredit.sn',   'telephone': '77 100 00 03'},
    {'first_name': 'Khady',      'last_name': 'Faye',     'username': 'agent_faye',     'email': 'khady.faye@microcredit.sn',     'telephone': '77 100 00 04'},
    {'first_name': 'Mamadou',    'last_name': 'Diagne',   'username': 'agent_diagne',   'email': 'mamadou.diagne@microcredit.sn', 'telephone': '77 100 00 05'},
    {'first_name': 'Sokhna',     'last_name': 'Niang',    'username': 'agent_niang',    'email': 'sokhna.niang@microcredit.sn',   'telephone': '77 100 00 06'},
    {'first_name': 'Abdoulaye',  'last_name': 'Sy',       'username': 'agent_sy',       'email': 'abdoulaye.sy@microcredit.sn',   'telephone': '77 100 00 07'},
    {'first_name': 'Coumba',     'last_name': 'Diallo',   'username': 'agent_cdiallo',  'email': 'coumba.diallo@microcredit.sn',  'telephone': '77 100 00 08'},
    {'first_name': 'Idrissa',    'last_name': 'Cisse',    'username': 'agent_cisse',    'email': 'idrissa.cisse@microcredit.sn',  'telephone': '77 100 00 09'},
    {'first_name': 'Awa',        'last_name': 'Dieng',    'username': 'agent_dieng',    'email': 'awa.dieng@microcredit.sn',      'telephone': '77 100 00 10'},
]


class Command(BaseCommand):
    help = 'Génère 10 clients et 10 agents avec des données réalistes'

    def handle(self, *args, **options):
        created_clients = []
        created_agents = []

        self.stdout.write('\n--- Création des clients ---')
        for data in CLIENTS:
            if User.objects.filter(email=data['email']).exists():
                self.stdout.write(self.style.WARNING(f"  [SKIP] {data['email']}"))
                continue
            user = User(**data, role='client')
            user.set_password('Client1234!')
            user.save()
            created_clients.append(user)
            self.stdout.write(self.style.SUCCESS(f"  [OK] {user.get_full_name()} — {user.email}"))

        self.stdout.write('\n--- Création des agents ---')
        for data in AGENTS:
            if User.objects.filter(email=data['email']).exists():
                self.stdout.write(self.style.WARNING(f"  [SKIP] {data['email']}"))
                continue
            user = User(**data, role='agent')
            user.set_password('Agent1234!')
            user.save()
            created_agents.append(user)
            self.stdout.write(self.style.SUCCESS(f"  [OK] {user.get_full_name()} — {user.email}"))

        self.stdout.write(self.style.SUCCESS(
            f'\nTerminé : {len(created_clients)} clients et {len(created_agents)} agents créés.'
        ))
        self.stdout.write('\nMot de passe clients : Client1234!')
        self.stdout.write('Mot de passe agents  : Agent1234!')
