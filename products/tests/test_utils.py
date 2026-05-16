"""
Utilitários e funções auxiliares para testes do aplicativo de produtos.
"""

from django.test import Client, TestCase

from products.tests.factories import (
    UserFactory,
)


class BaseTestCase(TestCase):
    """
    Classe base de teste com configuração comum e utilitários.
    Fornece setup padrão com cliente, usuário e outros usuários para testes.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create()
        self.other_user = UserFactory.create(username="otheruser")
        self.client.login(username="testuser", password="testpass123")

    def get_form_errors(self, response):
        """Get form errors from response context"""
        if "form" in response.context:
            return response.context["form"].errors
        return {}

    def clear_session_key(self, key):
        """Limpa uma chave específica da sessão do Django"""
        session = self.client.session
        session[key] = {}
        session.save()
