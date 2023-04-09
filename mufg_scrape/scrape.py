import logging.config
import os
from retry import retry
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common import exceptions

logger = logging.getLogger()
logger.setLevel(logging.INFO)
URL = 'http://www.dc.tr.mufg.jp/?top'
UID = os.environ.get('MUFG_UID')
PASSWORD = os.environ.get('MUFG_PASSWORD')


class MufgScrapeException(Exception):
    pass


class MufgScrape:
    def __init__(self, driver):
        self.driver = driver
        self.url = URL
        self.uid = UID
        self.password = PASSWORD

    def driver_close(self) -> None:
        # self.driver.close()
        # 複数Windowまとめて終了する為、quitする
        logger.debug('Driver closing...')
        self.driver.quit()
        logger.debug('Driver closed')

    def open_page(self) -> None:
        self.driver.get(self.url)
        logger.info('Target Page opened')

    def to_login_page(self) -> None:
        self.click_login_btn()
        self.switch_login_window()

    def click_login_btn(self) -> None:
        logger.info('LoginButton waiting for display...')
        WebDriverWait(self.driver, 10).until(
            expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'top_login_button'))
        )
        logger.info('LoginButton displayed')
        top_login_btn = self.driver.find_element(By.CLASS_NAME, 'top_login_button')
        top_login_btn.click()
        logger.info('LoginButton clicked')

    @retry(MufgScrapeException, tries=2, delay=2, logger=logger)
    def switch_login_window(self) -> None:
        logger.info('LoginWindow waiting for open...')
        if len(self.driver.window_handles) == 1:
            raise MufgScrapeException('LoginWindow not open')

        logger.info('LoginWindow opened')
        windows = self.driver.window_handles
        self.driver.switch_to.window(windows[1])
        logger.info('LoginWindow switched')

    def login(self) -> None:
        logger.info('LoginElements waiting for display...')
        WebDriverWait(self.driver, 10).until(
            expected_conditions.visibility_of_element_located((By.ID, 'envUid')),
            expected_conditions.visibility_of_element_located((By.ID, 'envPass'))
        )
        logger.info('LoginElements displayed')
        login_id = self.driver.find_element(By.ID, 'envUid')
        login_id.send_keys(self.uid)

        login_pass = self.driver.find_element(By.ID, 'envPass')
        login_pass.send_keys(self.password)

        logger.info('LoginElements send keys')
        login_btn = self.driver.find_element(By.ID, 'loginButton')
        login_btn.click()
        logger.info('LoginButton clicked')
        self.check_login_status()

    def check_login_status(self) -> None:
        logger.info('Check Login status...')
        WebDriverWait(self.driver, 10).until(
            expected_conditions.element_to_be_clickable((By.ID, 'logOut'))
        )
        logger.info('Login success')

    def scrape_top_page(self) -> str:
        self.close_modal_window()
        main_html = self.driver.page_source
        logger.info('TopPage Scrape success')
        return main_html

    def check_modal_window(self) -> None:
        logger.info('ModalWindow waiting for display...')
        try:
            WebDriverWait(self.driver, 10).until(
                expected_conditions.element_to_be_clickable((By.XPATH, '//*[@id="syohinGuideBookAlert"]/div'))
            )
            logger.info('ModalWindow displayed')
        except exceptions.TimeoutException:
            logger.warning('ModalWindow not open')

    def close_modal_window(self) -> None:
        self.check_modal_window()
        self.driver.find_element(By.XPATH, '//*[@id="syohinGuideBookAlert"]/div').click()
        logger.info('ModalWindow CloseButton clicked')

    def to_product_page(self) -> None:
        self.click_detail_btn()
        self.click_product_tab()

    def click_detail_btn(self) -> None:
        logger.info('ProductLink waiting for display...')
        WebDriverWait(self.driver, 10).until(
            expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'linkReview'))
        )
        logger.info('ProductLink displayed')
        # 運用資産状況ページへ遷移
        self.driver.find_element(By.CLASS_NAME, 'linkReview').click()
        logger.info('ProductLink clicked')

    def click_product_tab(self) -> None:
        logger.info('ProductInfoTab waiting for display...')
        WebDriverWait(self.driver, 10).until(
            expected_conditions.visibility_of_element_located((By.XPATH, '//*[@class="review_tab"]/ul/li'))
        )
        logger.info('ProductInfoTab displayed')
        # 運用資産タブ
        li_elems = self.driver.find_elements(By.XPATH, '//*[@class="review_tab"]/ul/li')
        # 運用商品別情報(タブ2番目)をクリック
        if len(li_elems) != 2:
            raise MufgScrapeException('ProductInfoTab not found')
        li_elems[1].click()

    def scrape_product_page(self) -> str:
        self.check_asset_table()
        product_html = self.driver.page_source
        logger.info('ProductPage Scrape success')
        return product_html

    def check_asset_table(self) -> None:
        logger.info('AssetTable waiting for display...')
        WebDriverWait(self.driver, 10).until(
            expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'asset_table'))
        )
        logger.info('AssetTable displayed')

    def logout(self) -> None:
        logger.info('LogoutButton waiting for display...')
        WebDriverWait(self.driver, 10).until(
            expected_conditions.element_to_be_clickable((By.ID, 'logOut'))
        )
        logger.info('LogoutButton displayed')
        logout_btn = self.driver.find_element(By.ID, 'logOut')
        logout_btn.click()
        logger.info('LogoutButton clicked')
