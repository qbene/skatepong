#!/bin/bash

set -eu
set -x

install_system()
{
  sudo apt -y install python3 python3-pip git
  sudo apt -y install python3-smbus i2c-tools
  sudo apt -y install libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 libsdl2-ttf-2.0-0
  sudo apt -y install libsdl2-dev
  sudo apt -y install qjoypad # For game controller
  sudo apt -y install unclutter # To hide mouse cursor
  pip3 install --upgrade pip
  pip3 install --root-user-action=ignore poetry
}

main ()
{
  install_system
}

main $@
