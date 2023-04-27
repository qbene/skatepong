#!usr/bin/python3

#-----------------------------------------------------------------------
# IMPORTS
#-----------------------------------------------------------------------

import skatepong.game

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
        CALIBRATION : Allows paddles calibratation upon request.
    """

    # Game scenes (used for game navigation):
    SCENE_WELCOME = 0
    SCENE_WAITING_GYROS = 1
    SCENE_WAITING_PLAYERS = 2
    SCENE_COUNTDOWN = 3
    SCENE_GAME_ONGOING = 4
    SCENE_GAME_END = 5
    SCENE_CALIBRATION = 6

    game = skatepong.game.Game(dev_mode = True)
    while True:
        
        if game.game_status == SCENE_WELCOME:
            game.welcome()
        elif game.game_status == SCENE_WAITING_GYROS:
            game.wait_gyros()
            game.create_game_elements()
        elif game.game_status == SCENE_WAITING_PLAYERS:
            game.wait_players()
        elif game.game_status == SCENE_COUNTDOWN:
            game.countdown()
        elif game.game_status == SCENE_GAME_ONGOING:
            game.game_ongoing()
        elif game.game_status == SCENE_GAME_END:
            game.game_end()
        elif game.game_status == SCENE_CALIBRATION:
            game.calibrate_pads()
       
if __name__ == '__main__':
    main()
