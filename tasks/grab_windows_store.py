"""
Credits:
https://github.com/ThomasPe/MS-Store-API
https://github.com/ThomasPe/MS-Store-API/issues/9
https://github.com/LSPosed/MagiskOnWSALocal/blob/main/scripts/generateWSALinks.py
https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-wusp/b8a2ad1d-11c4-4b64-a2cc-12771fcb079b

"""

import atexit
import base64
import json
import tempfile
import textwrap
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

import requests

APPS_TO_CHECK = {
    "9NP83LWLPZ9K": "Apple Devices Preview",
    "9PFHDD62MXS1": "Apple Music Preview",
    "9NM4T8B9JQZ1": "Apple TV Preview",
    # "9PKTQ5699M62": "iCloud",  # Currently unsupported because there's multiple architectures
    # "9PB2MZ1ZMB1S": "iTunes",  # Has iTunes, iPodVoiceOver, and MobileDeviceSupport
}
release_types = {"Retail": "retail", "Release Preview": "RP", "Insider Slow": "WIS", "Insider Fast": "WIF"}
RELEASE_TYPE = release_types["Retail"]


windows_store_session = requests.Session()
WINDOWS_STORE_SEARCH_PRODUCTS_V9 = "https://storeedgefd.dsx.mp.microsoft.com/v9.0/search?appVersion=22203.1401.0.0&market=US&locale=en-US&deviceFamily=windows.desktop&query={query}&mediaType=apps&productFamilies=apps"  # pylint: disable=line-too-long  # noqa: E501
WINDOWS_STORE_GET_PRODUCTS_V9 = (
    "https://storeedgefd.dsx.mp.microsoft.com/v9.0/products/{product_id}?market=US&locale=en-US&deviceFamily=windows.desktop"
)


def get_search_results(query: str):
    response = windows_store_session.get(WINDOWS_STORE_SEARCH_PRODUCTS_V9.format(query=query))
    # Path("tmp/search_results.json").write_bytes(response.content)

    response.raise_for_status()

    data = response.json()
    apps = []
    for result in data["Payload"]["HighlightedResults"] + data["Payload"]["SearchResults"]:
        print(result)
        app_info = {
            "name": result["Title"],
            "publisher": result["PublisherName"],
            "product_id": result["ProductId"],
            "description": result.get("LongDescription", result.get("Description")),
        }

        apps.append(app_info)

    return apps


def print_search_results(results: list[dict]):
    for result in results:
        print(f"{result['name']} ({result['publisher']}) - {result['product_id']}")
        tab_char = "\t"
        print(f"{textwrap.indent(result['description'], tab_char)}\n")


def get_full_details(product_id: str):
    response = windows_store_session.get(WINDOWS_STORE_GET_PRODUCTS_V9.format(product_id=product_id))
    # Path("tmp/get_products.json").write_bytes(response.content)

    response.raise_for_status()

    data = response.json()
    product_data = data["Payload"]
    for sku in data["Payload"]["Skus"]:
        if sku["SkuType"] == "full":
            fulfillment_data = json.loads(sku["FulfillmentData"])

            return {
                "name": product_data["Title"],
                "publisher": product_data["PublisherName"],
                "product_id": product_data["ProductId"],
                "description": product_data.get("LongDescription", product_data.get("Description")),
                "last_update_date": product_data["LastUpdateDateUtc"],
                "revision_id": product_data["RevisionId"],
                "package_family_names": product_data["PackageFamilyNames"],
                "wu_category_id": fulfillment_data["WuCategoryId"],
            }

    raise ValueError("No full SKU found")


# SOAP garbage...

# TODO: Use if statements/exceptions instead of asserts

WINDOWS_UPDATE_CERT = """
-----BEGIN CERTIFICATE-----
MIIGmzCCBIOgAwIBAgITMwAAAcrn0tzFq9ZvpAAAAAAByjANBgkqhkiG9w0BAQsF
ADCBhDELMAkGA1UEBhMCVVMxEzARBgNVBAgTCldhc2hpbmd0b24xEDAOBgNVBAcT
B1JlZG1vbmQxHjAcBgNVBAoTFU1pY3Jvc29mdCBDb3Jwb3JhdGlvbjEuMCwGA1UE
AxMlTWljcm9zb2Z0IFVwZGF0ZSBTZWN1cmUgU2VydmVyIENBIDIuMTAeFw0yMjEx
MTcwMDIwMDFaFw0yMzExMTcwMDIwMDFaMHQxCzAJBgNVBAYTAlVTMQswCQYDVQQI
EwJXQTEQMA4GA1UEBxMHUmVkbW9uZDESMBAGA1UEChMJTWljcm9zb2Z0MQwwCgYD
VQQLEwNEU1AxJDAiBgNVBAMMGyouZGVsaXZlcnkubXAubWljcm9zb2Z0LmNvbTCC
ASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAMy8Dc9axvMR1mHtlNv1vflp
qXG6dZ2c7YWfuIP4D6JogbxtNtG/92B8ZMubIqSeVKqHMdvFvCXqVwnWJYlK4sI8
bh/8Jpo5CcFBPa57o+ZuNFSqQ9uIU12QeaKOCThW/pcRQhIeD56laNmo7Ekih7II
bhqNV7IN7JWxCgXPmTQ6b1uP5SSDvryiBF/drum1dS+xwC5un9JboS5L6d6LuAGF
NTc61jFOeYrOEBI8OztZN/42jKz2DtooNb/lxualFbNLKd8fNDqMKsyKdToZu4tc
IwZGsZcQGItcWz1N09lhWrLBGHC9fF8t3yi4yTFJyddawZcsinctEoPcBjnufcUC
AwEAAaOCAhMwggIPMA4GA1UdDwEB/wQEAwIE8DATBgNVHSUEDDAKBggrBgEFBQcD
ATAMBgNVHRMBAf8EAjAAMIG4BgNVHREEgbAwga2CGyouZGVsaXZlcnkubXAubWlj
cm9zb2Z0LmNvbYIjKi5iYWNrZW5kLmRlbGl2ZXJ5Lm1wLm1pY3Jvc29mdC5jb22C
HyouZmUzLmRlbGl2ZXJ5Lm1wLm1pY3Jvc29mdC5jb22CJyouYmFja2VuZC5mZTMu
ZGVsaXZlcnkubXAubWljcm9zb2Z0LmNvbYIfKi5mZTYuZGVsaXZlcnkubXAubWlj
cm9zb2Z0LmNvbTAdBgNVHQ4EFgQU7fvTm+jWBvwNeD28CJ7bIprDoMUwHwYDVR0j
BBgwFoAU0vI9hHSGG1CFql3lpQea8EfTLmkwaAYDVR0fBGEwXzBdoFugWYZXaHR0
cDovL3d3dy5taWNyb3NvZnQuY29tL3BraW9wcy9jcmwvTWljcm9zb2Z0JTIwVXBk
YXRlJTIwU2VjdXJlJTIwU2VydmVyJTIwQ0ElMjAyLjEuY3JsMHUGCCsGAQUFBwEB
BGkwZzBlBggrBgEFBQcwAoZZaHR0cDovL3d3dy5taWNyb3NvZnQuY29tL3BraW9w
cy9jZXJ0cy9NaWNyb3NvZnQlMjBVcGRhdGUlMjBTZWN1cmUlMjBTZXJ2ZXIlMjBD
QSUyMDIuMS5jcnQwDQYJKoZIhvcNAQELBQADggIBAHXlnFxZsN3dESS2Woi1jDy8
NXa058VjS0qa8xMEygkxtaMo45ikCbSUpcj04T9P02vQb2jFekTCvtfmP2mtx7o0
693Cu88+5YXOw/Zd7qn5sxi8kt9godVUca1LFV0fCi5tyZ/VwCGkJTgf4tWwqY4a
StLtd0rf4/8zUKeXO/1xPETZoF/42F8d/nSpGraKBZdKZ2y7YXOHsjdP9mcKTZuC
Q1pPP0lxraz5ust76ldD+ZGkUiNNv8S0B4qFs5Z47C+Pe60aSqbrGH3pZsqvbX4M
UdvzhzG4sgh47v4oLFjwtMNFFD8LDRp1vCn/ujexVZjakeAu9MlHrU9hFAHXWVlC
6hgFpxMz/k3DGHLrnC741U2PAq9D/gOUa5ToZrfPdWpkkFhUxRPr3GcERx9mzNi4
KfI0epsGS0mPrm1DfIGy0feXVHpD8ovQILVRrUy6SNMFcT5XZkoTVho1fPQ1341F
qm7EPqwBswgBrWkm6SHdvg4UYznyqqNl9eJJQalQTNSqNjYh3ZttnQalG57bDr9f
sMvA60FUhoo78YRHf4AvVp7SakNSqK8x1CQpQ2zJBxPqX1dU3YCPHTcmzMXykzUD
wgIfGiUU9LejP6WD85DyqKpfFXFqj8cTmN0+l0mUGM2DCKBExI2BeGqaUhDMAGAA
J4KQov+q6I1F7uIVEEOt
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIHADCCBOigAwIBAgITMwAAAAq4kaLIClCl3wAAAAAACjANBgkqhkiG9w0BAQsF
ADCBiDELMAkGA1UEBhMCVVMxEzARBgNVBAgTCldhc2hpbmd0b24xEDAOBgNVBAcT
B1JlZG1vbmQxHjAcBgNVBAoTFU1pY3Jvc29mdCBDb3Jwb3JhdGlvbjEyMDAGA1UE
AxMpTWljcm9zb2Z0IFJvb3QgQ2VydGlmaWNhdGUgQXV0aG9yaXR5IDIwMTEwHhcN
MTIwNjIxMTczMzM1WhcNMjcwNjIxMTc0MzM1WjCBhDELMAkGA1UEBhMCVVMxEzAR
BgNVBAgTCldhc2hpbmd0b24xEDAOBgNVBAcTB1JlZG1vbmQxHjAcBgNVBAoTFU1p
Y3Jvc29mdCBDb3Jwb3JhdGlvbjEuMCwGA1UEAxMlTWljcm9zb2Z0IFVwZGF0ZSBT
ZWN1cmUgU2VydmVyIENBIDIuMTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoC
ggIBAIsV6r17t2cxpIcOFIqSCXjB1Wi28ppZ4H/IGmdG3jGaAqrI50dJ6ak6h0yF
/jwuG0cERatWEbtguFI2idurX8gorvMbOaC/BqJk2azmI0PNaZWQ5a+Ib5jb+yLC
ByxI8UyFA1pqzUBh4SIaIuObKz3s44ubK8xVZYEUuszhiv7QvDonFzpHQfu4MPEE
MtHVOW56RssyKuFzdos1OhXYjpSCZni+kXwLowGugOMJhCxpK9mMJNTyPzUHd+Gf
41RDX+yK/SRYT6NUYNIAX3VEK9Lvf7s+tl77d/vhnmalQB8xPNDjMgS4p+ulEt9w
Gmrwo1IQuFjDiH2kszH5f2FTri3Mgjr2SotDZPLMk93g1RQuSAZmEED2I+efOVC4
dyESKUB7/Hf0MNNeujezZyA7ih3/mXg5ppuFz61acjBRKlmNKBc1MnqUHbBSBX9K
BuBNfeqW1SsMoy2JWrVcKqvEtqbTX2mfEEMA/aecmMO6S7vo2CM8c7OBFjY9sbxh
msAS3TC0kLffSK3YF2oDMqdgW57PGm14ZVSP01KO5W6E8sq43xkd2rT6KZ7IHqPW
18QwPsHbffy5eQbgumeadF3cryR7ElIt1VccANw9mqA+km1DWoL3tYb+nlS0MMKd
YNFPT903Vx0chN5ej9CQXHBu4zq3Rkmz7wF5YJVEO9gZ0CJlAgMBAAGjggFjMIIB
XzAQBgkrBgEEAYI3FQEEAwIBADAdBgNVHQ4EFgQU0vI9hHSGG1CFql3lpQea8EfT
LmkwGQYJKwYBBAGCNxQCBAweCgBTAHUAYgBDAEEwCwYDVR0PBAQDAgGGMBIGA1Ud
EwEB/wQIMAYBAf8CAQAwHwYDVR0jBBgwFoAUci06AjGQQ7kUBU7h6qfHMdEjiTQw
WgYDVR0fBFMwUTBPoE2gS4ZJaHR0cDovL2NybC5taWNyb3NvZnQuY29tL3BraS9j
cmwvcHJvZHVjdHMvTWljUm9vQ2VyQXV0MjAxMV8yMDExXzAzXzIyLmNybDBeBggr
BgEFBQcBAQRSMFAwTgYIKwYBBQUHMAKGQmh0dHA6Ly93d3cubWljcm9zb2Z0LmNv
bS9wa2kvY2VydHMvTWljUm9vQ2VyQXV0MjAxMV8yMDExXzAzXzIyLmNydDATBgNV
HSUEDDAKBggrBgEFBQcDATANBgkqhkiG9w0BAQsFAAOCAgEAopvuA2tH2+meSVsn
VatGbRha0QgVj4Saq5ZlNJW0Qpyf4pRyuZT+KLK2/Ia6ZzUugrtLAECro+hIEB5K
29S+pnY1nzSMn+lSZJwGWfRZTWn466g21wKFMInPpO3QB8yfzr2zwniissTh8Jkn
8Uejsz/EkGU520E3FCT26dlU1YtzHnrcZ7d8qp4tLFEVeSsrxkqpYJQxalJIZ3HH
uhOG3BQLmLtJDs822W1knAR6c+iYuLDbJ9o8TnOY9/lIWy8Vv2z3i+LEn27O7QSl
vTZHyCgFJMgjhELOSLliGhA3411RX8kyCE9AJ1OLufdcejOYwMG0POpmrj3s/Q5n
+Bfm5JQHaGGCUy7XfKMRbyYJejjcC1YtLS5HVxBf/Smh7nruCYIpDimr8AIgJCVz
ekbVxTHzuSYdXLZgnpUzu71MgFGSBh5DAHaErUmwwztK/TIyak9zwodWouV+2clp
HYgCWASmHOkRysH6T3n46pDmexplqG5dGM5QNrCjn5u1ptgVdDPR1LGHTT+KGT+F
45owrOFOwUOuz2H6RFUPgwPkCOYnK4bM17tdlaQ4DrtghSqL03ZaPFdASXHa+fZB
1ro0E6c8fv9vqaf7NvhIQE+BepDH87/f3gCGCzZ0pTNnbRH2k2VCc4CbaWZRKWg8
5c95ZPsdlHeynrIjVZ76ubrfiuM=
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIF7TCCA9WgAwIBAgIQP4vItfyfspZDtWnWbELhRDANBgkqhkiG9w0BAQsFADCB
iDELMAkGA1UEBhMCVVMxEzARBgNVBAgTCldhc2hpbmd0b24xEDAOBgNVBAcTB1Jl
ZG1vbmQxHjAcBgNVBAoTFU1pY3Jvc29mdCBDb3Jwb3JhdGlvbjEyMDAGA1UEAxMp
TWljcm9zb2Z0IFJvb3QgQ2VydGlmaWNhdGUgQXV0aG9yaXR5IDIwMTEwHhcNMTEw
MzIyMjIwNTI4WhcNMzYwMzIyMjIxMzA0WjCBiDELMAkGA1UEBhMCVVMxEzARBgNV
BAgTCldhc2hpbmd0b24xEDAOBgNVBAcTB1JlZG1vbmQxHjAcBgNVBAoTFU1pY3Jv
c29mdCBDb3Jwb3JhdGlvbjEyMDAGA1UEAxMpTWljcm9zb2Z0IFJvb3QgQ2VydGlm
aWNhdGUgQXV0aG9yaXR5IDIwMTEwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIK
AoICAQCygEGqNThNE3IyaCJNuLLx/9VSvGzH9dJKjDbu0cJcfoyKrq8TKG/Ac+M6
ztAlqFo6be+ouFmrEyNozQwph9FvgFyPRH9dkAFSWKxRxV8qh9zc2AodwQO5e7BW
6KPeZGHCnvjzfLnsDbVU/ky2ZU+I8JxImQxCCwl8MVkXeQZ4KI2JOkwDJb5xalwL
54RgpJki49KvhKSn+9GY7Qyp3pSJ4Q6g3MDOmT3qCFK7VnnkH4S6Hri0xElcTzFL
h93dBWcmmYDgcRGjuKVB4qRTufcyKYMME782XgSzS0NHL2vikR7TmE/dQgfI6B0S
/Jmpaz6SfsjWaTr8ZL22CZ3K/QwLopt3YEsDlKQwaRLWQi3BQUzK3Kr9j1uDRprZ
/LHR47PJf0h6zSTwQY9cdNCssBAgBkm3xy0hyFfj0IbzA2j70M5xwYmZSmQBbP3s
MJHPQTySx+W6hh1hhMdfgzlirrSSL0fzC/hV66AfWdC7dJse0Hbm8ukG1xDo+mTe
acY1logC8Ea4PyeZb8txiSk190gWAjWP1Xl8TQLPX+uKg09FcYj5qQ1OcunCnAfP
SRtOBA5jUYxe2ADBVSy2xuDCZU7JNDn1nLPEfuhhbhNfFcRf2X7tHc7uROzLLoax
7Dj2cO2rXBPB2Q8Nx4CyVe0096yb5MPa50c8prWPMd/FS6/r8QIDAQABo1EwTzAL
BgNVHQ8EBAMCAYYwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQUci06AjGQQ7kU
BU7h6qfHMdEjiTQwEAYJKwYBBAGCNxUBBAMCAQAwDQYJKoZIhvcNAQELBQADggIB
AH9yzw+3xRXbm8BJyiZb/p4T5tPw0tuXX/JLP02zrhmu7deXoKzvqTqjwkGw5biR
nhOBJAPmCf0/V0A5ISRW0RAvS0CpNoZLtFNXmvvxfomPEf4YbFGq6O0JlbXlccmh
6Yd1phV/yX43VF50k8XDZ8wNT2uoFwxtCJJ+i92Bqi1wIcM9BhS7vyRep4TXPw8h
Ir1LAAbblxzYXtTFC1yHblCk6MM4pPvLLMWSZpuFXst6bJN8gClYW1e1QGm6CHmm
ZGIVnYeWRbVmIyADixxzoNOieTPgUFmG2y/lAiXqcyqfABTINseSO+lOAOzYVgm5
M0kS0lQLAausR7aRKX1MtHWAUgHoyoL2n8ysnI8X6i8msKtyrAv+nlEex0NVZ09R
s1fWtuzuUrc66U7h14GIvE+OdbtLqPA1qibUZ2dJsnBMO5PcHd94kIZysjik0dyS
TclY6ysSXNQ7roxrsIPlAT/4CTL2kzU0Iq/dNw13CYArzUgA8YyZGUcFAenRv9FO
0OYoQzeZpApKCNmacXPSqs0xE2N2oTdvkjgefRI8ZjLny23h/FKJ3crWZgWalmG+
oijHHKOnNlA8OqTfSm7mhzvO6/DggTedEzxSjr25HTTGHdUKaj2YKXCMiSrRq4IQ
SB/c9O+lxbtVGjhjhE63bK2VVOxlIhBJF7jAHscPrFRH
-----END CERTIFICATE-----
""".strip()

windows_update_session = requests.Session()
temp_cert = tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False)
temp_cert.write(WINDOWS_UPDATE_CERT)
temp_cert.flush()
atexit.register(temp_cert.close)
windows_update_session.verify = temp_cert.name
windows_update_session.headers.update(
    {
        "Content-Type": "application/soap+xml; charset=utf-8",
    }
)

# TODO: Standardize the body, and maybe make it with ET
# TODO: Maybe pull out the header into a separate variable?

WINDOWS_UPDATE_URL = "https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx"
WINDOWS_UPDATE_SECURED_URL = "https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx/secured"

GET_COOKIE_BODY = """
<Envelope xmlns="http://www.w3.org/2003/05/soap-envelope">
    <Header xmlns:a="http://www.w3.org/2005/08/addressing"
        xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <a:Action>http://www.microsoft.com/SoftwareDistribution/Server/ClientWebService/GetCookie</a:Action>
        <a:To>https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx</a:To>
        <Security xmlns="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
            xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
            <u:Timestamp>
                <u:Created>2023-09-08T00:00:00.000Z</u:Created>
                <u:Expires>2023-09-08T00:00:00.001Z</u:Expires>
            </u:Timestamp>
            <WindowsUpdateTicketsToken u:id="ClientMSA"
                xmlns="http://schemas.microsoft.com/msus/2014/10/WindowsUpdateAuthorization">
                <TicketType Name="MSA" Version="1.0" Policy="MBI_SSL">
                    <user>{user}</user>
                </TicketType>
            </WindowsUpdateTicketsToken>
        </Security>
    </Header>
    <Body>
        <GetCookie xmlns="http://www.microsoft.com/SoftwareDistribution/Server/ClientWebService">
            <oldCookie>
            </oldCookie>
            <lastChange>2015-10-21T17:01:07.1472913Z</lastChange>
            <currentTime>2017-12-02T00:16:15.217Z</currentTime>
            <protocolVersion>1.40</protocolVersion>
        </GetCookie>
    </Body>
</Envelope>
""".strip()

NAMESPACES = {
    "s": "http://www.w3.org/2003/05/soap-envelope",
    "a": "http://www.w3.org/2005/08/addressing",
    "u": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "ms": "http://www.microsoft.com/SoftwareDistribution/Server/ClientWebService",
}


def get_cookie(user: Optional[str] = None):
    response = windows_update_session.post(
        WINDOWS_UPDATE_URL,
        data=GET_COOKIE_BODY.format(user=user or ""),
    )

    try:
        response.raise_for_status()
    except requests.HTTPError:
        print(response.text)
        raise

    root = ET.fromstring(response.content)
    cookie_wrapper = root.find("./s:Body/ms:GetCookieResponse/ms:GetCookieResult", namespaces=NAMESPACES)
    if cookie_wrapper is None:
        raise RuntimeError("Could not get cookie")

    cookie_data = cookie_wrapper.find("./ms:EncryptedData", namespaces=NAMESPACES)
    expiration = cookie_wrapper.find("./ms:Expiration", namespaces=NAMESPACES)

    if expiration is None or expiration.text is None:
        raise RuntimeError("Could not get cookie expiration")
    if cookie_data is None or cookie_data.text is None:
        raise RuntimeError("Could not get cookie data")

    return cookie_data.text, expiration.text


GET_INFO_BODY = """
<Envelope xmlns="http://www.w3.org/2003/05/soap-envelope">
    <Header xmlns:a="http://www.w3.org/2005/08/addressing"
        xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <a:Action>http://www.microsoft.com/SoftwareDistribution/Server/ClientWebService/SyncUpdates</a:Action>
        <a:To>https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx</a:To>
        <Security xmlns="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
            xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
            <u:Timestamp>
                <u:Created>2023-09-08T00:00:00.000Z</u:Created>
                <u:Expires>2023-09-08T00:00:00.001Z</u:Expires>
            </u:Timestamp>
            <WindowsUpdateTicketsToken u:id="ClientMSA"
                xmlns="http://schemas.microsoft.com/msus/2014/10/WindowsUpdateAuthorization">
                <TicketType Name="MSA" Version="1.0" Policy="MBI_SSL">
                    <user>{user}</user>
                </TicketType>
            </WindowsUpdateTicketsToken>
        </Security>
    </Header>
    <Body>
        <SyncUpdates xmlns="http://www.microsoft.com/SoftwareDistribution/Server/ClientWebService">
            <cookie>
                <Expiration>{expiration}</Expiration>
                <EncryptedData>{cookie}</EncryptedData>
            </cookie>
            <parameters>
                <ExpressQuery>false</ExpressQuery>
                <InstalledNonLeafUpdateIDs>
                    <int>1</int>
                    <int>2</int>
                    <int>11</int>
                    <int>23110993</int>
                </InstalledNonLeafUpdateIDs>
                <OtherCachedUpdateIDs>
                </OtherCachedUpdateIDs>
                <SkipSoftwareSync>false</SkipSoftwareSync>
                <NeedTwoGroupOutOfScopeUpdates>true</NeedTwoGroupOutOfScopeUpdates>
                <FilterAppCategoryIds>
                    <CategoryIdentifier>
                        <Id>{category_id}</Id>
                    </CategoryIdentifier>
                </FilterAppCategoryIds>
                <TreatAppCategoryIdsAsInstalled>true</TreatAppCategoryIdsAsInstalled>
                <AlsoPerformRegularSync>false</AlsoPerformRegularSync>
                <ComputerSpec/>
                <ExtendedUpdateInfoParameters>
                    <XmlUpdateFragmentTypes>
                        <XmlUpdateFragmentType>Extended</XmlUpdateFragmentType>
                    </XmlUpdateFragmentTypes>
                    <Locales>
                        <string>en-US</string>
                        <string>en</string>
                    </Locales>
                </ExtendedUpdateInfoParameters>
                <ClientPreferredLanguages>
                    <string>en-US</string>
                </ClientPreferredLanguages>
                <ProductsParameters>
                    <SyncCurrentVersionOnly>false</SyncCurrentVersionOnly>
                    <DeviceAttributes>BranchReadinessLevel=CB;CurrentBranch=rs_prerelease;OEMModel=Virtual Machine;FlightRing={release_type};AttrDataVer=21;SystemManufacturer=Microsoft Corporation;InstallLanguage=en-US;OSUILocale=en-US;InstallationType=Client;FlightingBranchName=external;FirmwareVersion=Hyper-V UEFI Release v2.5;SystemProductName=Virtual Machine;OSSkuId=48;FlightContent=Branch;App=WU;OEMName_Uncleaned=Microsoft Corporation;AppVer=10.0.22621.900;OSArchitecture=AMD64;SystemSKU=None;UpdateManagementGroup=2;IsFlightingEnabled=1;IsDeviceRetailDemo=0;TelemetryLevel=3;OSVersion=10.0.22621.900;DeviceFamily=Windows.Desktop;</DeviceAttributes>
                    <CallerAttributes>Interactive=1;IsSeeker=0;</CallerAttributes>
                    <Products/>
                </ProductsParameters>
            </parameters>
        </SyncUpdates>
    </Body>
</Envelope>
""".strip()


def parse_wrapped_xml(xml: ET.Element) -> ET.Element:
    wrapped_xml = xml.find("./ms:Xml", namespaces=NAMESPACES)
    if wrapped_xml is None:
        raise ValueError("Expected wrapped XML")

    unwrapped = ET.fromstring(
        f'<root:ParsedXmlWrapper xmlns:root="https://example.com/root_xmlns_for_wrapper_element">{wrapped_xml.text}</root:ParsedXmlWrapper>'
    )
    # wrapped_xml.clear()
    # wrapped_xml.append(a)

    return unwrapped


def get_update_info(cookie: str, cookie_expiration: str, category_id: str, release_type: str, user: Optional[str] = None):
    response = windows_update_session.post(
        WINDOWS_UPDATE_URL,
        data=GET_INFO_BODY.format(
            cookie=cookie,
            expiration=cookie_expiration,
            category_id=category_id,
            release_type=release_type,
            user=user or "",
        ),
    )
    # Path("tmp/update_info.xml").write_bytes(response.content)

    try:
        response.raise_for_status()
    except requests.HTTPError:
        print(response.text)
        raise

    root = ET.fromstring(response.content)
    updates_result = root.find("./s:Body/ms:SyncUpdatesResponse/ms:SyncUpdatesResult", namespaces=NAMESPACES)
    assert updates_result is not None

    extended_updates = updates_result.find("./ms:ExtendedUpdateInfo/ms:Updates", namespaces=NAMESPACES)
    assert extended_updates is not None

    file_details = {}

    for extended_update in extended_updates:
        update_id = extended_update.find("./ms:ID", namespaces=NAMESPACES)
        assert update_id is not None
        update_id = update_id.text
        update_info = parse_wrapped_xml(extended_update)

        # continue

        files = update_info.find("./Files")
        if files is None:
            continue

        extended_properties = update_info.find("./ExtendedProperties")
        if extended_properties is None:
            raise RuntimeError("Expected extended properties in update info")

        # Ignore libraries
        if extended_properties.attrib["IsAppxFramework"] == "true":
            continue

        for file in files:
            # if "InstallerSpecificIdentifier" in file.attrib and "FileName" in file.attrib:
            if "FileName" in file.attrib:
                # assert update_id not in file_details
                this_file_details = {
                    "filename": file.attrib["FileName"],
                    "identity": extended_properties.attrib["PackageIdentityName"],
                    "installer_specific_identifier": file.attrib.get("InstallerSpecificIdentifier"),
                    "digest": base64.b64decode(file.attrib["Digest"]).hex(),
                    "digest_type": file.attrib["DigestAlgorithm"],
                    "size": int(file.attrib["Size"]),
                }

                additional_digest = file.find("./AdditionalDigest")
                if additional_digest is not None:
                    if not additional_digest.text:
                        raise RuntimeError("Additional digest has no data")

                    this_file_details["additional_digest"] = base64.b64decode(additional_digest.text).hex()
                    this_file_details["additional_digest_type"] = additional_digest.attrib["Algorithm"]

                file_details.setdefault(update_id, []).append(this_file_details)

    new_updates = updates_result.find("./ms:NewUpdates", namespaces=NAMESPACES)
    assert new_updates is not None

    identities = {}

    for new_update in new_updates:
        identity_id = new_update.find("./ms:ID", namespaces=NAMESPACES)
        assert identity_id is not None
        identity_id = identity_id.text
        update_info = parse_wrapped_xml(new_update)

        # continue

        if update_info.find("./Properties/SecuredFragment") is None:
            # This update ID is not available for download
            continue

        update_identity = update_info.find("./UpdateIdentity")
        assert update_identity is not None
        update_id = update_identity.attrib["UpdateID"]
        revision_number = update_identity.attrib["RevisionNumber"]
        identities.setdefault(identity_id, []).append((update_id, revision_number))

    # print(ET.tostring(root, encoding="unicode"))

    info = []

    for update_id in file_details:
        details = {
            "files": file_details.get(update_id, []),
            "update_ids": identities.get(update_id, []),
        }

        assert details["files"] and details["update_ids"]
        info.append(details)

    assert len(info) == 1
    return info[0]


GET_FE3_LINKS_BODY = """
<Envelope xmlns="http://www.w3.org/2003/05/soap-envelope">
    <Header xmlns:a="http://www.w3.org/2005/08/addressing"
        xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <a:Action>http://www.microsoft.com/SoftwareDistribution/Server/ClientWebService/GetExtendedUpdateInfo2</a:Action>
        <a:To>https://fe3.delivery.mp.microsoft.com/ClientWebService/client.asmx/secured</a:To>
        <Security xmlns="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
            xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
            <u:Timestamp>
                <u:Created>2023-09-08T00:00:00.000Z</u:Created>
                <u:Expires>2023-09-08T00:00:00.001Z</u:Expires>
            </u:Timestamp>
            <WindowsUpdateTicketsToken u:id="ClientMSA"
                xmlns="http://schemas.microsoft.com/msus/2014/10/WindowsUpdateAuthorization">
                <TicketType Name="MSA" Version="1.0" Policy="MBI_SSL">
                    <user>{user}</user>
                </TicketType>
            </WindowsUpdateTicketsToken>
        </Security>
    </Header>
    <Body>
        <GetExtendedUpdateInfo2 xmlns="http://www.microsoft.com/SoftwareDistribution/Server/ClientWebService">
            <updateIDs>
                <UpdateIdentity>
                    <UpdateID>{update_id}</UpdateID>
                    <RevisionNumber>{revision_number}</RevisionNumber>
                </UpdateIdentity>
            </updateIDs>
            <infoTypes>
                <XmlUpdateFragmentType>FileUrl</XmlUpdateFragmentType>
                <XmlUpdateFragmentType>FileDecryption</XmlUpdateFragmentType>
            </infoTypes>
            <deviceAttributes>BranchReadinessLevel=CB;CurrentBranch=rs_prerelease;OEMModel=Virtual Machine;FlightRing={release_type};AttrDataVer=21;SystemManufacturer=Microsoft Corporation;InstallLanguage=en-US;OSUILocale=en-US;InstallationType=Client;FlightingBranchName=external;FirmwareVersion=Hyper-V UEFI Release v2.5;SystemProductName=Virtual Machine;OSSkuId=48;FlightContent=Branch;App=WU;OEMName_Uncleaned=Microsoft Corporation;AppVer=10.0.22621.900;OSArchitecture=AMD64;SystemSKU=None;UpdateManagementGroup=2;IsFlightingEnabled=1;IsDeviceRetailDemo=0;TelemetryLevel=3;OSVersion=10.0.22621.900;DeviceFamily=Windows.Desktop;</deviceAttributes>
        </GetExtendedUpdateInfo2>
    </Body>
</Envelope>
""".strip()


def get_fe3_links(update_id, revision_number, release_type, user: Optional[str] = None):
    response = windows_update_session.post(
        WINDOWS_UPDATE_SECURED_URL,
        data=GET_FE3_LINKS_BODY.format(update_id=update_id, revision_number=revision_number, release_type=release_type, user=user or ""),
    )
    # Path("tmp/fe3_links.xml").write_bytes(response.content)

    response.raise_for_status()

    root = ET.fromstring(response.content)

    files = root.find("./s:Body/ms:GetExtendedUpdateInfo2Response/ms:GetExtendedUpdateInfo2Result/ms:FileLocations", namespaces=NAMESPACES)
    assert files is not None

    links = []

    for file in files:
        digest = file.find("./ms:FileDigest", namespaces=NAMESPACES)
        url = file.find("./ms:Url", namespaces=NAMESPACES)
        assert digest is not None and digest.text is not None
        assert url is not None and url.text is not None
        links.append((url.text, digest.text))

    return links


def merge_files_with_links(files, links):
    for link in links:
        for file in files:
            if file["digest"] == base64.b64decode(link[1]).hex():
                file["url"] = link[0]
                break
        else:
            raise ValueError(f"Could not find file with digest {link[1]} in {files}")


if __name__ == "__main__":
    print("Getting cookie...")
    cookie = get_cookie()

    apps = []

    for app_product_id, app_name in APPS_TO_CHECK.items():
        print(f"Checking {app_name}...")

        details = get_full_details(app_product_id)

        app_info = details | get_update_info(*cookie, category_id=details["wu_category_id"], release_type=RELEASE_TYPE)

        for update_id, revision_number in app_info["update_ids"]:
            print(f"Getting links for {update_id} rev {revision_number}...")
            links = get_fe3_links(update_id, revision_number, RELEASE_TYPE)
            merge_files_with_links(app_info["files"], links)

        # print(f"Final info for {app_product_id} is")
        # pprint(app_info)
        apps.append(app_info)

    json.dump(apps, Path("import_wu.json").open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)

    print("Done!")
