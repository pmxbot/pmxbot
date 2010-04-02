# vim:ts=4:sw=4:expandtab
"""Exposes several SGMLParser subclasses.

This work, including the source code, documentation
and related data, is placed into the public domain.

The orginal author is Robert Brewer.

THIS SOFTWARE IS PROVIDED AS-IS, WITHOUT WARRANTY
OF ANY KIND, NOT EVEN THE IMPLIED WARRANTY OF
MERCHANTABILITY. THE AUTHOR OF THIS SOFTWARE
ASSUMES _NO_ RESPONSIBILITY FOR ANY CONSEQUENCE
RESULTING FROM THE USE, MODIFICATION, OR
REDISTRIBUTION OF THIS SOFTWARE.

If you don't need thread-safety, you might create a single instance of the
parser you want, and feed it yourself. You also might use the classes
directly if you need to customize them in some way; for example, you may
need to alter the list of unsafe_tags in the Sanitizer class, either
per-instance or by subclassing it.

If you need thread-safe parsing, you should use the functions provided.
They create a new instance each time, so you get a *small* performance
hit, but by the same token, each thread can work on its own instance.
"""

import re
import sgmllib
import htmlentitydefs
from xml.sax.saxutils import quoteattr

interesting = re.compile('[&<]')
incomplete = re.compile('&([a-zA-Z][a-zA-Z0-9]*|#[0-9]*)?|'
                           '<([a-zA-Z][^<>]*|'
                              '/([a-zA-Z][^<>]*)?|'
                              '![^<>]*)?')

entityref = re.compile('&([a-zA-Z][-.a-zA-Z0-9]*)[^a-zA-Z0-9]')
charref = re.compile('&#([0-9]+)[^0-9]')

starttagopen = re.compile('<[>a-zA-Z]')


class MoreReasonableSGMLParser(sgmllib.SGMLParser):
    """Just like an SGML Parser, but with more information passed
    to the handle_ methods. For example, handle_entityref passes
    the whole match, ampersand, name, and trailer."""
    
    # Internal -- handle data as far as reasonable.  May leave state
    # and data to be processed by a subsequent call.  If 'end' is
    # true, force handling all data as if followed by EOF marker.
    def goahead(self, end):
        rawdata = self.rawdata
        i = 0
        n = len(rawdata)
        while i < n:
            if self.nomoretags:
                self.handle_data(rawdata[i:n])
                i = n
                break
            match = interesting.search(rawdata, i)
            if match: j = match.start()
            else: j = n
            if i < j:
                self.handle_data(rawdata[i:j])
            i = j
            if i == n: break
            if rawdata[i] == '<':
                if starttagopen.match(rawdata, i):
                    if self.literal:
                        self.handle_data(rawdata[i])
                        i = i+1
                        continue
                    k = self.parse_starttag(i)
                    if k < 0: break
                    i = k
                    continue
                if rawdata.startswith("</", i):
                    k = self.parse_endtag(i)
                    if k < 0: break
                    i = k
                    self.literal = 0
                    continue
                if self.literal:
                    if n > (i + 1):
                        self.handle_data("<")
                        i = i+1
                    else:
                        # incomplete
                        break
                    continue
                if rawdata.startswith("<!--", i):
                        # Strictly speaking, a comment is --.*--
                        # within a declaration tag <!...>.
                        # This should be removed,
                        # and comments handled only in parse_declaration.
                    k = self.parse_comment(i)
                    if k < 0: break
                    i = k
                    continue
                if rawdata.startswith("<?", i):
                    k = self.parse_pi(i)
                    if k < 0: break
                    i = i+k
                    continue
                if rawdata.startswith("<!", i):
                    # This is some sort of declaration; in "HTML as
                    # deployed," this should only be the document type
                    # declaration ("<!DOCTYPE html...>").
                    k = self.parse_declaration(i)
                    if k < 0: break
                    i = k
                    continue
            elif rawdata[i] == '&':
                if self.literal:
                    self.handle_data(rawdata[i])
                    i = i+1
                    continue
                match = charref.match(rawdata, i)
                if match:
                    name = match.group(1)
                    self.handle_charref(name)
                    i = match.end(0)
                    if rawdata[i-1] != ';': i = i-1
                    continue
                match = entityref.match(rawdata, i)
                if match:
                    name = match.group(1)
                    i = match.end(0)
                    trailer = rawdata[i-1]
                    self.handle_entityref(name, trailer)
                    if trailer != ';': i = i-1
                    continue
            else:
                self.error('neither < nor & ??')
            # We get here only if incomplete matches but
            # nothing else
            match = incomplete.match(rawdata, i)
            if not match:
                self.handle_data(rawdata[i])
                i = i+1
                continue
            j = match.end(0)
            if j == n:
                break # Really incomplete
            self.handle_data(rawdata[i:j])
            i = j
        # end while
        if end and i < n:
            self.handle_data(rawdata[i:n])
            i = n
        self.rawdata = rawdata[i:]
        # XXX if end: check for empty stack


class Plaintext(MoreReasonableSGMLParser):
    """Strips all HTML from content.
    Entities are translated to their Unicode equivalents where possible."""
    
    def handle_data(self, data):
        self.result.append(data)
    
    def handle_charref(self, ref):
        try:
            self.result.append(unichr(int(ref)))
        except ValueError:
            self.result.append(u"?")
        
    def handle_entityref(self, ref, trailer):
        try:
            cp = htmlentitydefs.name2codepoint[ref]
            self.result.append(unichr(cp))
            if trailer != ";":
                self.result.append(trailer)
        except KeyError:
            self.result.append("&" + ref + trailer)
        except ValueError:
            self.result.append("?")
            if trailer != ";":
                self.result.append(trailer)

def plaintext(content):
    """Strips all HTML from content.
    Entities are translated to their Unicode equivalents where possible."""
    s = Plaintext()
    s.result = []
    s.feed(content)
    s.close()
    return u"".join(s.result)


class StripTags(MoreReasonableSGMLParser):
    """Strips HTML tags from content. Entities are retained."""
    
    def handle_data(self, data):
        self.result.append(data)
    
    def handle_charref(self, ref):
        self.result.append('&#' + ref + ';')
    
    def handle_entityref(self, ref, trailer):
        self.result.append('&' + ref + trailer)

def striptags(content):
    """Strips HTML tags from content. Entities are retained."""
    s = StripTags()
    s.result = []
    s.feed(content)
    s.close()
    return u"".join(s.result)


class Sanitizer(MoreReasonableSGMLParser):
    """Strips specific HTML tags from content. Entities are retained."""
    
    unsafe_tags = [u'!doctype', u'applet', u'base', u'basefont', u'bgsound',
                   u'blink', u'body', u'button', u'comment', u'embed',
                   u'fieldset', u'fn', u'form', u'frame', u'frameset',
                   u'head', u'html', u'iframe', u'ilayer', u'input',
                   u'isindex', u'keygen', u'label', u'layer', u'legend',
                   u'link', u'meta', u'noembed', u'noframes', u'noscript',
                   u'object', u'optgroup', u'option', u'param', u'plaintext',
                   u'select', u'script', u'style', u'textarea', u'title',
                   ]
    replacement = u"<!-- Prohibited Content -->"
    javascript = r"""(?i)href\w*=['"]javascript:"""
    unsafe_attributes = [u'abort', u'blur', u'change', u'click', 'dblclick',
                         u'error', u'focus', u'keydown', u'keypress', u'keyup',
                         u'load', u'mousedown', u'mouseout', u'mouseover',
                         u'mouseup', u'reset', u'resize', u'submit', u'unload',
                         ]
    empty_tags = [u'area', u'base', u'basefont', u'br', u'hr', u'img',
                  u'input', u'link', u'meta', u'param',
                  ]
    
    def handle_data(self, data):
        self.result.append(data)
    
    def handle_charref(self, ref):
        self.result.append('&#' + ref + ';')
    
    def handle_entityref(self, ref, trailer):
        self.result.append('&' + ref + trailer)
    
    def handle_decl(self, data):
        tag = data.split(" ")[0].lower()
        if ("!" + tag) in self.unsafe_tags:
            self.result.append(self.replacement)
        else:
            self.result.append(u'<!' + data + '>')
    
    def unknown_starttag(self, tag, attributes):
        if tag in self.unsafe_tags:
            self.result.append(self.replacement)
        else:
            attrs = []
            for name, value in attributes:
                if name not in self.unsafe_attributes:
                    attrs.append(' ' + name + '=' + quoteattr(value))
            if tag in self.empty_tags:
                tail = ' />'
            else:
                tail = '>'
            self.result.append('<' + tag + ''.join(attrs) + tail)
    
    def unknown_endtag(self, tag):
        if tag in self.unsafe_tags:
            self.result.append(self.replacement)
        else:
            if tag not in self.empty_tags:
                self.result.append('</' + tag + '>')

def sanitize(content):
    """Strips specific HTML tags from content. Entities are retained."""
    s = Sanitizer()
    s.result = []
    s.feed(content)
    s.close()
    return u"".join(s.result)


