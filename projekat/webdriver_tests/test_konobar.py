# Sofija Pavlovic 0340/2022

import time
from datetime import date
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from projekat.models import (
    Zaposleni, TipArtikla, Artikal, Polje, Sto, Racun, Stavka, Recenzija, Smena
)


class WebdriverTestKonobar(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        cls.driver = webdriver.Chrome(options=options)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            username="konobar1",
            password="123",
            first_name="Pera",
            last_name="Peric",
            email="pera@example.com",
        )
        self.zap = Zaposleni.objects.create(user=self.user, tip="K")

        self.tip = TipArtikla.objects.create(naziv="Piće")
        self.kafa = Artikal.objects.create(
            tip_artikla=self.tip, naziv="Kafa",
            cena=100, velicina_serviranja="200ml",
            kolicina_na_stanju=20
        )
        self.nema = Artikal.objects.create(
            tip_artikla=self.tip, naziv="BezZalihe",
            cena=50, velicina_serviranja="100ml",
            kolicina_na_stanju=0
        )

        self.polje_a = Polje.objects.create(x=0, y=0)
        self.sto_a = Sto.objects.create(polje=self.polje_a)
        self.polje_b = Polje.objects.create(x=1, y=0)
        self.sto_b = Sto.objects.create(polje=self.polje_b)
        self.polje_c = Polje.objects.create(x=2, y=0)
        self.sto_c = Sto.objects.create(polje=self.polje_c)

        self.racun_a = Racun.objects.create(
            konobar=self.zap, sto=self.sto_a, status="O", datum_otvaranja=date.today()
        )
        self.stavka_kafa = Stavka.objects.create(
            racun=self.racun_a, artikal=self.kafa, kolicina=2, cena=200
        )
        self.stavka_nema = Stavka.objects.create(
            racun=self.racun_a, artikal=self.nema, kolicina=1, cena=50
        )

        other_user = User.objects.create_user(username="konobar2", password="123")
        other_zap = Zaposleni.objects.create(user=other_user, tip="K")
        Racun.objects.create(
            konobar=other_zap, sto=self.sto_c, status="O", datum_otvaranja=date.today()
        )

        Recenzija.objects.create(racun=self.racun_a, konobar=self.zap, ocena=4)
        Recenzija.objects.create(racun=self.racun_a, konobar=self.zap, ocena=2)
        Smena.objects.create(konobar=self.zap, datum=date.today(), broj_smene=1)


    def login_as_konobar(self):
        """Prijava kao konobar"""
        self.driver.get(f"{self.live_server_url}/projekat/")

        username = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password = self.driver.find_element(By.NAME, "password")

        username.send_keys("konobar1")
        password.send_keys("123")
        self.driver.find_element(By.TAG_NAME, "button").click()

        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/projekat/konobar")
        )

    def open_racun(self, sto_id):
        self.driver.get(f"{self.live_server_url}{reverse('racun', args=[sto_id])}")

    def row_for(self, artikal_naziv):
        """Vrati WebElement reda u tabeli računa za dati artikal (po nazivu)."""
        xpath = f"//tr[td[normalize-space()='{artikal_naziv}']]"
        return WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )


    def test_konobar_profil(self):
        """Profil: učitavanje stranice, prikaz pozdrava i imena, tabele sa ocenama."""
        self.login_as_konobar()

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        page = self.driver.page_source
        self.assertIn("Dobrodošli", page)
        self.assertIn("Pera", page)
        self.assertIn("Broj recenzija", page)
        self.assertIn("Prosečna ocena", page)

    def test_raspored(self):
        """Klik na 'Pregled smena' u meniju otvara raspored i prikazuje današnji red."""
        self.login_as_konobar()
        self.driver.find_element(By.LINK_TEXT, "Pregled smena").click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        self.assertIn("Raspored za trenutnu nedelju", self.driver.page_source)
        self.assertIn("X", self.driver.page_source)

    def test_stolovi(self):
        """Pregled stolova: mreža ćelija; klik na slobodan sto vodi na /racun/<id>."""
        self.login_as_konobar()
        self.driver.find_element(By.LINK_TEXT, "Pregled stolova").click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cell"))
        )

        disabled = self.driver.find_elements(By.CSS_SELECTOR, "div.table-disabled.cell")
        self.assertTrue(len(disabled) >= 1)

        link = self.driver.find_element(By.CSS_SELECTOR, "a > div.table.cell")
        link.click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        self.assertIn("Pregled računa", self.driver.page_source)

    def test_racun_otvaranje_racuna_dodavanje_stavke(self):
        """Otvaranje računa na stolu bez računa → dodaj stavku preko forme."""
        self.login_as_konobar()

        self.open_racun(self.sto_b.id)
        wait = WebDriverWait(self.driver, 15)

        open_form = wait.until(
            EC.presence_of_element_located((By.XPATH, "//form[.//button[@id='open']]"))
        )

        self.driver.execute_script("""
            var f = arguments[0];
            var h = document.createElement('input');
            h.type = 'hidden';
            h.name = 'action';
            h.value = 'open';
            f.appendChild(h);
            f.submit();
        """, open_form)

        wait.until(EC.staleness_of(open_form))

        nova_stavka_link = wait.until(
            EC.presence_of_element_located((By.LINK_TEXT, "Nova stavka"))
        )
        self.assertIsNotNone(nova_stavka_link)

        nova_stavka_link.click()
        wait.until(EC.presence_of_element_located((By.ID, "formh1")))
        self.assertIn("Nova stavka", self.driver.page_source)

        Select(self.driver.find_element(By.NAME, "nazivArtikla")).select_by_visible_text("Kafa")
        self.driver.find_element(By.NAME, "kolicinaArtikla").send_keys("3")
        confirm_btn = self.driver.find_element(By.CSS_SELECTOR, "button.add-button")
        confirm_btn.click()

        wait.until(EC.url_contains(f"/racun/{self.sto_b.id}"))
        row = self.row_for("Kafa")
        tds = row.find_elements(By.TAG_NAME, "td")
        self.assertEqual(tds[1].text.strip(), "3")
        self.assertEqual(tds[3].text.strip(), "300")

    def test_racun_povecanje_smanjenje_kolicine(self):
        """Na postojećoj stavci (Kafa x2) klikni + pa − i proveri vrednosti."""
        self.login_as_konobar()
        self.open_racun(self.sto_a.id)

        plus_btn = self.driver.find_element(
            By.XPATH,
            f"//tr[td[normalize-space()='Kafa']]//form[input[@name='id' and @value='{self.stavka_kafa.id}']]//button[@name='action' and @value='inc']"
        )

        plus_btn.click()

        WebDriverWait(self.driver, 10).until(EC.staleness_of(plus_btn))

        row_after_plus = self.row_for("Kafa")
        tds_after_plus = row_after_plus.find_elements(By.TAG_NAME, "td")

        self.assertEqual(tds_after_plus[1].text.strip(), "3")
        self.assertEqual(tds_after_plus[3].text.strip(), "300")

        minus_btn = self.driver.find_element(
            By.XPATH,
            f"//tr[td[normalize-space()='Kafa']]//form[input[@name='id' and @value='{self.stavka_kafa.id}']]//button[@name='action' and @value='dec']"
        )

        minus_btn.click()

        WebDriverWait(self.driver, 10).until(EC.staleness_of(minus_btn))

        row_after_minus = self.row_for("Kafa")
        tds_after_minus = row_after_minus.find_elements(By.TAG_NAME, "td")

        self.assertEqual(tds_after_minus[1].text.strip(), "2")
        self.assertEqual(tds_after_minus[3].text.strip(), "200")

    def test_racun_neomoguceno_povecanje_kolicine(self):
        """Za artikal bez zaliha '+' dugme je disabled (preostala_kolicina == 0)."""
        self.login_as_konobar()
        self.open_racun(self.sto_a.id)

        plus_btn = self.driver.find_element(
            By.XPATH,
            f"//tr[td[normalize-space()='BezZalihe']]//form[input[@name='id' and @value='{self.stavka_nema.id}']]//button[@name='action' and @value='inc']"
        )
        self.assertTrue(plus_btn.get_attribute("disabled") is not None)

    def test_racun_zatvaranje_racuna(self):
        """Zatvaranje računa: pojavi se poruka o nepostojanju otvorenog računa + dugme 'Otvori račun'."""
        self.login_as_konobar()
        self.open_racun(self.sto_a.id)

        close_btn = self.driver.find_element(By.CSS_SELECTOR, "form.close-form button.add-button")
        close_btn.click()

        WebDriverWait(self.driver, 10).until(EC.url_contains(f"/racun/{self.sto_a.id}"))
        page = self.driver.page_source
        self.assertIn("Dati sto trenutno nema otvoren račun.", page)

        self.assertIsNotNone(
            self.driver.find_element(By.ID, "open")
        )
