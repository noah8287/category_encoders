"""
Base IO code for datasets
"""

import pkg_resources
import pandas as pd

def load_postcodes(target_type='binary'):
    """Return a dataframe for target encoding with 100 UK postcodes and hierarchy.

    Contains the following fields:
        index                100 non-null int64
        postcode             100 non-null object
        HIER_postcode1       100 non-null object
        HIER_postcode2       100 non-null object
        HIER_postcode3       100 non-null object
        HIER_postcode4       100 non-null object
        target_binary        100 non-null int64
        target_non_binary    100 non-null int64
        target_categorical   100 non-null object

    Parameters
    ----------
    target_type : str, default='binary'
        Options are 'binary', 'non_binary', 'categorical'

    Returns
    -------
    X: A dataframe containing features
    y: A dataframe containing the target variable

    """
    stream = pkg_resources.resource_stream(__name__, 'data/postcode_dataset_100.csv')
    df = pd.read_csv(stream, encoding='latin-1')
    X = df[df.columns[~df.columns.str.startswith('target')]]
    y = df[f'target_{target_type}']
    return X, y