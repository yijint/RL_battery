'''
### Loading data from gridstatus
- example: https://docs.gridstatus.io/en/latest/Examples/caiso/Downloading%20CAISO%20Data.html
- API: https://docs.gridstatus.io/en/stable/_modules/gridstatus/caiso.html#CAISO.get_solar_and_wind_forecast_dam
- data decisions: https://docs.google.com/document/d/1ZrfWcvQF2d5r5BqVCnbPZ2dhwZTkmr_CQQ22Ic-wWqE/edit?tab=t.0

Note that retrieving the wind and solar requires the latest version of gridstatus which has a dependency conflict with gridworld, so this is run in a different conda environment from gridworld.
'''

# import packages 
import gridstatus
import pandas as pd

# load grid
caiso = gridstatus.CAISO()

# MOER data is available for Jan 01, 2017 - Oct 31, 2024,
# but CAISO only provides last 39 months of data (3 years and 3 months),
# so load data for that range only 
start='20210901'
end='20241101'

# retrieve and save load, load forecast, and price (lmp) data 
print('Retrieving load and load forecast data')
load_df = caiso.get_load(start, end=end) # takes 8 minutes
load_forecast_df = caiso.get_load_forecast(start, end=end) # takes 4 minutes

print('Saving load and load forecast data')
load_df.to_csv(f'raw_data/load/caiso_5min_load_{start}_{end}')
load_forecast_df.to_csv(f'raw_data/load_forecast/caiso_hourly_load_forecast_{start}_{end}')