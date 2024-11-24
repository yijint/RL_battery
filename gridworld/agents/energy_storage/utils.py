"""
Return data in the desired date range 
"""

# import packages
import pandas as pd
import matplotlib.pyplot as plt

# desired data range example
# start_date = pd.Timestamp('2021-10-01', tz='UTC')
# end_date = pd.Timestamp('2024-10-01', tz='UTC')

def get_desired_dates(df, start_date, end_date):
    df['interval_start'] = pd.to_datetime(df['interval_start'], utc=True)
    df['interval_end'] = pd.to_datetime(df['interval_end'], utc=True)
    df = df[(df['interval_start'] >= start_date) & (df['interval_start'] < end_date)].reset_index(drop=True)
    return df

def get_data(start_date, end_date):
    # set file paths
    lmp_fp = 'data/cleaned_data/lmp/caiso_5min_rtm_sp15_lmp_20211001_20240930'
    load_fp = 'data/cleaned_data/load/caiso_5min_load_20211001_20240930'
    load_forecast_fp = 'data/cleaned_data/load_forecast/caiso_hourly_load_forecast_20211001_20240930'
    moer_fp = 'data/cleaned_data/moer/caiso_sdge_5min_moer_v2_20211001_20240930'
    solar_wind_forecast_fp = 'data/cleaned_data/solar_wind_forecast/caiso_sp15_hourly_solar_wind_forecast_20211001_20240930'
    
    # read data
    lmp_df = pd.read_csv(lmp_fp)
    load_df = pd.read_csv(load_fp)
    load_forecast_df = pd.read_csv(load_forecast_fp)
    moer_df = pd.read_csv(moer_fp)
    solar_wind_forecast_df = pd.read_csv(solar_wind_forecast_fp)

    # extract data 
    lmp_df = get_desired_dates(lmp_df, start_date, end_date)
    load_df = get_desired_dates(load_df, start_date, end_date)
    load_forecast_df = get_desired_dates(load_forecast_df, start_date, end_date)
    moer_df = get_desired_dates(moer_df, start_date, end_date)
    solar_wind_forecast_df = get_desired_dates(solar_wind_forecast_df, start_date, end_date)
    return lmp_df, load_df, load_forecast_df, moer_df, solar_wind_forecast_df