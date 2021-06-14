import os
import random
import re
import time

import requests
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from neural_network_module.neural_network import NeuralNetwork
from xpath import xpath


class Bot:
    def __init__(self, headless, db, discord_webhook_url):
        # Init database
        self.db = db

        # Init neural network
        self.neural_network = NeuralNetwork()

        # Init browser driver
        profile = webdriver.FirefoxProfile()
        profile.set_preference(
            "general.useragent.override",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0",
        )
        options = Options()

        options.headless = headless

        self.driver = webdriver.Firefox(
            profile, service_log_path=os.devnull, options=options
        )

        self.driver.maximize_window()

        self.discord_webhook_url = discord_webhook_url

    def quit(self):
        self.driver.quit()

    def login(self, insta_username, insta_password):
        print("Login")
        self.driver.get("https://www.instagram.com/accounts/login/")

        self.driver.implicitly_wait(3)  # wait seconds

        # Wait until page is loaded
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )

        # Manage cookie popup
        try:
            cookie_button = self.driver.find_element_by_xpath(xpath["accept_btn"])
            cookie_button.click()

            # Wait until pop up is closed
            try:
                WebDriverWait(self.driver, 120).until(
                    EC.invisibility_of_element_located((By.XPATH, xpath["accept_btn"]))
                )
            except TimeoutException:
                pass

        except NoSuchElementException:
            pass

        self.driver.find_element_by_name("username").send_keys(insta_username)
        self.driver.find_element_by_name("password").send_keys(insta_password)

        # Log in
        self.driver.find_element_by_xpath(xpath["login_btn"]).click()

        # Manage save login info page
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath["not_now_btn"]))
            )
            time.sleep(random.randint(2, 4))  # wait seconds
        except TimeoutException:
            pass

        try:
            login_info_button = self.driver.find_element_by_xpath(xpath["not_now_btn"])
            login_info_button.click()
        except NoSuchElementException:
            pass

        # Manage notification popup
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath["not_now_btn"]))
            )
            time.sleep(random.randint(2, 4))  # wait seconds
        except TimeoutException:
            pass

        try:
            notification_button = self.driver.find_element_by_xpath(
                xpath["not_now_btn"]
            )
            notification_button.click()
        except NoSuchElementException:
            pass

    def _wait(self, min, max, why=None):
        wait = random.uniform(min, max)

        why = "wait {}s, {}".format(wait, why)
        print(why)

        time.sleep(wait)  # wait seconds

    def _wait_and_scroll(self):
        self._wait(8.8, 31.8, "before scroll")

        # Go to the bottom page to trigger new images loading
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait until end of new images loading
        try:
            WebDriverWait(self.driver, 120).until(
                EC.invisibility_of_element_located((By.XPATH, xpath["loading_svg"]))
            )
        except TimeoutException:
            pass

        time.sleep(2)  # wait seconds

    def _find_new_image(self, history):
        # Find div images
        try:
            all_div_images = self.driver.find_elements_by_xpath(xpath["images_div"])

        except ElementClickInterceptedException:
            return

        # Get new div images
        if not history:
            new_div_images = all_div_images
        else:
            new_div_images = []

            # Filter old div images
            for div_elem in all_div_images:
                image_elem = div_elem.find_element_by_class_name("FFVAD")
                image_url = image_elem.get_attribute("src")

                if image_url not in history:
                    new_div_images.append(div_elem)

        print("\nnew images:", len(new_div_images))
        print("history:", len(history), "\n")

        return new_div_images

    def _open_image(self, div_image):
        # Scroll to element
        self.driver.execute_script(
            "window.scrollTo(0, {});".format(div_image.location["y"])
        )

        # Open image box and comment
        div_image.click()

        self._wait(2.4, 5.1, "watching image")

    def _close_image(self):
        image_box = self.driver.find_element_by_xpath(xpath["image_box"])
        action = ActionChains(self.driver)
        action.move_to_element_with_offset(image_box, -5, -5)
        action.click()
        action.perform()

    def _get_user_name(self):
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        xpath["user_name"],
                    )
                )
            )
        except TimeoutException:
            return

        user_name = self.driver.find_element_by_xpath(xpath["user_name"]).text

        return user_name

    def _get_image_words(self):
        try:
            # Find author image's description
            description_text = self.driver.find_element_by_xpath(
                xpath["description"]
            ).text.lower()

            words = re.sub("[^\w]", " ", description_text).split()

        # If no description, do noting
        except NoSuchElementException:
            pass

        # Find first comment, some times
        try:
            comment_text = self.driver.find_element_by_xpath(
                xpath["first_comment"]
            ).text.lower()

            words += re.sub("[^\w]", " ", comment_text).split()

        # If no first comment, do noting
        except NoSuchElementException:
            pass

        return words

    def _check_user_name(self, user_name):
        if not user_name:
            print("No user name")
            return True

        if self.db.contains_value_in_table("forbidden_words_in_user_name", user_name):
            print("User name banned by contains forbidden words")
            return True

        if self.db.exist_in_table("user_name_banned", user_name):
            print("User name banned")
            return True

        return False

    def _check_words(self, words):
        filter_passed = True
        confidence_limit = 91

        # If words, change confidence_limit
        if words:
            if self.db.exist_in_table("forbidden_words", words):
                filter_passed = False

            if self.db.exist_in_table("ignoring_words", words):
                if not self.db.exist_in_table("wanted_words", words):
                    filter_passed = False
                else:
                    confidence_limit = 70

            elif self.db.exist_in_table("wanted_words", words):
                confidence_limit = 60

            # Max average read speed
            min_wait = len(words) * (60 / 300)

            # Min average read speed
            max_wait = len(words) * (60 / 270)

            self._wait(min_wait, max_wait, "reading comment")

        return filter_passed, confidence_limit

    def _like(self, user_name):
        # Check if not too much user like
        if self.db.count_like(user_name) < 4:
            try:
                self.driver.find_element_by_xpath(xpath["liked_btn_svg"])

                like_elem = self.driver.find_element_by_xpath(xpath["like_btn"])

                like_elem.click()

                self._wait(0.7, 2.8, "image liked")

                return 1

            except NoSuchElementException:
                print("Already liked")
                return 0

        else:
            print("Too much user like")
            return 2

    def _send_notification(self, confidence, like_state, url):
        content = "{:.2f}% ".format(confidence)

        if like_state == 1:
            content += ":heart: "

        elif like_state == 2:
            content += ":broken_heart: "

        content += url
        data = {"content": content}

        requests.post(self.discord_webhook_url, data=data)
        print(url)

    def run(self, min_loc, max_loc):
        locations_url = self.db.get_random_locations(min_loc, max_loc)

        for city_url in locations_url:

            # Go to explore instagram
            print("############################################")
            print(city_url.split("/")[-2])
            print("############################################\n")
            try:
                self.driver.get(city_url)
            except TimeoutException:
                continue

            time.sleep(random.randint(2, 4))  # wait seconds

            history = []

            for nb_load in range(random.randint(4, 9)):
                if nb_load > 0:
                    self._wait_and_scroll()

                new_div_images = self._find_new_image(history)

                if not new_div_images:
                    continue

                for div_image in new_div_images:
                    image_elem = div_image.find_element_by_class_name("FFVAD")
                    image_url = image_elem.get_attribute("src")

                    if not image_url:
                        continue

                    history.append(image_url)

                    link_elem = div_image.find_element_by_tag_name("a")
                    url = link_elem.get_attribute("href")

                    # Check if already send by insert url into database
                    if self.db.already_send(url):
                        print("Already checked")
                        continue

                    # Detect objects
                    detections = self.neural_network.detect(image_url)

                    print()

                    # For the third first finded objects, check if there is a cat
                    for detection in detections:
                        label = "{}: {:.2f}%".format(
                            detection["classe"], detection["confidence"]
                        )
                        print(label)

                        # If it's a cat with upper X % of precision
                        if (
                            detection["confidence"] > 55
                            and detection["classe"] == "cat"
                        ):

                            self._open_image(div_image)
                            user_name = self._get_user_name()

                            if self._check_user_name(user_name):
                                self._close_image()
                                # Break detection loop
                                break

                            words = self._get_image_words()
                            filter_passed, confidence_limit = self._check_words(words)

                            like_state = 0

                            # Like if not already liked
                            if (
                                filter_passed
                                and detection["confidence"] > confidence_limit
                            ):
                                like_state = self._like(user_name)

                            self._close_image()

                            if not filter_passed:
                                print("Filter not passed:", url)

                            else:
                                # Check if already send by insert url into database
                                if self.db.add_like(user_name, like_state, url):
                                    self._send_notification(
                                        detection["confidence"], like_state, url
                                    )

                                else:
                                    print("Already sended")

                            # Break detection loop,
                            # because we found a cat in third first objects
                            break
