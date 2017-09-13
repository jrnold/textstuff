""" Miscellaneous utility functions """
import re
from itertools import chain

import email_normalize
import tldextract

_CAMEL_CASE_PATTERN = r".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)"


def normalize_email(email):
    """ Normalize an email

    Parameters
    ------------
    email: str
        An email

    Returns
    --------
    str
        The normalized email string

    """
    return email_normalize.normalize(email, resolve=False)


def normalize_url(url):
    """ Normalize a url

    Normalize a url by returning only its domain.

    Parameters
    ----------
    url: str
        A url

    Returns
    --------
    str
        The url's domain

    """
    return '.'.join(tldextract.extract(url)[1:])


# def lik_phone_number(string):
#     """ String is like a phone number
#
#     Parameters
#     -----------
#     string: str
#         A string
#
#     Returns
#     --------
#     bool
#         ``True`` is the string is a phone number.
#
#     """
#     textacy.


def split_camel_case(string):
    """ Split Word on Camel Case

    Split word on internal uppercase letters, but allowing for sequences of
    all-caps letters.

    Parameters
    -----------
    string: str
        The string to split

    Returns
    --------
    list of str
        A list of strings after splitting the word

    This pattern is from this
    `stackoverflow <https://stackoverflow.com/questions/29916065/how-to-do-camelcase-split-in-python>`__.
    answer.

    """  # noqc
    return [m.group(0) for m in re.finditer(_CAMEL_CASE_PATTERN, string)]
