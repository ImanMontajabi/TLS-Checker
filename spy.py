import scapy.all as scapy

request = scapy.ARP()
print(scapy.ls(scapy.ARP()))
