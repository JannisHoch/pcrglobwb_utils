#!/usr/bin/env python

"""Tests for `pcrglobwb_utils` package."""

import pytest

import pcrglobwb_utils
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


# def test_command_line_interface():
#     """Test the CLI."""
#     runner = CliRunner()
#     result = runner.invoke(cli.main)
#     assert result.exit_code == 0
#     assert 'pcrglobwb_utils.cli.main' in result.output
#     help_result = runner.invoke(cli.main, ['--help'])
#     assert help_result.exit_code == 0
#     assert '--help  Show this message and exit.' in help_result.output

def test_daily2monthly():

    date_today = datetime.now()
    days = pd.date_range(date_today, date_today + timedelta(7), freq='D')

    np.random.seed(seed=1111)
    data = np.random.randint(1, high=100, size=len(days))
    df = pd.DataFrame({'test': days, 'col2': data})
    df = df.set_index('test')

    df_test = pcrglobwb_utils.time_funcs.daily2monthly(df, averaging=False)

    assert float(df_test.sum()) == float(df.sum())

def test_daily2yearly():

    date_today = datetime.now()
    days = pd.date_range(date_today, date_today + timedelta(7), freq='D')

    np.random.seed(seed=1111)
    data = np.random.randint(1, high=100, size=len(days))
    df = pd.DataFrame({'test': days, 'col2': data})
    df = df.set_index('test')

    df_test = pcrglobwb_utils.time_funcs.daily2yearly(df, averaging=False)

    assert float(df_test.sum()) == float(df.sum())


