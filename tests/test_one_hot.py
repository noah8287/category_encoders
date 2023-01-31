import pandas as pd
from unittest import TestCase  # or `from unittest import ...` if on Python 3.4+
import numpy as np
import tests.helpers as th

import category_encoders as encoders


class TestOneHotEncoderTestCase(TestCase):

    def test_one_hot(self):
        X = th.create_dataset(n_rows=100)
        X_t = th.create_dataset(n_rows=50, extras=True)
        enc = encoders.OneHotEncoder(verbose=1, return_df=False)
        enc.fit(X)
        self.assertEqual(enc.transform(X_t).shape[1],
                         enc.transform(X).shape[1],
                         'We have to get the same count of columns despite the presence of a new value')

        enc = encoders.OneHotEncoder(verbose=1, return_df=True, handle_unknown='indicator')
        enc.fit(X)
        out = enc.transform(X_t)
        self.assertIn('extra_-1', out.columns.values)

        enc = encoders.OneHotEncoder(verbose=1, return_df=True, handle_unknown='return_nan')
        enc.fit(X)
        out = enc.transform(X_t)
        self.assertEqual(len([x for x in out.columns.values if str(x).startswith('extra_')]), 3)

        enc = encoders.OneHotEncoder(verbose=1, return_df=True, handle_unknown='error')
        # The exception is already raised in fit() because transform() is called there to get
        # feature_names right.
        enc.fit(X)
        with self.assertRaises(ValueError):
            enc.transform(X_t)

        enc = encoders.OneHotEncoder(verbose=1, return_df=True, handle_unknown='return_nan', use_cat_names=True)
        enc.fit(X)
        out = enc.transform(X_t)
        self.assertIn('extra_A', out.columns.values)

        enc = encoders.OneHotEncoder(verbose=1, return_df=True, use_cat_names=True, handle_unknown='indicator')
        enc.fit(X)
        out = enc.transform(X_t)
        self.assertIn('extra_-1', out.columns.values)

        # test inverse_transform
        X_i = th.create_dataset(n_rows=100, has_missing=False)
        X_i_t = th.create_dataset(n_rows=50, has_missing=False)
        cols = ['underscore', 'none', 'extra', 'categorical']

        enc = encoders.OneHotEncoder(verbose=1, use_cat_names=True, cols=cols)
        enc.fit(X_i)
        obtained = enc.inverse_transform(enc.transform(X_i_t))
        th.verify_inverse_transform(X_i_t, obtained)

    def test_fit_transform_HaveMissingValuesAndUseCatNames_ExpectCorrectValue(self):
        encoder = encoders.OneHotEncoder(cols=[0], use_cat_names=True, handle_unknown='indicator', return_df=False)

        result = encoder.fit_transform([[-1]])

        self.assertListEqual([[1, 0]], result.tolist())

    def test_inverse_transform_HaveDedupedColumns_ExpectCorrectInverseTransform(self):
        encoder = encoders.OneHotEncoder(cols=['match', 'match_box'], use_cat_names=True)
        value = pd.DataFrame({'match': pd.Series('box_-1'), 'match_box': pd.Series(-1)})

        transformed = encoder.fit_transform(value)
        inverse_transformed = encoder.inverse_transform(transformed)

        assert value.equals(inverse_transformed)

    def test_inverse_transform_HaveNoCatNames_ExpectCorrectInverseTransform(self):
        encoder = encoders.OneHotEncoder(cols=['match', 'match_box'], use_cat_names=False)
        value = pd.DataFrame({'match': pd.Series('box_-1'), 'match_box': pd.Series(-1)})

        transformed = encoder.fit_transform(value)
        inverse_transformed = encoder.inverse_transform(transformed)

        assert value.equals(inverse_transformed)

    def test_fit_transform_HaveColumnAppearTwice_ExpectColumnsDeduped(self):
        encoder = encoders.OneHotEncoder(cols=['match', 'match_box'], use_cat_names=True, handle_unknown='indicator')
        value = pd.DataFrame({'match': pd.Series('box_-1'), 'match_box': pd.Series('-1')})

        result = encoder.fit_transform(value)
        columns = result.columns.tolist()

        self.assertSetEqual({'match_box_-1', 'match_-1', 'match_box_-1#', 'match_box_-1##'}, set(columns))

    def test_fit_transform_HaveHandleUnknownValueAndUnseenValues_ExpectAllZeroes(self):
        train = pd.DataFrame({'city': ['Chicago', 'Seattle']})
        test = pd.DataFrame({'city': ['Chicago', 'Detroit']})
        expected_result = pd.DataFrame({'city_1': [1, 0],
                                        'city_2': [0, 0]},
                                       columns=['city_1', 'city_2'])

        enc = encoders.OneHotEncoder(handle_unknown='value')
        result = enc.fit(train).transform(test)

        pd.testing.assert_frame_equal(expected_result, result)

    def test_fit_transform_HaveHandleUnknownValueAndSeenValues_ExpectMappingUsed(self):
        train = pd.DataFrame({'city': ['Chicago', 'Seattle']})
        expected_result = pd.DataFrame({'city_1': [1, 0],
                                        'city_2': [0, 1]},
                                       columns=['city_1', 'city_2'])

        enc = encoders.OneHotEncoder(handle_unknown='value')
        result = enc.fit(train).transform(train)

        pd.testing.assert_frame_equal(expected_result, result)

    def test_fit_transform_HaveHandleUnknownIndicatorAndNoMissingValue_ExpectExtraColumn(self):
        train = pd.DataFrame({'city': ['Chicago', 'Seattle']})
        expected_result = pd.DataFrame({'city_1': [1, 0],
                                        'city_2': [0, 1],
                                        'city_-1': [0, 0]},
                                       columns=['city_1', 'city_2', 'city_-1'])

        enc = encoders.OneHotEncoder(handle_unknown='indicator')
        result = enc.fit(train).transform(train)

        pd.testing.assert_frame_equal(expected_result, result)

    def test_fit_transform_HaveHandleUnknownIndicatorAndMissingValue_ExpectValueSet(self):
        train = pd.DataFrame({'city': ['Chicago', 'Seattle']})
        test = pd.DataFrame({'city': ['Chicago', 'Detroit']})
        expected_result = pd.DataFrame({'city_1': [1, 0],
                                        'city_2': [0, 0],
                                        'city_-1': [0, 1]},
                                       columns=['city_1', 'city_2', 'city_-1'])

        enc = encoders.OneHotEncoder(handle_unknown='indicator')
        result = enc.fit(train).transform(test)

        pd.testing.assert_frame_equal(expected_result, result)

    def test_HandleMissingError(self):
        data_no_missing = ['A', 'B', 'B']
        data_w_missing = [np.nan, 'B', 'B']
        encoder = encoders.OneHotEncoder(handle_missing="error")

        result = encoder.fit_transform(data_no_missing)
        expected = [[1, 0],
                    [0, 1],
                    [0, 1]]
        self.assertEqual(result.values.tolist(), expected)

        self.assertRaisesRegex(ValueError, '.*null.*', encoder.transform, data_w_missing)

        self.assertRaisesRegex(ValueError, '.*null.*', encoder.fit, data_w_missing)

    def test_HandleMissingReturnNan(self):
        train = pd.DataFrame({'x': ['A', np.nan, 'B']})
        encoder = encoders.OneHotEncoder(handle_missing='return_nan', use_cat_names=True)
        result = encoder.fit_transform(train)
        pd.testing.assert_frame_equal(
            result,
            pd.DataFrame({'x_A': [1, np.nan, 0], 'x_B': [0, np.nan, 1]}),
        )
        
    def test_HandleMissingIgnore(self):
        train = pd.DataFrame({'x': ['A', 'B', np.nan],
                              'y': ['A', None, 'A'],
                              'z': [np.NaN, 'B', 'B']})
        train['z'] = train['z'].astype('category')
        
        expected_result = pd.DataFrame({'x_A': [1, 0, 0],
                                        'x_B': [0, 1, 0],
                                        'y_A': [1, 0, 1],
                                        'z_B': [0, 1, 1]})    
        encoder = encoders.OneHotEncoder(handle_missing='ignore', use_cat_names=True)
        result = encoder.fit_transform(train)
        
        pd.testing.assert_frame_equal(result, expected_result)
        
    def test_HandleMissingIgnore_ExpectMappingUsed(self):
        train = pd.DataFrame({'city': ['Chicago', np.NaN,'Geneva']})
        expected_result = pd.DataFrame({'city_1': [1, 0, 0],
                                        'city_3': [0, 0, 1]})

        encoder = encoders.OneHotEncoder(handle_missing='ignore')
        result = encoder.fit(train).transform(train)

        pd.testing.assert_frame_equal(expected_result, result)

    def test_HandleMissingIndicator_NanInTrain_ExpectAsColumn(self):
        train = ['A', 'B', np.nan]

        encoder = encoders.OneHotEncoder(handle_missing='indicator', handle_unknown='value')
        result = encoder.fit_transform(train)

        expected = [[1, 0, 0],
                    [0, 1, 0],
                    [0, 0, 1]]
        self.assertEqual(result.values.tolist(), expected)

    def test_HandleMissingIndicator_HaveNoNan_ExpectSecondColumn(self):
        train = ['A', 'B']

        encoder = encoders.OneHotEncoder(handle_missing='indicator', handle_unknown='value')
        result = encoder.fit_transform(train)

        expected = [[1, 0, 0],
                    [0, 1, 0]]
        self.assertEqual(result.values.tolist(), expected)

    def test_HandleMissingIndicator_NanNoNanInTrain_ExpectAsNanColumn(self):
        train = ['A', 'B']
        test = ['A', 'B', np.nan]

        encoder = encoders.OneHotEncoder(handle_missing='indicator', handle_unknown='value')
        encoded_train = encoder.fit_transform(train)
        encoded_test = encoder.transform(test)

        expected_1 = [[1, 0, 0],
                      [0, 1, 0]]
        self.assertEqual(encoded_train.values.tolist(), expected_1)

        expected_2 = [[1, 0, 0],
                      [0, 1, 0],
                      [0, 0, 1]]
        self.assertEqual(encoded_test.values.tolist(), expected_2)

    def test_HandleUnknown_HaveNoUnknownInTrain_ExpectIndicatorInTest(self):
        train = ['A', 'B']
        test = ['A', 'B', 'C']

        encoder = encoders.OneHotEncoder(handle_unknown='indicator', handle_missing='value')
        encoder.fit(train)
        result = encoder.transform(test)

        expected = [[1, 0, 0],
                    [0, 1, 0],
                    [0, 0, 1]]
        self.assertEqual(result.values.tolist(), expected)

    def test_HandleUnknown_HaveOnlyKnown_ExpectSecondColumn(self):
        train = ['A', 'B']

        encoder = encoders.OneHotEncoder(handle_unknown='indicator', handle_missing='value')
        result = encoder.fit_transform(train)

        expected = [[1, 0, 0],
                    [0, 1, 0]]
        self.assertEqual(result.values.tolist(), expected)

    def test_inverse_transform_HaveNanInTrainAndHandleMissingValue_ExpectReturnedWithNan(self):
        train = pd.DataFrame({'city': ['chicago', np.nan]})

        enc = encoders.OneHotEncoder(handle_missing='value', handle_unknown='value')
        result = enc.fit_transform(train)
        original = enc.inverse_transform(result)

        pd.testing.assert_frame_equal(train, original)

    def test_inverse_transform_HaveNanInTrainAndHandleMissingReturnNan_ExpectReturnedWithNan(self):
        train = pd.DataFrame({'city': ['chicago', np.nan]})

        enc = encoders.OneHotEncoder(handle_missing='return_nan', handle_unknown='value')
        result = enc.fit_transform(train)
        original = enc.inverse_transform(result)

        pd.testing.assert_frame_equal(train, original)

    def test_inverse_transform_BothFieldsAreReturnNanWithNan_ExpectValueError(self):
        train = pd.DataFrame({'city': ['chicago', np.nan]})
        test = pd.DataFrame({'city': ['chicago', 'los angeles']})

        enc = encoders.OneHotEncoder(handle_missing='return_nan', handle_unknown='return_nan')
        enc.fit(train)
        result = enc.transform(test)
        
        message = 'inverse_transform is not supported because transform impute '\
                  'the unknown category nan when encode city'

        with self.assertWarns(UserWarning, msg=message) as w:
            enc.inverse_transform(result)

    def test_inverse_transform_HaveMissingAndNoUnknown_ExpectInversed(self):
        train = pd.DataFrame({'city': ['chicago', np.nan]})
        test = pd.DataFrame({'city': ['chicago', 'los angeles']})

        enc = encoders.OneHotEncoder(handle_missing='value', handle_unknown='return_nan')
        enc.fit(train)
        result = enc.transform(test)
        original = enc.inverse_transform(result)

        pd.testing.assert_frame_equal(train, original)

    def test_inverse_transform_HaveHandleMissingValueAndHandleUnknownReturnNan_ExpectBestInverse(self):
        train = pd.DataFrame({'city': ['chicago', np.nan]})
        test = pd.DataFrame({'city': ['chicago', np.nan, 'los angeles']})
        expected = pd.DataFrame({'city': ['chicago', np.nan, np.nan]})

        enc = encoders.OneHotEncoder(handle_missing='value', handle_unknown='return_nan')
        enc.fit(train)
        result = enc.transform(test)
        original = enc.inverse_transform(result)

        pd.testing.assert_frame_equal(expected, original)
