#!/bin/sh

run_app ()
{
  local app_name=$1
  local controller_conf=$2
  shift 2

  exec qjoypad $controller_conf &
  
  $HOME/opt/$app_name/.venv/bin/$app_name $@
}

main ()
{
  run_app skatepong "ness_controller_skatepong" $@
}

main $@
