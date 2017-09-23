"""Utility functions and classes for working with SpaCy."""
import logging
from operator import attrgetter

import spacy
from spacy.tokens import Doc, Span

LOGGER = logging.getLogger(__name__)

DEFAULT_ATTRS = [
    spacy.attrs.HEAD, spacy.attrs.DEP, spacy.attrs.TAG, spacy.attrs.ENT_TYPE,
    spacy.attrs.ENT_IOB
]
""" Attributes needed to reconstruct a SpaCy parse """

ENTITIES_TIME = ("DATE", "TIME")
"""Time entities recognized by Spacy."""

ENTITIES_NUMERIC = ("PERCENT", "MONEY", "QUANTITY", "ORDINAL", "CARDINAL")
"""Numeric entiies recognizd by Spacy."""

# Content words
CONTENT_POS = ("ADJ", "ADV", "NOUN", "PROPN", "VERB")
"""Content word part of speech tags."""

# Function words
FUNCTION_POS = ("ADP", "AUX", "CONJ", "DET", "INTJ", "PRON", "PART", "PRON",
                "SCONJ")
""".Function words part of speech tags."""

OPEN_CLASS_POS = ("ADJ", "ADV", "INTJ", "NOUN", "PROPN", "VERB")
"""Open-class Word POS Tags.

POS corresponding to open class words in the
 [Universal Part of Speech Tags](http://universaldependencies.org/u/pos/)
"""

CLOSED_CLASS_POS = ("ADP", "AUX", "CONJ", "DET", "NUM", "PART", "PRON",
                    "SCONJ")
""" Open Class Word POS Tags

POS corresponding to closed class words in the
 [Universal Part of Speech Tags](http://universaldependencies.org/u/pos/)
"""

# Others
OTHER_POS = ("PUNCT", "SYM", "X")
""" Non Open or Closed Class POS Tags

POS corresponding to closed class words in the
[Universal Part of Speech Tags](http://universaldependencies.org/u/pos/)
"""


def doc_copy(doc):
    """Create a copy of a Spacy document.

    Currently this serializes and deserializes the document to make a copy.
    I haven't figured out another way to do this.

    This is useful, because some methods, like Span are useful but change
    the document in place.

    Parameters
    ------------
    doc : :py:class:`~spacy.tokens.Doc`
        Spacy document

    Returns
    --------
    doc : :py:class:`~spacy.tokens.Doc`
        Copy of the Spacy document

    """
    # There has to be a better way of doing it, but I can't figure out how
    # copy.deepcopy doesn't work because Doc objects can't be pickled
    return Doc(doc.vocab).from_bytes(doc.to_bytes())


def find_spans(tok, spans):
    """Get any spans in which a token appears.

    Parameters
    ----------
    tok: :class:`spacy.tokens.Token`, :class:`spacy.token.Span`
        A SpaCy token or span. If ``tok`` is a span, then its root token is
        used.
    spans: iterable
        An iterable yielding :py:class:`~spacy.tokens.Span` objects

    Yields
    --------
    list of (int, :class:`spacy.tokens.Span`)
        A tuple with the span number and span object in which the
        token appears.

    """
    if isinstance(tok, Span):
        tok = tok.root
    return [(i, span) for i, span in enumerate(spans) if tok in span]


def find_end(tok):
    """Find the named entity span in which a token appears.

    Parameters
    ----------
    tok: :class:`spacy.tokens.Token`, :class:`spacy.token.Span`
        A SpaCy token or span. If ``tok`` is a span, then its root token is
        used.

    Returns
    --------
    (int, :class:`spacy.tokens.Span`) or None
        A tuple with the span number and mamed entity span which the
        token appears. If the token is not in a named entity, then this
        function returns ``None``.

    """
    if tok.ent_iob_ == "O":
        return None
    else:
        return list(find_spans(tok, tok.doc.ents))[0]


def find_noun_chunk(tok):
    """Find the noun-chunk in which a token appears.

    Parameters
    ----------
    tok: :class:`spacy.tokens.Token`, :class:`spacy.token.Span`
        A SpaCy token or span. If ``tok`` is a span, then its root token is
        used.

    Returns
    --------
    (int, :class:`spacy.tokens.Span`) or None
        A tuple with the span number and moun chunk span which the
        token appears. If the token is not in a noun chunk, then this
        function returns ``None``.

    """
    try:
        return list(find_spans(tok, tok.doc.noun_chunks))[0]
    except IndexError:
        pass


def find_sent(tok):
    """Find the sentence in which the token appears.

    Parameters
    ----------
    tok: :class:`spacy.tokens.Token`, :class:`spacy.token.Span`
        A SpaCy token or span. If ``tok`` is a span, then its root token is
        used.

    Returns
    --------
    (int, :class:`spacy.tokens.Span`) or None
        A tuple with the sentence number and sentence span in which the
        token appears. If the token is not in a noun chunk, then this
        function returns ``None``.

    """
    try:
        return list(find_spans(tok, tok.doc.sents))[0]
    except IndexError:
        pass


def remove_leading(predicate, span):
    """Remove leading tokens from a span.

    Drop leading tokens from a span as long as the predicate is true.

    Parameters
    -----------
    predicate: callable
        A callable that returns ``True`` if the token is to be dropped.
    span: :py:class:`~spacy.tokens.Span`
        A SpaCy span.

    Returns
    --------
    :py:class:`~spacy.tokens.Span`
        A SpaCy span without the leading tokens that matched the predicate.

    """
    while predicate(span[0]):
        span = span[1:]
    if len(span) > 0:
        return span


def remove_trailing(predicate, span):
    """Remove trailing tokens from a span.

    Drop trailing tokens from a span as long as the predicate is true.

    Parameters
    -----------
    predicate: callable
        A callable that returns ``True`` if the token is to be dropped.
    span: :py:class:`~spacy.tokens.Span`
        A SpaCy span.

    Returns
    --------
    :py:class:`~spacy.tokens.Span`
        A SpaCy span without the leading tokens that matched the predicate.

    """
    while predicate(span[-1]):
        span = span[:-1]
    if len(span) > 0:
        return span


def spans_overlap(x, y):
    """Check if two spans overlap.

    Parameters
    ------------
    x, y: :class:`spacy.tokens.Span`
        Spacy spans

    Returns
    --------
    bool
        ``True`` if the spans overlap, ``False`` otherwise.

    """
    return not (x.end > y.start or x.start > y.end)


def filter_overlapping_spans(spans):
    """Remove overlapping Spans.

    Parameters
    -----------
    spans: ``iterable`` of :class:`spacy.token.Span`
        An iterable of spans.

    Yield
    -------
    :class:`spacy.token.Span`
        An iterable of spans. Only non-overlapping spans are
        returned, with earlier spans taking precedence,
        after sorting the spans in increasing order.

    """
    i = -1
    for span in sorted(spans, attrgetter("start")):
        if span.start > i:
            yield span
            i = span.end


def merge_entities(doc):
    """Merge entities in-place.

    Parameters
    -----------
    doc: :py:class:`~spacy.tokens.Doc`
        Merge named entities into tokens, in place.

    """
    for ent in doc.ents:
        try:
            ent.merge(ent.root.tag_, ent.text, ent.root.ent_type_)
        except IndexError as e:
            LOGGER.exception("Unable to merge entity \"%s\"; skipping...",
                             ent.text)


def merge_noun_chunks(doc):
    """Merge noun chunks in-place.

    Parameters
    -----------
    doc: :py:class:`~spacy.tokens.Doc`
        Merge named entities into tokens, in place.

    """
    for np in doc.noun_chunks:
        try:
            np.merge(np.root.tag_, np.text, np.root.ent_type_)
        except IndexError as e:
            LOGGER.exception("Unable to merge noun chunk \"%s\"; skipping ...",
                             np.text)


def spans_subset(x, y):
    """Check whether span x is a subset of span y."""
    return (x.start >= y.start) and (x.end <= y.end)


def spans_superset(x, y):
    """Chec whether span x is a superset of span y."""
    return (x.start < y.start) and (x.end > y.end)


def span_before(x, y):
    """Is span x immediately before span y."""
    return (x.end == y.start)


def span_after(x, y):
    """Check whether span x is immediately after span y."""
    return (x.end == y.start)


def span_neighboring(x, y):
    """Check whether span x is an immediate neighbor of span y."""
    return span_before(x, y) or span_after(x, y)


def span_union(x, y):
    """Return a span with the union of span x and span y."""
    # if not neighboring?
    return Span(x.doc, min(x.start, y.start), max(x.end, y.end))


def span_intersect(x, y):
    """Return a span with intersection of span x and span y."""
    if spans_overlap(x, y):
        return Span(x.doc, max(x.start, y.start), min(x.end, y.end))


def span_diff(x, y):
    """Return a span with the difference of span x and span y."""
    if not spans_overlap(x, y):
        return x
    else:
        return Span(x.doc, max(x.start, y.start), min(x.end, y.end))


def tokens_to_span(tokens, contiguous=True):
    """Return a span incorporating all tokens."""
    # assumed but not checked that all tokens are from the same doc
    start = min((tok.i for tok in tokens))
    end = max((tok.i for tok in tokens)) + 1
    # check all tokens are contiguous
    if contiguous:
        # use set to ensure tha they are unique indices
        tokens = sorted(list(set(tokens)), lambda x: x.i)
        # by pigeon hole - only need to check the size to see that they're all
        # there
        if len(tokens) < (start - end + 1):
            return None
    return Span(tokens[0].doc, start, end)


def tokens_to_spans(tokens):
    """Yield spans of contiguous tokens from an iterable of tokens."""
    # The document is finite, so I can assume that the iterable is ...?
    # assumed but not checked that all tokens are from the same doc
    toks = sorted(list(set(tokens)), lambda x: x.i)
    last_i = None
    start = None
    end = None
    for tok in toks:
        if start is None:
            start = tok.i
            end = tok.i
        else:
            if tok.i - last_i == 1:
                end = tok.i
            else:
                yield Span(tok.doc, start, end + 1)
                start = tok.i
                end = tok.i
    return Span(tok.doc, start, end + 1)
