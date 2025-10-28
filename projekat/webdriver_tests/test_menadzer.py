# Aleksa Sekulic 0021/2022
import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
import base64

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from projekat.models import Polje, Sto, Rezervacija, TipArtikla, Artikal, Dostava, Zaposleni, Smena


class WebdriverTestMenadzer(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        cls.driver = webdriver.Chrome(options=chrome_options)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        # Common data for tests
        self.polje = Polje.objects.create(x=0, y=0)
        self.sto = Sto.objects.create(polje=self.polje)

        self.tip_artikla = TipArtikla.objects.create(naziv="Pica")
        self.artikal = Artikal.objects.create(
            naziv="Margarita",
            tip_artikla=self.tip_artikla,
            cena=500,
            velicina_serviranja="Srednja",
            kolicina_na_stanju=10
        )

        self.rezervacija = Rezervacija.objects.create(
            sto=self.sto,
            datum_vreme=timezone.now(),
            ime="Lazar",
            status="U TOKU"
        )

        self.dostava = Dostava.objects.create(
            artikal=self.artikal,
            kolicina=2,
            status="U TOKU"
        )

        # Two waiters
        self.k1 = Zaposleni.objects.create(
            user=User.objects.create_user('konobar1', 'k1@test.com', 'test123'),
            tip='K'
        )
        self.k2 = Zaposleni.objects.create(
            user=User.objects.create_user('konobar2', 'k2@test.com', 'test123'),
            tip='K'
        )

    def login_as_manager(self):
        """Logs in through the login form at /projekat/"""
        User.objects.create_user(username="menadzer", password="test123")
        Zaposleni.objects.create(user=User.objects.get(username="menadzer"), tip="M")

        self.driver.get(f"{self.live_server_url}/projekat/")

        # Wait for username input to appear
        username_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = self.driver.find_element(By.NAME, "password")

        # Fill out the form
        username_input.send_keys("menadzer")
        password_input.send_keys("test123")

        # Click the "Prijavi se" button
        self.driver.find_element(By.TAG_NAME, "button").click()

        # Wait until redirect to menadzer dashboard
        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/projekat/menadzer/")
        )

        # Sanity check: ensure we're logged in
        current_url = self.driver.current_url
        assert "/projekat/menadzer/" in current_url, f"Unexpected URL after login: {current_url}"

    # === TESTS ===

    def test_generate_qr_code_successfully(self):
        self.login_as_manager()
        self.driver.get(f"{self.live_server_url}/projekat/menadzer/qr_kod/")

        select = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "sto_id"))
        )

        for option in select.find_elements(By.TAG_NAME, "option"):
            if option.get_attribute("value") == str(self.sto.id):
                option.click()
                break

        button = self.driver.find_element(By.TAG_NAME, "button")
        button.click()

        img = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "QR"))
        )

        self.assertTrue(img.get_attribute("src").startswith("data:image/png;base64,"))
        img_data = img.get_attribute("src").split(",")[1]
        self.assertTrue(len(base64.b64decode(img_data)) > 0)

    def test_dostava_page_displays_table(self):
        self.login_as_manager()
        self.driver.get(f"{self.live_server_url}/projekat/menadzer/dostave/")

        table = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, "table"))
        )
        self.assertIn("Margarita", table.text)

    def test_rezervacija_page_displays_table(self):
        self.login_as_manager()
        self.driver.get(f"{self.live_server_url}/projekat/menadzer/rezervacije/")

        table = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, "table"))
        )
        self.assertIn("Lazar", table.text)

    def test_stanje_artikala_page_displays_table(self):
        self.login_as_manager()
        self.driver.get(f"{self.live_server_url}/projekat/menadzer/stanje_artikala/")

        table = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, "table"))
        )
        self.assertIn("Margarita", table.text)

    def test_dodaj_konobara_u_smene(self):
        self.login_as_manager()

        target_date = date.today() + timedelta(days=8)
        shift_number = 2

        # Open the "add waiter" page
        url = f"{self.live_server_url}/projekat/menadzer/dodaj_konobara?date={target_date}&shift={shift_number}"
        self.driver.get(url)

        select_elem = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "worker"))
        )
        select = Select(select_elem)

        WebDriverWait(self.driver, 10).until(lambda d: len(select.options) > 1)
        chosen_value = select.options[-1].get_attribute("value")
        select.select_by_value(chosen_value)

        save_button = self.driver.find_element(By.TAG_NAME, "button")
        save_button.click()
        time.sleep(1)

        smena = Smena.objects.filter(
            datum=target_date, broj_smene=shift_number, konobar__id=chosen_value
        )
        self.assertTrue(smena.exists())
