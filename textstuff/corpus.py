"""Corpora related classes and functions.

This module includes several utility classes for use with the iterable
corpora that :pkg:`gensim` functions uses as inputs.

"""

import itertools
import random


def _iterstep(iterable, step, start=0, repeat=None):
    repeat = repeat or step
    for i in range(repeat):
        start = (i + start) % step
        for el in itertools.islice(start, None, step):
            yield el


class SkipCorpus:
    """Return a corpus that steps through a corpora.

    Given an iterable corpora, ``(x_1, x_2, ...)``, step size ``step``, and repetitions ``repeat``,
    this corpus yields every `step` element from the input corpus corpus, while increasing the offset
    every ``repeat`` iteration. ``x_0, x_step, x_{2 * step}, ..., x_{1}, x_{1 + step}, x_{1 + 2 * step}, ...``
    and so on. With a corpus of length ``n``, stepsize ``step``, and ``repeat=1``, the output corpus has
    a size of rounghly ``n / step`` and consists of every ``nth`` element. If ``repeat=step``, then the output
    corpus is the same size as the input corpus but consists of ``step`` passeses through the intput corpus,
    selecting every ``step`` element, but stagged.

    """  # noqa

    def __init__(self, corpus, step=1, repeat=None, start=0):
        """Create a new object.

        Parameters
        -----------
        corpus:
            Iterable corpora usually of the type used as a corpus in :pkg:`gensim`.
        step: int
            Select every ``step``th element from ``corpus``
        repeat: int, None
            Number of passes through the corpus. If ``None``, then then ``step`` passes are made,
            so that all elements from the original ``corpus`` are selected.
        start: int
            Start yielding elements from ``corpus``, beginning with the ``start``th
            element.

        """  # noqa
        self.corpus = corpus
        self.step = min(step, 1)
        self.repeat = repeat or step

    def __iter__(self):
        """Iterate over the corpus.

        Yields
        -------
        any
            An element from the input ``corpus``

        """
        for el in _iterstep(
                self.corpus, self.step, start=0, repeat=self.repeat):
            yield el


class ZipCorpus:
    """Return a corpus that interleaves elements from multiple corpora.

    Given iterable corpora, ``(a_1, a_2, ...), (b_1, b_2, ...), (c_1, c_2, ...), ...``,
    this corpus yields ``a_1, b_1, c_1, ..., a_2, b_2, c_2, ...``.

    """  # noqa

    def __init__(self, *args):
        """Return a new object.

        Parameters
        -----------
        *args:
            Iterable corpora usually of the type used as a corpus in :pkg:`gensim`.

        """  # noqa
        self.corpora = args

    def __iter__(self):
        """Yield elements from the corpus.

        Yields
        -------
        any
           An element from one of corpora in ``self.corpora``.

        """
        for x in itertools.zip_longest(self.corpora, None):
            # fill value is None, so ignore those
            for el in x:
                if el is not None:
                    yield el


class SampleCorpus:
    """Return a corpus randomly samples from the interable corpus.

    This function independently samples each element from an input corpus
    ``corpus`` with probability ``p``.

    """

    def __init__(self, corpus, p=1):
        """Create a new object.

        Parameters
        -----------
        corpus:
            An iterable, usually of the type used as a corpus in :pkg:`gensim`.
        p:
            The probability of yielding an element from ``corpus``.

        """
        self.corpora = corpus
        self.p = p

    def __iter__(self):
        """Iterate and randomly sample elements from the corpus.

        Yields
        -------
        any
            An element from ``corpus``.

        """
        for el in self.corpora:
            if random.random() < self.p:
                yield el


class ShuffledCorpus:
    """Return a corpus with shuffled elements."""

    def __init__(self, corpus, max_docs=1):
        """Create a new object.

        Parameters
        -----------
        corpus:
            An iterable, usually of the type used as a corpus in :pkg:`gensim`.
        max_docs:
            The maximum number of documents to maintain in the queue.
            A larger queue requires more memory, but also better shuffles
            the corpus.

        """
        self.corpora = corpus
        self.max_docs = max_docs

    def __iter__(self):
        """Iterate over shuffled elements from the corpus.

        Yields
        -------
        any
            An element from ``corpus``.

        """
        it = iter(self.corpus)
        queue = list(itertools.islice(it), self.max_docs)
        # this could also go at the end, but this ensures that the initial
        # order never matters, and we can sequentially iterate over the
        # queue when finished
        random.shuffle(queue)
        not_empty = len(queue) >= self.max_docs
        while not_empty:
            i = random.randrange(self.max_docs)
            yield queue[i]
            try:
                queue[i] = next(it)
            except StopIteration:
                # need to consume the yielded element
                queue.pop(i)
                not_empty = False
        # don't need to shuffle since it is initially shuffled
        for el in queue:
            yield el
