import time
import matplotlib
matplotlib.use('Agg') # Cannot Visualize With AGG
import matplotlib.pyplot as plt
from halo import Halo
from datetime import datetime
import mplfinance as mpf
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np
from PIL import Image
from statistics import NormalDist
from config import config as cfg
from easydict import EasyDict as edict
import os
import shutil


# Handy lambdas
create_path  = lambda name : Path(name).mkdir(parents=True, exist_ok=True)
get_time     = lambda : datetime.now().strftime('%Y%m%d%H%M%S')
normalize_df = lambda df, key: ((df[key] - df[key].min()) / (df[key].max()-df[key].min())) 
remove_dir = lambda dir_p : shutil.rmtree(dir_p)



def get_latest_price_stat(df, key="close"):
	latest_price = df[key][-1]
	i = -2
	leq = lambda x,y : x <= y
	leq_f = leq(latest_price, df[key][i])
	# stat = "NO_STAT_YET"
	dic = edict({
		"latest_price" : latest_price,
		"low" : True if leq_f else False,
		"for_duration" : None
	})
	
	while True:
		if abs(i) <= len(df.index):
				if leq_f:
					still_less = leq(latest_price, df[key][i])
					if not still_less:
						diff = df.index[-1] - df.index[i]
						dic.for_duration = diff
						break
				else:
					still_greater = not leq(latest_price, df[key][i])
					if not still_greater:
						diff = df.index[-1] - df.index[i]
						dic.for_duration = diff
						break
		else:
			if leq_f:
				dic.for_duration = np.inf
			else:
				dic.for_duration = np.inf
			break
		i = i - 1
	return dic



def calculate_best_fit(df, key="close", deg=4):

	normalized_price_df = normalize_df(df, key) 
	# Getting best fit line
	x_lspc = np.linspace(0, 1, len(df.index)) 
	coeffs = np.polyfit(x_lspc, normalized_price_df, deg)	
	poly_fn = np.poly1d(coeffs)
	y_hat = poly_fn(x_lspc) # for plotting 

	y_hatd = np.gradient(y_hat)
	crt_points = np.where(np.diff(np.sign(y_hatd)))[0] # Find switching points
	crt_points_dt = [df.index[pt] for pt in crt_points]


	fit_df = pd.Series(y_hat, df.index, name="bestfit")
	if len(crt_points_dt) != 0:
		inf_pts_df = pd.Series(fit_df[crt_points_dt],index=crt_points_dt, name="infpts")

	_, ax = plt.subplots(1,1)
	fit_df.plot(ax=ax)
	if len(crt_points_dt) != 0:
		inf_pts_df.plot(ax=ax, style='.', markersize=10, color="green")	
	plt.show()	
	dic = edict({
		"coeffs" : coeffs,
		"inf_pts" : crt_points_dt
	})

	return dic


def calculate_gradient(df, key="close"):
	assert key in ["open", "close", "high", "low"], "[ERROR] Key must be either 'open', 'close', 'high' , or 'low'"
	normalized_price_df = normalize_df(df,key) 
	slope_df = pd.Series( np.gradient(normalized_price_df), df.index, name="gradient")

	num_pts = round((cfg.return_history_hrs * 60) / cfg.api_interval)
	

	slope_df_np = slope_df.to_numpy()
	dic = edict({
		"gradient_history" : slope_df[-num_pts:],
		"percentile_history":  [ ((-abs(slope_df_np[-i]) < slope_df_np) & ( slope_df_np < abs(slope_df_np[-i])) ).sum() / len(slope_df_np) for i in range(1, num_pts + 1) ]
	})

	# print(dic)	
	# Visualization
	# _ , axes = plt.subplots(2, 1, sharex=True)
	# normalized_price_df.plot(ax=axes[0])
	# slope_df.plot(ax=axes[1])
	# plt.axhline(y=-slope_df[-1], color='r', linestyle='-')
	# plt.axhline(y=slope_df[-1], color='r', linestyle='-')
	# plt.fill_between(normalized_price_df.index , -slope_df[-1],slope_df[-1],color='green', alpha=0.5)
	# plt.show()

	return dic




def save_price_figure(df):
	timenow = get_time()
	create_path('imgs/{}'.format(timenow))
	
	props = dict(boxstyle='square', facecolor='blue')
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
	figure.set_dpi(200)
	figure.canvas.draw()
	pil_image = Image.frombytes('RGB', figure.canvas.get_width_height(), figure.canvas.tostring_rgb())
	
	save_dir  = 'imgs/{}'.format(timenow)
	save_path =  os.path.join(save_dir, 'prices_{}_{}.png'.format(df.asset_name, df.asset_code)) 
	pil_image.save(save_path)
	figure.clf()
	return save_dir, save_path


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
				df, _   = kr.get_ohlc_data(asset["code"], cfg.api_interval) # Returns 12 hours of data
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
