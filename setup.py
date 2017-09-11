from setuptools import setup

setup(name='textstuff',
      version='0.0.1',
      description='Miscellaneous functions for dealing with text data',
      url='http://github.com/jrnold/textstuff',
      author='Jeffrey B. Arnold',
      author_email='jeffrey.arnold@gmail.com',
      license='MIT',
      packages=['textstuff'],
      install_requires=[
          "pandas",
          "spacy",
          "textacy"
      ]
      zip_safe=False)
