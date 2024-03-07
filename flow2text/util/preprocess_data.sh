#!/bin/sh

set -e 

# ../util/process_data_argus.sh
../../../util/pcap_to_csv.sh  
../../../util/pcapng_to_csv.sh
