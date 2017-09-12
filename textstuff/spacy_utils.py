import logging
from operator import attrgetter

from spacy.tokens import Doc

LOGGER = logging.getLogger(__name__)


ENTITIES_TIME = ("DATE", "TIME")
""" Time entities recognized by Spacy """


ENTITIES_NUMERIC = ("PERCENT", "MONEY", "QUANTITY", "ORDINAL", "CARDINAL")
""" Numeric entiies recognizd by Spacy """

# Content words
CONTENT_POS = ("ADJ", "ADV", "NOUN", "PROPN", "VERB")
""" Content word part of speech tags"""

# Function words
FUNCTION_POS = ("ADP", "AUX", "CONJ", "DET", "INTJ", "PRON", "PART", "PRON",
                "SCONJ")
""" Function words part of speech tags"""

OPEN_CLASS_POS = ("ADJ", "ADV", "INTJ", "NOUN", "PROPN", "VERB")
""" Open Class Word POS Tags

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
    """ Create a copy of a Spacy document

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


def tok_spans(tok, spans):
    """ Get any spans in which a token appears

    Parameters
    ----------
    tok: :py:class:`~spacy.tokens.Token`
        A Spacy token
    spans: iterable
        An iterable yielding :py:class:`~spacy.tokens.Span` objects

    Yields
    --------
    :py:class:`~spacy.tokens.Span`
        The spans from `spans` in which the token appears, if any.

    """
    return (span for span in spans if tok in span)


def tok_ent(tok):
    """ Get the entity in which a token appears

    Parameters
    ----------
    tok: :py:class:`~spacy.tokens.Token`
        A Spacy token

    Returns
    --------
    :py:class:`~spacy.tokens.Span` or ``None``
        The entity span in which the token appears, if any.

    """
    ents = list(tok_spans(tok, tok.doc.ents))
    return ents[0] if len(ents) else None


def tok_noun_chunk(tok):
    """ Get noun-chunk (if any) in which the token appears

    Parameters
    ----------
    tok: :py:class:`~spacy.tokens.Token`
        A Spacy token

    Returns
    --------
    :py:class:`~spacy.tokens.Span` or ``None``
        The noun chunk span in which the token appears, if any.

    """
    np = list(tok_spans(tok, tok.doc.noun_chunks))
    return np[0] if len(np) else None


def tok_sent(tok):
    """ Get the sentence in which the token appears

    Parameters
    ----------
    tok: :py:class:`~spacy.tokens.Token`
        A Spacy token

    Returns
    --------
    :py:class:`~spacy.tokens.Span` or ``None``
        The sentence span in which the token appears.

    """
    sents = list(tok_spans(tok, tok.doc.sents))
    return sents[0] if len(sents) else None


def remove_leading(predicate, span):
    """ Remove leading tokens from a span

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
    """ Remove trailing tokens from a span

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
    """ Check if two spans overlap

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
    """ Remove overlapping Spans


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
    """ Merge entities in-place

    Parameters
    -----------
    doc: :py:class:`~spacy.tokens.Doc`
        Merge named entities into tokens, in place.
    """
    for ent in doc.ents:
        try:
            ent.merge(ent.root.tag_,
                      ent.text,
                      ent.root.ent_type_)
        except IndexError as e:
            LOGGER.exception("Unable to merge entity \"%s\"; skipping...",
                             ent.text)


def merge_noun_chunks(doc):
    """ Merge noun chunks in-place

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