import random
from functools import lru_cache
from unittest import TestCase

import analysis


class TestAnalysis(TestCase):
    def test_parse_numeric(self):
        self.assertEqual('100.0', analysis.parse_numeric('100.0'))
        self.assertEqual('100', analysis.parse_numeric('100'))
        self.assertEqual('.1', analysis.parse_numeric('.1'))

        self.assertRaises(ValueError, analysis.parse_numeric, '')
        self.assertRaises(ValueError, analysis.parse_numeric, 'Not a number')

        # It removes leading dollar symbols
        self.assertEqual('100', analysis.parse_numeric('$100'))

        # As well as commas
        self.assertEqual('10000', analysis.parse_numeric('$10,000'))

        # But it leaves a sign or decimal point intact
        self.assertEqual('100.25', analysis.parse_numeric('$100.25'))
        self.assertEqual('-100.25', analysis.parse_numeric('$-100.25'))

        # Though it won't like if there's more than one
        self.assertRaises(ValueError, analysis.parse_numeric, '1.31.56')

        # And it doesn't like other symbols
        self.assertRaises(ValueError, analysis.parse_numeric, '1/31/56')
        self.assertRaises(ValueError, analysis.parse_numeric, '€100')

    def test_get_first_digit(self):
        # get_first_digit returns the first non-zero digit it encounters
        self.assertEqual('2', analysis.get_first_digit('25'))

        # It handles leading zeroes
        self.assertEqual('2', analysis.get_first_digit('0.25'))

        # It also handles negative numbers
        self.assertEqual('2', analysis.get_first_digit('-0.25'))

        # And it raises a ValueError in the event of a string without non-zero digits
        self.assertRaises(ValueError, analysis.get_first_digit, '0.0')

        # Or a string including characters which cannot be parsed
        self.assertRaises(ValueError, analysis.get_first_digit, '5c00bf')

    def test_clean_data_and_observed_distribution(self):
        # A non-exhaustive list of combinations of decimal points, zeroes, and significant digits
        data = ['0', '0.0', '01', '020', '0.3', '.4', '50', '60.0', '70.7', '808.8', '.09']

        # Add negative signs for good measure
        data += ['-' + item for item in data]

        # And some bad data
        data += ['eleventy-one', '\n', '', 'Pi is exactly 3']

        # We should get back first non-zero digits when available
        # And we should get back a count of 2 for each digit from our dict constructor
        cleaned_data = analysis.clean_data(data)
        self.assertEqual([1, 2, 3, 4, 5, 6, 7, 8, 9] * 2, cleaned_data)
        self.assertEqual({x: 2 for x in range(1, 10)}, analysis.observed_distribution(cleaned_data))

    def test_benford_function_and_expected_distribution_for_n(self):
        # Frequencies below taken from table III of Benford's original paper (1938, p. 556)
        atomic_weight_frequencies = [0.301, 0.176, 0.125, 0.097, 0.079, 0.067, 0.058, 0.051, 0.046]

        # Benford rounded figures in his paper so we'll look for near but not exact equality
        for i, frequency in enumerate(atomic_weight_frequencies):
            self.assertAlmostEqual(frequency, analysis.benford(i + 1), places=3)
            self.assertAlmostEqual(frequency, analysis.expected_distribution(1)[i + 1], places=3)

            n = 37  # Try it for n > 1 and the inequality gets larger,
            # but we know the formula behind the function is sound
            self.assertAlmostEqual(frequency * n, analysis.expected_distribution(n)[i + 1], places=1)

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

    def test_sum_chi_squares_and_goodness_of_fit(self):
        # Helper functions for generating data
        @lru_cache(maxsize=1000)
        def fibonacci(n):
            if n == 1:
                return 1
            if n == 2:
                return 1
            elif n > 2:
                return fibonacci(n - 1) + fibonacci(n - 2)

        def random_with_n_digits(n):
            range_start = 10 ** (n - 1)
            range_end = (10 ** n) - 1
            return str(random.randint(range_start, range_end))

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

        # Similarly we assume that the sum of squared differences will be quite high for a sequence
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

        # Lastly, let's see if the Fibonacci digits pass our goodness of fit test--
        # i.e., if the test statistic failed to exceed the critical value
        self.assertFalse(analysis.goodness_of_fit(
            fibonacci_expected_distribution,
            fibonacci_observed_distribution)['0.001']
        )

        # Meanwhile the random data shouldn't pass
        self.assertTrue(analysis.goodness_of_fit(
            random_expected_distribution,
            random_observed_distribution)['0.001']
        )

        # The conforms_to_benford() function ties it all together in a DRY way
        # It returns a dict of critical values : test results
        for critical_value, test_result in analysis.conforms_to_benford(fibonacci_data).items():
            self.assertFalse(test_result)