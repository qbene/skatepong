#!/bin/bash

set -eu
set -x

install_project()
{
  local project=$1
  local dest=$2
  local controller=$3
  local version=${4:-main}

  mkdir -p "$HOME/opt/"
  rm -rf  "$HOME/opt/$dest"
  git clone "$project" --branch "$version" "$HOME/opt/$dest"
  (
    cd "$HOME/opt/$dest";
    poetry config --local virtualenvs.in-project true;
    poetry install;
    cp "/opt/$dest/$controller" "$HOME/.qjoypad3"
  )
}

main ()
{
  install_project 'https://github.com/qbene/skatepong.git' 'skatepong' 'ness_controller_skatepong.lyt'
}

main $@
