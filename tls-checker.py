import ssl
import socket
import csv
import json
import concurrent.futures
import dns.resolver
import requests
import random
from progress.spinner import PixelSpinner


web_addrs = [] # all urls from csv
print('\n** You can ignore the questions and just press Enter **\n')
take_file_name = input('- Which file? [irani or all]:').strip().lower()
file_name = take_file_name if (take_file_name == 'irani') or (take_file_name == 'all') else 'all'
with open(f'./{file_name}.csv') as urls:
    csv_reader = csv.reader(urls)
    for row in csv_reader:
        web_addrs.append(row[0])
len_webaddr = len(web_addrs)
random.shuffle(web_addrs)
# take length of csv chunk
input_urls = [] # list for threads
try:
    how_many = int(input(f'- How many url of "{file_name}.csv" do you want to check? [1-{len_webaddr}]:').strip())
except ValueError:
    how_many = len_webaddr

how_many = max(how_many, 1)
how_many = min(how_many, len_webaddr)
# make input of threads
length = 30 if how_many >= 30 else 1
for i in range(0, how_many, length):
    input_urls.append(web_addrs[i:min(i+length, how_many)])
# set iso code
print('* Guidance: https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes')
take_iso_name = input('- preferred country? [Germany = DE, Netherland = NL, ...]:').strip().upper()

def get_info(web_addrs: list) -> dict:
    api_token = '3bd22fe89c5c42d386d84297d53389d3'
    port = 443
    context = ssl.create_default_context()
    context.set_alpn_protocols(['h2', 'http/1.1', 'h3'])
    result = {}
    spinner = PixelSpinner('------------------------------- Searching ')
    for web_addr in web_addrs:
        spinner.next()
        try:
            sock = socket.create_connection((web_addr, port), timeout=5)
            conn = context.wrap_socket(sock, server_hostname=web_addr)
            resolve_server = dns.resolver.resolve(web_addr)
            ip_server = [rdata for rdata in resolve_server]
            url = f'https://api.findip.net/{ip_server[0]}/?token={api_token}'
            response = requests.get(url, timeout=5).json()
        except:
            continue
        else:
            cipher = conn.cipher()
            alpn = conn.selected_alpn_protocol()
            iso_code = response['country']['iso_code']
            if take_iso_name != '':
                if (cipher[1] == 'TLSv1.3') and ((alpn == 'h2') or (alpn == 'h3')) and (take_iso_name == iso_code):
                    country = response['country']['names']['en']
                    city = response['city']['names']['en']
                    isp = response['traits']['isp']
                    issuer = conn.getpeercert()['issuer'][1][0][1]
                    print(f'\naddress = {web_addr}\nalpn = {conn.selected_alpn_protocol()}\nissuer = {issuer}\ncipher = {cipher[0]}\nTLS = {cipher[1]}\nkey_length = {cipher[2]}\ncountry = {country}\niso_code = {iso_code}\ncity = {city}\nisp = {isp}\n', end='')
                    result[web_addr] = [issuer, alpn, cipher[0], cipher[1], cipher[2], country, iso_code, city, isp]
                else:
                    continue
            else:
                if (cipher[1] == 'TLSv1.3') and ((alpn == 'h2') or (alpn == 'h3')):
                    country = response['country']['names']['en']
                    city = response['city']['names']['en']
                    isp = response['traits']['isp']
                    issuer = conn.getpeercert()['issuer'][1][0][1]
                    print(f'\naddress = {web_addr}\nalpn = {conn.selected_alpn_protocol()}\nissuer = {issuer}\ncipher = {cipher[0]}\nTLS = {cipher[1]}\nkey_length = {cipher[2]}\ncountry = {country}\niso_code = {iso_code}\ncity = {city}\nisp = {isp}\n', end='')
                    result[web_addr] = [issuer, alpn, cipher[0], cipher[1], cipher[2], country, iso_code, city, isp]
                else:
                    continue
    return result

outlist = []
with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executer:
    tasks = [executer.submit(get_info, url_group) for url_group in input_urls]
    for task in concurrent.futures.as_completed(tasks):
        result = task.result()
        outlist.append(result)
with open('./result.json', 'w', encoding='utf-8') as f:
    json.dump(outlist, f, ensure_ascii=False, indent=4)