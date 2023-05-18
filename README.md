Copyright © 2023 Quentin BENETHUILLERE. All rights reserved.

------------------------------------------------------------------------
INTRODUCTION
------------------------------------------------------------------------

SKATEPONG is 2 players pong game, with real skateboards as actuators.
A gyroscope is mounted under each skateboard itself mounted on a pivot.

- Objective : Shoot the ball beyond the oponent's zone (+1 point).
- End : Game ends when a player reaches 10 points.
- The two paddles are controlled independently based on the angular
  rotation measured by the gyroscopes mounted under each skateboard.
  
- Games scenes :
	WELCOME : Splash screen at application start.
	WAITING_GYROS : Waiting that both gyroscopes are connected.
	WAITING_PLAYERS : Waiting for motion on both skates.
	COUNTDOWN : Countdown before the actual game starts.
	GAME_ONGOING : Game running.
	GAME_END : Winner is announced + pads calib before next game
	CALIBRATION_REQUESTED : Paddles calibratation upon request.
	
- NES controller / keyboard controls are presented in a dedicated doc.
- Electrical wiring is presented in a dedicated doc.
	
------------------------------------------------------------------------
MATERIAL
------------------------------------------------------------------------

- 1 x Raspberry Pi >= Model 3B 
Notes : This game has been tested with Raspberry Pi 3 Model B+, and
Raspberry Pi Model 4. Performances are better with Raspberry Pi Model 4
which can handle displaying the game at high resolution without 
requiring a resolution reduction in pygame as the Raspberry Pi 3  
Model B+ needs.

- 1 x SD card >= 8Go
- 2 x gyroscopes MPU-6050
- 1 x NES controller
- 1 x display + cable to connect RPI and display (ex: HDMI cable).
- Wiring to connect RPi and gyroscopes

------------------------------------------------------------------------
CONFIGURATION GUIDE
------------------------------------------------------------------------

The methods below present how to configure a Rsapberry Pi for running
the Skatepong game.

------------------------------------------------------------------------
METHOD 1 : Script installation
------------------------------------------------------------------------

Run the scripts found in this repository in the following order :
./install_skatepong_system.sh
./install_skatepong_project.sh
=> This clones the git repository in : "/home/<user>/opt/"
The game automatically starts at boot, otherwise it is also possible to 
start it by running the following command from the git folder :
./run_skatepong_sh

------------------------------------------------------------------------
METHOD 2 : Manual installation using poetry
------------------------------------------------------------------------

1 - Activate the i2c communication in your Rspberry Pi and reboot.

2 - Clone the Skatepong git repository and open a terminal from this folder:

3 - Create a Python virutal environment.

4 - Activate the virtual environment :
. .venv/bin/activate

5 - Install poetry on your virtual environment :
pip3 install poetry

6 - Run poetry (using the project configuration files):
poetry install

7 - Install the following packages on your system :
sudo apt install python3-smbus i2c-tools
sudo apt install libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 libsdl2-ttf-2.0-0
sudo apt install libsdl2-dev
sudo apt install qjoypad # For game controller
sudo apt install unclutter # To hide mouse cursor

8 - Copy the file "controller_config/ness_controller_skatepong.lyt" 
in the folder "/home/<user_name>/.qjoypad3". 
Note : DO NOT RENAME THE FILE

9 - To start the game, from the git folder :
./run_skatepong.sh

------------------------------------------------------------------------
METHOD 3 : Manual installation using PIP
------------------------------------------------------------------------

1 - Activate the i2c communication in your Rspberry Pi and reboot.

2 - Clone the Skatepong git repository.

3 - Create a Python virutal environment.

4 - Activate the virtual environment :
. .venv/bin/activate

5 - Install packages via PIP3 on your virtual environment:
pip3 install mpu6050-raspberrypi
pip3 install smbus
pip3 install smbus2 #Module that replaces "smbus"
pip3 install pygame

6 - Install the following packages on your system :
sudo apt install python3-smbus i2c-tools
sudo apt install libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 libsdl2-ttf-2.0-0
sudo apt install libsdl2-dev
sudo apt install qjoypad # For game controller
sudo apt install unclutter # To hide mouse cursor

7 - Copy the file "controller_config/ness_controller_skatepong.lyt" 
in the folder "/home/<user_name>/.qjoypad3". 
Note : DO NOT RENAME THE FILE

8 - To start the game, from the git folder :
./run_skatepong.sh

------------------------------------------------------------------------
IN CASE OF ISSUES
------------------------------------------------------------------------

- If issues are raised related to ".h" files:
sudo apt install gcc linux-headers

- If issues are raised with SDL2 packages:
sudo apt install python3-pygame-sdl2

- If previous solutions are not sufficient, try:
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
sudo apt install libfreetype6-dev libportmidi-dev libjpeg-dev 
sudo apt install python3-setuptools python3-dev python3-numpy

Copyright © 2023 Quentin BENETHUILLERE. All rights reserved.
