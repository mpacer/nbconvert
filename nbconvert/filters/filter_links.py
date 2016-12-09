#!/usr/bin/env python3
"""A pandoc filter used in converting notebooks to Latex.
Converts links between notebooks to Latex cross-references.
"""
import re

from pandocfilters import RawInline, applyJSONFilters

def resolve_references(source):
    """
    This applies the resolve_one_reference to the text passed in via the source argument.

    This expects content in the form of a string encoded JSON object as represented
    internally in ``pandoc``.
    """
    return applyJSONFilters([resolve_one_reference], source)

def resolve_one_reference(key, val, fmt, meta):
    """
    This takes a tuple of arguments that are compatible with ``pandocfilters.walk()`` that
    allows identifying hyperlinks in the document and transforms them into valid LaTeX 
    \\ref{} calls so that linking to headers between cells is possible.

    See the documentation in ``pandocfilters.walk()`` for further information on the meaning
    and specification of ``key``, ``val``, ``fmt``, and ``meta``. 
    """
    
    if key == 'Link':
        target = val[2][0]
        m = re.match(r'#(.+)$', target)
        if m:
            # pandoc automatically makes labels for headings.
            label = m.group(1).lower()
            label = re.sub(r'[^\w-]+', '', label) # Strip HTML entities
            return RawInline('tex', r'Section \ref{%s}' % label)

    # Other elements will be returned unchanged.



def remove_one_link(key, val, fmt, meta):
    """
    This takes a tuple of arguments that are compatible with ``pandocfilters.walk()`` that
    allows identifying hyperlinks in the document and transforms them into valid LaTeX 
    \\ref{} calls so that linking to headers between cells is possible.

    See the documentation in ``pandocfilters.walk()`` for further information on the meaning
    and specification of ``key``, ``val``, ``fmt``, and ``meta``. 
    """
    
    if key == 'Link':
        return 

    # Other elements will be returned unchanged.

def remove_links(source):
    """
    This applies the resolve_one_reference to the text passed in via the source argument.

    This expects content in the form of a string encoded JSON object as represented
    internally in ``pandoc``.
    """
    return applyJSONFilters([remove_one_link], source)

