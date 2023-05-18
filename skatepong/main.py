#!usr/bin/python3

"""
Copyright © 2023 Quentin BENETHUILLERE. All rights reserved.
"""

#-----------------------------------------------------------------------
# IMPORTS
#-----------------------------------------------------------------------

import skatepong.game
import skatepong.constants as skt_cst

#-----------------------------------------------------------------------
# CODE
#-----------------------------------------------------------------------

def main():
    """
    2 players pong game, with real skateboards as actuators.
    
    - Objective : Shoot the ball beyond the oponent's zone (+1 point).
    - End : Game ends when a player reaches a given number of points.
    - The two paddles are controlled independently based on the angular
      rotation measured by the gyroscopes mounted under each skateboard.
      
    - Games scenes :
        WELCOME : Splash screen at application start.
        WAITING_GYROS : Waiting that both gyroscopes are connected.
        WAITING_PLAYERS : Waiting for motion on both skates.
        COUNTDOWN : Countdown before the actual game starts.
        GAME_ONGOING : Game running.
        GAME_END : Game has ended, the winner is announced.
        AUTO_CALIBRATION : Pads calib. once steady skates bef. new game.
        CALIBRATION_REQUESTED : Paddles calibratation upon request.
    """

    game = skatepong.game.Game(full_screen = True)
    while True:
        if game.game_status == skt_cst.SCENE_WELCOME:
            game.welcome()
        elif game.game_status == skt_cst.SCENE_WAITING_GYROS:
            game.wait_gyros()
            game.create_game_elements()
        elif game.game_status == skt_cst.SCENE_WAITING_PLAYERS:
            game.wait_players()
        elif game.game_status == skt_cst.SCENE_COUNTDOWN:
            game.countdown()
        elif game.game_status == skt_cst.SCENE_GAME_ONGOING:
            game.game_ongoing()
        elif game.game_status == skt_cst.SCENE_GAME_END:
            game.game_end()
        elif game.game_status == skt_cst.SCENE_CALIBRATION_REQUESTED:
            game.calibrate_pads()

if __name__ == '__main__':
    main()

"""
Copyright © 2023 Quentin BENETHUILLERE. All rights reserved.
"""
