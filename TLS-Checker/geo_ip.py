import os
import geoip2.database
from geoip2 import errors


def geo_information(ip: str) -> list:
    """
    Retrieves geographic information for a given IP address using MaxMind
    GeoIP databases.

    Args:
        ip (str): The IP address for which geographic information is to be
        retrieved.

    Returns:
        list: A list containing geographic information for the given IP address.

    Notes:
        The function uses MaxMind GeoIP databases (GeoLite2-ASN.mmdb and
        GeoLite2-City.mmdb)
        to retrieve the following information:
        - Autonomous System Number (ASN) and ASN organization for the IP address.
        - ISO code and country name for the registered country associated
        with the IP address.
        If the information is not found for any of the databases or the IP
        address is not found,
        None values are appended to the list.
    """

    geo_info: list[str | int | None] = list()
    path = os.getcwd()
    with geoip2.database.Reader(f'{path}/GeoLite2-ASN.mmdb') as reader:
        try:
            response_asn = reader.asn(ip)
        except geoip2.errors.AddressNotFoundError:
            geo_info.extend([None, None])
        else:
            geo_info.append(response_asn.autonomous_system_number)
            geo_info.append(response_asn.autonomous_system_organization)
    with geoip2.database.Reader(f'{path}/GeoLite2-City.mmdb') as reader:
        try:
            response_city = reader.city(ip)
        except geoip2.errors.AddressNotFoundError:
            geo_info.extend([None, None])
        else:
            geo_info.append(response_city.registered_country.iso_code)
            geo_info.append(response_city.registered_country.names['en'])
        finally:
            return geo_info
