""" Miscellaneous utility functions """
import itertools
import random
import re

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


def bio2biolu(iterable):
    """Convert BIO tags to BILOU tags."""
    it = iter(iterable)
    current = None
    lookahead = next(it)
    empty = False
    errmsg = "Only values of {'B', 'I', 'O'} are allowed."
    while not empty:
        current = lookahead
        try:
            lookahead = next(it)
        except StopIteration:
            if current == "O":
                yield "O"
            elif current == "B":
                yield "U"
            elif current == "I":
                yield "L"
            else:
                raise ValueError(errmsg)
            empty = True
            continue
        if current == "O":
            if lookahead in {"B", "O"}:
                yield "O"
            elif lookahead == "I":
                raise ValueError("'I' cannot follow 'O'.")
            else:
                raise ValueError(errmsg)
        elif current == "B":
            if lookahead in {"O", "B"}:
                yield "U"
            elif lookahead in {"I"}:
                yield "B"
            else:
                raise ValueError(errmsg)
        elif current == "I":
            if lookahead == "I":
                yield "I"
            elif lookahead in {"O", "B"}:
                yield "L"
            else:
                raise ValueError(errmsg)
        else:
            raise ValueError(errmsg)


def biolu2bio(iterable):
    """Convert BIOLU tags to BIO tags."""
    it = iter(iterable)
    lag = None
    # TODO: maybe should test the validity of BILOU and not check for
    # correctness
    for x in it:
        if x == "O":
            if lag and lag not in {"L", "U", "O"}:
                raise ValueError("'O' must follow 'L', 'U', or 'O'")
            else:
                yield "O"
        elif x == "B":
            if lag and lag not in {"L", "O", "U"}:
                raise ValueError("'O' must follow 'L', 'U', or 'O'")
            else:
                yield "B"
        elif x == "I":
            if lag and lag not in {"B", "I"}:
                raise ValueError("'O' must follow 'B', or 'I'")
            else:
                yield "I"
        elif x in {"L"}:
            if lag and lag not in {"B", "I"}:
                raise ValueError("'L' must follow 'B', or 'I'")
            else:
                yield "L"
        elif x in {"U"}:
            if lag and lag not in {"L", "O", "U"}:
                raise ValueError("'U' must follow 'L', 'O', or 'U'")
            else:
                yield "L"
        else:
            raise ValueError
