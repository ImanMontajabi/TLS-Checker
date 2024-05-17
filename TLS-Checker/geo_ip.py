import os
import geoip2.database


def geo_information(ip: str) -> list:
    geo_info: list[str | int | None] = list()
    path = os.getcwd()
    with geoip2.database.Reader(f'{path}/GeoLite2-ASN.mmdb') as reader:
        response_asn = reader.asn(ip)
        geo_info.append(response_asn.autonomous_system_number)
        geo_info.append(response_asn.autonomous_system_organization)
    with geoip2.database.Reader(f'{path}/GeoLite2-City.mmdb') as reader:
        response_city = reader.city(ip)
        geo_info.append(response_city.registered_country.iso_code)
        geo_info.append(response_city.registered_country.names['en'])

    return geo_info
