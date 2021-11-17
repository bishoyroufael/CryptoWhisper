import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from halo import Halo
from datetime import datetime
import mplfinance as mpf
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np
from PIL import Image

create_path = lambda name : Path(name).mkdir(parents=True, exist_ok=True)
get_time    = lambda : datetime.now().strftime('%Y%m%d%H%M%S')

def compare_with_duration(df, key="close"):
	latest_price = df[key][-1]
	i = -2
	leq = lambda x,y : x <= y
	leq_f = leq(latest_price, df[key][i])
	stat = "NO_STAT_YET"
	dic = {
		"low" : True if leq_f else False,
		"for_duration" : None
	}
	
	while True:
		if abs(i) <= len(df.index):
				if leq_f:
					still_less = leq(latest_price, df[key][i])
					if not still_less:
						diff = df.index[-1] - df.index[i]
						stat = "Lowest price in {}".format(diff)
						dic["for_duration"] = diff
						break
				else:
					still_greater = not leq(latest_price, df[key][i])
					if not still_greater:
						diff = df.index[-1] - df.index[i]
						stat = "Highest price in {}".format(df.index[-1]- df.index[i])
						dic["for_duration"] = diff
						break
		else:
			if leq_f:
				stat = "Lowest price since in the graph!".format(df.index[i])
			else:
				stat = "Highest price in the graph!".format(df.index[i])
			break
		i = i - 1
	return stat, dic

def calculate_gradient(dfs_array, key="close"):
	assert len(dfs_array) != 0, '[ERROR] Recieved an empty array, please ensure that the API is working'
	assert key in ["open", "close", "high", "low"], "[ERROR] Key must be either 'open', 'close', 'high' , or 'low'"
	for df in dfs_array:
		slope = pd.Series( np.gradient(df[key]), df.index, name="gradient")
		price_key = df[key]
		concat = pd.concat([price_key, slope], axis=1)
		concat.plot()
		plt.show()

def save_prices_figure(dfs_array):
	assert len(dfs_array) != 0, '[ERROR] Recieved an empty array, please ensure that the API is working'
	timenow = get_time()
	create_path('imgs/{}'.format(timenow))
	
	props = dict(boxstyle='square', facecolor='blue')
	for df in dfs_array:
		figure = mpf.figure(tight_layout=True, figsize=(15,6))
		ax = figure.add_subplot(1, 1, 1)
		title = df.asset_name + " ({})".format(df.asset_code)
		ax.set_xlabel('Time')
		ax.set_ylabel('Price')
		ax.set_title (title)
		ax.tick_params(axis="x", colors="blue")
		ax.tick_params(axis="y", colors="blue")
		ax.text(0.85, 0.90, 'LCP: {} \nDate: {}'.format(df['close'][-1], df.index[-1]), size=12, color='white',bbox=props, transform=ax.transAxes)
		mpf.plot(df, type='line', mav=(3,6,9), volume=False, warn_too_much_data=999999, ax=ax)
		# figure.savefig('imgs/{}/prices_{}_{}.png'.format(timenow, df.asset_name, df.asset_code), dpi=200)
		figure.set_dpi(200)
		figure.canvas.draw()
		pil_image = Image.frombytes('RGB', figure.canvas.get_width_height(), figure.canvas.tostring_rgb())
		pil_image.save('imgs/{}/prices_{}_{}.png'.format(timenow, df.asset_name, df.asset_code))
		figure.clf()


@Halo(text="Fetching from API ...", spinner='dots')
def get_prices(kr, assets):
	'''
	Get recent low prices
	---------------------

	Args: 
	-	kr			: KrakenAPI() class instance
	-	Assets		: Array containing dics of {name: asset_name, code: asset_code}
	Returns: 
	-	prices		: Array of dataframes having the specified price name daily
	'''
	assert len(assets) != 0, "[ERR] Assets can't be empty!"
	
	prices = []

	convert_timestamp = lambda timestamp : datetime.fromtimestamp(timestamp)	
	for asset in assets:
		print("[INFO] Getting: {}".format(asset["code"]))
		flag = True
		while flag: # Keep trying if api limit is reached 
			try:
				df, _   = kr.get_ohlc_data(asset["code"], 5) # Returns 12 hours of data
				df.asset_name = asset["name"] # Metadata for figures
				df.asset_code = asset["code"] # Metadata for figures
				df ["time"] = [convert_timestamp(x) for x in df["time"]]
				df.set_index("time", inplace=True)
				prices.append(df)
				time.sleep(1)
				flag = False
			except:
				# print("[INFO] Failed, retrying after 5 secs ...")
				time.sleep(5)	
	return prices
