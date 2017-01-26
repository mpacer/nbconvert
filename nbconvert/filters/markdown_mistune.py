"""Markdown filters with mistune

Used from markdown.py
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import re

import mistune

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from traitlets.config import LoggingConfigurable

from nbconvert.filters.strings import add_anchor
from nbconvert.utils.exceptions import ConversionException


class MathBlockGrammar(mistune.BlockGrammar):
    block_math = re.compile(r"^\$\$(.*?)\$\$", re.DOTALL)
    latex_environment = re.compile(r"^\\begin\{([a-z]*\*?)\}(.*?)\\end\{\1\}",
                                                re.DOTALL)

class MathBlockLexer(mistune.BlockLexer):
    default_rules = ['block_math', 'latex_environment'] + mistune.BlockLexer.default_rules

    def __init__(self, rules=None, **kwargs):
        if rules is None:
            rules = MathBlockGrammar()
        super(MathBlockLexer, self).__init__(rules, **kwargs)

    def parse_block_math(self, m):
        """Parse a $$math$$ block"""
        self.tokens.append({
            'type': 'block_math',
            'text': m.group(1)
        })

    def parse_latex_environment(self, m):
        self.tokens.append({
            'type': 'latex_environment',
            'name': m.group(1),
            'text': m.group(2)
        })


class MathInlineGrammar(mistune.InlineGrammar):
    math = re.compile(r"^\$(.+?)\$", re.DOTALL)
    block_math = re.compile(r"^\$\$(.+?)\$\$", re.DOTALL)
    text = re.compile(r'^[\s\S]+?(?=[\\<!\[_*`~$]|https?://| {2,}\n|$)')


class MathInlineLexer(mistune.InlineLexer):
    default_rules = ['block_math', 'math'] + mistune.InlineLexer.default_rules

    def __init__(self, renderer, rules=None, **kwargs):
        if rules is None:
            rules = MathInlineGrammar()
        super(MathInlineLexer, self).__init__(renderer, rules, **kwargs)

    def output_math(self, m):
        return self.renderer.inline_math(m.group(1))

    def output_block_math(self, m):
        return self.renderer.block_math(m.group(1))


class MarkdownWithMath(mistune.Markdown):
    def __init__(self, renderer, **kwargs):
        if 'inline' not in kwargs:
            kwargs['inline'] = MathInlineLexer
        if 'block' not in kwargs:
            kwargs['block'] = MathBlockLexer
        super(MarkdownWithMath, self).__init__(renderer, **kwargs)

    def output_block_math(self):
        return self.renderer.block_math(self.token['text'])

    def output_latex_environment(self):
        return self.renderer.latex_environment(self.token['name'], self.token['text'])


class IPythonRenderer(mistune.Renderer):
    def block_code(self, code, lang):
        if lang:
            try:
                lexer = get_lexer_by_name(lang, stripall=True)
            except ClassNotFound:
                code = lang + '\n' + code
                lang = None

        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code)

        formatter = HtmlFormatter()
        return highlight(code, lexer, formatter)

    def header(self, text, level, raw=None):
        html = super(IPythonRenderer, self).header(text, level, raw=raw)
        if hasattr(self, 'local_config'):
            # if this does have a config, pass it in to the add_anchor class instance 
            return add_anchor(config=self.local_config)(html)
        else:
            return add_anchor()(html)

    # Pass math through unaltered - mathjax does the rendering in the browser
    def block_math(self, text):
        return '$$%s$$' % text

    def latex_environment(self, name, text):
        return r'\begin{%s}%s\end{%s}' % (name, text, name)

    def inline_math(self, text):
        return '$%s$' % text

class Markdown2Html_Mistune(LoggingConfigurable):
    def __init__(self, **kw):
        super(Markdown2Html_Mistune, self).__init__(**kw)

    def __call__(self, source):
        """Convert a markdown string to HTML using mistune"""
        renderer=IPythonRenderer(escape=False)
        # when called appropriately by register filter, it will inherit from template's config
        renderer.local_config = self.config
        return MarkdownWithMath(renderer=renderer).render(source)

markdown2html_mistune = Markdown2Html_Mistune
