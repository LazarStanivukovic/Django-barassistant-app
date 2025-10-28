# Lazar Stanivukovic 0590/2022
import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from projekat.models import *
from django.contrib.auth.models import User

class WebdriverTestGost(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.browser = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username='konobar1', password='123')
        self.konobar = Zaposleni.objects.create(user=self.user, tip='K')
        self.polje = Polje.objects.create(x=1, y=1)
        self.sto = Sto.objects.create(polje=self.polje)
        self.tip = TipArtikla.objects.create(naziv='Pivo')
        self.artikal = Artikal.objects.create(
            tip_artikla=self.tip,
            naziv='Jelen',
            cena=300,
            velicina_serviranja='0.5l',
            kolicina_na_stanju=10
        )
        self.racun = Racun.objects.create(konobar=self.konobar, sto=self.sto, status='O')
        Stavka.objects.create(racun=self.racun, artikal=self.artikal, kolicina=1, cena=300)

    def test_ulaz_redirects_to_pocetna(self):
        self.browser.get(f"{self.live_server_url}/projekat/ulaz/{self.sto.id}/")
        WebDriverWait(self.browser, 5).until(
            lambda b: "/projekat/gost/" in b.current_url
        )
        self.assertIn("/projekat/gost/", self.browser.current_url)

    def test_pocetna_page_loads(self):
        self.browser.get(f"{self.live_server_url}/projekat/ulaz/{self.sto.id}/")
        WebDriverWait(self.browser, 5).until(
            lambda b: "The Three Carrots Pub" in b.page_source
        )
        self.assertIn("The Three Carrots Pub", self.browser.page_source)

    def test_karta_pica_displays_artikli(self):
        self.browser.get(f"{self.live_server_url}/projekat/ulaz/{self.sto.id}/")
        self.browser.get(f"{self.live_server_url}/projekat/gost/karta_pica/")
        WebDriverWait(self.browser, 5).until(
            lambda b: "Jelen" in b.page_source
        )
        self.assertIn("Jelen", self.browser.page_source)

    def test_racun_gost_displays_stavke(self):
        self.browser.get(f"{self.live_server_url}/projekat/ulaz/{self.sto.id}/")
        self.browser.get(f"{self.live_server_url}/projekat/gost/racun/{self.sto.id}/")
        WebDriverWait(self.browser, 5).until(
            lambda b: "300" in b.page_source
        )
        self.assertIn("300", self.browser.page_source)

    def test_oceni_nas_form_submission(self):
        self.browser.get(f"{self.live_server_url}/projekat/ulaz/{self.sto.id}/")
        self.browser.get(f"{self.live_server_url}/projekat/gost/oceni_nas/")

        star = WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#stars .star[data-value='5']"))
        )
        star.click()

        submit_btn = WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.confirm-btn"))
        )
        submit_btn.click()

        WebDriverWait(self.browser, 5).until(
            lambda b: "/projekat/gost/" in b.current_url
        )
        self.assertIn("/projekat/gost/", self.browser.current_url)

        time.sleep(1)
        self.assertTrue(Recenzija.objects.filter(racun=self.racun, konobar=self.konobar).exists())
