""" Miscellaneous utility functions """
import itertools
import random
import re
<<<<<<< HEAD
=======
import furl
>>>>>>> 2c1057db492da36f5c28cf437697b207ab49e4b3

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


def shuffle_iterable(iterable, n=None):
    """ Shuffle an iterable

    Shuffle an interable. If ``n`` is ``None`` and the iterable is finite,
    then this function puts the iterable into a list and shuffles it
    with ``random.shuffle``, otherwise it raises a ``TypeError``.

    If ``n`` is an integer, this function can shuffle even infinite iterables,
    by keeping a queue of ``n`` elements and randomly removing elements from
    it. If ``n = 1``, this is equivalent to iterating in order, and if
    ``n = len(iterable)`` it is equivalent to shuffling the entire sequence.


    Parameters
    -----------
    iterable: iterabable
        An iterable
    n: int, None
        The size of the queue to use when shuffling.

    Yields
    -------
    el:
        An element from ``iterable`` in a random order

    Raises
    -------
    TypeError
        If ``n`` is ``None``, and ``iterable`` does not have a length.
        In this case, a finite ``n`` must be specified.


    """
    # simple case: finite iterable, and n = length of iterable
    if n is None:
        # this is here to raise and error if no len for the iterable
        len(iterable)
        it = list(iterable)
        random.shuffle(it)
        for el in it:
            yield el
    else:
        queue = list(itertools.islice(iterable, n))
        empty = len(queue) < n
        # randomly select element from queue to remove
        # and replace with element from the iterable
        while not empty:
            # selecting and replacing by the index means that the queue does
            # not need to resized. If pop() used, then there is overhead
            # of resizing the queue
            i = random.randrange(0, n)
            yield queue[i]
            try:
                queue[i] = next(iterable)
            except StopIteration:
                # need to pop off the element which was already selected
                # before the remaining queue is shuffled
                queue.pop(i)
                empty = True
        # iterable has no other elements
        # shuffle the queue and yield remaining elements
        random.shuffle(queue)
        for el in queue:
            yield el
