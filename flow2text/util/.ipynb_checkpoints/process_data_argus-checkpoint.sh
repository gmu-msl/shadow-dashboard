#!/bin/bash
shopt -s nullglob
for i in $(find data -type f -name "*.pcap*"); do
      filename=$(basename $i ng)
      filename=$(basename $filename .pcap)
      argus -r $i -w $filename.argus
      ra -r $filename.argus -c',' -s srcid rank stime ltime trans flgs seq dur runtime idle mean stddev sum min max smac dmac soui doui saddr daddr proto sport dport stos dtos sdsb ddsb sco dco sttl dttl shops dhops sipid dipid smpls dmpls autoid sas das ias cause nstroke snstroke dnstroke pkts spkts dpkts bytes sbytes dbytes appbytes sappbytes dappbytes pcr load sload dload loss sloss dloss ploss psloss pdloss retrans sretrans dretrans pretrans psretrans pdretrans sgap dgap rate srate drate dir sintpkt sintdist sintpktact sintdistact sintpktidl sintdistidl dintpkt dintdist dintpktact dintdistact dintpktidl dintdistidl sjit sjitact sjitidle djit djitact djitidle state label suser duser swin dwin svlan dvlan svid dvid svpri dvpri srng erng stcpb dtcpb tcprtt synack ackdat tcpopt inode offset smeansz dmeansz spktsz smaxsz dpktsz dmaxsz sminsz dminsz dminsz > $filename.csv
done
mkdir data/argus
mkdir data/argus/csv
mv *.argus data/argus/
mv *.csv data/argus/csv

