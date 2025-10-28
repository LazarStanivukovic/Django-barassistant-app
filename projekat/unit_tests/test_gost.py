# Lazar Stanivukovic 0590/2022
from django.test import TestCase
from django.urls import reverse

from projekat.models import *


class UnitTestGost(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='konobar1',
            password='123',
            first_name='Marko',
            last_name='Markovic',
            email='marko@example.com'
        )

        self.zaposleni = Zaposleni.objects.create(
            user=self.user,
            tip='K'
        )

        self.polje = Polje.objects.create(
            x=1,
            y=2
        )

        self.sto = Sto.objects.create(
            polje=self.polje
        )

        self.racun = Racun.objects.create(
            konobar=self.zaposleni,
            sto=self.sto,
            status='O'
        )

        self.tip = TipArtikla.objects.create(
            naziv="Pivo"
        )

        self.artikal1 = Artikal.objects.create(
            naziv='Lav',
            cena=150,
            velicina_serviranja='',
            kolicina_na_stanju=1,
            tip_artikla=self.tip
        )

        self.artikal2 = Artikal.objects.create(
            naziv='Jelen',
            cena=300,
            velicina_serviranja='',
            kolicina_na_stanju=1,
            tip_artikla=self.tip
        )

        self.stavka1 = Stavka.objects.create(
            racun=self.racun,
            artikal=self.artikal1,
            kolicina=1,
            cena=150
        )

        self.stavka2 = Stavka.objects.create(
            racun=self.racun,
            artikal=self.artikal2,
            kolicina=2,
            cena=600
        )

        self.client.get(reverse('ulaz', args=[self.sto.id]))


    def test_pocetna_view(self):
        """Test that pocetna page renders correctly with context."""
        response = self.client.get(reverse('pocetna'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gost/pocetna.html')
        self.assertIn('ime', response.context)
        self.assertIn('id', response.context)
        self.assertEqual(response.context['id'], self.sto.id)

    def test_karta_pica_view(self):
        """Test karta_pica returns all artikli."""
        response = self.client.get(reverse('karta_pica'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gost/karta_pica.html')
        self.assertIn('artikli', response.context)
        self.assertEqual(len(response.context['artikli']), 2)

    def test_racun_gost_view(self):
        """Test racun_gost view returns konobar, stavke, ukupno."""
        response = self.client.get(reverse('racun_gost', args=[self.sto.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gost/racun.html')
        self.assertEqual(response.context['konobar'], self.zaposleni)
        self.assertEqual(len(response.context['stavke']), 2)
        self.assertEqual(response.context['ukupno'], 750)

    def test_oceni_nas_post_creates_or_updates_recenzija(self):
        """Test that oceni_nas POST creates new Recenzija."""
        url = reverse('oceni_nas')
        response = self.client.post(url, {'ocena': 4})

        self.assertRedirects(response, reverse('pocetna'))

        recenzija = Recenzija.objects.first()
        self.assertIsNotNone(recenzija)
        self.assertEqual(recenzija.ocena, 4)
        self.assertEqual(recenzija.racun, self.racun)
        self.assertEqual(recenzija.konobar, self.zaposleni)

        self.client.post(url, {'ocena': 3})
        recenzija.refresh_from_db()
        self.assertEqual(recenzija.ocena, 3)

