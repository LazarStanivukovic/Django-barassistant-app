#Sofija Pavlovic 0340/2022
from datetime import date
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User

from projekat.models import (
    Zaposleni,
    Recenzija,
    Smena,
    Polje,
    Sto,
    Racun,
    Stavka,
    Artikal,
    TipArtikla,
)


class UnitTestKonobar(TestCase):
    """Jedinični testovi za konobarske view-ove."""

    def setUp(self):
        """Kreira konobara, sto, račun i osnovne podatke, i prijavljuje korisnika."""
        self.user = User.objects.create_user(
            username='konobar1',
            password='123',
            first_name='Pera',
            last_name='Peric',
            email='konobar@test.com',
            is_staff=False,
            is_superuser=False,
        )
        self.konobar = Zaposleni.objects.create(user=self.user, tip='K')
        self.client.login(username='konobar1', password='123')

        self.tip = TipArtikla.objects.create(naziv='Piće')
        self.artikal = Artikal.objects.create(
            naziv='Kafa',
            tip_artikla=self.tip,
            cena=100,
            velicina_serviranja='200ml',
            kolicina_na_stanju=10,
        )

        self.polje1 = Polje.objects.create(x=0, y=0)
        self.sto1 = Sto.objects.create(polje=self.polje1)

        self.racun1 = Racun.objects.create(
            konobar=self.konobar,
            sto=self.sto1,
            status='O',
            datum_otvaranja=timezone.now().date(),
        )

        self.stavka1 = Stavka.objects.create(
            racun=self.racun1,
            artikal=self.artikal,
            kolicina=2,
            cena=200,
        )

        Recenzija.objects.create(racun=self.racun1, konobar=self.konobar, ocena=4)
        Recenzija.objects.create(racun=self.racun1, konobar=self.konobar, ocena=2)

        Smena.objects.create(
            konobar=self.konobar,
            datum=date.today(),
            broj_smene=1,
        )

    def test_konobar_profil_view(self):
        """Profil konobara se učitava i vraća prosečnu ocenu i broj ocena."""
        url = reverse('konobar')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'konobar/profil.html')
        self.assertIn('prosecnaOcena', response.context)
        self.assertIn('brojOcena', response.context)

        self.assertEqual(response.context['brojOcena'], 2)
        self.assertEqual(response.context['prosecnaOcena'], 3.0)

    def test_smene_view(self):
        """Raspored smena vraća 200, koristi pravi template i kontekst sa 7 dana."""
        url = reverse('smene')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'konobar/raspored.html')
        self.assertIn('week_dates', response.context)
        self.assertIn('firstShift', response.context)
        self.assertIn('secondShift', response.context)

        self.assertEqual(len(response.context['week_dates']), 7)

    def test_stolovi_view(self):
        """Prikaz stolova (raspored lokala) vraća 200 i kontekst 'polja'."""
        url = reverse('stolovi')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'konobar/stolovi.html')
        self.assertIn('polja', response.context)

    def test_racun_view_get(self):
        """Pregled računa za određeni sto vraća otvoren=1 i listu stavki."""
        url = reverse('racun', args=[self.sto1.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'konobar/racun.html')
        self.assertIn('stavke', response.context)
        self.assertIn('otvoren', response.context)
        self.assertIn('konobar', response.context)

        self.assertEqual(response.context['otvoren'], 1)
        self.assertEqual(response.context['konobar'], self.user.username)
        self.assertEqual(len(response.context['stavke']), 1)

    def test_racun_post_open(self):
        """POST sa action='open' otvara novi račun za sto koji ga nema."""
        polje2 = Polje.objects.create(x=1, y=1)
        sto2 = Sto.objects.create(polje=polje2)

        url = reverse('racun', args=[sto2.id])
        response = self.client.post(url, {'action': 'open'})

        self.assertRedirects(response, reverse('racun', args=[sto2.id]))

        self.assertTrue(
            Racun.objects.filter(sto=sto2, status='O', konobar=self.konobar).exists()
        )

    def test_racun_post_inc(self):
        """POST sa action='inc' uvećava količinu stavke i smanjuje stanje artikla."""
        url = reverse('racun', args=[self.sto1.id])
        response = self.client.post(
            url,
            {
                'id': self.stavka1.id,
                'action': 'inc',
            },
        )

        self.assertRedirects(response, reverse('racun', args=[self.sto1.id]))

        self.stavka1.refresh_from_db()
        self.artikal.refresh_from_db()

        self.assertEqual(self.stavka1.kolicina, 3)
        self.assertEqual(self.stavka1.cena, 300)
        self.assertEqual(self.artikal.kolicina_na_stanju, 9)

    def test_stavka_view_get(self):
        """GET na /stavka/<sto_id> vraća formu za dodavanje nove stavke."""
        url = reverse('stavka', args=[self.sto1.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'konobar/stavka.html')
        self.assertIn('artikli', response.context)
        self.assertIn('nedovoljno', response.context)
        self.assertEqual(response.context['nedovoljno'], "0")

    def test_stavka_post_dodaj(self):
        """POST na /stavka/<sto_id> kreira novu stavku na otvorenom računu tog stola."""
        polje3 = Polje.objects.create(x=2, y=2)
        sto3 = Sto.objects.create(polje=polje3)
        racun3 = Racun.objects.create(
            konobar=self.konobar,
            sto=sto3,
            status='O',
            datum_otvaranja=timezone.now().date(),
        )

        novi_artikal = Artikal.objects.create(
            naziv='Sok',
            tip_artikla=self.tip,
            cena=150,
            velicina_serviranja='0.33l',
            kolicina_na_stanju=20,
        )

        url = reverse('stavka', args=[sto3.id])
        response = self.client.post(
            url,
            {
                'nazivArtikla': 'Sok',
                'kolicinaArtikla': '3',
            },
        )

        self.assertRedirects(response, reverse('racun', args=[sto3.id]))

        nova_stavka = Stavka.objects.get(racun=racun3, artikal=novi_artikal)
        self.assertEqual(nova_stavka.kolicina, 3)
        self.assertEqual(nova_stavka.cena, 450)
