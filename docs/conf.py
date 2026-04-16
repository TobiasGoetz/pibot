import sys
from pathlib import Path
import tomllib

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str((_repo_root / 'src').resolve()))
with (_repo_root / 'pyproject.toml').open('rb') as pyprojectFile:
    _pyproject = tomllib.load(pyprojectFile)
_project = _pyproject['project']

# Distribution name -> short title (e.g. pibot-discord -> Pibot Discord)
_projectName = _project['name']
project = ' '.join(part.capitalize() for part in _projectName.replace('_', '-').split('-'))

_authorList = _project.get('authors') or []
author = ', '.join(entry['name'] for entry in _authorList)

_version = _project['version']
version = release = _version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
]

# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'discord': ('https://discordpy.readthedocs.io/en/stable', None),
    'pymongo': ('https://pymongo.readthedocs.io/en/stable', None),
}

exclude_patterns = ['_build']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
