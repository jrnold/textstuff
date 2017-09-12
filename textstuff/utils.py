import email_normalize
import tldextract


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
