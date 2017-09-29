"""Setup scrtip for the textstuff package."""
from setuptools import setup

version = {}
with open("./textstuff/version.py") as fp:
    exec(fp.read(), version)

setup(name='textstuff',
      version=version['__version__'],
      description='Miscellaneous functions for dealing with text data',
      url='http://github.com/jrnold/textstuff',
      author='Jeffrey B. Arnold',
      author_email='jeffrey.arnold@gmail.com',
      license='MIT',
      packages=['textstuff', 'textstuff.spacy'],
      install_requires=[
          "email_normalize",
          "furl",
          "spacy>=1.9.0",
          "textacy",
          "tldextract"
          ],
      python_requires='>=3.6',
      zip_safe=False)
