#!/usr/bin/python
import time
import logging
import yaml
import os
import sys
import socket
import requests
from datetime import datetime
from enum import Enum
from PIL import Image,ImageDraw,ImageFont

dirname = os.path.dirname(__file__)

libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)
from waveshare_epd import epd2in13_V2

# Globals
configFile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.yaml')
currentTickerIndex = 0

# Fonts
font15 = ImageFont.truetype(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Font.ttc'), 15)
font20 = ImageFont.truetype(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Font.ttc'), 20)
font25 = ImageFont.truetype(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Font.ttc'), 25)
font32 = ImageFont.truetype(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Font.ttc'), 32)

# Images
upBMP = Image.open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'up.bmp'))
upBMP = upBMP.resize((25, 25))
downBMP = Image.open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'down.bmp'))
downBMP = downBMP.resize((25, 25))

class connectionType(Enum):
    INTERNET = 1
    API = 2


def main(loglevel=logging.WARNING):
    # To debug, uncomment this line (default is warning)
    loglevel = logging.DEBUG
    logging.basicConfig(level=loglevel)

    try:
        logging.info("[Stock-Ticker] Starting stock ticker...")

        # Load configuration file (config.yaml)
        logging.info("[Stock-Ticker] Attempt to load config...")
        with open(configFile) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        logging.info(config)

        # Check internet connection
        connectionCheck(connectionType.INTERNET)

        # Initialize display
        if(config["debug"]["ignoreDisplayCode"] == False):
            epd = epd2in13_V2.EPD()
            logging.info("[Display] Init & clear display...")
            epd.init(epd.FULL_UPDATE)

        # Ticker
        logging.info("[Stock-Ticker] Start ticker process...")
        while True:
            updateStockTicker(config, epd)
            time.sleep(10)

    except Exception as e:
        logging.info(e)

# Update the ticker, load new data & refresh display
def updateStockTicker(config, epd):
    global currentTickerIndex

    stockData = fetchStockData(config, config["stockData"]["tickers"][currentTickerIndex])

    if(currentTickerIndex != (len(config["stockData"]["tickers"]) - 1)):
        currentTickerIndex += 1
    else:
        currentTickerIndex = 0

    logging.info("[Current Ticker] Current ticker has updated to index {} ({})".format(currentTickerIndex, config["stockData"]["tickers"][currentTickerIndex]))

    if(config["debug"]["ignoreDisplayCode"] == False):
        updateDisplay(stockData, epd)

# Update the e-Paper display
def updateDisplay(stockData, epd):
    logging.info("[Display] Starting display update...")

    epd = epd2in13_V2.EPD()
    epd.init(epd.FULL_UPDATE)
    image = Image.new('L', (epd.height, epd.width), 255)    # 255: clear the image with white
    draw = ImageDraw.Draw(image)              
    
    draw.text((0,0),stockData["ticker"],font=font25,fill = 0)
    draw.text((0,25),stockData["companyName"],font=font15,fill = 0)

    percentageSinceLastClose = round(calculatePercentageIncreaseDecrease(stockData["previousClose"],stockData["price"]), 2)
    draw.text((180, 0),"{:.2f}%".format(percentageSinceLastClose) ,font=font20,fill = 0)
    if(percentageSinceLastClose >= 0):
        image.paste(upBMP, (150,0))
    else:
        image.paste(downBMP, (150,0))    


    # draw.rectangle([(0,100),(250,250)],outline = 0)
    draw.line((0,101, 300,101), fill=0)

    draw.text((0, 50), "{}".format(stockData["price"]), font=font32,fill=0)

    dayText = datetime.today().strftime("%A")[0:3]
    fullDateText = datetime.today().strftime("%d %b %y | %H:%M")
    draw.text((0, 102), "{} {}".format(dayText, fullDateText), font=font15, fill=0)

    image=image.transpose(Image.ROTATE_90)
    epd.display(epd.getbuffer(image))

# Fetch stock data from API
def fetchStockData(config, ticker):
    requestUrl = config['stockData']['url'] + "stockInfo/{}".format(ticker)
    logging.info("[Stock Data] Attempting to fetch data for ticker: {}".format(ticker))
    response = requests.get(requestUrl)
    if(response.status_code == 200):
        return response.json()
    else:
        logging.info("[Stock Data] Failed to fetch stock data: returned error {}".format(response.status_code))
        # TO-DO: Add way to handle API request fail

# Handle connection checks
def connectionCheck(conType):
    logging.info("[Connection Check] Attempting {} connection check...".format(conType.name))
    if(conType == connectionType.INTERNET):
        try:
            host = socket.gethostbyname("google.com")
            s = socket.create_connection((host, 80), 2)
            s.close()
            logging.info("[Connection Check] Internet connection passed, connected")
            return True
        except:
            logging.info("[Connection Check] Internet connection failed, check internet connection")
            time.sleep(1)
        return False
    elif(conType == connectionType.API):
        print("api if check")

# Percentage increase/decrease
def calculatePercentageIncreaseDecrease(num1, num2):
    return (num2 - num1) * 100 / num1

# def getStockData():
    

main()