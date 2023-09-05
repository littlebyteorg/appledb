"""
Credits:
https://github.com/ThomasPe/MS-Store-API
https://github.com/ThomasPe/MS-Store-API/issues/9
https://github.com/LSPosed/MagiskOnWSALocal/blob/main/scripts/generateWSALinks.py
https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-wusp/b8a2ad1d-11c4-4b64-a2cc-12771fcb079b

"""

import base64
import json
import textwrap
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

import requests


APPS_TO_CHECK = {
    "9NP83LWLPZ9K": "Apple Devices Preview",
}
release_types = {"Retail": "retail", "Release Preview": "RP", "Insider Slow": "WIS", "Insider Fast": "WIF"}
RELEASE_TYPE = release_types["Retail"]


windows_store_session = requests.Session()
WINDOWS_STORE_SEARCH_PRODUCTS_V9 = "https://storeedgefd.dsx.mp.microsoft.com/v9.0/search?appVersion=22203.1401.0.0&market=US&locale=en-US&deviceFamily=windows.desktop&query={query}&mediaType=apps&productFamilies=apps"
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

windows_update_session = requests.Session()
windows_update_session.verify = str(Path("tasks/WU.pem"))
windows_update_session.headers.update(
    {
        "Content-Type": "application/soap+xml; charset=utf-8",
    }
)

# TODO: Standardize the body, and maybe make it with ET

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
                    "size": file.attrib["Size"],
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
