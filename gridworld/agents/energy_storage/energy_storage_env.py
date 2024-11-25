import numpy as np
import pandas as pd

from scipy.stats import truncnorm

import gymnasium as gym

from gridworld import ComponentEnv
from gridworld.utils import maybe_rescale_box_space, to_raw, to_scaled

from gridworld.log import logger

from utils import get_data
import datetime

class EnergyStorageEnv(ComponentEnv):
    """Simple model of energy storage device that has (separate) linear models 
    for charging and discharging.  Gym specs:
    
        - Observation space:  State of charge (energy stored).
        - Action space:  [-1, 1] for fully charging / discharging, resp.
        - Reward:  0. (reimplement to have a non-trivial reward).
    """

    def __init__(
        self,
        name: str = None,
        storage_range: tuple = (3.0, 50.0),
        initial_storage_mean: float = 30.0,
        initial_storage_std: float = 5.0,
        charge_efficiency: float = 0.95,
        discharge_efficiency: float = 0.9,
        max_power: float = 15.0,
        max_episode_steps: int = 288, 
        control_timedelta: pd.Timedelta = pd.Timedelta(300, "s"),
        rescale_spaces: bool = True,
        date = pd.Timestamp('2021-10-01', tz='UTC'),
        **kwargs
    ):

        super().__init__(name=name)

        self.storage_range = storage_range
        self.initial_storage_mean = initial_storage_mean
        self.initial_storage_std = initial_storage_std
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency
        self.max_power = max_power
        self.current_storage = None
        self.rescale_spaces = rescale_spaces

        self.simulation_step = 0
        self.max_episode_steps = max_episode_steps

        self.control_interval_in_hr = control_timedelta.seconds / 3600.0

        self._obs_labels = ["stage_of_charge",
                            "locational_marginal_price",
                            "load",
                            "load_forecast",
                            "marginal_operating_emissions_rate",
                            "solar_forecast",
                            "wind_forecast"]

        self._observation_space = gym.spaces.Box(
            shape=(1,),
            low=self.storage_range[0],
            high=self.storage_range[1],
            dtype=np.float64
        )
        self.observation_space = maybe_rescale_box_space(
            self._observation_space, rescale=self.rescale_spaces)

        self._action_space = gym.spaces.Box(
            shape=(1,),
            low=-1.0,
            high=1.0,
            dtype=np.float64
        )
        self.action_space = maybe_rescale_box_space(
            self._action_space, rescale=self.rescale_spaces)

        print(f'Retrieving data for {date.date()}...')
        lmp_df, load_df, load_forecast_df, moer_df, solar_wind_forecast_df = get_data(date, date+datetime.timedelta(hours=24)+datetime.timedelta(minutes=5))
        
        if len(lmp_df) != 288+1:
            raise Exception("Incomplete LMP data for this date. Data is available for 2021-10-01 to 2024-09-30, with many missing data in the months of Nov-Mar.")
        if len(load_df) != 288+1:
            raise Exception("Incomplete load data for this date. Data is available for 2021-10-01 to 2024-09-30, with some missing spots.")
        if len(moer_df) != 288+1:
            raise Exception("Incomplete MOER data for this date. Data is available for 2021-10-01 to 2024-09-30, with some missing spots.")
        if len(load_forecast_df) != 24+1:
            raise Exception("Incomplete load forecast data for this date. Data is available for 2021-10-01 to 2024-09-30, with some missing spots.")
        if len(solar_wind_forecast_df) != 24+1:
            raise Exception("Incomplete solar and wind forecast data for this date. Data is available for 2021-10-01 to 2024-09-30, with some missing spots.")

        print('Data retrieved!')
            
        self.date = date
        self.lmp_df = lmp_df
        self.load_df = load_df
        self.load_forecast_df = load_forecast_df
        self.moer_df = moer_df
        self.solar_wind_forecast_df = solar_wind_forecast_df

        self.current_datetime = date
        self._update_current_obs()

    def _update_current_obs(self):
        # get current values 
        self.lmp = self.lmp_df[self.lmp_df['interval_start'] == self.current_datetime].lmp.values.item()
        self.load = self.load_df[self.load_df['interval_start'] == self.current_datetime].load.values.item()
        self.moer = self.moer_df[self.moer_df['interval_start'] == self.current_datetime].moer.values.item()

        # get forecasts 
        self.load_forecast = self._get_hourly_forecast_for_next_5_min(self.load_forecast_df).load_forecast.values.item()
        self.solar_forecast = self._get_hourly_forecast_for_next_5_min(self.solar_wind_forecast_df).solar_mw.values.item()
        self.wind_forecast = self._get_hourly_forecast_for_next_5_min(self.solar_wind_forecast_df).wind_mw.values.item()

    def _get_hourly_forecast_for_next_5_min(self, df):
        # if self.simulation_step != self.max_episode_steps:
        forecast_datetime = self.current_datetime + datetime.timedelta(minutes=5)
        # else:
        #     forecast_datetime = self.current_datetime
        return df[((df['interval_start'] <= forecast_datetime).values & (df['interval_end'] > forecast_datetime).values)]

    def reset(self, **kwargs):
        """ Reset the battery storage at the beginning of an episode.
        """

        self.simulation_step = 0
        self.current_datetime = self.date
        
        init_storage = kwargs['init_storage'] if 'init_storage' in kwargs.keys() else None

        if init_storage is None:
            # Initial battery storage is sampled from a truncated normal distribution.
            self.current_storage =\
                float(truncnorm(-1, 1).rvs() *\
                self.initial_storage_std + self.initial_storage_mean)
        else:
            try:
                init_storage = float(init_storage)
                init_storage = np.clip(
                    init_storage, self.storage_range[0], self.storage_range[1])
            except (TypeError, ValueError) as e:
                print(e)
                print("init_storage value needs to be a float, use default value instead")
                init_storage = self.initial_storage_mean

            self.current_storage = init_storage
        
        return self.get_obs(**kwargs)
            

    def validate_power(self, power):
        """ Sanity check if the battery can provide such power given its current 
            SOC, e.g., cannot discharge when SOC is at minimum.

        Args:
          power: A float, the controlled power to the storage. It discharges if 
            the value is positive, else it is negative.

        Return:
          power: A float, the feasible power of the energy storage.
        """

        if power > 0:
            # ensure the discharging power is within the range.
            if self.current_storage - \
                    power * self.control_interval_in_hr / self.discharge_efficiency <\
                    self.storage_range[0]:
                power = max(self.current_storage - self.storage_range[0], 0.0) /\
                    self.control_interval_in_hr

        elif power < 0:
            # ensure charging does not exceed the limit
            if self.current_storage - \
                    self.charge_efficiency * power * self.control_interval_in_hr >\
                    self.storage_range[1]:
                power = - max(self.storage_range[1] - self.current_storage, 0.0) /\
                    self.control_interval_in_hr

        return power


    def step(self, action: np.ndarray, **kwargs):
        """ Implement control to the storage.
        """

        self.simulation_step += 1
        self.current_datetime = self.current_datetime + datetime.timedelta(minutes=5)
        self._update_current_obs()

        if self.rescale_spaces:
            action = to_raw(action, self._action_space.low, self._action_space.high)

        power = action[0] * self.max_power
        power = self.validate_power(power)

        if power < 0.0:
            self.current_storage -= self.charge_efficiency * power * self.control_interval_in_hr
            # In case of small numerical error:
            self.current_storage = min(self.current_storage, self.storage_range[1])
        elif power > 0.0:
            self.current_storage -= power * self.control_interval_in_hr / self.discharge_efficiency
            self.current_storage = max(self.current_storage, self.storage_range[0])

        #  Convert to the positive for load and negative for generation convention.
        self._real_power = -power

        obs, obs_meta = self.get_obs()
        rew, _ = self.step_reward(power)

        return obs, rew, self.is_terminal(), obs_meta

    def step_reward(self, power):
        # Reward = (electricity price per unit + moer per unit) * units discharged/charged (negative for charging, positive for discharging) 
        es_reward = (self.lmp + self.moer) * power
        # es_reward = 0.0  # Currently we don't have a component level reward for energy storage
        reward_meta = {}

        return es_reward, reward_meta

    def get_obs(self, **kwargs):
        """ The only observation for the energy storage is its SOC.
        """

        raw_obs = np.array([self.current_storage])
        if self.rescale_spaces:
            obs = to_scaled(raw_obs, self._observation_space.low, self._observation_space.high)
        else:
            obs = raw_obs

        obs = [obs.item(), self.lmp, self.load, self.load_forecast, self.moer, self.solar_forecast, self.wind_forecast]
        
        return obs, {"state_of_charge": raw_obs, 
                     "locational_marginal_price": self.lmp, 
                     "load": self.load, 
                     "load_forecast": self.load_forecast,
                     "marginal_operating_emissions_rate": self.moer, 
                     "solar_forecast": self.solar_forecast,
                     "wind_forecast": self.wind_forecast}

    def is_terminal(self):
        return self.simulation_step >= self.max_episode_steps


if __name__ == '__main__':

    env = EnergyStorageEnv('ES')
    state = env.reset()
    done = False

    power_history = []
    soc_history = []

    while not done:
        # act = env.action_space.sample()
        act = [-1.0]
        state, reward, done, info = env.step(act)
        power = env.real_power
        power_history.append(power)
        soc_history.append(state)

    import matplotlib.pyplot as plt

    plt.plot(power_history)
    plt.plot(soc_history)
    plt.show()

