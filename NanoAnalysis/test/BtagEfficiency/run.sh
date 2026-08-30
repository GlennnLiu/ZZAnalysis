#!/bin/sh

for s in 0
do
    python3 btagEfficiency.py -y 2022 -l 8 -i /eos/cms/store/group/phys_higgs/cmshzz4l/cjlst/HIG-26-STXS/260623/2022 -s $s
    python3 btagEfficiency.py -y 2022EE -l 26.7 -i /eos/cms/store/group/phys_higgs/cmshzz4l/cjlst/HIG-26-STXS/260623/2022EE -s $s
    python3 btagEfficiency.py -y 2023preBPix -l 17.96 -i /eos/cms/store/group/phys_higgs/cmshzz4l/cjlst/HIG-26-STXS/260623/2023preBPix -s $s
    python3 btagEfficiency.py -y 2023postBPix -l 9.7 -i /eos/cms/store/group/phys_higgs/cmshzz4l/cjlst/HIG-26-STXS/260623/2023postBPix -s $s
    python3 btagEfficiency.py -y 2024 -l 109.95 -i /eos/cms/store/group/phys_higgs/cmshzz4l/cjlst/HIG-26-STXS/260623/2024 -s $s
done
