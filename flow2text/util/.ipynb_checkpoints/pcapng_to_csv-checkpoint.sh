#!/bin/bash
shopt -s nullglob
for f in $(find data -type f -name "*.pcapng"); do
    base=${f##*/}
    tshark -r "$f" \
        -T fields -e frame.number -e frame.time \
        -e ip.src -e ip.dst -e ip.proto \
        -e ip.len -e tcp.srcport -e tcp.dstport\
        -e tcp.ack -e tcp.seq -e tcp.len \
        -e tcp.reassembled.length \
        -e dtls.handshake.extension.len -e dtls.handshake.extension.type -e dtls.handshake.session_id \
        -e dtls.handshake.session_id_length -e dtls.handshake.session_ticket_length -e dtls.handshake.sig_hash_alg_len -e dtls.handshake.sig_len -e dtls.handshake.version \
        -e dtls.heartbeat_message.padding -e dtls.heartbeat_message.payload_length -e dtls.heartbeat_message.payload_length.invalid -e dtls.record.content_type -e dtls.record.content_type \
        -e dtls.record.length -e dtls.record.sequence_number -e dtls.record.version -e dtls.change_cipher_spec -e dtls.fragment.count -e dtls.handshake.cert_type.types_len \
        -e dtls.handshake.certificate_length -e dtls.handshake.certificates_length -e dtls.handshake.cipher_suites_length -e dtls.handshake.comp_methods_length -e dtls.handshake.exponent_len \
        -e dtls.handshake.extension.len -e dtls.handshake.extensions_alpn_str -e dtls.handshake.extensions_alpn_str_len -e dtls.handshake.extensions_key_share_client_length \
        -e http.request -e udp.port -e frame.time_relative -e frame.time_delta -e tcp.time_relative -e tcp.time_delta \
        -e tcp.payload -e dns.qry.name -e dns.opt.client.addr4 -e dns.opt.client.addr6 -e dns.opt.client.addr\
        -E header=y -E separator=, -E quote=d \
        -E occurrence=f> ./"${base%.pcap}.csv"
done
mkdir data/csv
mv *.csv data/csv

