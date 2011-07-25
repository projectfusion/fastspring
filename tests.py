#!/usr/bin/env python
#
# Copyright (C) 2011 by OD Consultancy Ltd.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import unittest
import urlparse
from xml.etree import ElementTree
from mock import Mock

import fastspring

TEST_SUB_XML = """\
<?xml version="1.0"?>
<subscription>
  <status>active</status>
  <statusChanged>2010-08-15T00:00:00.000Z</statusChanged>
  <statusReason>completed</statusReason>
  <cancelable>true</cancelable>
  <reference/>
  <test>true</test>
  <referrer/>
  <sourceName/>
  <sourceKey/>
  <sourceCampaign/>
  <customer>
    <firstName/>
    <lastName/>
    <company/>
    <email/>
    <phoneNumber/>
  </customer>
  <customerUrl/>
  <productName/>
  <quantity>0</quantity>
  <nextPeriodDate>2010-08-15Z</nextPeriodDate>
  <end>2010-08-15Z</end>
</subscription>"""

TEST_LOCPRI_TEXT = """\
user_country=US
user_language=en
user_currency=USD
product_1_path=/myproductpath
product_1_quantity=1
product_1_unit_value=29.95
product_1_unit_currency=USD
product_1_unit_display=$29.95
product_1_unit_html=$29.95"""

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.fastspring = fastspring.FastSpring("test_company", "test_username", "test_password")
        self.fastspring.http.request = Mock()

    def mock_response(self, status_code):
        class Response(object):
            def __init__(self):
                self.status = status_code
        return Response()

    def test_init(self):
        # make sure internal vars are initialised properly
        self.assertEqual(self.fastspring.api_url_base, "https://api.fastspring.com/company/test_company")
        self.assertEqual(self.fastspring.store_url_base, "://sites.fastspring.com/test_company")
        self.assertEqual(self.fastspring.company, "test_company")
        self.assertEqual(self.fastspring.username, "test_username")
        self.assertEqual(self.fastspring.password, "test_password")
        self.assertEqual(self.fastspring.auth_params, "user=test_username&pass=test_password")

    def test_get_subscription(self):
        # make sure the correct URL is requested, that data is parsed
        # correctly and that errors are reported correctly
        self.fastspring.http.request.return_value = (self.mock_response(200), TEST_SUB_XML)
        sub = self.fastspring.get_subscription("test_reference")
        self.assertEqual(sub["status"], "active")
        self.assertEqual(sub["statusChanged"], "2010-08-15T00:00:00.000Z")
        self.assertEqual(sub["end"], "2010-08-15Z")
        self.assertEqual(1, self.fastspring.http.request.call_count)
        args, kwargs = self.fastspring.http.request.call_args
        self.assertEqual(kwargs, {})
        self.assertEqual(len(args), 1)
        url = urlparse.urlparse(args[0])
        self.assertEqual(url.scheme, "https")
        self.assertEqual(url.netloc, "api.fastspring.com")
        self.assertEqual(url.path, "/company/test_company/subscription/test_reference")
        qs = urlparse.parse_qs(url.query)
        self.assertEqual(qs['user'][0], "test_username")
        self.assertEqual(qs['pass'][0], "test_password")
        self.fastspring.http.request.return_value = (self.mock_response(404), "Not found")
        self.assertRaises(fastspring.FastSpringRequestError, self.fastspring.get_subscription, "test_reference")

    def test_update_subscription(self):
        # make sure the correct URL is requested and that errors are
        # reported correctly
        self.fastspring.http.request.return_value = (self.mock_response(200), "")
        # test with full arguments
        self.fastspring.update_subscription("test_reference", product_path="/test_product", quantity=1, no_end_date=True, coupon="test_coupon", proration=True)
        self.assertEqual(1, self.fastspring.http.request.call_count)
        args, kwargs = self.fastspring.http.request.call_args
        self.assertEqual(len(kwargs.keys()), 2)
        self.assertEqual(kwargs["method"], "PUT")
        xml = ElementTree.XML(kwargs["body"])
        self.assertEqual(xml.find("productPath").text, "/test_product")
        self.assertEqual(xml.find("quantity").text, "1")
        self.assertEqual(xml.find("no-end-date").text, None)
        self.assertEqual(xml.find("coupon").text, "test_coupon")
        self.assertEqual(xml.find("proration").text, "true")
        self.assertEqual(len(args), 1)
        url = urlparse.urlparse(args[0])
        self.assertEqual(url.scheme, "https")
        self.assertEqual(url.netloc, "api.fastspring.com")
        self.assertEqual(url.path, "/company/test_company/subscription/test_reference")
        qs = urlparse.parse_qs(url.query)
        self.assertEqual(qs['user'][0], "test_username")
        self.assertEqual(qs['pass'][0], "test_password")
        # test with partial arguments
        self.fastspring.update_subscription("test_reference", product_path="/test_product")
        self.assertEqual(2, self.fastspring.http.request.call_count)
        args, kwargs = self.fastspring.http.request.call_args
        self.assertEqual(len(kwargs.keys()), 2)
        self.assertEqual(kwargs["method"], "PUT")
        xml = ElementTree.XML(kwargs["body"])
        self.assertEqual(xml.find("productPath").text, "/test_product")
        self.assertEqual(xml.find("quantity"), None)
        self.assertEqual(xml.find("no-end-date"), None)
        self.assertEqual(xml.find("coupon"), None)
        self.assertEqual(xml.find("proration"), None)
        self.assertEqual(len(args), 1)
        url = urlparse.urlparse(args[0])
        self.assertEqual(url.scheme, "https")
        self.assertEqual(url.netloc, "api.fastspring.com")
        self.assertEqual(url.path, "/company/test_company/subscription/test_reference")
        qs = urlparse.parse_qs(url.query)
        self.assertEqual(qs['user'][0], "test_username")
        self.assertEqual(qs['pass'][0], "test_password")
        # test error handling
        self.fastspring.http.request.return_value = (self.mock_response(404), "Not found")
        self.assertRaises(fastspring.FastSpringRequestError, self.fastspring.update_subscription, "test_reference", product_path="/test_product")

    def test_delete_subscription(self):
        # make sure the correct URL is requested, that data is parsed
        # correctly and that errors are reported correctly
        self.fastspring.http.request.return_value = (self.mock_response(200), TEST_SUB_XML)
        sub = self.fastspring.delete_subscription("test_reference")
        self.assertEqual(sub["status"], "active")
        self.assertEqual(sub["statusChanged"], "2010-08-15T00:00:00.000Z")
        self.assertEqual(sub["end"], "2010-08-15Z")
        self.assertEqual(1, self.fastspring.http.request.call_count)
        args, kwargs = self.fastspring.http.request.call_args
        self.assertEqual(len(kwargs.keys()), 1)
        self.assertEqual(kwargs["method"], "DELETE")
        self.assertEqual(len(args), 1)
        url = urlparse.urlparse(args[0])
        self.assertEqual(url.scheme, "https")
        self.assertEqual(url.netloc, "api.fastspring.com")
        self.assertEqual(url.path, "/company/test_company/subscription/test_reference")
        qs = urlparse.parse_qs(url.query)
        self.assertEqual(qs['user'][0], "test_username")
        self.assertEqual(qs['pass'][0], "test_password")
        # test error handling
        self.fastspring.http.request.return_value = (self.mock_response(404), "Not found")
        self.assertRaises(fastspring.FastSpringRequestError, self.fastspring.delete_subscription, "test_reference")

    def test_get_localised_price(self):
        # make sure the correct URL is requested, that data is parsed
        # correctly and errors are reported correctly
        self.fastspring.http.request.return_value = (self.mock_response(200), TEST_LOCPRI_TEXT)
        price = self.fastspring.get_localised_price("/test_product", "127.0.0.1", "127.0.0.2", "en")
        self.assertEqual(price, "$29.95")
        self.assertEqual(1, self.fastspring.http.request.call_count)
        args, kwargs = self.fastspring.http.request.call_args
        self.assertEqual(kwargs, {})
        self.assertEqual(len(args), 1)
        url = urlparse.urlparse(args[0])
        self.assertEqual(url.scheme, "http")
        self.assertEqual(url.netloc, "sites.fastspring.com")
        self.assertEqual(url.path, "/test_company/api/price")
        qs = urlparse.parse_qs(url.query)
        self.assertEqual(qs['product_1_path'][0], "/test_product")
        self.assertEqual(qs['user_remote_addr'][0], "127.0.0.1")
        self.assertEqual(qs['user_x_forwarded_for'][0], "127.0.0.2")
        self.assertEqual(qs['user_accept_language'][0], "en")
        # test error handling
        self.fastspring.http.request.return_value = (self.mock_response(404), "Not found")
        self.assertRaises(fastspring.FastSpringRequestError, self.fastspring.get_localised_price, "/test_product", "127.0.0.1", "127.0.0.2", "en")

    def test_short_order_url(self):
        # make sure the correct URL is returned
        self.assertEqual(self.fastspring.short_order_url("/test_product"), "https://sites.fastspring.com/test_company/instant/test_product")
        self.assertEqual(self.fastspring.short_order_url("/test_product", referrer="test_referrer"), "https://sites.fastspring.com/test_company/instant/test_product?referrer=test_referrer")
        self.assertEqual(self.fastspring.short_order_url("/test_product", test_mode=True), "https://sites.fastspring.com/test_company/instant/test_product?mode=test")
        self.assertEqual(self.fastspring.short_order_url("/test_product", referrer="test_referrer", test_mode=True), "https://sites.fastspring.com/test_company/instant/test_product?referrer=test_referrer&mode=test")

if __name__ == '__main__':
    unittest.main()
