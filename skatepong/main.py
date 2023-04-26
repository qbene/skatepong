#!usr/bin/python3

#------------------------------------------------------------------------------
# IMPORTS
#------------------------------------------------------------------------------

#import pygame
import skatepong.game

#------------------------------------------------------------------------------
# DEVELOPMENT VARIABLES
#------------------------------------------------------------------------------

DEV_MODE = True # Used to avoid full screen display mode during dev phase.
"""
#------------------------------------------------------------------------------
# CONSTANTS THAT CAN BE ADJUSTED
#------------------------------------------------------------------------------

# Game parameters
WINNING_SCORE = 10 # Number of goals to win the game
BALL_ANGLE_MAX = 60 # Max angle after paddle collision (degrees) [30-75]
VELOCITY_ANGLE_FACTOR = 2 # Allows to increase ball velocity when angle (longer distance) [2 - 3]
# Delays
DELAY_INACT_PLAYER = 5 # Delay after which a player is considered inactive (s)
DELAY_COUNTDOWN = 3 # Countdown initial time before starting the game (s)
DELAY_GAME_END = 5 # Delay after game ends (s)
DELAY_BEF_PAD_CALIB = 10 # Delay before paddles calibration starts (s)
DELAY_AFT_PAD_CALIB = 10 # Delay after paddles calibration is done (s)
# Technical parameters
FPS = 60 # Max number of frames per second
#GYRO_SENSITIVITY = mpu6050.GYRO_RANGE_500DEG
'''Possible values:
mpu6050.GYRO_RANGE_250DEG
mpu6050.GYRO_RANGE_500DEG
mpu6050.GYRO_RANGE_1000DEG
mpu6050.GYRO_RANGE_2000DEG
'''
# Sizes ([indicates recommended values])
WELCOME_RADIUS_RATIO = 0.25 # Ratio to screen height [0.1 - 0.5]
PAD_WIDTH_RATIO = 0.015 # Ratio to screen width [0.005 - 0.1]
PAD_HEIGHT_RATIO = 0.2 # Ratio to screen height [0.05 - 0.2]
PAD_X_OFFSET_RATIO = 0.02 # Ratio to screen width [0.01 - 0.02] - Frame offset
BALL_RADIUS_RATIO = 0.02 # Ratio to min screen width/height [0.01 - 0.04]
PAD_FLAT_BOUNCE_RATIO = 0.01 # # Ratio to screen width [0.005 - 0.02]
BALL_V_RATIO = 0.025 # Ratio to min screen width [0.005 - 0.025]
MID_LINE_HEIGHT_RATIO = 0.05 # Ratio to screen height [ideally 1/x -> int]
MID_LINE_WIDTH_RATIO = 0.006 # Ratio to screen width [0.005 - 0.01]
SCORE_Y_OFFSET_RATIO = 0.02 # Ratio to screen height (to set score vertically)
CENTER_CROSS_MULTIPLIER = 3 # To be multiplied with MID_LINE_WIDTH_RATIO [2 - 5]
# Texts
FONT_NAME = "comicsans" # Font used for texts
FONT_RATIO_0_05 = 0.05 # Ratio to screen height
FONT_RATIO_0_1 = 0.1 # Ratio to screen height
FONT_RATIO_0_15 = 0.15 # Ratio to screen height
FONT_RATIO_0_2 = 0.2 # Ratio to screen height
"""
#------------------------------------------------------------------------------
# CONSTANTS
#------------------------------------------------------------------------------

# Game scenes (used to navigate between one another) :
SCENE_WELCOME = 0
SCENE_WAITING_GYROS = 1
SCENE_WAITING_PLAYERS = 2
SCENE_COUNTDOWN = 3
SCENE_GAME_ONGOING = 4
SCENE_GAME_END = 5
SCENE_CALIBRATION = 6

"""
# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (127, 127, 127)
"""

#------------------------------------------------------------------------------
# CODE
#------------------------------------------------------------------------------

def main():
    """
    Skatepong is a pong game for 2 players, with real skateboards as actuators.
    
    - Objective : 1 point each time a player shoots the ball inside the oponent's zone.
    - End : Game stops after a given number of points has been reached.
    - The 2 paddles are controlled independently based on the movements detected
    by a gyroscope mounted under each skateboard.
    - Scenes description :
        SCENE_WELCOME : Splash screen at game start.
        SCENE_WAITING_PLAYERS : Waiting for motion on both skates.
        SCENE_COUNTDOWN : Countdown before the game actually starts.
        SCENE_GAME_ONGOING : Game itself.
        SCENE_GAME_END : Announces the winner, with final score.
        SCENE_CALIBRATION : Allows to calibrate paddles when requested by user.
    """

    game = skatepong.game.Game(dev_mode = True)
    while True:
        
        if game.game_status == SCENE_WELCOME:
            game.welcome()
        elif game.game_status == SCENE_WAITING_GYROS: # Waiting for gyroscopes to be connected
            game.wait_gyros()
            game.create_game_elements()
        elif game.game_status == SCENE_WAITING_PLAYERS: # Waiting for players
            game.wait_players()
        elif game.game_status == SCENE_COUNTDOWN: # Countdown before start
            game.countdown()
        elif game.game_status == SCENE_GAME_ONGOING: # Game ongoing
            game.game_ongoing()
        elif game.game_status == SCENE_GAME_END: # Game finished
            game.game_end()
        elif game_status == SCENE_CALIBRATION: # Paddle/Gyroscopes calibration
            game.calibrate_pads()
       
if __name__ == '__main__':
    main()
