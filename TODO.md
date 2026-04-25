# General

- [x] fix imports due to refactor of notebooks to /notebooks and subfolders

# Notebooks

## /pedals/oscillator.ipynb

- [ ] approach is wrong -> propagate new formulas to python script, new error propagation, + latex to explain the formula, docs, progress etc. See google doc

## synthesizer.ipynb

- [ ] change visual style of knob (`widget/knob.js`) to resemble minimoog model D knobs
- [ ] change visual style of switch (`widget/switch.js`) to resemble minimoog switches
- [ ] wire filter section (cutoff, emphasis, contour, attack/decay/sustain, filter mod, kbd ctrl)
- [ ] wire loudness contour (attack/decay/sustain envelope on VCA)
- [ ] wire noise source (white/pink noise generator + mixer channel)
- [ ] wire oscillator modulation switch (route osc3/noise to osc pitch)
- [ ] wire mod source/type switches + mod mix knob
- [ ] wire LFO (rate knob, glide/decay switches, pitch/mod wheels)
- [ ] wire A=440 reference tone switch
- [ ] wire main output on/off switch

# Helpers/Utils

## cells/filter_chain.py

- [x] refactor code into multiple files in new module `/cells/filter_chain/`

## utils/snv/

- [ ] see utils.snv.layout
