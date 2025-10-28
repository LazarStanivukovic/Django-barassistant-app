# Aleksa Sekulic 0021/2022


from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from projekat.models import (
    Zaposleni, TipArtikla, Artikal, Dostava, Polje, Sto,
    Rezervacija, Racun, Stavka, Smena
)
from datetime import datetime, date, timedelta

class UnitTestMenadzer(TestCase):
    def setUp(self):
        self.client = Client()

        # Menadzer user
        self.user = User.objects.create_user(
            username='menadzer', password='test123',
            first_name='Lazar', last_name='Stanivukovic'
        )
        self.menadzer = Zaposleni.objects.create(user=self.user, tip='M')
        self.client.login(username='menadzer', password='test123')

        # Tip artikla i artikal
        self.tip_artikla = TipArtikla.objects.create(naziv='Piće')
        self.artikal = Artikal.objects.create(
            tip_artikla=self.tip_artikla,
            naziv='Kafa',
            cena=200,
            velicina_serviranja='200ml',
            kolicina_na_stanju=10
        )

        # Polje i sto
        self.polje = Polje.objects.create(x=1, y=1)
        self.sto = Sto.objects.create(polje=self.polje)

        # Konobar
        self.konobar_user = User.objects.create_user(username='konobar', password='123')
        self.konobar = Zaposleni.objects.create(user=self.konobar_user, tip='K')

        # Racun
        self.racun = Racun.objects.create(konobar=self.konobar, sto=self.sto, status='O')

    # ---- VIEW TESTS ----
    def test_menadzer_view(self):
        response = self.client.get(reverse('menadzer'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'menadzer/profil.html')

    def test_dostave_view(self):
        response = self.client.get(reverse('dostave'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'menadzer/dostava.html')

    def test_dodaj_dostavu_post(self):
        response = self.client.post(reverse('dodaj_dostavu'), {
            'artikal': self.artikal.id,
            'kolicina': 5,
            'status': 'U TOKU'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Dostava.objects.filter(kolicina=5).exists())

    def test_rezervacije_view(self):
        response = self.client.get(reverse('rezervacije'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'menadzer/rezervacija.html')

    def test_dodaj_rezervaciju(self):
        response = self.client.post(reverse('dodaj_rezervaciju'), {
            'sto': self.sto.id,
            'ime': 'Petar',
            'datum_vreme': (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
            'status': 'U TOKU'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Rezervacija.objects.filter(ime='Petar').exists())

    def test_raspored_po_smenama_view(self):
        response = self.client.get(reverse('raspored_po_smenama'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'menadzer/raspored.html')

    def test_dodaj_raspored_po_smenama(self):
        # Just GET the schedule page
        response = self.client.get(reverse('raspored_po_smenama'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'menadzer/raspored.html')
        self.assertIn('week_dates', response.context)
        self.assertIn('firstShift', response.context)
        self.assertIn('secondShift', response.context)

    def test_dodaj_konobara_creates_shift(self):
        today = date.today()
        response = self.client.post(reverse('dodaj_konobara') + f'?date={today.isoformat()}&shift=1', {
            'worker': self.konobar.id
        })
        self.assertTrue(Smena.objects.filter(konobar=self.konobar, datum=today, broj_smene=1).exists())
        self.assertEqual(response.status_code, 200)  # Or 302 if you redirect after POST

    def test_dodaj_konobara(self):
        # GET request must pass date and shift
        next_date = date.today().isoformat()
        response = self.client.get(
            reverse('dodaj_konobara'),
            {'date': next_date, 'shift': '1'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'menadzer/dodaj_konobara.html')

        # POST request to assign a worker
        response = self.client.post(
            reverse('dodaj_konobara') + f'?date={next_date}&shift=1',
            {'worker': self.konobar.id}
        )
        self.assertEqual(response.status_code, 200)  # View renders the page
        self.assertTrue(Smena.objects.filter(konobar=self.konobar, datum=next_date, broj_smene=1).exists())


    def test_stanje_artikala(self):
        response = self.client.get(reverse('stanje_artikala'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'menadzer/stanje.html')

    def test_statistika_get(self):
        response = self.client.get(reverse('statistika'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'menadzer/statistika.html')

    def test_napravi_statistiku(self):
        Stavka.objects.create(racun=self.racun, artikal=self.artikal, kolicina=2, cena=400)
        response = self.client.post(reverse('napravi_statistiku'), {'interval': 7})
        self.assertEqual(response.status_code, 302)  # redirect after POST

    def test_qr_kod_view(self):
        response = self.client.get(reverse('qr_kod'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'menadzer/qr_kod.html')
