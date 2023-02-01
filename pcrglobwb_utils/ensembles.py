
import pandas as pd

from . import time_funcs

class ensemble_data():
    """Analyzing and visualizing ensemble time series.

    Args:
        *arg: list of pandas dataframe with matching datetime index
    """

    def __init__(self, *arg) -> pd.DataFrame:
        """Creates object based on an ensemble of input dataframes.
        """

        temp = []
        for argument in arg:
            temp.append(argument)
        
        self.df_ens = pd.concat(temp, axis=1)

    def calc_stats(self) -> pd.DataFrame:
        """Calculates mean, max, and min for each time step.

        Returns:
            pd.DataFrame: dataframe containing the input dataframes as well as columns for mean, max, and min.
        """        

        self.df_stats = self.df_ens.copy()

        self.df_stats['mean'] = self.df_stats.mean(axis=1)
        self.df_stats['max'] = self.df_stats.max(axis=1)
        self.df_stats['min'] = self.df_stats.min(axis=1)

        return self.df_stats

    def calc_climatology(self) -> pd.DataFrame:
        """Calculates the climatological (long-term) average per month.

        Args:
            plot (bool): whether or not to plot mean, max, min (default: False)

        Returns:
            pd.DataFrame: dataframe containing the climatological (long-term) monthly averages.
        """        

        df_out = time_funcs.calc_monthly_climatology(self.df_ens)

        return df_out
