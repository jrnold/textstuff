""" Miscellaneous utility functions """
import re
import furl

import email_normalize
import tldextract

_CAMEL_CASE_PATTERN = r".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)"


def normalize_email(email):
    """Normalize an email.

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


def url_domain(url):
    """Return the domain of a url."""
    return '.'.join(tldextract.extract(url)[1:])


def url_tld(url):
    """Return the top-level domain of a url."""
    return tldextract.extract(url)[2]


class UrlNormalizer:
    """Class to normalize URLs."""

    def __init__(self,
                 scheme=False,
                 username=False,
                 password=False,
                 host=True,
                 subdomain=True,
                 domain=True,
                 tld=True,
                 port=False,
                 path=False,
                 params=False,
                 fragment=False,
                 query=False):
        self.scheme = scheme
        self.username = username
        self.password = password
        self.host = host
        self.subdomain = subdomain
        self.domain = domain
        self.tld = tld
        self.port = port
        self.path = path
        self.query = query
        self.params = params
        self.fragment = fragment

    def normalize(self, url):
        """Normalize a URL."""
        f = furl.furl(url)
        attrs = ("scheme", "username", "password", "port", "fragment",
                 "path", "params", "query")
        for a in attrs:
            if not self.__getattribute__(a):
                setattr(f, a, None)
        if self.host:
            subdomain, domain, tld = tldextract.extract(f.host)
            host = []
            if self.subdomain:
                host.append(subdomain)
            if self.domain:
                host.append(domain)
            if self.tld:
                host.append(tld)
            f.host = '.'.join(host)
        return f.url


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
    """Split a camel cased word.

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

    """  # noqa
    return [m.group(0) for m in re.finditer(_CAMEL_CASE_PATTERN, string)]
