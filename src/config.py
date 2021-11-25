from easydict import EasyDict as edict
from datetime import timedelta

config = edict(
    {
        'api_interval': 5, 
        'return_history_hrs': 2,
        'alert_threshold_percentile': 0.85,
        'alert_time_delta': timedelta (hours= 6, minutes= 0)
    })