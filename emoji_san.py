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
import upload

URL = "https://{team_name}.slack.com/customize/emoji"

def lambda_handler(event, context):
    load_dotenv(join(dirname(__file__), ".env"))
    parameters = parse_token(event["body"])
    payload = command(parameters)

    return { "statusCode": 200, "body": json.dumps(payload) }

def parse_token(token):
    parsed = urlparse.parse_qs(token)
    return {
        "user_id": parsed["user_id"][0],
        "channel_id": parsed["channel_id"][0],
        "text": parsed["text"][0],
        "response_url": parsed["response_url"][0],
        "team_id": parsed["team_id"][0],
        "channel_name": parsed["channel_name"][0],
        "token": parsed["token"][0],
        "command": parsed["command"][0],
        "team_domain": parsed["team_domain"][0],
        "user_name": parsed["user_name"][0],
    }

def command(parameters):
    if parameters["command"] == "/emojisan":
        return command_emojisan(parameters)
    else:
        return {
            "text": "Not supported command: %s" % parameters["command"]
        }

def command_emojisan(parameters):
    image = download_image(parameters["text"])
    image = resize_image(image)
    image.save("/tmp/temp.jpg", "JPEG")
    session = requests.session()
    session.headers = {"Cookie": os.environ["SLACK_COOKIE"]}
    session.url = URL.format(team_name=os.environ["SLACK_TEAM"])
    upload_emoji(session, "hogehoge", "/tmp/temp.jpg")
    return {
        "text": "Emoji Sanです %s" % (parameters["text"])
    }

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
    session.post(session.url, data=data, files=files, allow_redirects=False)