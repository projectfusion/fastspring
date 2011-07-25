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

"""Fastspring/Saasy client library.

"""

import re
import urllib
from xml.etree import ElementTree
import httplib2

class FastSpringRequestError(Exception):

    def __init__(self, response, content):
        self.code = response.status
        self.content = content
        Exception.__init__(self, u"%d %s" % (response.status, content))


class XMLResponse(object):
    """A really simple object for querying XML data returned from 
    fastspring requests.

    """
    def __init__(self, xml):
        self.xml = ElementTree.XML(xml)

    def __getitem__(self, key):
        attr = self.xml.find(key)
        return attr != None and attr.text or None    


class Subscription(XMLResponse):
    """A response from the get_subscription call.

    """
    def __init__(self, xml):
        super(Subscription, self).__init__(xml)

    @property
    def is_active(self):
        return self['status'] == 'active'


class FastSpring(object):
    """FastSpring interface class."""

    def __init__(self, company, username, password):
        """Create a new instance, set up auth parameters.

        """
        self.api_url_base = "https://api.fastspring.com/company/"+company
        self.store_url_base = "://sites.fastspring.com/"+company
        self.company = company
        self.username = username
        self.password = password
        self.auth_params = urllib.urlencode({"user": username, "pass": password})
        self.http = httplib2.Http()

    def get_subscription(self, reference):
        """Get subscription details."""
        url = "%s/subscription/%s?%s" % (self.api_url_base, reference, self.auth_params)
        response, content = self.http.request(url)
        if response.status != 200:
            raise FastSpringRequestError(response, content)
        return Subscription(content)

    def update_subscription(self, reference, product_path=None, quantity=None, no_end_date=None, coupon=None, proration=None):
        """Update subscription details.

        <subscription>
            <productPath>(optional)</productPath>
            <quantity>(optional)</quantity>
            <no-end-date>(optional)</no-end-date>
            <coupon>(optional)</coupon>
            <proration>true|false (optional)</proration>
        </subscription>

        """
        root = ElementTree.Element("subscription")
        if product_path is not None:
            ElementTree.SubElement(root, "productPath").text = product_path
        if quantity is not None:
            ElementTree.SubElement(root, "quantity").text = unicode(quantity)
        if no_end_date:
            ElementTree.SubElement(root, "no-end-date")
        if coupon is not None:
            ElementTree.SubElement(root, "coupon").text = coupon
        if proration is not None:
            ElementTree.SubElement(root, "proration").text = proration and "true" or "false"
        url = "%s/subscription/%s?%s" % (self.api_url_base, reference, self.auth_params)
        response, content = self.http.request(url, method="PUT", body=ElementTree.tostring(root))
        if response.status != 200:
            raise FastSpringRequestError(response, content)

    def delete_subscription(self, reference):
        """Delete a subscription.

        """
        url = "%s/subscription/%s?%s" % (self.api_url_base, reference, self.auth_params)
        response, content = self.http.request(url, method="DELETE")
        if response.status != 200:
            raise FastSpringRequestError(response, content)
        return Subscription(content)

    def get_localised_price(self, product_path, remote_addr, x_forwarded_for, accept_language):
        """Get a localisted price based on HTTP request headers.

        Returns a HTML-ified value (eg $10.00 or 10.00&eur;).

        """
        args = urllib.urlencode({"product_1_path": product_path,
                                 "user_remote_addr": remote_addr,
                                 "user_x_forwarded_for": x_forwarded_for,
                                 "user_accept_language": accept_language})
        url = "http%s/api/price?%s" % (self.store_url_base, args)
        response, content = self.http.request(url)
        if response.status != 200:
            raise FastSpringRequestError(response, content)
        m = re.search(r"^product_1_unit_html=(.+)$", content, re.M)
        if m:
            return m.group(1)
        else:
            return None

    def short_order_url(self, product_path, referrer=None, test_mode=False):
        """Get a link to an order page on the store for the given product.

        """
        url = "https%s/instant%s" % (self.store_url_base, product_path)
        args = {}
        if referrer is not None:
            args['referrer'] = referrer
        if test_mode != False:
            args['mode'] = 'test'
        if args:
            url = "%s?%s" % (url, urllib.urlencode(args))
        return url

