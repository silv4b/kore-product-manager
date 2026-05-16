"""
Mixin para simplificar testes que precisam de autenticação
"""

from django.test import Client, TestCase

from products.tests.factories import UserFactory


class AuthenticatedTestCase(TestCase):
    """Classe base para testes que precisam de autenticação"""

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.user = UserFactory.create_admin()
        self.client.force_login(self.user)

    def create_user(self, **kwargs):
        """Helper para criar usuários adicionais"""
        return UserFactory.create(**kwargs)

    def login_as(self, user):
        """Helper para fazer login como usuário específico"""
        self.client.force_login(user)
