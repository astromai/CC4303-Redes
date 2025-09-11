import socket
from dnslib import *

udp_socket_address = ('localhost', 8000)

def recv_dns_message():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(udp_socket_address)
    print("BIP BOP COMENZANDO!!")
    try:
        while True:
            data, addr = udp_socket.recvfrom(4096)
            response_data = resolver(data)
            if response_data:
                udp_socket.sendto(response_data, addr)
    except KeyboardInterrupt:
        print("\n\rServer interrumpido...")
    finally:
        print("\n\rCerrando socket...")
        udp_socket.close()

def parse_dns_message(data):
    dns_record = DNSRecord.parse(data)
    parsed = {
        "questions": [],
        "answers": [],
        "authoritative": [],
        "additional": []
    }
    for q in dns_record.questions:
        parsed["questions"].append({"name": q.qname, "type": q.qtype, "class": q.qclass})
    for rr in dns_record.rr:
        parsed["answers"].append({"name": rr.rname, "type": rr.rtype, "class": rr.rclass, "ttl": rr.ttl, "data": rr.rdata})
    for rr in dns_record.auth:
        parsed["authoritative"].append({"name": rr.rname, "type": rr.rtype, "class": rr.rclass, "ttl": rr.ttl, "data": rr.rdata})
    for rr in dns_record.ar:
        parsed["additional"].append({"name": rr.rname, "type": rr.rtype, "class": rr.rclass, "ttl": rr.ttl, "data": rr.rdata})
    return parsed

def resolver(data):
    root_ip = '192.33.4.12'
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        qname = str(DNSRecord.parse(data).questions[0].qname)
        current_ip = root_ip
        ns_name = '.'
        while True:
            print(f"(debug) Consultando '{qname}' a '{ns_name}' con dirección IP '{current_ip}'")
            udp_socket.sendto(data, (current_ip, 53))
            response_data, _ = udp_socket.recvfrom(4096)
            dt = parse_dns_message(response_data)
            for answer in dt['answers']:
                if answer['type'] == QTYPE.A:
                    return response_data
            found_ns = False
            for ns_record in dt['authoritative']:
                if ns_record['type'] == QTYPE.NS:
                    ns_name = str(ns_record['data'])
                    target_ip = None
                    for ar in dt['additional']:
                        if ar['type'] == QTYPE.A and str(ar['name']) == ns_name:
                            target_ip = str(ar['data'])
                            break
                    if target_ip:
                        current_ip = target_ip
                        found_ns = True
                        break
                    ns_ip_bytes = resolver(DNSRecord.question(ns_name).pack())
                    ns_dt = parse_dns_message(ns_ip_bytes)
                    if ns_dt['answers']:
                        current_ip = str(ns_dt['answers'][0]['data'])
                        found_ns = True
                        break
            if not found_ns:
                return None
    except Exception as e:
        print(f"Error en resolver: {e}")
        return None
    finally:
        udp_socket.close()

if __name__ == "__main__":
    recv_dns_message()
