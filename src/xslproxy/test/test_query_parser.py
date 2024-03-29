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

        xsls, paths, params = xsl.XslQueryStringParser().parse(qs)

        expected_xsls = ["first", "sécönd"]
        self.assertEqual(xsls, expected_xsls)

        expected_paths = {"first": "first", "sécönd": "sécönd"}
        self.assertEqual(paths, expected_paths)

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

    def test_query_string_with_alias(self):
        """
        Test query string parsing with parameters
        """

        # Generate with:
        # urllib.parse.unquote(urllib.parse.urlencode([
        #   ("xsl[]", "first"),
        #   ("xsl[]", "twö"),
        #   ("xa[twö]", "path/to/sécönd"),
        # ])).encode('utf-8')

        qs = b'xsl[]=first' + \
            b'&xsl[]=tw\xc3\xb6' + \
            b'&xa[tw\xc3\xb6]=path/to/s\xc3\xa9c\xc3\xb6nd'

        xsls, paths, params = xsl.XslQueryStringParser().parse(qs)

        expected_xsls = ["first", "twö"]
        self.assertEqual(xsls, expected_xsls)

        expected_paths = {"first": "first", "twö": "path/to/sécönd"}
        self.assertEqual(paths, expected_paths)

        expected_params = {"first": {}, "twö": {}}
        self.assertEqual(params, expected_params)
