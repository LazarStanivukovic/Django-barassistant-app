#Andrej Veličkov 0569/2022
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from projekat.models import Zaposleni, Artikal, TipArtikla, Polje


class UnitTestAdmin(TestCase):
    """Jedinični testovi za administratorske view-ove."""

    def setUp(self):
        """Kreira admin korisnika i prijavljuje ga u sistem."""
        self.user = User.objects.create_user(
            username='admin1',
            password='123',
            first_name='Admin',
            last_name='Test',
            email='admin@test.com',
            is_staff=True,
            is_superuser=True
        )
        self.zaposleni = Zaposleni.objects.create(user=self.user, tip='A')
        self.client.login(username='admin1', password='123')

    def test_admin_profil_view(self):
        """Test da profil stranica vraća 200 i koristi ispravan template."""
        url = reverse('admin')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/profil.html')

    def test_pregled_zaposlenih_view(self):
        """Test da pregled zaposlenih vraća 200 i koristi odgovarajući template."""
        url = reverse('zaposleni')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/zaposleni.html')
        self.assertIn('zaposleni', response.context)

    def test_dodaj_zaposlenog_post(self):
        """Test dodavanja novog zaposlenog (POST)."""
        url = reverse('dodaj_zaposlenog')
        data = {
            'first_name': 'Pera',
            'last_name': 'Peric',
            'email': 'pera@example.com',
            'username': 'pera',
            'password': '123',
            'tip': 'K'
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('zaposleni'))
        self.assertTrue(Zaposleni.objects.filter(user__username='pera').exists())

    def test_pregled_artikala_view(self):
        """Test da pregled artikala vraća 200 i renderuje ispravan template."""
        tip = TipArtikla.objects.create(naziv='Piće')
        Artikal.objects.create(
            naziv='Sok',
            tip_artikla=tip,
            cena=200,
            velicina_serviranja='',
            kolicina_na_stanju=0
        )
        url = reverse('artikli')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/artikal.html')
        self.assertIn('artikli', response.context)
        self.assertEqual(len(response.context['artikli']), 1)

    def test_dodaj_artikal_post(self):
        """Test da se novi artikal može uspešno dodati — admin ne unosi količinu ni veličinu."""
        tip = TipArtikla.objects.create(naziv='Hrana')
        url = reverse('dodaj_artikal')
        data = {
            'naziv': 'Pizza',
            'cena': 600,
            'tip': tip.id
        }
        response = self.client.post(url, data)

        self.assertRedirects(response, reverse('artikli'))

        art = Artikal.objects.get(naziv='Pizza')
        self.assertEqual(art.kolicina_na_stanju, 0)
        self.assertEqual(art.velicina_serviranja, '')
        self.assertEqual(art.cena, 600)

    def test_promeni_cenu_view(self):
        """Test da se cena artikla može prikazati i promeniti."""
        tip = TipArtikla.objects.create(naziv='Piće')
        art = Artikal.objects.create(
            naziv='Kafa',
            tip_artikla=tip,
            cena=100,
            velicina_serviranja='',
            kolicina_na_stanju=0
        )
        url = reverse('promeni_cenu')

        response = self.client.post(url, {'id': art.id})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/promeni_cenu.html')

        response2 = self.client.post(url, {'id': art.id, 'nova_cena': 150})
        self.assertRedirects(response2, reverse('artikli'))

        art.refresh_from_db()
        self.assertEqual(art.cena, 150)

    def test_pregled_tipova_artikala_view(self):
        """Test da pregled tipova artikala vraća listu i pravi template."""
        TipArtikla.objects.create(naziv='Kafa')
        url = reverse('tipovi_artikala')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/tipovi_artikala.html')
        self.assertIn('artikli', response.context)
        self.assertEqual(len(response.context['artikli']), 1)

    def test_dodaj_tip_artikla_post(self):
        """Test da se novi tip artikla može dodati."""
        url = reverse('dodaj_tip_artikla')
        response = self.client.post(url, {'naziv': 'Nova Kategorija'})
        self.assertRedirects(response, reverse('tipovi_artikala'))
        self.assertTrue(TipArtikla.objects.filter(naziv='Nova Kategorija').exists())

    def test_raspored_stolova_view(self):
        """Test da se raspored stolova iscrtava bez greške."""
        Polje.objects.create(x=0, y=0)
        url = reverse('raspored_stolova')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/raspored_stolova.html')
        self.assertIn('polja', response.context)
