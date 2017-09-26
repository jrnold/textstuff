from .utils import shuffle_iterable


class ShuffledCorpus:
    """ Return a corpus that is a shuffled version of input iterable ``corpus``

    This will return the documents in ``corpus`` in a random order.
    If the ``corpus`` has a length and ``n=None``, then this is equivalent
    to using ``random.shuffle`` on the corpus.

    However, this function will can also shuffle a corpus without loading all
    of it into memory. If ``n`` is not ``None``, at most ``n`` elements are
    kept in memory. The iterable is shuffled by placing each new element in the
    queue of ``n`` elements, and then randomly removing an element from that
    queue with equal probability.

    Parameters
    -----------
    corpus:
        A corpus as defined by :py:pkg:`~gensim`---an iterable that yields
        documents.
    n: int, None
        The size of the queue to use to shuffle elements.

    """  # noqa
    def __init__(self, corpus, n=None):
        if n is None:
            try:
                len(corpus)
            except TypeError:
                msg = "If n is None, then the corpus have a length."
                raise ValueError(msg)
        self.corpus = corpus

    def __iter__(self):
        for el in shuffle_iterable(self.corpus):
            yield el
