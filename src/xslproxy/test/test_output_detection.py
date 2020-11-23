import unittest

from defusedxml.lxml import fromstring as defusedxml_fromstring

from xslproxy import xsl


class XslQueryParserTestCase(unittest.TestCase):

    def test_output_detection_default_fallback(self):
        """
        Test output detection for a stylesheet without output declaration
        """

        stylesheet = defusedxml_fromstring("""
            <xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns="http://www.w3.org/TR/xhtml1/strict">
            </xsl:stylesheet>
        """)

        result = xsl.XslOutputMethodDetection().detect(stylesheet)
        self.assertEqual(result, "xml")

    def test_output_detection_explicit_xml(self):
        """
        Test output detection for a stylesheet which has method set to xml
        """

        stylesheet = defusedxml_fromstring("""
            <xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns="http://www.w3.org/TR/xhtml1/strict">
                <xsl:output method="xml" indent="yes" />
            </xsl:stylesheet>
        """)

        result = xsl.XslOutputMethodDetection().detect(stylesheet)
        self.assertEqual(result, "xml")

    def test_output_detection_explicit_html(self):
        """
        Test output detection for a stylesheet which has method set to html
        """

        stylesheet = defusedxml_fromstring("""
            <xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns="http://www.w3.org/TR/xhtml1/strict">
                <xsl:output method="html" indent="yes" />
            </xsl:stylesheet>
        """)

        result = xsl.XslOutputMethodDetection().detect(stylesheet)
        self.assertEqual(result, "html")

    def test_output_detection_explicit_text(self):
        """
        Test output detection for a stylesheet which has method set to text
        """

        stylesheet = defusedxml_fromstring("""
            <xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns="http://www.w3.org/TR/xtext1/strict">
                <xsl:output method="text" indent="yes" />
            </xsl:stylesheet>
        """)

        result = xsl.XslOutputMethodDetection().detect(stylesheet)
        self.assertEqual(result, "text")
