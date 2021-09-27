#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 26 10:05:16 2021

@author: ryzon
"""
import socket
import os
import datetime
import pandas_ta as pta
import btalib
import pandas as pd
import json
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from time import sleep
from binance import ThreadedWebsocketManager
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import logging
import tkinter as tk
import re
from dotenv import load_dotenv

ClientMultiSocket = socket.socket()
host = '127.0.0.1'
port = 2005

load_dotenv()

root= tk.Tk()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
testnet_api_key = os.getenv('SPOT_TESTNET_KEY')
testnet_secret_key = os.getenv('SPOT_TESTNET_SECRET')
client = Client(testnet_api_key, testnet_secret_key)
client.API_URL = 'https://testnet.binance.vision/api'
BUY_PERCENT = float(os.getenv('SPOT_BUY_PERCENT'))
SELL_PERCENT = float(os.getenv('SPOT_SELL_PERCENT'))
ST_PRICE_PERCENT = float(os.getenv('SPOT_STOP_PRICE_PERCENT'))
STL_PRICE_PERCENT = float(os.getenv('SPOT_STOPLIMIT_PRICE_PERCENT'))
DEFAULT_USDT = float(os.getenv('SPOT_DEFAULT_USDT'))
set_default = True

def exit_root():
    root.destroy()


def saveDetails():
    global set_default,BUY_PERCENT,SELL_PERCENT,ST_PRICE_PERCENT,STL_PRICE_PERCENT,DEFAULT_USDT
    set_default = False
    STL_PRICE_PERCENT = float(entry1.get())
    SELL_PERCENT = float(entry2.get())
    ST_PRICE_PERCENT = float(entry3.get())
    BUY_PERCENT = float(entry4.get())
    DEFAULT_USDT = float(entry5.get())
    testnet_api_key = entry6.get()
    testnet_secret_key = entry7.get()

    os.environ['SPOT_BUY_PERCENT'] = str(BUY_PERCENT)
    os.environ['SPOT_SELL_PERCENT'] = str(SELL_PERCENT)
    os.environ['SPOT_STOP_PRICE_PERCENT'] = str(ST_PRICE_PERCENT)
    os.environ['SPOT_STOPLIMIT_PRICE_PERCENT'] = str(STL_PRICE_PERCENT)
    os.environ['SPOT_DEFAULT_USDT'] = str(DEFAULT_USDT)
    root.destroy()
    
def nospecial(text):
	text = re.sub("[^a-zA-Z0-9]+", " ",text)
	return text

def extract_perc(perc, num):
    result = float((perc/100)*num)
    return float(result)

def get_account_balances():
    balance = client.get_account()
    return balance

def get_account_balance(asset):
    balance = client.get_asset_balance(asset=asset,timestamp=client.get_server_time()['serverTime'])
    return balance['free']

usdt_balance = get_account_balance('USDT')
btc_balance = get_account_balance('BTC')

canvas1 = tk.Canvas(root, width = 500, height = 450,  relief = 'raised')
canvas1.pack()

label2 = tk.Label(root, text='ENTER STOP LIMIT PERCENT:')
label2.config(font=('helvetica', 10))
canvas1.create_window(150, 40, window=label2)

label3 = tk.Label(root, text='ENTER SELL PERCENT:')
label3.config(font=('helvetica', 10))
canvas1.create_window(150, 80, window=label3)

label4 = tk.Label(root, text='ENTER STOP PERCENT:')
label4.config(font=('helvetica', 10))
canvas1.create_window(150, 120, window=label4)

label5 = tk.Label(root, text='ENTER BUY PERCENT:')
label5.config(font=('helvetica', 10))
canvas1.create_window(150, 160, window=label5)

label6 = tk.Label(root, text='ENTER USDT VALUE:')
label6.config(font=('helvetica', 10))
canvas1.create_window(150, 200, window=label6)

label7 = tk.Label(root, text='USDT ACCOUNT BALANCE:                        {}'.format(usdt_balance))
label7.config(font=('helvetica', 10))
canvas1.create_window(250, 240, window=label7)

label8 = tk.Label(root, text='BTC ACCOUNT BALANCE:                         {}'.format(btc_balance))
label8.config(font=('helvetica', 10))
canvas1.create_window(250, 280, window=label8)

label9 = tk.Label(root, text='ENTER API KEY:')
label9.config(font=('helvetica', 10))
canvas1.create_window(150, 320, window=label9)

label10 = tk.Label(root, text='ENTER API SECRET:')
label10.config(font=('helvetica', 10))
canvas1.create_window(150, 360, window=label10)


entry1 = tk.Entry (root) 
entry1.insert(0, STL_PRICE_PERCENT)
canvas1.create_window(350, 40, window=entry1)
entry2 = tk.Entry (root) 
entry2.insert(0, SELL_PERCENT)
canvas1.create_window(350, 80, window=entry2)
entry3 = tk.Entry (root) 
entry3.insert(0, ST_PRICE_PERCENT)
canvas1.create_window(350, 120, window=entry3)
entry4 = tk.Entry (root) 
entry4.insert(0, BUY_PERCENT)
canvas1.create_window(350, 160, window=entry4)
entry5 = tk.Entry (root) 
entry5.insert(0, DEFAULT_USDT)
canvas1.create_window(350, 200, window=entry5)
entry6 = tk.Entry (root) 
entry6.insert(0, testnet_api_key)
canvas1.create_window(350, 320, window=entry6)
entry7 = tk.Entry (root) 
entry7.insert(0, testnet_secret_key)
canvas1.create_window(350, 360, window=entry7)

button1 = tk.Button(text='SAVE DETAILS', command=saveDetails, bg='white', fg='black', font=('helvetica', 9, 'bold'))
canvas1.create_window(250, 400, window=button1)
root.mainloop()

def get_symbol_price(symbol):
    price = client.get_symbol_ticker(symbol=symbol)
    return price['price']


def get_time_stamp(symbol, time_interval):
    time_stamp = client._get_earliest_valid_timestamp(symbol=symbol, interval=time_interval)
    return time_stamp


def get_historical_price(symbol, time_interval, time_stamp, limit):
    bars = client.get_historical_klines(symbol, time_interval, time_stamp, limit=limit)
    for line in bars:
        del line[5:]

    price_df = pd.DataFrame(bars,
                            columns=['date', 'open', 'high', 'low', 'close'])
    price_df['ema'] = price_df['close'].ewm(span=10).mean()
    price_df['rsi'] = pta.rsi(price_df['close'].astype(float), length=14)
    price_df.set_index('date', inplace=True)
    return price_df.tail(5)

def buy_symbol(symbol, quantity, price):
    try:
        buy_market = client.create_order(
            symbol=symbol,
            side='BUY',
            type='LIMIT',
            quantity=quantity,
            timeInForce='GTC',
            price=price,
            timestamp=client.get_server_time()['serverTime'],
            newOrderRespType='FULL')

        return buy_market

    except BinanceAPIException as e:
        return e
    except BinanceOrderException as e:
        return e
        
def sell_oco_symbol(symbol, quantity, r, t_price , t_limit_price):
    try:
        sell_market = client.order_oco_sell(
            symbol= symbol,                                            
            quantity= quantity,                                            
            price= r,                                            
            stopPrice= t_price,                                            
            stopLimitPrice= t_limit_price,                                            
            stopLimitTimeInForce= 'GTC',
            timestamp=client.get_server_time()['serverTime'])
        
        return sell_market

    except BinanceAPIException as e:
        return e
    except BinanceOrderException as e:
        return e 

def parser(msg):
    temp = msg
    target = temp.lower()
    if "zone" in target:
        pass
    elif "short" in target:
        pass
    elif "buy" in target:
        try:
            index_hash = target.lower().index('#')
            token = nospecial(target[index_hash+1:])
        except:
            index_hash = 0
            token = nospecial(target[index_hash])
        if "rebuy" in token.lower():
            index_reb = token.lower().index('rebuy')
            token = token[:index_reb]
        if "buy" in token.lower():
            index_reb = token.lower().index('buy')
            token = token[:index_reb]
        if "spot" in token.lower():
            index_reb = token.lower().index('spot')
            token = token[:index_reb]
        if "setup" in token.lower():
            index_reb = token.lower().index('setup')
            token = token[:index_reb]
        if "scalp" in token.lower():
            index_reb = token.lower().index('scalp')
            token = token[:index_reb]
        token = str(token)+'USDT'
        token = token.replace(" ",'')
        print(token)
        token = token.upper()
        try:
            exchange_info = client.get_orderbook_ticker(symbol=token)
            div_value = float(exchange_info['askPrice'])
            value = float(div_value) + extract_perc(BUY_PERCENT, div_value)
            price_precision = str(float(div_value))
            prc_precision_index = price_precision.index('.')
            prc_precision = len(price_precision) - prc_precision_index - 1
            if int(prc_precision) == 1 and int(price_precision[-1])==0:
                prc_zero_precision=True
            else:
                prc_zero_precision = False     
            quantity_precision = float(exchange_info['askQty'])
            quantity_precision = str(float(quantity_precision))
            qty_precision_index = quantity_precision.index('.')
            qty_precision = len(quantity_precision) - qty_precision_index - 1
            if int(qty_precision) == 1 and int(quantity_precision[-1])==0:
                qty_zero_precision=True
            else:
                qty_zero_precision = False     
            qs = float(DEFAULT_USDT/value)
            qs = round(qs, qty_precision)
            price = round(value, prc_precision)
            try:
                resp = buy_symbol(token, qs, price)
                print(resp)
                avg_value = 0
                items = 0
                for key,value in resp.items():
                    if 'price' == key:
                        avg_value = float(avg_value) + float(value)
                        items = float(items) + float(1)     
                temp_price = float(avg_value/items)
                total_price = float(temp_price) - extract_perc(ST_PRICE_PERCENT, temp_price)
                t_price = round(total_price, prc_precision)
                total_limit_price = float(temp_price) - extract_perc(STL_PRICE_PERCENT, temp_price)
                t_limit_price = round(total_limit_price, prc_precision)
                total_pr = temp_price + extract_perc(SELL_PERCENT, temp_price)
                r = round(total_pr, prc_precision)
                if prc_zero_precision == True and qty_zero_precision == True:
                    resp2 = sell_oco_symbol(token, int(qs) ,int(r) , int(t_price), int(t_limit_price))    
                elif prc_zero_precision == False and qty_zero_precision == True:
                    resp2 = sell_oco_symbol(token, int(qs) ,r , t_price, t_limit_price)    
                elif prc_zero_precision == True and qty_zero_precision == False:
                    resp2 = sell_oco_symbol(token, qs ,int(r) , int(t_price), int(t_limit_price))    
                else:
                    resp2 = sell_oco_symbol(token, qs ,r , t_price, t_limit_price)  
                print(resp2)
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)
try:
    ClientMultiSocket.connect((host, port))
except socket.error as e:
    print(str(e))

res = ClientMultiSocket.recv(1024)
while True:
    res = ClientMultiSocket.recv(1024)
    parser(res.decode('utf-8'))

ClientMultiSocket.close()