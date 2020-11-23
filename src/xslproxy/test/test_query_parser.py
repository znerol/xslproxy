import unittest

from lxml import etree
from xslproxy import xsl


class XslQueryParserTestCase(unittest.TestCase):

    def test_query_string_with_params(self):
        """
        Test query string parsing with parameters
        """

        # Generate with:
        # urllib.parse.unquote(urllib.parse.urlencode([
        #   ("xsl[]", "first"),
        #   ("xsl[]", "sécönd"),
        #   ("sp[first][string-param]", "héllö wôrld"),
        #   ("sp[first][string-param-2]", "http://example.com"),
        #   ("xp[first][xpath-param]", "//a/b[@c=\"d\"]")
        # ])).encode('utf-8')

        qs = b'xsl[]=first' + \
            b'&xsl[]=s\xc3\xa9c\xc3\xb6nd' + \
            b'&sp[first][string-param]=h\xc3\xa9ll\xc3\xb6+w\xc3\xb4rld' + \
            b'&sp[first][string-param-2]=http://example.com' + \
            b'&xp[first][xpath-param]=//a/b[@c="d"]'

        xsls, params = xsl.XslQueryStringParser().parse(qs)

        expected_xsls = ["first", "sécönd"]
        self.assertEqual(xsls, expected_xsls)

        # These assertions are rather brittle. Regrettably XPath and XSLT
        # quoted strings do not implement equality or proper hashing. Thus we
        # have to inspect repr and instanceof respectively.
        self.assertEqual(len(params), 2)
        self.assertIn("first", params)
        self.assertIn("sécönd", params)

        self.assertEqual(len(params["first"]), 3)
        self.assertIn(
            "_XSLTQuotedStringParam", repr(params["first"]["string-param"]))
        self.assertIn(
            "_XSLTQuotedStringParam", repr(params["first"]["string-param-2"]))
        self.assertIsInstance(
            params["first"]["xpath-param"], etree.XPath)

        self.assertEqual(len(params["sécönd"]), 0)
