#!/bin/sh

for s in 0 1
do
    python3 btagEfficiency.py -y 2022 -l 8 -i /eos/user/a/atarabin/STXS_samples/PROD_samplesNano_2022_MC_8d4c03f7 -s $s
    python3 btagEfficiency.py -y 2022EE -l 26.7 -i /eos/user/a/atarabin/STXS_samples/PROD_samplesNano_2022EE_MC_8d4c03f7 -s $s
    # python3 btagEfficiency.py -y 2023 -l 17.8 -i /eos/user/a/atarabin/STXS_samples/PROD_samplesNano_2023preBPix_MC_8d4c03f7 -s $s
    # python3 btagEfficiency.py -y 2023BPix -l 9.5 -i /eos/user/a/atarabin/STXS_samples/PROD_samplesNano_2023postBPix_MC_8d4c03f7 -s $s
done
