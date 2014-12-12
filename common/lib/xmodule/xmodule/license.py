"""
Different types of licenses for content

This file contains a base license class as well as a some useful specific license classes, namely:
    - ARRLicense (All Rights Reserved License)
    - CCLicense (Creative Commons License)

The classes provide utility funcions for dealing with licensing, such as getting an image representation
of a license, a url to a page describing the specifics of the license, converting licenses to and from json
and storing some vital information about licenses, in particular the version.
"""
import requests
from cStringIO import StringIO
from lxml import etree
from django.utils.translation import ugettext as _

from django.conf import settings

from xblock.fields import JSONField

class License(JSONField):
    """
    Base License class
    """

    _default = None
    MUTABLE = False

    def __init__(self, license=None, version=None, *args, **kwargs):
        self.license = license
        self.version = version
        super(JSONField, self).__init__(*args, **kwargs)

    @property
    def img_url(self):
        """
        Stub property for img_url
        """

        return ""

    def img(self, big=False):
        """
        Return a piece of html with a reference to a license image
        """

        if not self.license:
            return _("No license.")

        if (big):
            img_size = "88x31"
        else:
            img_size = "80x15"

        img = "<img src='{img_url}/{img_size}.png' />".format(
            img_url=self.img_url,
            img_size=img_size
        )

        return img

    @property
    def html(self):
        """
        Return a piece of html that describes the license

        This method should be overridden in child classes to provide the desired html.
        """
        return u"<p>" + _("This resource is not licensed.") + u"</p>"

    def to_json(self, value):
        """
        Return a JSON representation of the license
        """
        if value is None:
            return None
        elif isinstance(value, License):
            return {"license": value.license, "version": value.version}
        else:
            raise TypeError("Cannot convert {!r} to json".format(value))


    def from_json(self, field):
        """
        Construct a new license object from a valid JSON representation
        """
        if field is None:
            return field
        elif not field or field is "":
            return None
        elif isinstance(field, basestring):
            if field == "ARR":
                return ARRLicense(field)
            elif field[0:5] == "CC-BY" or field == "CC0":
                return CCLicense(field)
            else:
                raise ValueError('Invalid license.')
        elif isinstance(field, dict):
            return parse_license(field['license'], field['version'])
        elif isinstance(field, License):
            return field
        else:
            raise ValueError('Invalid license.')

    enforce_type = from_json


class ARRLicense(License):
    """
    License class for an 'All rights reserved' license
    """

    def __init__(self, license, version=None, *args, **kwargs):
        super(ARRLicense, self).__init__(license, version, *args, **kwargs)

    @property
    def html(self):
        """
        Return a piece of html that descripts the license
        """
        phrase = _("All rights reserved")
        return "<div class='xmodule_licensable'><span class='license-icon license-arr'></span><span class='license-text'>{phrase}</span></div>".format(
            phrase=phrase
        )


class CCLicense(License):
    """
    License class for a Creative Commons license
    """

    def __init__(self, license, version=None, *args, **kwargs):
        super(CCLicense, self).__init__(license, version, *args, **kwargs)
        # If no version was set during initialization, we may assume the most recent version of a CC license and fetch that using the API
        if self.license and not self.version:
            data = CCLicense.get_cc_api_data(self.license)
            license_img = data.find(".//a")
            self.version = license_img.get("href").split("/")[-2]

    @property
    def img_url(self):
        if self.license == "CC0":
            license_string = "zero/1.0"
        else:
            # The Creative Commons License is stored as a string formatted in the following way: 'CC-BY-SA'. First it is converted to lowercase.
            # The split and join serve to remove the 'CC-' from the beginning of the license string.

            license = self.license.lower()
            attrs = license.split("-")
            attrs = attrs[1:]
            license = "-".join(attrs)

            license_string = "{license}/{version}/".format(
                license=license,
                version=self.version
            )

        img_url = "http://i.creativecommons.org/l/{license}".format(
            license=license_string
        )

        return img_url

    @property
    def html(self):
        """
        Return a piece of html that describes the license
        """

        licenseHtml = []
        licenseLink = []
        licenseText = []
        if 'BY' in self.license:
            licenseHtml.append("<span class='license-icon license-cc-by'></span>")
            licenseLink.append("by")
            licenseText.append(_("Attribution"))
        if 'NC' in self.license:
            licenseHtml.append("<span class='license-icon license-cc-nc'></span>")
            licenseLink.append("nc")
            licenseText.append(_("NonCommercial"))
        if 'SA' in self.license:
            licenseHtml.append("<span class='license-icon license-cc-sa'></span>")
            licenseLink.append("sa")
            licenseText.append(_("ShareAlike"))
        if 'ND' in self.license:
            licenseHtml.append("<span class='license-icon license-cc-nd'></span>")
            licenseLink.append("nd")
            licenseText.append(_("NonDerivatives"))

        phrase = _("Some rights reserved")
        return "<a rel='license' href='http://creativecommons.org/licenses/{licenseLink}/{version}/' data-tooltip='{description}' target='_blank' class='license'>{licenseHtml}<span class='license-text'>{phrase}</span></a>".format(
            description=self.description,
            version=self.version,
            licenseLink='-'.join(licenseLink),
            licenseText='-'.join(licenseText),
            licenseHtml=''.join(licenseHtml),
            phrase=phrase
        )

    @property
    def description(self):
        """
        Return a text that describes the license
        """

        # If the text hasn't been stored already, fetch it using the API
        if not hasattr(self, 'text'):
            data = CCLicense.get_cc_api_data(self.license)

            # Change the tag to be a paragraph
            data.tag = "p"

            # Remove the image from the API response
            img = data.find(".//a")
            img.getparent().remove(img)

            # And convert the html to a string
            self.text = etree.tostring(data, method="html")

        return self.text

    @staticmethod
    def cc_attributes_from_license(license):
        """
        Convert a license object to a tuple of values representing the relevant CC attributes

        The returning tuple contains a string and two boolean values which represent:
          - The license class, either 'zero' or 'standard'
          - Are commercial applications of the content allowed, 'yes', 'no' or 'only under the same license' (share alike)
          - Are derivatives of the content allowed, 'true' by default
        """
        commercial = "y"
        derivatives = "y"

        if license == "CC0":
            license_class = "zero"
        else:
            license_class = "standard"

            # Split the license attributes and remove the 'CC-' from the beginning of the string
            attrs = iter(license.split("-")[1:])

            # Then iterate over the remaining attributes that are set
            for s in attrs:
                if s == "SA":
                    derivatives = "sa"
                elif s == "NC":
                    commercial = "n"
                elif s == "ND":
                    derivatives = "n"

        return (license_class, commercial, derivatives)

    @staticmethod
    def get_cc_api_data(license):
        """
        Fetch data about a CC license using the API at creativecommons.org
        """
        (license_class,commercial,derivatives) = CCLicense.cc_attributes_from_license(license)

        # Format the url for the particular license
        url = "http://api.creativecommons.org/rest/1.5/license/{license_class}/get?commercial={commercial}&derivatives={derivatives}".format(
            license_class=license_class,
            commercial=commercial,
            derivatives=derivatives
        )

        # Fetch the license data
        xml_data = requests.get(url).content

        # Set up the response parser
        edx_xml_parser = etree.XMLParser(
            dtd_validation=False,
            load_dtd=False,
            remove_comments=True,
            remove_blank_text=True
        )

        # Parse the response file and extract the relevant data
        license_file = StringIO(xml_data.encode('ascii', 'ignore'))
        xml_obj = etree.parse(
            license_file,
            parser=edx_xml_parser
        ).getroot()
        data = xml_obj.find("html")

        return data

def parse_license(license, version=None):
    """
    Return a license object appropriate to the license

    This is a simple utility function to allowed for easy conversion between license strings and license objects. It
    accepts a license string and an optional license version and returns the corresponding license object. It also accounts
    for the license parameter already being a license object.
    """

    if license is None:
        return license
    elif license is "":
        return None
    elif isinstance(license, basestring):
        if license == "ARR":
            return ARRLicense(license,version)
        elif license[0:5] == "CC-BY" or license == "CC0":
            return CCLicense(license,version)
        else:
            raise ValueError('Invalid license.')
    elif isinstance(license, dict):
        return parse_license(license=license['license'], version=license['version'])
    elif isinstance(license, License):
        return license
    else:
        raise ValueError('Invalid license.')

