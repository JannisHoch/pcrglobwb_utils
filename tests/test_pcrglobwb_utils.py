#!/usr/bin/env python

"""Tests for `pcrglobwb_utils` package."""

import pytest

import pcrglobwb_utils
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_daily2monthly():

    date_today = datetime.now()
    days = pd.date_range(date_today, date_today + timedelta(7), freq='D')

    np.random.seed(seed=1111)
    data = np.random.randint(1, high=100, size=len(days))
    df = pd.DataFrame({'test': days, 'col2': data})
    df = df.set_index('test')

    df_test = pcrglobwb_utils.time_funcs.resample_to_month(df,  stat_func='sum')

    assert float(df_test.sum()) == float(df.sum())

def test_daily2yearly():

    date_today = datetime.now()
    days = pd.date_range(date_today, date_today + timedelta(7), freq='D')

    np.random.seed(seed=1111)
    data = np.random.randint(1, high=100, size=len(days))
    df = pd.DataFrame({'test': days, 'col2': data})
    df = df.set_index('test')

    df_test = pcrglobwb_utils.time_funcs.resample_to_annual(df,  stat_func='sum')

    assert float(df_test.sum()) == float(df.sum())

def test_get_grdc_station_properties():

    # path is relative to main pcrglobwb_utils folder
    fo = './examples/example_data/GRDC/files/3629000_Obidos.day'

    obs = pcrglobwb_utils.obs_data.grdc_data(fo)

    plot_title, properties = obs.get_grdc_station_properties()

    assert properties['station'] == 'OBIDOS - PORTO'


