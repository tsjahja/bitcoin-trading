import gdax
import json
import numpy as np
import openpyxl
from openpyxl.workbook import Workbook
import time

VOLUME_ORDER_DIFFERENCE = 3;
STREAK_TRESHOLD = 3;

BITCOIN = 'BTC-USD'
OUTPUT_FILE = 'bitcoin-trading-history.xlsx'



def create_new_file():
	new_book = Workbook()
	new_sheet = new_book.worksheets[0]
	new_sheet.title = BITCOIN
	new_sheet.append(['Timestamp', 'Bidding average price', 'Bidding total volume', 'Asking average price', 'Asking total volume', 'Current price', 'Action'])
	new_book.save(filename = OUTPUT_FILE)

def get_average_price(order_book):
	volume =  np.multiply(order_book[:, 2], order_book[:, 1])
	total_volume = sum(volume)
	total_price = sum(np.multiply(order_book[:, 0], volume))
	return [total_price / total_volume, total_volume]

def get_recent_trade():
	trades = np.array(public_client.get_product_trades(product_id=BITCOIN))
	sell_size = 0.00
	buy_size = 0.00
	for trade in trades:
		if trade['side'] == 'buy':
			buy_size = buy_size + float(trade['size'])
		else:
			sell_size = sell_size + float(trade['size'])
	return buy_size, sell_size

def write_to_file(time, bids, asks, current_price, action):
	book = openpyxl.load_workbook(OUTPUT_FILE)
	sheet = book.active

	if action == 'BUY':
		sign = 1
	elif action == 'SELL':
		sign = -1
	else:
		sign = 0

	sheet.append([time['iso'], bids[0], bids[1], asks[0], asks[1], current_price, action, current_price * sign])
	book.save(OUTPUT_FILE)

def run(auth_client, public_client, been_bought_streak):

	order_book = public_client.get_product_order_book(BITCOIN, level=2)
	bids_order_book = np.array(order_book["bids"], dtype=float)
	asks_order_book = np.array(order_book["asks"], dtype=float)

	time = public_client.get_time()
	bids = get_average_price(bids_order_book)
	asks = get_average_price(asks_order_book)
	current_price = public_client.get_product_ticker(product_id=BITCOIN)["price"]
	# recent_trade = get_recent_trade()

	print ''
	print 'time:', time['iso']
	print 'bids:', bids
	print 'asks:', asks
	print 'price:', current_price
	# print 'trade quantity', recent_trade
	bought_streak = buy_sell(auth_client, bids[1], asks[1], current_price, been_bought_streak[0], been_bought_streak[1], been_bought_streak[2])
	print bought_streak
	print '--------------------------------'

	if (bought_streak[0] > 0 and been_bought_streak[0] < 0):
		action = 'BUY'
	elif (bought_streak[0] < 0 and been_bought_streak[0] > 0):
		action = 'SELL'
	else:
		action = ''

	write_to_file(time, bids, asks, current_price, action)
	return bought_streak

def buy_sell(auth_client, bids_volume, asks_volume, price, bought_price, buy_streak, sell_streak):

	# price going up potential
	if (bids_volume > VOLUME_ORDER_DIFFERENCE * asks_volume):
		buy_streak += 1
		if (bought_price < 0 and buy_streak >= STREAK_TRESHOLD):
			buy(auth_client, price)
			print 'BUY', price
			bought_price = price
			buy_streak = 0
			
	# price going down potential
	elif (asks_volume > VOLUME_ORDER_DIFFERENCE * bids_volume):
		sell_streak += 1
		if (bought_price > 0 and bought_price < price and sell_streak >= STREAK_TRESHOLD):
			sell(auth_client, price)
			print 'SELL', price
			bought_price = -1
			sell_streak = 0
	else:
		sell_streak = 0
		buy_streak = 0

	return bought_price, buy_streak, sell_streak

def buy(auth_client, buy_price):
	auth_client.buy(price=buy_price, size='1', product_id=BITCOIN)

def sell(auth_client, sell_price):
	auth_client.sell(price=sell_price, size='1', product_id=BITCOIN)


if __name__ == '__main__':
	create_new_file()
	public_client = gdax.PublicClient()
	# Use the sandbox API (requires a different set of API access credentials)
	auth_client = gdax.AuthenticatedClient(key, b64secret, passphrase, api_url="https://api-public.sandbox.gdax.com")

	bought_streak = -1, 0, 0
	while True:
		bought_streak = run(auth_client, public_client, bought_streak)
		time.sleep(1)








