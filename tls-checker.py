import ssl
import socket
import sys
import csv
import json
import concurrent.futures
import random
import os
import re
try:
    import dns.resolver
    import requests
    from progress.spinner import MoonSpinner
    import patoolib
except ImportError:
    print('\n** Please install required modules: pip install -r requirements.txt **')
    install = input('- Would you like to install requirements automatically? [y=YES, n=NO]:').strip().lower()
    if install == 'y':
        import subprocess
        subprocess.run('pip3 install -r requirements.txt'.split(' '))
        import dns.resolver
        import requests
        from progress.spinner import MoonSpinner
        import patoolib
    elif install == 'n':
        sys.exit(0)
    else:
        sys.exit(1)



print('\n** You can ignore the questions and just press Enter **\n')
get_file_name = input('- Which file? [i=irani.csv or 1=file1.csv or 2=file2.csv]:').strip().lower()
if get_file_name == 'i':
    file_name = 'irani'
    print('+ irani.csv is selected.')
elif get_file_name == '1':
    file_name = 'file1'
    print('+ file1.csv is selected.')
else:
    file_name = 'file2'
    print('+ file2.csv is selected.')
try:
    # this list includes all urls from csv
    web_addrs = []
    with open(f'./{file_name}.csv') as urls:
        csv_reader = csv.reader(urls)
        for row in csv_reader:
            web_addrs.append(row[0])
except FileNotFoundError:
    patoolib.extract_archive("./csvfiles.zip", outdir=".")
    os.remove('./csvfiles.zip')
    # this list includes all urls from csv
    web_addrs = [] 
    with open(f'./{file_name}.csv') as urls:
        csv_reader = csv.reader(urls)
        for row in csv_reader:
            web_addrs.append(row[0])
len_webaddr = len(web_addrs)
""" 
Get length of csv chunk and
fill input_urls list for threads
"""
input_urls = []

try:
    how_many = int(input(f'- How many url of "{file_name}.csv" do you want to check? [1-{len_webaddr}]:').strip())
    print(f'+ {how_many} urls are selected.')
except ValueError:
    how_many = len_webaddr
    print(f'+ {how_many} urls are selected.')

how_many = max(how_many, 1)
how_many = min(how_many, len_webaddr)
randomized = input('- Do you want to use randomized search? [y=YES, n=NO]:').strip().lower()
if randomized == 'y':
    random.shuffle(web_addrs)
    print('+ Randomized search is selected.')
elif randomized == 'n':
    print('+ Normal search is selected.')
else:
    random.shuffle(web_addrs)
    print('+ Randomized search is selected.')
# make input of threads
length = 30 if how_many >= 30 else 1
for i in range(0, how_many, length):
    input_urls.append(web_addrs[i:min(i+length, how_many)])
# set iso code
print('* Guidance: https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes')
get_iso_name = input('- preferred country? [DE=Germany, NL=Netherland, ...]:').strip().upper()
# set AS organization name and regex for filter AS organization names during search
get_AS_organization_name = input('- preferred AS Organization? [Hetzner, Vultr, OVH, Akamai,...]:').strip().lower()
pattern = re.compile(r'[^.,\s]*'+get_AS_organization_name+'[^.,\s]*[.,]?', re.IGNORECASE)



def get_info(web_addrs: list) -> dict:
    api_token = '3bd22fe89c5c42d386d84297d53389d3'
    port = 443
    context = ssl.create_default_context()
    context.set_alpn_protocols(['h2', 'http/1.1', 'h3'])
    result = {}
    spinner = MoonSpinner('••••••••••••••••••••••••••••••••••••• ')
    for web_addr in web_addrs:
        spinner.next()
        try:
            sock = socket.create_connection((web_addr, port), timeout=5)
            conn = context.wrap_socket(sock, server_hostname=web_addr)
            resolve_server = dns.resolver.resolve(web_addr)
            ip_server = [rdata for rdata in resolve_server]
            url = f'https://api.findip.net/{ip_server[0]}/?token={api_token}'
            response = requests.get(url, timeout=5).json()
            cipher = conn.cipher()
            alpn = conn.selected_alpn_protocol()
            iso_code = response['country']['iso_code']
            AS_organization = response['traits']['autonomous_system_organization']
            country = response['country']['names']['en']
            city = response['city']['names']['en']
            issuer = conn.getpeercert()['issuer'][1][0][1]
        except:
            continue
        else:
            if get_iso_name and get_AS_organization_name:
                condition = (cipher[1] == 'TLSv1.3') and ((alpn == 'h2') or (alpn == 'h3')) and (get_iso_name == iso_code) and (pattern.findall(AS_organization))
            elif get_iso_name:
                condition = (cipher[1] == 'TLSv1.3') and ((alpn == 'h2') or (alpn == 'h3')) and (get_iso_name == iso_code)
            elif get_AS_organization_name:
                condition = (cipher[1] == 'TLSv1.3') and ((alpn == 'h2') or (alpn == 'h3')) and (pattern.findall(AS_organization))
            else:
                condition = (cipher[1] == 'TLSv1.3') and ((alpn == 'h2') or (alpn == 'h3'))
            if condition:
                print(f'\naddress = {web_addr}\nalpn = {conn.selected_alpn_protocol()}\nissuer = {issuer}\ncipher = {cipher[0]}\nTLS = {cipher[1]}\nkey_length = {cipher[2]}\ncountry = {country}\niso_code = {iso_code}\ncity = {city}\nAS organization = {AS_organization}\n', end='')
                result[web_addr] = [issuer, alpn, cipher[0], cipher[1], cipher[2], country, iso_code, city, AS_organization]
            else:
                continue

    return result

def main() -> list:
    outlist = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executer:
        tasks = [executer.submit(get_info, url_group) for url_group in input_urls]
        for task in concurrent.futures.as_completed(tasks):
            result = task.result()
            if result:
                outlist.append(result)
    return outlist

def save_output(lst):
    with open('./result.json', 'w', encoding='utf-8') as f:
        json.dump(lst, f, ensure_ascii=False, indent=4)



if __name__ == '__main__':
    outlist = main()
    save_output(outlist)
    

    