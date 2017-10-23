# -*- coding: utf-8 -*-

import os
import json
import upload
import urlparse
import requests
import commands
import threading
from PIL import Image
from StringIO import StringIO
from os.path import join, dirname
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import upload

URL = "https://{team_name}.slack.com/customize/emoji"

def lambda_handler(event, context):
    load_dotenv(join(dirname(__file__), ".env"))
    payload = command(event)

    return { "statusCode": 200, "body": json.dumps(payload) }

def command(parameters):
    if parameters["command"] == "/emojisan":
        return command_emojisan(parameters)
    else:
        return {
            "text": "Not supported command: %s" % parameters["command"]
        }

def command_emojisan(parameters):
    image = download_image(parameters["image_url"])
    image = resize_image(image)
    image.save("/tmp/temp.jpg", "JPEG")
    session = requests.session()
    session.headers = {"Cookie": os.environ["SLACK_COOKIE"]}
    session.url = URL.format(team_name=os.environ["SLACK_TEAM"])
    e = upload_emoji(session, parameters["emoji_name"], "/tmp/temp.jpg")
    notify_slack(parameters)

def download_image(url):
    response = requests.get(url)
    return Image.open(StringIO(response.content))

def resize_image(image):
    image.thumbnail((128, 128), Image.ANTIALIAS)
    return image

def upload_emoji(session, emoji_name, filename):
    # Fetch the form first, to generate a crumb.
    r = session.get(session.url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    crumb = soup.find("input", attrs={"name": "crumb"})["value"]

    data = {
        'add': 1,
        'crumb': crumb,
        'name': emoji_name,
        'mode': 'data',
    }
    files = {'img': open(filename, 'rb')}
    return session.post(session.url, data=data, files=files, allow_redirects=False)

def notify_slack(parameters):
    payload = {
        "text": "Success upload: [:%s:]" % parameters["emoji_name"]
    }
    requests.post(parameters["response_url"], data=json.dumps(payload))