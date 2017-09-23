"""Extract information for SpaCy documents into data frames."""
import hashlib
import sqlite3
from collections import OrderedDict

import pandas as pd
from textacy.extract import direct_quotations, subject_verb_object_triples


def _doc_hash(doc):
    """Generate a unique ID for a SpaCy document from a hash of its text."""
    h = hashlib.sha1()
    h.update(doc.text.encode("utf-8"))
    return h.hexdigest()


def doc_dict(doc, doc_id=None):
    """Return an ordered dictionary from a SpaCy document."""
    doc_id = doc_id or _doc_hash(doc)
    """Return Spacy Document information as an ordered dictionary."""
    return OrderedDict(
        (('doc_id', doc_id), ('tokens', len(doc)), ('sentences',
                                                    len(list(doc.sents))),
         ('noun_chunks', len(list(doc.noun_chunks))), ('ents',
                                                       len(list(doc.ents)))))


def doc_dataframe(doc, doc_id=None):
    """Convert a SpaCy document to Pandas data frame."""
    return pd.DataFrame.from_dict([doc_dict(doc)])


def tokens_dict(doc, doc_id=None):
    """Yield an ordered dict for each token."""
    doc_id = doc_id or _doc_hash(doc)
    for sid, sent in enumerate(doc.sents):
        for tok in sent:
            d = ((('doc_id', doc_id), ('sent', sid), ('i', tok.i), ('orth',
                                                                    tok.orth_),
                  ('lemma',
                   tok.lemma_), ('ent_iob',
                                 tok.ent_iob_), ('ent_type',
                                                 tok.ent_type_), ('ent_id',
                                                                  tok.ent_id),
                  ('shape', tok.shape_), ('pos', tok.pos_), ('tag', tok.tag_),
                  ('head', tok.head.i), ('dep', tok.dep_), ('lang', tok.lang_),
                  ('idx', tok.idx), ('whitespace',
                                     tok.whitespace_), ('is_alpha',
                                                        tok.is_alpha),
                  ('is_ascii', tok.is_ascii), ('is_digit',
                                               tok.is_digit), ('is_title',
                                                               tok.is_title),
                  ('is_punct', tok.is_punct), ('is_space',
                                               tok.is_space), ('like_num',
                                                               tok.like_num),
                  ('like_email', tok.like_email), ('is_oov',
                                                   tok.is_oov), ('is_stop',
                                                                 tok.is_stop)))
            yield OrderedDict(d)


def tokens_dataframe(doc, doc_id=None):
    """Return a Pandas dataframe of token data."""
    return pd.DataFrame.from_records(list(tokens_dict(doc, doc_id=doc_id)))


def ents_records(doc, doc_id=None):
    """Yield dicts of named entities from a document."""
    doc_id = doc_id or _doc_hash(doc)
    for i, ent in enumerate(doc.ents):
        yield OrderedDict(
            (('doc_id', doc_id), ('ent_id', i), ('start',
                                                 ent.start), ('end', ent.end),
             ('root', ent.root.i), ('label', ent.label_), ('text', ent.text),
             ('lemma', ent.lemma_), ('pos', ent.root.pos_), ('tag',
                                                             ent.root.tag_)))


def ents_dataframe(doc, doc_id=None):
    """Return document entities as a DataFrame."""
    return pd.DataFrame.from_records(ents_records(doc))


def noun_chunks_records(doc, doc_id=None):
    """Yield noun chunks from a document."""
    doc_id = doc_id or _doc_hash(doc)
    for i, chunk in enumerate(doc.noun_chunks):
        yield OrderedDict(
            (('doc_id', doc_id), ('chunk_id', i), ('start', chunk.start),
             ('end', chunk.end), ('root', chunk.root.i),
             ('label', chunk.label_), ('text', chunk.text), ('lemma',
                                                             chunk.lemma_),
             ('pos', chunk.root.pos_), ('tag', chunk.root.tag_)))


def noun_chunks_dataframe(doc, doc_id=None):
    """Return document noun chunks as a Pandas data frame."""
    return pd.DataFrame.from_records(noun_chunks_records(doc))


class ParsedCorpusDB:
    """Store a corpus of Spacy parsed documents to a database.

    This stores the parsed documents in a database with the
    following tables
    - ``documents``: One row per document
    - ``token``: One row per token per document
    - ``ents``: Entities
    - ``noun_chunks``: Noun chunks
    Parameters
    -----------
    db : str
        Database engine string
    """

    _TABLE_DDL = """
    CREATE TABLE documents (
        doc_id TEXT,
        tokens INT CHECK (tokens >= 0),
        sentences INT (sentences >= 0),
        noun_chunks INT (noun_chunks >= 0),
        ents INT CHECK (ents >= 0),
        PRIMARY KEY (doc_id)
    );
    CREATE TABLE tokens (
        doc_id TEXT NOT NULL,
        sent INT NOT NULL CHECK (sent >= 0),
        i INT NOT NULL CHECK (i >= 0),
        orth TEXT NOT NULL,
        lemma TEXT,
        ent_iob TEXT,
        ent_type TEXT,
        ent_id BIGINT,
        shape TEXT,
        pos TEXT,
        tag TEXT,
        head BIGINT,
        dep TEXT,
        lang TEXT,
        idx INT NOT NULL,
        whitespace TEXT NOT NULL,
        is_alpha BOOLEAN NOT NULL,
        is_ascii BOOLEAN NOT NULL,
        is_digit BOOLEAN NOT NULL,
        is_title BOOLEAN NOT NULL,
        is_punct BOOLEAN NOT NULL,
        is_space BOOLEAN NOT NULL,
        like_num BOOLEAN NOT NULL,
        like_email BOOLEAN NOT NULL,
        is_oov BOOLEAN NOT NULL,
        is_stop BOOLEAN NOT NULL,
        CHECK (is_alpha IN (0, 1)),
        CHECK (is_ascii IN (0, 1)),
        CHECK (is_digit IN (0, 1)),
        CHECK (is_title IN (0, 1)),
        CHECK (is_punct IN (0, 1)),
        CHECK (is_space IN (0, 1)),
        CHECK (like_num IN (0, 1)),
        CHECK (like_email IN (0, 1)),
        CHECK (is_oov IN (0, 1)),
        CHECK (is_stop IN (0, 1)),
        PRIMARY KEY (doc_id, i),
        FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
    );
    CREATE TABLE ents (
        doc_id TEXT NOT NULL,
        ent_num INT CHECK (ent_Num >= 0),
        start_i INT NOT NULL CHECK (start_i >= 0),
        end_i INT NOT NULL CHECK (end_i >= 0),
        root INT NOT NULL CHECK (root >= 0),
        label TEXT,
        text TEXT,
        lemma TEXT,
        pos TEXT,
        tag TEXT,
        PRIMARY KEY (doc_id, ent_num),
        FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
    );
    CREATE TABLE noun_chunks (
        doc_id TEXT,
        chunk_num INT,
        start_i INT NOT NULL CHECK (start_i >= 0),
        end_i INT NOT NULL CHECK (end_i >= 0),
        root INT NOT NULL CHECK (root >= 0),
        label TEXT,
        text TEXT,
        lemma TEXT,
        pos TEXT,
        tag TEXT,
        PRIMARY KEY (doc_id, chunk_id),
        FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
    );
    """
    _TABLES = {
        'documents': doc_dataframe,
        'tokens': tokens_dataframe,
        'ents': ents_dataframe,
        'noun_chunks': noun_chunks_dataframe
    }

    def __init__(self, db):
        """Initialize the object."""
        self.db = db
        # internal counter for number of docs
        self._i = 0
        # initialze tables if a SQLite3 connection
        if isinstance(db, sqlite3.Connection):
            self.db.executescript(self._TABLE_DDL)

    @staticmethod
    def _digest(doc):
        """Create unique ID for a document."""
        m = hashlib.sha1()
        m.update(doc.text.encode("utf-8"))
        return m.digest()

    def _add_rows(self, id_, doc, table, f, *args, **kwargs):
        """Add multiple rows into a table."""
        df = f(doc, doc_id=id_, *args, **kwargs)
        if df is not None:
            df.to_sql(table, self.db, index=False, if_exists="append")

    def add_doc(self, doc, id_=None, *args, **kwargs):
        """Add a document to the database.

        Parameters
        -----------
        doc: :class:`spacy.Doc`
            A Spacy document
        id_: str
            An identifier for the document

        """
        id_ = id_ or self._digest(doc)
        for tbl, f in self._TABLES.items():
            self._add_rows(id_, doc, tbl, f, *args, **kwargs)

    def add_docs(self, docs, *args, **kwargs):
        """Add multiple documents to the corpus.

        Parameters
        -----------
        docs: iterator of (str, :class:`spacy.Doc`) tuples
            An iterator providing tuples with document identifiers
            the Spacy parsed documents.

        """
        for id_, d in docs:
            self.add_doc(id_, d, *args, **kwargs)


def word_vectors_to_df(vocab):
    """Return a data frame of word vectors from a vocabulary."""
    def f(lexeme):
        if lexeme.vector_norm > 0:
            return pd.DataFrame({
                "word": lexeme.orth_,
                "dim": list(range(lexeme.vector.shape[0])),
                "value": lexeme.vector
            })

    return pd.concat((f(lexeme) for lexeme in vocab))


def doc_vector_to_df(doc, doc_id=None):
    """Return a data frame of document word vectors."""
    return pd.DataFrame({
        "doc_id": doc_id,
        "dim": list(range(doc.vector.shape[0])),
        "value": doc.vector
    })


def sent_vectors_to_df(doc, doc_id=None):
    """Return a data frame of sentence word vectors from a document."""
    def f(sent, sent_id, doc_id):
        return pd.DataFrame({
            "doc_id": doc_id,
            "sent_id": sent_id,
            "dim": list(range(sent.vector.shape[0])),
            "value": doc.vector
        })

    return pd.concat(f(sent, i, doc_id) for i, sent in enumerate(doc.sents))


def svo_to_records(doc, doc_id=None):
    """Yield records of subject, verb, object triples from a document."""
    for sent_id, sent in enumerate(doc.sents):
        for svo_id, (s, v, o) in enumerate(subject_verb_object_triples(sent)):
            d = OrderedDict(
                (("doc_id", doc_id), ("sent_id", sent_id), ("svo_id", svo_id),
                 ("subject", s.text), ("subject_start",
                                       s.start), ("subject_end", s.end),
                 ("subject_tag", s.root.tag_), ("subject_ptag", ' '.join([
                     t.tag_ for t in s
                 ])), ("subject_pos", s.root.pos_), ("subject_ppos", ' '.join(
                     [t.pos_
                      for t in s])), ("subject_ent_type", s.root.ent_type_),
                 ("verb", v.text), ("verb_start", v.start), ("verb_end",
                                                             v.end),
                 ("verb_tag", v.root.tag_), ("subject_ptag", ' '.join([
                     t.tag_ for t in s
                 ])), ("verb_pos", v.root.pos_), ("verb_ppos", ' '.join(
                     [t.pos_ for t in s])), ("verb_dep",
                                             v.root.dep_), ("verb", v.text),
                 ("object", o.text), ("object_start", o.start), ("object_end",
                                                                 o.end),
                 ("object_tag", o.root.tag_), ("object_stag", ' '.join([
                     t.tag_ for t in s
                 ])), ("object_pos", o.root.pos_), ("object_spos", ' '.join(
                     [t.pos_ for t in s])), ("object_ent_type",
                                             o.root.ent_type_), ("object_dep",
                                                                 o.root.dep_)))
            yield d


def svo_to_dataframe(doc, doc_id=None):
    """Return a data frame of subject, verb, object triples."""
    return pd.DataFrame.from_records(svo_to_records(doc))


def direct_quotations_to_records(doc, doc_id=None):
    """Yield records of direct quotation from a document."""
    for quotation_id, (speaker, rv,
                       quote) in enumerate(direct_quotations(doc)):
        d = OrderedDict(
            (("doc_id", doc_id), ("quotation_id", quotation_id),
             ("speaker", speaker.text), ("speaker_start", speaker.start),
             ("speaker_end", speaker.end), ("rv", rv), ("rv_i", rv.i),
             ("quote", quote), ("quote_start", quote.start), ("quote_end",
                                                              quote.end)))
        yield d


def direct_quotations_to_dataframe(doc, doc_id=None):
    """Return a data frame with direct quotation from a data frame."""
    return pd.DataFrame.from_records(
        direct_quotations_to_records(doc, doc_id=doc_id))
