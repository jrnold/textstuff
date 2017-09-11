""" Some functions to make working with Spacy documents easier

"""
import itertools
from functools import partial
from types import GeneratorType
from heapq import merge
from operator import attrgetter
import os.path
import logging
import json

import spacy
import pandas as pd
from spacy.tokens import Doc, Token, Span


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

POS corresponding to open class words in the [Universal Part of Speech Tags](http://universaldependencies.org/u/pos/)
"""

CLOSED_CLASS_POS = ("ADP", "AUX", "CONJ", "DET", "NUM", "PART", "PRON", "SCONJ")
""" Open Class Word POS Tags

POS corresponding to closed class words in the [Universal Part of Speech Tags](http://universaldependencies.org/u/pos/)
"""

# Others
OTHER_POS = ("PUNCT", "SYM", "X")
""" Non Open or Closed Class POS Tags

POS corresponding to closed class words in the [Universal Part of Speech Tags](http://universaldependencies.org/u/pos/)
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


def text_with_ws(tok, lemma=False, lower=False):
    """ Return text with whitespace

    Like the `text_with_ws` property for :py:class:`~spacy.tokens.Token.Token`,
    but with more options.

    Parameters
    -----------
    tok : :py:class:`~spacy.tokens.Token`
        Token object
    lemma : bool
        If ``True``, then the non-whitespace text is :py:meth:`~spacy.tokens.Token.lemma_`.
    lower : bool
        If ``True`` and  ``lemma=False` then the non-whitespace text is :py:meth:`~spacy.token.Token.lower_`.

    Returns
    --------
    str
        The token's text, including trailing whitespace.

    """  # noqa
    if lemma:
        text = tok.lemma_
    elif lower:
        text = tok.lower_
    else:
        text = tok.text
    return text + whitespace_

lemma_with_ws = partial(text_with_ws, lemma=True, lower=True)
lower_with_ws = partial(text_with_ws, lemma=False, loewr=True)

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
    while fun(span[0]):
        span = span[1:]
    if len(span) > 0:
        return span

def remove_det(span):
    """ Remove leading determiner from a span

    Parameters
    -----------
    span: :py:class:`~spacy.tokens.Span`
        SpaCy Span

    Returns
    -------
    :py:class:`~spacy.tokens.Span`
        SpaCy span without the leading determiner

    """
    # doesn't consider if > 1 determiners, or if only determiner
    if span[0].pos_ != "DET":
        return span
    else:
        return Span(span.doc, span.start + 1, span.end)

# From itertools package documentation
def _flatten(listOfLists):
    "Flatten one level of nesting"
    return itertools.chain.from_iterable(listOfLists)

def span_chunks(doc, spans=[], function=None):
    """ Partition document into spans given list of span chunks

    Given a list of spans, return a partition of spans that includes
    all tokens in the document. The primary use is to iterate over
    spans including named entities without formally merging them.
    The returns spans will include the original set of spans,
    as well as a one token span for any token not included in the orginal spans.
    This also allows filtering on the tokens not in the spans.

    Parameters
    ----------
    doc : :py:class:`~spacy.tokens.Doc`
        Spacy document to partition into chunks
    spans : iterable of :py:class:`~spacy.tokens.Span`
        List of existing (and non-overlapping spans)
    function : function
        Function that filters tokens to include in the returned
        spans (only for those tokens not in the ``spans`` argument).
        It should take one argument, which is a :py:class:`~spacy.tokens.Token` object.

    Yields
    --------
    :py:class:`~spacy.tokens.Span`
        Iterates through the spans in order

    """
    # if spans is an iterator best to not allow it to be exhausted
    spans = sorted(spans)
    span_toks = set(_flatten(spans))
    # this will be sorted
    other_spans = (Span(doc, t.i, t.i + 1) for
                        t in filter(function, doc)
                        if t not in span_toks)
    # Can use this because both spans and other_spans are sorted
    return merge(spans, other_spans, key=attrgetter("start"))
