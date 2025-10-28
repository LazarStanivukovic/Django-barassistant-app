#Andrej Veličkov 0569/2022
import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from projekat.models import Zaposleni, TipArtikla, Artikal, Polje


class WebdriverTestAdmin(StaticLiveServerTestCase):
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
            username="admin1",
            password="123",
            first_name="Ana",
            last_name="Nikolic",
            email="ana@example.com",
            is_staff=True
        )
        self.zaposleni = Zaposleni.objects.create(user=self.user, tip="A")

        self.tip = TipArtikla.objects.create(naziv="Kafa")
        self.artikal = Artikal.objects.create(
            naziv="Espresso",
            tip_artikla=self.tip,
            cena=150,
            velicina_serviranja="100ml",
            kolicina_na_stanju=50
        )
        self.polje = Polje.objects.create(x=1, y=1)

    def login_as_admin(self):
        """Prijava na sistem kao admin kroz /projekat/."""
        self.driver.get(f"{self.live_server_url}/projekat/")

        username_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = self.driver.find_element(By.NAME, "password")

        username_input.send_keys("admin1")
        password_input.send_keys("123")
        self.driver.find_element(By.TAG_NAME, "button").click()

        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/projekat/admin/")
        )


    def test_admin_profil_prikaz(self):
        """Test da se profil učitava ispravno nakon prijave."""
        self.login_as_admin()
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        self.assertIn("Dobrodošli", self.driver.page_source)
        self.assertIn("Ana", self.driver.page_source)

    def test_pregled_zaposlenih(self):
        """Test prikaza svih zaposlenih."""
        self.login_as_admin()
        self.driver.get(f"{self.live_server_url}/projekat/admin/zaposleni/")
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        self.assertIn("Korisničko ime", self.driver.page_source)

    def test_dodaj_zaposlenog(self):
        """Test dodavanja novog zaposlenog."""
        self.login_as_admin()
        self.driver.get(f"{self.live_server_url}/projekat/admin/zaposleni/dodaj/")

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, "first_name"))
        )

        self.driver.find_element(By.NAME, "first_name").send_keys("Pera")
        self.driver.find_element(By.NAME, "last_name").send_keys("Peric")
        self.driver.find_element(By.NAME, "email").send_keys("pera@example.com")
        self.driver.find_element(By.NAME, "username").send_keys("pera")
        self.driver.find_element(By.NAME, "password").send_keys("123")

        tip_radio = self.driver.find_element(By.CSS_SELECTOR, "input[name='tip'][value='K']")
        self.driver.execute_script("arguments[0].click();", tip_radio)

        self.driver.find_element(By.CSS_SELECTOR, "button.add-button").click()

        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/projekat/admin/zaposleni/")
        )
        time.sleep(1)
        self.assertTrue(Zaposleni.objects.filter(user__username="pera").exists())

    def test_pregled_artikala(self):
        """Test prikaza liste artikala."""
        self.login_as_admin()
        self.driver.get(f"{self.live_server_url}/projekat/admin/artikli/")
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        self.assertIn("Espresso", self.driver.page_source)

    def test_dodaj_artikal(self):
        """Test dodavanja novog artikla."""
        self.login_as_admin()
        self.driver.get(f"{self.live_server_url}/projekat/admin/artikli/dodaj/")

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, "naziv"))
        )

        self.driver.find_element(By.NAME, "naziv").send_keys("Latte")
        self.driver.find_element(By.NAME, "cena").send_keys("250")

        select_tip = self.driver.find_element(By.NAME, "tip")
        self.driver.execute_script("arguments[0].value = arguments[1];", select_tip, str(self.tip.id))

        self.driver.find_element(By.CSS_SELECTOR, "button.add-button").click()

        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/projekat/admin/artikli/")
        )
        time.sleep(1)
        self.assertTrue(Artikal.objects.filter(naziv="Latte").exists())

    def test_promeni_cenu(self):
        """Test promene cene artikla — proverava da li se nova cena sačuva u bazi."""
        self.login_as_admin()

        self.driver.get(f"{self.live_server_url}/projekat/admin/artikli/promeni/?id={self.artikal.id}")

        nova_cena_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "nova_cena"))
        )

        nova_cena_input.clear()
        nova_cena_input.send_keys("200")

        sacuvaj_dugme = self.driver.find_element(By.CSS_SELECTOR, "button.add-button")
        sacuvaj_dugme.click()

        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/projekat/admin/artikli/")
        )

        time.sleep(1)

        self.artikal.refresh_from_db()

        self.assertEqual(
            self.artikal.cena,
            200,
            msg=f"Očekivana cena 200, ali u bazi je {self.artikal.cena}"
        )

    def test_pregled_tipova_artikala(self):
        """Test prikaza tipova artikala."""
        self.login_as_admin()
        self.driver.get(f"{self.live_server_url}/projekat/admin/tipovi_artikala/")
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        self.assertIn("Kafa", self.driver.page_source)

    def test_dodaj_tip_artikla(self):
        """Test dodavanja novog tipa artikla."""
        self.login_as_admin()
        self.driver.get(f"{self.live_server_url}/projekat/admin/tipovi_artikala/dodaj/")

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, "naziv"))
        )
        self.driver.find_element(By.NAME, "naziv").send_keys("Novo pice")
        self.driver.find_element(By.CSS_SELECTOR, "button.add-button").click()

        WebDriverWait(self.driver, 5).until(
            EC.url_contains("/projekat/admin/tipovi_artikala/")
        )
        time.sleep(1)
        self.assertTrue(TipArtikla.objects.filter(naziv="Novo pice").exists())

    def test_raspored_stolova(self):
        """Test učitavanja rasporeda stolova."""
        self.login_as_admin()
        self.driver.get(f"{self.live_server_url}/projekat/admin/raspored_stolova/")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cell"))
        )
        self.assertIn("Raspored", self.driver.page_source)
