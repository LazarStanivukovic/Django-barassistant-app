# Lazar Stanivukovic 0590/2022
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from projekat.models import Zaposleni
from unittest.mock import patch

class UnitTestPrijava(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='123', email='test@example.com')
        self.konobar = Zaposleni.objects.create(user=self.user, tip='K')

    def test_prijava_success(self):
        """POST with correct credentials redirects according to role"""
        response = self.client.post(reverse('prijava'), {'username': 'testuser', 'password': '123'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('konobar'))

    def test_odjava_success(self):
        """Authenticated user logs out successfully"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(reverse('odjava'))
        self.assertFalse('_auth_user_id' in self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('prijava'))

    @patch('projekat.views.prijavaView.reset_password')
    def test_restauracija_success(self, mock_reset):
        """POST with existing email triggers password reset"""
        mock_reset.return_value = None
        response = self.client.post(reverse('restauracija'), {'email': 'test@example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'prijava/restauracija.html')
        self.assertEqual(response.context['msg'], 'Lozinka poslata')
        self.assertTrue(response.context['success'])
        mock_reset.assert_called_once_with(self.user)
