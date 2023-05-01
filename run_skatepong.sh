#!/bin/sh

# Open git folder :
cd /home/qbe/Documents/projects/skatepong/git/skatepong
# Activate virtual environment :
. .venv/bin/activate
# Multi-Trheading : 
# - Start qjoypad for game control with the ness controller skatepong setup
# - run game
qjoypad "ness_controller_skatepong" & skatepong

