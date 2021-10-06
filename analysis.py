import math

# Assuming 8 degrees of freedom,
CRITICAL_VALUES = {
    '0.10': 13.362,
    '0.05': 15.507,
    '0.025': 17.535,
    '0.01': 20.090,
    '0.001': 26.125,
}


# Taken from https://www.itl.nist.gov/div898/handbook/eda/section3/eda3674.htm


def parse_numeric(string):
    # Some minimal string formatting
    string_sans_commas = string.replace(',', '')
    parsed_string = string_sans_commas.lstrip('$')

    try:
        float(parsed_string)
    except ValueError:
        raise
    else:
        return parsed_string


def get_first_digit(string):
    try:
        parsed_string = parse_numeric(string)
    except ValueError:
        raise

    chars = list(parsed_string)

    while chars:
        first_char = chars.pop(0)
        if first_char in '123456789':
            return first_char
        # Leading zeroes are not significant and should be stripped for the analysis
        elif first_char in '-.0':
            continue
        else:
            break

    raise ValueError(f'Cannot parse string: "{string}"')


def clean_data(raw_data):
    skipped, data = [], []

    for string in raw_data:
        try:
            first_digit = get_first_digit(string)
        except ValueError:
            skipped.append(string)
            # raise
        else:
            data.append(int(first_digit))

    return data


def benford(x):
    return math.log10(1 + (1 / x))


def expected_distribution(n):
    return {str(x): benford(x) * n for x in range(1, 10)}


def observed_distribution(digits):
    return {str(x): digits.count(x) for x in range(1, 10)}


def sum_chi_squares(expected_dist, observed_dist):
    def chi_square(expected_n, observed_n):
        return (observed_n - expected_n) ** 2 / expected_n

    try:
        return sum([
            chi_square(expected_dist[i], observed_dist[i])
            for i in [str(j) for j in range(1, 10)]
        ])
    except ZeroDivisionError:
        # Expected to result only in the event of rounding the
        # benford() function above to fewer digits in function
        # expected_distribution(), combined with very small n
        return float('inf')


def goodness_of_fit(expected_dist, observed_dist):
    test_statistic = sum_chi_squares(expected_dist, observed_dist)
    return {p: test_statistic > CRITICAL_VALUES[p]
            for p in CRITICAL_VALUES}


def conforms_to_benford(raw_data):
    digits = clean_data(raw_data)
    return goodness_of_fit(expected_distribution(len(digits)),
                           observed_distribution(digits))
