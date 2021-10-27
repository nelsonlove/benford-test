import random
from functools import lru_cache

from benford import analysis
from unittest import TestCase


class TestParseNumeric(TestCase):
    def test_simple_cases(self):
        self.assertEqual('100.0', analysis.parse_numeric('100.0'))
        self.assertEqual('100', analysis.parse_numeric('100'))
        self.assertEqual('.1', analysis.parse_numeric('.1'))

    def test_removes_leading_sign(self):
        self.assertEqual('100.25', analysis.parse_numeric('-100.25'))

    def test_removes_leading_dollar_symbol(self):
        self.assertEqual('100', analysis.parse_numeric('$100'))
        self.assertEqual('100.25', analysis.parse_numeric('$100.25'))
        self.assertEqual('100.25', analysis.parse_numeric('$-100.25'))
        self.assertEqual('100.25', analysis.parse_numeric('-$100.25'))

    def test_removes_commas(self):
        self.assertEqual('1234', analysis.parse_numeric('1,234'))
        self.assertEqual('10000', analysis.parse_numeric('$10,000'))

    def test_raises_value_error_on_empty_string(self):
        self.assertRaises(ValueError, analysis.parse_numeric, '')

    def test_raises_value_error_on_non_numeric_string(self):
        self.assertRaises(ValueError, analysis.parse_numeric, 'Not a number')

    def test_raises_value_error_on_multiple_decimal_points(self):
        self.assertRaises(ValueError, analysis.parse_numeric, '1.31.56')

    def test_raises_value_error_on_unknown_symbol_in_otherwise_numeric_string(self):
        self.assertRaises(ValueError, analysis.parse_numeric, '1/31/56')
        self.assertRaises(ValueError, analysis.parse_numeric, '€100')


class TestGetFirstDigit(TestCase):
    def test_simple_cases(self):
        self.assertEqual('2', analysis.get_first_digit('25'))
        self.assertEqual('4', analysis.get_first_digit('4'))
        self.assertEqual('1', analysis.get_first_digit('123'))

    def test_strips_leading_zeroes(self):
        self.assertEqual('2', analysis.get_first_digit('0.25'))

    def test_strips_sign_from_negative_number(self):
        self.assertEqual('2', analysis.get_first_digit('-0.25'))

    def test_raises_value_error_on_string_without_nonzero_digits(self):
        self.assertRaises(ValueError, analysis.get_first_digit, '0.0')

    def test_raises_value_error_on_non_numeric_string(self):
        self.assertRaises(ValueError, analysis.get_first_digit, '5c00bf')


class TestDistributions(TestCase):
    def setUp(self):
        # A non-exhaustive list of combinations of decimal points, zeroes, and significant digits
        raw_data = ['0', '0.0', '01', '020', '-$0.3', '.4', '50', '60.0', '70.7', '$808.8', '.09']

        # Add negative signs and bad data for good measure
        raw_data += ['-' + item for item in raw_data]
        raw_data += ['eleventy-one', '\n', '', 'Pi is exactly 3']

        self.data = analysis.clean_data(raw_data)

    def test_clean_data(self):
        self.assertEqual([1, 2, 3, 4, 5, 6, 7, 8, 9] * 2, self.data)

    def test_observed_distribution_is_accurate(self):
        self.assertEqual(
            {str(x): 2 for x in range(1, 10)},
            analysis.observed_distribution(self.data)
        )

    def test_observed_distribution_on_empty_list(self):
        self.assertEqual(
            {str(x): 0 for x in range(1, 10)},
            analysis.observed_distribution([])
        )

    def test_observed_distribution_on_absent_digits(self):
        self.assertEqual(
            {
                '1': 2,
                '2': 2,
                '3': 0,
                '4': 0,
                '5': 0,
                '6': 0,
                '7': 0,
                '8': 0,
                '9': 0,
            },
            analysis.observed_distribution([1, 2, 2, 1])
        )

    def test_expected_distribution_with_originally_published_table(self):
        # Frequencies in % below taken from table III of Benford's original paper (1938, p. 556)
        expected_frequencies = [0.301, 0.176, 0.125, 0.097, 0.079, 0.067, 0.058, 0.051, 0.046]

        # Benford rounded figures in his paper so we'll look for near but not exact equality
        for i, published_frequency in enumerate(expected_frequencies):
            self.assertAlmostEqual(published_frequency, analysis.benford(i + 1),
                                   places=3)

            # Using a distribution with n=1 because above data is represented in percentages
            self.assertAlmostEqual(published_frequency,
                                   analysis.expected_distribution(1)[str(i + 1)],
                                   places=3)

    def test_expected_distribution_with_published_atomic_weight_data(self):
        # Benford tested his observation on atomic weights of the first 91 elements,
        # reporting the sum of the differences between the expected and actual distribution
        # in table IV of his paper (1938, p. 557)

        atomic_weights_n = 91
        observed_percentages = [0.472, 0.187, 0.055, 0.044, 0.066, 0.044, 0.033, 0.044, 0.05]
        observed_sum_of_differences = 35.4

        expected_distribution = analysis.expected_distribution(atomic_weights_n)

        differences_from_expected = [abs(value - observed_percentages[i] * atomic_weights_n)
                                     for i, value in enumerate(expected_distribution.values())]

        # Benford used atomic weight data from 1938, so the answer won't match exactly--
        # and unfortunately, similar discrepancies result from trying to derive his
        # mathematically grounded sequences because of how floats are represented, but we
        # should still be able to get fairly close, and we know that this won't pose a
        # problem for data which we have in advance
        self.assertTrue(
            abs(round(observed_sum_of_differences) - round(sum(differences_from_expected))) <= 1
        )

    def test_goodness_of_fit_with_fibonacci_numbers(self):
        @lru_cache(maxsize=1000)
        def fibonacci(n):
            if n == 1:
                return 1
            if n == 2:
                return 1
            elif n > 2:
                return fibonacci(n - 1) + fibonacci(n - 2)

        # Here we assume that the sum of squared differences will be very low for a sequence which
        # closely approximates Benford's law (in our case, the first digits of the Fibonacci series)

        fibonacci_data = [str(fibonacci(x)) for x in range(1, 200)]
        fibonacci_leading_digits = analysis.clean_data(fibonacci_data)
        fibonacci_expected_distribution = analysis.expected_distribution(len(fibonacci_data))
        fibonacci_observed_distribution = analysis.observed_distribution(fibonacci_leading_digits)
        fibonacci_sum_chi_squares = analysis.sum_chi_squares(
            fibonacci_expected_distribution,
            fibonacci_observed_distribution
        )
        self.assertLess(fibonacci_sum_chi_squares, 1.334)  # critical value at p = 0.995

        # Lastly, let's see if the Fibonacci digits pass our goodness of fit test--
        # i.e., if the test statistic failed to exceed the critical value
        self.assertFalse(analysis.goodness_of_fit(
            fibonacci_expected_distribution,
            fibonacci_observed_distribution)['0.001']
        )

        # The conforms_to_benford() function ties it all together in a DRY way
        # It returns a dict of critical values : test results
        for critical_value, test_result in analysis.conforms_to_benford(fibonacci_data).items():
            self.assertFalse(test_result)

    def test_goodness_of_fit_with_randomly_generated_numbers(self):
        def random_with_n_digits(n):
            range_start = 10 ** (n - 1)
            range_end = (10 ** n) - 1
            return str(random.randint(range_start, range_end))

        # Here assume that the sum of squared differences will be quite high for a sequence
        # that violates it (in our case, a list of numbers generated by random.randint())

        random_data = [random_with_n_digits(random.randint(2, 4)) for _ in range(1000)]
        random_leading_digits = analysis.clean_data(random_data)
        random_expected_distribution = analysis.expected_distribution(len(random_data))
        random_observed_distribution = analysis.observed_distribution(random_leading_digits)
        random_sum_chi_squares = analysis.sum_chi_squares(
            random_expected_distribution,
            random_observed_distribution
        )
        self.assertGreater(random_sum_chi_squares, 26.124)  # critical value at p = 0.001

        # Our random data should be flatly distributed, so it should return True here,
        # indicating that we can reject the null hypothesis that the data is distributed
        # according to Benford's law
        self.assertTrue(analysis.goodness_of_fit(
            random_expected_distribution,
            random_observed_distribution)['0.001']
        )