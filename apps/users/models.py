from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CLIENT = 'client'
    ROLE_AGENT = 'agent'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_CLIENT, 'Client'),
        (ROLE_AGENT, 'Agent de crédit'),
        (ROLE_ADMIN, 'Administrateur'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_CLIENT)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    @property
    def is_client(self):
        return self.role == self.ROLE_CLIENT

    @property
    def is_agent(self):
        return self.role == self.ROLE_AGENT

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN
