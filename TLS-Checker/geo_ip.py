import os
import geoip2.database
from geoip2 import errors


def geo_information(ip: str) -> list:
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
