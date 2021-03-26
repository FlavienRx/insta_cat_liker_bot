# 2 8,10,13,16,19,21 * * * cd bot/jopy_bot/ && pipenv run python jopy_bot.py

import argparse
import os
import random
import re
import time

import requests
import sentry_sdk
from dotenv import load_dotenv
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

from db import DbWrapper
from neural_network_module.neural_network import NeuralNetwork
from xpath import xpath


load_dotenv()


# Init sentry
if os.environ.get("SENTRY_SDK_URL") and os.environ.get("ENVIRONMENT") != "developement":
    sentry_sdk.init(
        os.environ.get("SENTRY_SDK_URL"),
        traces_sample_rate=1.0,
        environment=os.environ.get("ENVIRONMENT"),
    )

# Get args
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--fast", action="store_true", help="Run script now")
args = parser.parse_args()

base_path = os.path.dirname(os.path.realpath(__file__))

db = DbWrapper(base_path, "database.db")

locations_url = db.get_random_locations(9, 13)

neural_network = NeuralNetwork()

# Wait to be more human
if not args.fast:
    time.sleep(random.randint(33, 1800))  # seconds

# Init browser driver
profile = webdriver.FirefoxProfile()
profile.set_preference(
    "general.useragent.override",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0",
)
options = Options()

if os.environ.get("ENVIRONMENT") == "production":
    options.headless = True

driver = webdriver.Firefox(profile, service_log_path=os.devnull, options=options)

driver.maximize_window()

# Start !!
print("Login\n")
driver.get("https://www.instagram.com/accounts/login/")

driver.implicitly_wait(3)  # seconds

# Wait until page is loaded
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))

# Manage cookie popup
try:
    time.sleep(random.randint(2, 4))  # seconds
    cookie_button = driver.find_element_by_xpath(xpath["accept_btn"])
    cookie_button.click()
except NoSuchElementException:
    pass

# Enter credentials
insta_username = os.environ.get("INSTA_USERNAME")
insta_password = os.environ.get("INSTA_PASSWORD")

driver.find_element_by_name("username").send_keys(insta_username)
driver.find_element_by_name("password").send_keys(insta_password)

# Log in
driver.find_element_by_xpath(xpath["login_btn"]).click()

# Manage save login info page
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, xpath["not_now_btn"]))
    )
    time.sleep(random.randint(2, 4))  # seconds
except TimeoutException:
    pass

try:
    login_info_button = driver.find_element_by_xpath(xpath["not_now_btn"])
    login_info_button.click()
except NoSuchElementException:
    pass

# Manage notification pop up
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, xpath["not_now_btn"]))
    )
    time.sleep(random.randint(2, 4))  # seconds
except TimeoutException:
    pass

try:
    notification_button = driver.find_element_by_xpath(xpath["not_now_btn"])
    notification_button.click()
except NoSuchElementException:
    pass

for city_url in locations_url:

    # Go to explore instagram
    print("############################################")
    print(city_url.split("/")[-2])
    print("############################################\n")
    try:
        driver.get(city_url)
    except TimeoutException:
        continue

    time.sleep(random.randint(2, 4))  # seconds

    history = []

    for nb_load in range(random.randint(4, 9)):
        if nb_load > 0:
            wait = random.uniform(8.8, 31.8)
            print("wait", wait, "s")
            time.sleep(wait)  # seconds

            # Go to the bottom page to trigger new images loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait until end of new images loading
            try:
                WebDriverWait(driver, 120).until(
                    EC.invisibility_of_element_located((By.XPATH, xpath["loading_svg"]))
                )
            except TimeoutException:
                pass

            time.sleep(2)  # seconds

        # Find div images
        try:
            all_div_image_elems = driver.find_elements_by_xpath(xpath["images_div"])

        except ElementClickInterceptedException:
            continue

        # Get new div images
        if not history:
            new_div_image_elems = all_div_image_elems
        else:
            new_div_image_elems = []

            # Filter old div images
            for div_elem in all_div_image_elems:
                image_elem = div_elem.find_element_by_class_name("FFVAD")
                image_url = image_elem.get_attribute("src")

                if image_url not in history:
                    new_div_image_elems.append(div_elem)

        print("new images:", len(new_div_image_elems))
        print("history:", len(history), "\n")

        for div_elem in new_div_image_elems:
            image_elem = div_elem.find_element_by_class_name("FFVAD")
            image_url = image_elem.get_attribute("src")

            if not image_url:
                continue

            history.append(image_url)

            detections = neural_network.detect(image_url)

            # For the third first finded objects, check if there is a cat
            for detection in detections:
                label = "{}: {:.2f}%".format(
                    detection["classe"], detection["confidence"]
                )
                print(label)

                # If it's a cat with upper x% of precision
                if detection["confidence"] > 55 and detection["classe"] == "cat":
                    link_elem = div_elem.find_element_by_tag_name("a")
                    url = link_elem.get_attribute("href")

                    # Check if already send by insert url into database
                    if db.already_send(url):
                        print("Already checked")
                        # Get ouf loop for finding cat
                        break
                        # Get ouf loop for check photos
                        break
                        # Get ouf loop for scroll down X times
                        break

                    # Scroll to element
                    driver.execute_script(
                        "window.scrollTo(0, {});".format(div_elem.location["y"])
                    )

                    # Open image box and comment
                    div_elem.click()

                    wait = random.uniform(2.4, 5.1)
                    print("wait", wait, "s, watching photo")
                    time.sleep(wait)  # seconds

                    try:
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located(
                                (
                                    By.XPATH,
                                    xpath["user_name"],
                                )
                            )
                        )
                    except TimeoutException:
                        print("No user name")
                        break

                    user_name = driver.find_element_by_xpath(xpath["user_name"]).text

                    if db.contains_value_in_table(
                        "forbidden_words_in_user_name", user_name
                    ):
                        print("User name banned by contains")
                        break

                    if db.exist_in_table("user_name_banned", user_name):
                        print("User name banned")
                        break

                    like_elem = driver.find_element_by_xpath(xpath["like_btn"])
                    pass_filter = True
                    like_state = ""
                    words = []
                    confidence_limit = 95

                    try:
                        # Find author image's description
                        description_text = driver.find_element_by_xpath(
                            xpath["description"]
                        ).text.lower()

                        words += re.sub("[^\w]", " ", description_text).split()

                    # If no description, do noting
                    except NoSuchElementException:
                        pass

                    # Find first comment, some times
                    try:
                        comment_text = driver.find_element_by_xpath(
                            xpath["first_comment"]
                        ).text.lower()

                        words += re.sub("[^\w]", " ", comment_text).split()

                    # If no first comment, do noting
                    except NoSuchElementException:
                        pass

                    # If words, change confidence_limit
                    if words:
                        if db.exist_in_table("forbidden_words", words):
                            pass_filter = False

                        if db.exist_in_table("ignoring_words", words):
                            if not db.exist_in_table("wanted_words", words):
                                pass_filter = False
                            else:
                                confidence_limit = 70

                        elif db.exist_in_table("wanted_words", words):
                            confidence_limit = 60

                        wait = len(words) * (60 / random.randint(270, 300))
                        print("wait", wait, "s, reading comment")
                        time.sleep(wait)  # seconds

                    # Like if not already liked
                    if pass_filter and detection["confidence"] > confidence_limit:
                        if db.count_like(user_name) < 4:
                            try:
                                driver.find_element_by_xpath(xpath["liked_btn_svg"])
                                like_elem = driver.find_element_by_xpath(
                                    xpath["like_btn"]
                                )
                                like_elem.click()

                                wait = random.uniform(0.7, 2.8)
                                print("wait", wait, "s, photo liked")
                                time.sleep(wait)  # seconds

                                like_state = ":heart: "

                            except NoSuchElementException:
                                print("Already liked")

                        else:
                            print("Too much user like")
                            continue
                            like_state = ":broken_heart: "

                    # Click image box
                    cross_elem = driver.find_element_by_xpath(xpath["cross_btn"])
                    cross_elem.click()

                    if not pass_filter:
                        print("Filter not pass:", url)
                    else:
                        # Check if already send by insert url into database
                        liked = 1 if like_state == ":heart: " else 0

                        if not db.add_like(user_name, liked, url):
                            print("Already sended")
                            break

                        content = "{:.2f}% ".format(detection["confidence"])

                        content += like_state
                        content += url

                        data = {"content": content}
                        discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
                        requests.post(discord_webhook_url, data=data)
                        print(url)

                    break

            print()

driver.quit()
db.close()
