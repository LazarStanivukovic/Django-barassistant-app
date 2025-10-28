# Lazar Stanivukovic 0590/2022
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from projekat.models import User, Zaposleni
from unittest.mock import patch

class WebdriverTestPrijava(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.browser = WebDriver()
        cls.browser.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='123', email='test@example.com'
        )
        self.konobar = Zaposleni.objects.create(user=self.user, tip='K')

    def test_prijava_success(self):
        self.browser.get(f"{self.live_server_url}/projekat/")

        username_input = WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = self.browser.find_element(By.NAME, "password")
        submit_btn = self.browser.find_element(By.XPATH, "//button[text()='Prijavi se']")

        username_input.send_keys("testuser")
        password_input.send_keys("123")
        submit_btn.click()

        WebDriverWait(self.browser, 5).until(lambda b: 'konobar' in b.current_url)
        self.assertIn('konobar', self.browser.current_url)

    def test_odjava_success(self):
        self.client.login(username='testuser', password='123')
        cookie = self.client.cookies['sessionid']

        self.browser.get(f"{self.live_server_url}/projekat/odjava/")
        self.browser.add_cookie({'name': 'sessionid', 'value': cookie.value, 'path': '/'})
        self.browser.get(f"{self.live_server_url}/projekat/odjava/")

        WebDriverWait(self.browser, 5).until(lambda b: b.current_url.endswith('/projekat/'))
        self.assertTrue(self.browser.current_url.endswith('/projekat/'))

    def test_restauracija_success(self):
        with patch('projekat.views.prijavaView.reset_password') as mock_reset:
            mock_reset.return_value = None

            self.browser.get(f"{self.live_server_url}/projekat/restauracija/")

            email_input = WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            submit_btn = self.browser.find_element(By.XPATH, "//button[text()='Pošalji']")

            email_input.send_keys("test@example.com")
            submit_btn.click()

            WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.confirmmsg"))
            )
            msg = self.browser.find_element(By.CSS_SELECTOR, "p.confirmmsg").text
            self.assertEqual(msg, "Lozinka poslata")
            mock_reset.assert_called_once_with(self.user)
