def parse_numeric(string):
    # Some minimal string formatting
    string_sans_commas = string.replace(',', '')
    string_sans_dollar_sign = string_sans_commas.lstrip('$')

    try:
        number = float(string_sans_dollar_sign)
    except ValueError:
        raise
    else:
        return str(number)
