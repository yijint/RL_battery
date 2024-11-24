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
print('Retrieving price (lmp) data')
lmp_df = caiso.get_lmp(start=start, end=end, market='REAL_TIME_5_MIN', locations = ["TH_SP15_GEN-APND"])

print('Saving price (lmp) data')
lmp_df.to_csv(f'raw_data/lmp/caiso_5min_lmp_{start}_{end}')