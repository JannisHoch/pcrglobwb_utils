#!/usr/bin/env python

"""Tests for `pcrglobwb_utils` package."""

import pytest

import pcrglobwb_utils
import pandas as pd
import os


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

    df = '../examples/example_data/Obidos_data.csv'
    print(os.getcwd())
    df = os.path.join(os.getcwd(), df)

    csv_obj = pcrglobwb_utils.obs_data.other_data(df)

    df_CSV = csv_obj.get_values_from_csv(t_col='YYYY-MM-DD', 
                                         v_col='Calculated', 
                                         plot=True,
                                         datetime_format='%d-%m-%Y')

    df_test = pcrglobwb_utils.time_funcs.daily2monthly(df_CSV)

    assert csv_obj.sum() == df_test.sum()


