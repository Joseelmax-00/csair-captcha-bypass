"""The purpose of this script is to test the security of tang.csair.com. It's a custom 
method designed to test the capabilities of their bot-detection measures, as well as 
good training on Selenium automation for myself. 

Do not use with commercial purposes, who knows, you might get sued."""

import json
import os
import time
import requests
from seleniumrequests import Chrome
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import ElementNotInteractableException
from img_detection import match_piece_to_gap, load_images


def wait_for_loading(driver):
    """Defines a custom wait condition to wait until the captcha has loaded correctly.

    Returns True if the captcha has already loaded, False if not."""
    element = driver.find_element(By.ID, 'slide-bigImg')
    if '/style/jquery-verify/img/loading.gif' in element.get_attribute('src'):
        return False
    else:
        return True

def captcha_exists(driver):
    """Defines a custom wait condition to wait until the captcha has disappeared (solved correctly).

    Returns True if the captcha is already solved, False if not."""
    try:
        element = driver.find_element(By.ID, 'verify-pic')
        element.click()
        return True
    except ElementNotInteractableException:
        return False

# Setup Chrome options
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
# chrome_options.add_argument("--headless") # Ensure GUI is off
# chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("--disable-dev-shm-usage")

# Set path to chromedriver as per your configuration
webdriver_service = Service(ChromeDriverManager().install())

# Choose Chrome Browser
driver = Chrome(service=webdriver_service, options=chrome_options)

# URL to navigate
url = "https://tang.csair.com/EN/WebFace/Tang.WebFace.Cargo/AgentAwbBrower.aspx?lan=en-us"
driver.get(url)

# AWS Code provided (Should be changed to actual code when in production)
prefix = 784
code = 34013033

time.sleep(1)  

# Input value for prefix into the textbox
prefix_input = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_txtPrefix')
prefix_input.clear()
prefix_input.send_keys(prefix)

time.sleep(1)  

# Input value for code into the textbox
code_input = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_txtNo')
code_input.clear()
code_input.send_keys(code)

button = driver.find_element(By.ID, 'btnSearch')
button.click()

# Wait until the 'src' attribute of the 'slide-bigImg' image changes from 'loading.gif'
WebDriverWait(driver, 60).until(wait_for_loading)

print("Captcha loaded. Saving images and processing captcha...")

# Get the captcha element
element = driver.find_element(By.ID, 'verify-pic')

# Take and save a screenshot of the element
# element.screenshot('captcha_screenshot.png')

# Ensure the directories for the captcha images exist
if not os.path.exists('big_imgs'):
    os.makedirs('big_imgs')
if not os.path.exists('small_imgs'):
    os.makedirs('small_imgs')

### Get the big image element
big_image_element = driver.find_element(By.ID, 'slide-bigImg')
# Get the URL of the image
big_image_url = big_image_element.get_attribute('src')
# Extract the image id from the URL
imgid = big_image_url.split('/')[-1]
response = requests.get(big_image_url)
# Open a file in write and binary mode and write the content of the response
with open(f'big_imgs/{imgid}.png', 'wb') as file:
    file.write(response.content)

### Get the small image element
small_image_element = driver.find_element(By.ID, 'slide-smallImg')
# Get the URL of the image
small_image_url = small_image_element.get_attribute('src')
# Send a GET request to the image URL
response = requests.get(small_image_url)
# Open a file in write and binary mode and write the content of the response
with open(f'small_imgs/{imgid}.png', 'wb') as file:
    file.write(response.content)


### Image detection
image, puzzle_piece = load_images(imgid)
locations = match_piece_to_gap(puzzle_piece, image)

for XYCoordinates in locations:

    slidex = XYCoordinates[0]
    js_movement_code = """
var element = $("#slide-img-btn"); // Select the element
var startX = 0; // The initial x-coordinate
var startY = 0; // The initial y-coordinate
var endX = SLIDEXREPLACE; // The final x-coordinate (100 pixels to the right)
var endY = 0; // The final y-coordinate (no vertical movement)

// Trigger the mousedown event at the start coordinates
var mousedown = jQuery.Event("mousedown", { clientX: startX, clientY: startY });
element.trigger(mousedown);

// Trigger multiple mousemove events to simulate a more realistic drag
var steps = endX; // Number of intermediate steps
for (var i = 1; i <= steps; i++) {
    var intermediateX = startX + (endX - startX) * i / steps;
    var intermediateY = startY + (endY - startY) * i / steps;
    var mousemove = jQuery.Event("mousemove", { clientX: intermediateX, clientY: intermediateY });
    element.trigger(mousemove);
}

// Trigger the mouseup event at the end coordinates
var mouseup = jQuery.Event("mouseup", { clientX: endX, clientY: endY });
element.trigger(mouseup);
""".replace("SLIDEXREPLACE", str(slidex))

    # Execute the JavaScript code
    driver.execute_script(js_movement_code)

    # Use a lambda to ensure that the function is called fresh every time
    wait = WebDriverWait(driver, 20)
    wait.until_not(lambda driver: captcha_exists(driver))
    if not captcha_exists(driver):
        break


print("Solved successfuly")
# Quit the driver after the operation
# driver.quit()

