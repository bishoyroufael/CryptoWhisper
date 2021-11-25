'''
	This is cryptowhisper, don't tell anyone about it ;)
	Author: Bishoy Roufael
'''
from krakipy import KrakenAPI
import time
import telegram_send
from utils import calculate_best_fit, calculate_gradient, get_prices, save_price_figure, get_latest_price_stat, remove_dir
import hjson
from multiprocessing import Pool
from config import config as cfg
import subprocess


if __name__ == '__main__':
	kr = KrakenAPI()
	assets_file = open('hjson/.assets')
	assets = hjson.load(assets_file)['assets']

	while True:
		try:
			dfs_arr = get_prices(kr, assets)		
			for df in dfs_arr:
				l_p = get_latest_price_stat(df)
				# calculate_best_fit(df)
				g_d = calculate_gradient(df)
				
				if (g_d.percentile_history[-1] > cfg.alert_threshold_percentile) and (l_p.low) and (l_p.for_duration > cfg.alert_time_delta):
					dir_path, img_path = save_price_figure(df)
					cmd_text   = 'telegram-send --format markdown "*Alert for {}!*\n\t*Price:* {}\n\t*Gradient Percentile:* {}\n\t*For Duration:* {}"'.format(df.asset_code,l_p.latest_price, g_d.percentile_history[-1], l_p.for_duration)
					cmd_image = 'telegram-send --image {} --caption {}'.format(img_path, df.asset_code)
					subprocess.run(cmd_text)
					subprocess.run(cmd_image)
					remove_dir(dir_path)
					# print(l_p, g_d)
			print("[INFO] Sleeping 60 secs ...")
			time.sleep(60)
		except Exception as e:
			print(e)
			break
	assets_file.close()