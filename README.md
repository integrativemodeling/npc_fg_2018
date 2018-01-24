 Overview
==========
Synopsis: The files in this folder can be used to reproduce the Brownian Dynamics simulations of FG repeats using IMP
          as described in Kim et al., 2018

Author: Barak Raveh

E-mail: barak.raveh@gmail.com or barak@salilab.org

Date last updated: Jan 9th, 2018

 Main folders
==============
Scripts/ - scripts for generating the FG repeats over an input scaffold

InputData/ - folder of input RMF file describing the scaffold

Output/ - output from running the script, as explained below

SampleOutput/ - sample of the main output from running the script

RepresentativeEnsemble/ - ensemble of output models (extracted from simulation outputs stored on Andrej's Salilab park4 file system, in folder /salilab/park4/barak/Runs/NPC_FullModel2016/FullNPC_Oct10_Cluster0model_Rg70_per_600aa_InflateObstacles_InflatedKaps, see .../Ensemble/make_ensemble.sh there)

Denisites/ - densities of various nups and all nups, from same folder as RepresentativeEnsemble/

 Prerequisites
===============
1) Download IMP (https://github.com/salilab/imp)

2) Download npctransport module under IMP's modeule folder from https://github.com/salilab/npctransport

3) Build IMP according to online instructions into folder $IMPFOLDER

 Protocol for generating FG repeats from scaffold of NPC
=========================================================
0) Create folder for output, e.g. "Output"

1) Create model of NPC from RMF file of scaffold (expected running time - few minutes) in output folder ("Output" in this example):

$ $IMPFOLDER/setup_environment.sh python Scripts/load_whole_new_coarse_grained_v5.py Output/config.pb InputData/47-35_1spoke.rmf3  >& Output/config.txt &


2) move to Output folder:

$ cd Output


3) Equilibrate and run for as long as desired by changing short_init_factor and short_sim_factor for shorter or longer equilibration and simulation, respectively:, and using a specific random seed using optional --random_seed flag; output file and movie file names could be changed as well, use --help option for more information (expected running time - hours to days depending on simulation time and system):

$ $IMPFOLDER/setup_environment.sh $IMPFOLDER/module_bin/npctransport/fg_simulation --configuration config.pb  --output output.pb --short_init_factor 0.25 --short_sim_factor 1.0 --conformations movie.rmf --random_seed $RANDOM >& LOG.fg_simulation &


4) The output movie file movie.rmf can be viewed using e.g. Chimera.
