'''
	This is cryptowhisper, don't tell anyone about it ;)
	Author: Bishoy Roufael
'''
from krakipy import KrakenAPI
import time
import telegram_send
from utils import calculate_gradient, get_prices, save_prices_figure, compare_with_duration
import hjson
from multiprocessing import Pool



if __name__ == '__main__':
	kr = KrakenAPI()
	assets_file = open('hjson/.assets')
	assets = hjson.load(assets_file)['assets']

	while True:
		try:
			dfs_arr = get_prices(kr, assets)		
			t = compare_with_duration(dfs_arr[0])
			# save_prices_figure(dfs_arr)
			print(t)
			# calculate_gradient(dfs)
			# draw_prices(dfs)
			# telegram_send.send(messages=["BTC: {} EUR \nETH: {} EUR".format(pra, prb)])	
			print("[INFO] Sleeping 60 secs ...")
			time.sleep(10)
		except Exception as e:
			print(e)
			break
	assets_file.close()