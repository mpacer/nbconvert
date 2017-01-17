# coding: utf-8
"""String filters.

Contains a collection of useful string manipulation filters for use in Jinja
templates.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import re
import textwrap
import warnings

try:
    from urllib.parse import quote  # Py 3
except ImportError:
    from urllib2 import quote  # Py 2
from xml.etree import ElementTree

from ipython_genutils import py3compat


__all__ = [
    'wrap_text',
    'html2text',
    'add_anchor',
    'strip_dollars',
    'strip_files_prefix',
    'comment_lines',
    'get_lines',
    'ipython2python',
    'posix_path',
    'path2url',
    'add_prompts',
    'ascii_only',
    'prevent_list_blocks',
]


def wrap_text(text, width=100):
    """ 
    Intelligently wrap text.
    Wrap text without breaking words if possible.
    
    Parameters
    ----------
    text : str
        Text to wrap.
    width : int, optional
        Number of characters to wrap to, default 100.
    """

    split_text = text.split('\n')
    wrp = map(lambda x:textwrap.wrap(x,width), split_text)
    wrpd = map('\n'.join, wrp)
    return '\n'.join(wrpd)


def html2text(element):
    """extract inner text from html
    
    Analog of jQuery's $(element).text()
    """
    if isinstance(element, py3compat.string_types):
        try:
            element = ElementTree.fromstring(element)
        except Exception:
            # failed to parse, just return it unmodified
            return element
    
    text = element.text or ""
    for child in element:
        text += html2text(child)
    text += (element.tail or "")
    return text


def _convert_header_id(header_contents):
    """Convert header contents to valid id value. Takes string as input, returns string.
    
    Note: this may be subject to change in the case of changes to how we wish to generate ids.

    For use on markdown headings.
    """
    return header_contents.replace(' ', '-')

def add_anchor(html):
    """Add an id and an anchor-link to an html header
    
    For use on markdown headings
    """
    try:
        h = ElementTree.fromstring(py3compat.cast_bytes_py2(html, encoding='utf-8'))
    except Exception:
        # failed to parse, just return it unmodified
        return html
    link = _convert_header_id(html2text(h))
    h.set('id', link)
    a = ElementTree.Element("a", {"class" : "anchor-link", "href" : "#" + link})
    a.text = u'¶'
    h.append(a)

    # Known issue of Python3.x, ElementTree.tostring() returns a byte string
    # instead of a text string.  See issue http://bugs.python.org/issue10942
    # Workaround is to make sure the bytes are casted to a string.
    return py3compat.decode(ElementTree.tostring(h), 'utf-8')


def add_prompts(code, first='>>> ', cont='... '):
    """Add prompts to code snippets"""
    new_code = []
    code_list = code.split('\n')
    new_code.append(first + code_list[0])
    for line in code_list[1:]:
        new_code.append(cont + line)
    return '\n'.join(new_code)

    
def strip_dollars(text):
    """
    Remove all dollar symbols from text
    
    Parameters
    ----------
    text : str
        Text to remove dollars from
    """

    return text.strip('$')


files_url_pattern = re.compile(r'(src|href)\=([\'"]?)/?files/')
markdown_url_pattern = re.compile(r'(!?)\[(?P<caption>.*?)\]\(/?files/(?P<location>.*?)\)')

def strip_files_prefix(text):
    """
    Fix all fake URLs that start with `files/`, stripping out the `files/` prefix.
    Applies to both urls (for html) and relative paths (for markdown paths).
    
    Parameters
    ----------
    text : str
        Text in which to replace 'src="files/real...' with 'src="real...'
    """
    cleaned_text = files_url_pattern.sub(r"\1=\2", text)
    cleaned_text = markdown_url_pattern.sub(r'\1[\2](\3)', cleaned_text)
    return cleaned_text


def comment_lines(text, prefix='# '):
    """
    Build a Python comment line from input text.
    
    Parameters
    ----------
    text : str
        Text to comment out.
    prefix : str
        Character to append to the start of each line.
    """
    
    #Replace line breaks with line breaks and comment symbols.
    #Also add a comment symbol at the beginning to comment out
    #the first line.
    return prefix + ('\n'+prefix).join(text.split('\n')) 


def get_lines(text, start=None,end=None):
    """
    Split the input text into separate lines and then return the 
    lines that the caller is interested in.
    
    Parameters
    ----------
    text : str
        Text to parse lines from.
    start : int, optional
        First line to grab from.
    end : int, optional
        Last line to grab from.
    """
    
    # Split the input into lines.
    lines = text.split("\n")
    
    # Return the right lines.
    return "\n".join(lines[start:end]) #re-join

def _mpl_magic_regex_generator(browser_backends=None):
    """Create regex for detecting incompatible backends in mpl magics.
    
    Parameters
    ----------

    interactive_backends: List
        List of strings, each of which is a forbidden matplotlib backend. 
    """
    if browser_backends is None:
        browser_backends = ["notebook", "inline"]
    no_mpl_be_str = "|".join(browser_backends)
    #  mpl_magic_backend_extractor = re.compile(r'(^% *matplotlib *\w*)({})'.format(no_mpl_be_str))
    #  return mpl_magic_backend_extractor
    return r'(^% *matplotlib *\w*)({})'.format(no_mpl_be_str)

def _remove_browser_mpl_backends(code, browser_backends=None):
    """Remove incompatible backends from mpl magics.
    
    Parameters
    ----------

    code : str
        IPython code with matplotlib magic
    notebook_backends: list of str
        List of strings, each of which is a forbidden matplotlib backend.
    """
    #  mpl_magic_regex_local = _mpl_magic_regex_generator(browser_backends)

    lines = code.split('\n')
    magic_line = [i for i,x in enumerate(lines) if re.match(_mpl_magic_regex_generator(browser_backends),lines[i])]
    import logging; logging.warn("hi", magic_line); 
    assert False, lines
    if len(magic_line)!=0: 
        # only change first backend declaration (since the rest shouldn't work anyway)
        #  regex_match = mpl_magic_regex_local.match(lines[magic_line[0]])
        regex_match = re.match(_mpl_magic_regex_generator(browser_backends),lines[magic_line[0]])
        lines[magic_line[0]] = regex_match.group(1) + "\n# nbconvert removed: " + regex_match.group(2)
        code = "\n".join(lines)
    return code

def ipython2python(code, no_browser=False, browser_backends=None):
    """Transform IPython syntax to pure Python syntax

    Parameters
    ----------

    code : str
        IPython code, to be transformed to pure Python
    no_browser: Boolean
        True if matplotlib backends should be filtered
    bad_backends: list of str
        List of strings, each of which is a forbidden matplotlib backend.
    """
    try:
        from IPython.core.inputsplitter import IPythonInputSplitter
    except ImportError:
        warnings.warn(
            "IPython is needed to transform IPython syntax to pure Python."
            " Install ipython if you need this functionality."
        )
        return code
    else:
        if no_browser and re.match("% *matplotlib", code):
            code = _remove_browser_mpl_backends(code, browser_backends)
        isp = IPythonInputSplitter(line_input_checker=False)
        return isp.transform_cell(code)

def posix_path(path):
    """Turn a path into posix-style path/to/etc
    
    Mainly for use in latex on Windows,
    where native Windows paths are not allowed.
    """
    if os.path.sep != '/':
        return path.replace(os.path.sep, '/')
    return path

def path2url(path):
    """Turn a file path into a URL"""
    parts = path.split(os.path.sep)
    return '/'.join(quote(part) for part in parts)

def ascii_only(s):
    """ensure a string is ascii"""
    s = py3compat.cast_unicode(s)
    return s.encode('ascii', 'replace').decode('ascii')

def prevent_list_blocks(s):
    """
    Prevent presence of enumerate or itemize blocks in latex headings cells
    """
    out = re.sub('(^\s*\d*)\.', '\\1\.', s)
    out = re.sub('(^\s*)\-', '\\1\-', out)
    out = re.sub('(^\s*)\+', '\\1\+', out)
    out = re.sub('(^\s*)\*', '\\1\*', out)
    return out
