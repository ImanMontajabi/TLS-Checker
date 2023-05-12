import ssl
import socket
import csv
import json
import concurrent.futures


input_urls = [] # list for threads
web_addrs = [] # all urls from csv
take_name = input('Which file? [irani or all]: ')
file_name = take_name if (take_name == 'irani') or (take_name == 'all') else 'all'
with open(f'./{file_name}.csv') as urls:
    csv_reader = csv.reader(urls)
    for row in csv_reader:
        web_addrs.append(row[0])
len_webaddr = len(web_addrs)
# take length of csv chunk
try:
    how_many = int(input(f'\nHow many url of "{file_name}.csv" do you want to check? [1-{len_webaddr}]:'))
except ValueError:
    how_many = len_webaddr

how_many = max(how_many, 1)
how_many = min(how_many, len_webaddr)
# make input of threads
length = 20 if how_many >= 20 else 1
for i in range(0, how_many, length):
    input_urls.append(web_addrs[i:min(i+length, how_many)])


def get_info(web_addrs: list) -> dict:
    port = 443
    context = ssl.create_default_context()
    context.set_alpn_protocols(['h2', 'http/1.1'])
    result = {}
    for web_addr in web_addrs:
        try:
            sock = socket.create_connection((web_addr, port), timeout=5)
            conn = context.wrap_socket(sock, server_hostname=web_addr)
        except:
            continue
        else:
            cipher = conn.cipher()
            alpn = conn.selected_alpn_protocol()
            if (cipher[1] == 'TLSv1.3') and (alpn == 'h2'):
                issuer = conn.getpeercert()['issuer'][1][0][1]
                print(f'address = {web_addr}\nalpn = {conn.selected_alpn_protocol()}\nissuer = {issuer}\ncipher = {cipher[0]}\nTLS = {cipher[1]}\nkey_length = {cipher[2]}\n---------------------')
                result[web_addr] = [issuer, alpn, cipher[0], cipher[1], cipher[2]]
            else:
                continue
    return result
        
outlist = []
with concurrent.futures.ThreadPoolExecutor() as executer:
    tasks = [executer.submit(get_info, url_group) for url_group in input_urls]
    for task in concurrent.futures.as_completed(tasks):
        result = task.result()
        outlist.append(result)
with open('./result.json', 'w') as f:
    json.dump(outlist, f, ensure_ascii=False, indent=4)