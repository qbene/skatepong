#!usr/bin/python3

"""
Copyright © 2023 Quentin BENETHUILLERE. All rights reserved.
"""

#-----------------------------------------------------------------------
# IMPORTS
#-----------------------------------------------------------------------

import pygame
import time
import math
import random
import os
import sys
from mpu6050 import mpu6050
import skatepong.gyro as skt_gyro
import skatepong.tools as skt_tls
import skatepong.game_objects as skt_obj
import skatepong.constants as skt_cst

#-----------------------------------------------------------------------
# CODE
#-----------------------------------------------------------------------

class Game():

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
        GAME_END : Winner is announced + pads calib before next game
        CALIBRATION_REQUESTED : Paddles calibratation upon request.
    """

    #-------------------------------------------------------------------
    # GAME PARAMETERS
    #-------------------------------------------------------------------

    # Main game parameters
    WINNING_SCORE = 10 # Number of goals to win the game
    BALL_ANGLE_MAX = 50 # Max angle after paddle collision (deg) [35-65]
    # Delays
    DELAY_WELCOME = 4 # Splash screen duration (s)
    DELAY_INACT_PLAYER = 5 # Delay before a player becomes inactive (s)
    DELAY_COUNTDOWN = 5 # Countdown before game starts (s)
    DELAY_MAX_GAME_END = 15 # Delay max after game ends before calib (s)
    DELAY_STEADY_BEF_CALIB = 3 # Duration steady skates before calib (s)
    # Technical parameters
    FPS = 25 # Max frames/sec (30 seems good compromise for RPI3 / RPI4)
    GYRO_SENSITIVITY = mpu6050.GYRO_RANGE_1000DEG
    """
    For GYRO_SENSITIVITY, use one of the following constants:
    mpu6050.GYRO_RANGE_250DEG = 0x00 # +/- 125 deg/s
    mpu6050.GYRO_RANGE_500DEG = 0x08 # +/- 250 deg/s
    mpu6050.GYRO_RANGE_1000DEG = 0x10 # +/- 500 deg/s
    mpu6050.GYRO_RANGE_2000DEG = 0x18 # +/- 1000 deg/s
    """
    # Sizes ([indicates recommended values])
    WELCOME_RADIUS_RATIO = 0.25 # Rat. disp. h [0.1 - 0.5]
    PAD_WIDTH_RATIO = 0.015 # Rat. disp. w [0.005 - 0.1]
    PAD_HEIGHT_RATIO = 0.2 # Rat. disp. h [0.05 - 0.2]
    PAD_X_OFFSET_RATIO = 0.02 # Rat. disp. w [0.01 - 0.02] frame offset
    BALL_RADIUS_RATIO = 0.02 # Rat. min disp. w/h [0.01 - 0.04]
    PAD_FLAT_BOUNCE_RATIO = 0.02 # Rat. disp. w [0.01 - 0.03]
    BALL_V_RATIO = 0.035 # Rat. disp. w [0.01 - 0.04]
    MID_LINE_WIDTH_RATIO = 0.006 # Rat. disp. w [0.005 - 0.01]
    SCORE_Y_OFFSET_RATIO = 0.02 # Rat. disp. h - frame vertical offset
    CENTER_CROSS_MULTIPLIER = 3 # Mid line thikness factor [2 - 5]
    # Text fonts parameters (names and sizes)
    FT_NM = "comicsans" # or 'quicksandmedium'. Font used for texts.
    # Other parameters
    GYRO_ACTIVE_RATIO = 0.07 # Rat. angular velocity / gyro sensitivity
    GYRO_STEADY_RATIO = 0.02 # Rat. angular velocity / gyro sensitivity
    PAD_VY_FACTOR_RPI3 = 0.70 #Factor to adjust paddle displacement
    PAD_VY_FACTOR_RPI4 = 0.60 #Factor to adjust paddle displacement
    

    def __init__(self, game_status = 0, l_score = 0, r_score = 0, \
    full_screen = True):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.game_status = game_status
        self.l_score = l_score
        self.r_score = r_score
        self.full_screen = full_screen
        self.win, self.win_w, self.win_h = self.create_window()
        self.ft_dic = skt_tls.comp_font_sizes(self.win_h)
        self.x_dic, self.y_dic = skt_tls.comp_common_coordinates( \
                                 self.win_w, self.win_h)

    #-------------------------------------------------------------------
    # SIDE FUNCTIONS
    #-------------------------------------------------------------------

    def create_window(self):
        """
        Initializes game window, and adjusts size to display resolution.
        """
        disp_w = pygame.display.Info().current_w # Disp. width (px)
        disp_h = pygame.display.Info().current_h # Disp. height (px)
        print ("Display resolution :", disp_w, disp_h)
        # Getting raspberry pi HW version (through cpu revision)
        cpu_rev = skt_tls.get_cpu_revision()
        rpi_4b = skt_tls.is_rpi_4b(cpu_rev)
        # Adjusting game resolution and paddle displacement factor
        # (a little different due to different game speed with RPI3/4)
        if rpi_4b == True:
            self.pad_vy_factor = self.PAD_VY_FACTOR_RPI4
            pass
        # If RPI HW < Mod 4B, game resolution reduc. to avoid lags
        else:
            self.pad_vy_factor = self.PAD_VY_FACTOR_RPI3
            # Most commom resolution for TV: 1920 x 1080
            if disp_w == 1920 and disp_h == 1080:
                print ("Game resolution reduced vs display resolution",\
                "for better performances on RPI 3 Model B+")
                disp_w = 1280
                disp_h = 720
            # If other wide reso, adjust h to keep A/R with w = 1280
            elif disp_w > 1280:
                print ("Game resolution reduced vs display resolution",\
                "for better performances on RPI 3 Model B+")
                disp_h = 1280 * disp_h / disp_w
                disp_w = 1280
        if self.full_screen == False:
            win = pygame.display.set_mode([disp_w, disp_h - 100])
            pygame.display.set_caption("Skatepong")
        else:
            win = pygame.display.set_mode([disp_w, disp_h], \
                                          pygame.FULLSCREEN)
        time.sleep(1/2) # Introduced after some failure at game init.
        win_w , win_h = pygame.display.get_surface().get_size()
        print ("Game resolution :", win_w, win_h)
        return win, win_w, win_h

    def comp_elem_sizes(self):
        """
        Computes game elements sizes/speeds based on display resolution.
        """
        pad_w = int(self.win_w * self.PAD_WIDTH_RATIO)
        pad_h = int(self.win_h * self.PAD_HEIGHT_RATIO)
        ball_r = min(int(self.win_w * self.BALL_RADIUS_RATIO), \
                     int(self.win_h * self.BALL_RADIUS_RATIO))
        ball_vx_straight = int(self.win_w * self.BALL_V_RATIO)
        return pad_w, pad_h, ball_r, ball_vx_straight

    def create_game_elements(self):
        """
        Creates game objects at program start.
        - Paddles centered vertically.
        - Ball centered horizontally and vertically.
        """
        pad_w, pad_h, ball_r, ball_vx_straight = self.comp_elem_sizes()
        l_pad_x =  int(self.win_w * self.PAD_X_OFFSET_RATIO)
        r_pad_x = self.win_w - int(self.PAD_X_OFFSET_RATIO*self.win_w) \
                  - pad_w
        pad_y = (self.win_h - pad_h) // 2
        self.l_pad = skt_obj.Paddle(self.win, self.win_h, l_pad_x, \
                     pad_y, pad_w, pad_h, skt_cst.WHITE, self.l_gyro, \
                     self.pad_vy_factor)
        self.r_pad = skt_obj.Paddle(self.win, self.win_h, r_pad_x, \
                     pad_y, pad_w, pad_h, skt_cst.WHITE, self.r_gyro, \
                     self.pad_vy_factor)
        self.ball = skt_obj.Ball(self.win, self.x_dic["0.50"], \
                                self.y_dic["0.50"], ball_r, \
                                skt_cst.WHITE, ball_vx_straight, 0, 0)

    def reinitialize_gyro_if_needed(self):
        """
        Recreates gyroscopes objects following deconnections.
        """
        if self.l_gyro.error:
            print("Issue : i2c communication with left gyroscope lost")
            try:
                self.l_gyro = skt_gyro.Gyro_one_axis( \
                            skt_gyro.Gyro_one_axis.I2C_ADDRESS_1,\
                            'y', self.GYRO_SENSITIVITY)
            except IOError:
                pass
            else:
                print("Left gyroscope reconnected")
                self.l_pad.gyro = self.l_gyro
        if self.r_gyro.error:
            print("Issue : i2c communication with right gyroscope lost")
            try:
                self.r_gyro = skt_gyro.Gyro_one_axis( \
                            skt_gyro.Gyro_one_axis.I2C_ADDRESS_2,\
                            'y', self.GYRO_SENSITIVITY)
            except IOError:
                pass
            else:
                print("Right gyroscope reconnected")
                self.r_pad.gyro = self.r_gyro

    def draw_game_objects(self, draw_pads = False, draw_ball = False, \
                          draw_scores = False, draw_line = False):
        """
        Draws the desired game elements (pads / ball / scores)
        Note : Each game scene do not require every single game object
        """
        l_score_rect = None
        r_score_rect = None
        l_pad_rect = None
        r_pad_rect = None
        ball_rect = None
        mid_line_h_rect = None
        mid_line_v_rect = None
        if draw_scores == True:
            txt_l = str(self.l_score)
            txt_r = str(self.r_score)
            l_score_rect = skt_tls.draw_text(self.win, self.FT_NM, \
                           self.ft_dic["0.10"], txt_l, \
                           self.x_dic["0.25"], self.y_dic["0.10"], \
                           skt_cst.WHITE)
            r_score_rect = skt_tls.draw_text(self.win, self.FT_NM, \
                           self.ft_dic["0.10"], txt_r, \
                           self.x_dic["0.75"], self.y_dic["0.10"], \
                           skt_cst.WHITE)
        if draw_pads == True:
            l_pad_rect = self.l_pad.draw(skt_cst.WHITE)
            r_pad_rect = self.r_pad.draw(skt_cst.WHITE)
        if draw_ball == True:
            ball_rect = self.ball.draw(skt_cst.WHITE)
        if draw_line == True:
            thick = int(self.win_w * self.MID_LINE_WIDTH_RATIO)
            horiz_w_factor = self.CENTER_CROSS_MULTIPLIER
            mid_line_h_rect, mid_line_v_rect = skt_tls.draw_mid_line(\
                                               self.win, self.win_w, \
                                               self.win_h, thick, \
                                               horiz_w_factor, \
                                               skt_cst.WHITE)

        return l_score_rect, r_score_rect, l_pad_rect, r_pad_rect, \
               ball_rect, mid_line_h_rect, mid_line_v_rect

    def erase_game_objects(self, color, pads = True, ball = True, \
                           scores = True):
        """
        Erases display of previous positions for changing game elements
        Note : This includes both pads / ball / scores.
        """
        l_sc_rect = None
        r_sc_rect = None
        l_pad_rect = None
        r_pad_rect = None
        ball_rect = None
        if scores == True:
            txt_l = str(self.l_score)
            txt_r = str(self.r_score)
            max_w_txt_sc = skt_tls.get_max_w_txt(self.FT_NM, \
                      self.ft_dic["0.10"], "1000")
            l_sc_rect =  pygame.Rect(0, 0, max_w_txt_sc, self.ft_dic["0.10"])
            r_sc_rect =  pygame.Rect(0, 0, max_w_txt_sc, self.ft_dic["0.10"])
            l_sc_rect.center = (self.x_dic["0.25"], self.y_dic["0.10"])
            r_sc_rect.center = (self.x_dic["0.75"], self.y_dic["0.10"])
            l_sc_rect = pygame.draw.rect(self.win, color, l_sc_rect)
            r_sc_rect = pygame.draw.rect(self.win, color, r_sc_rect)
        if pads == True:
            l_pad_rect = self.l_pad.draw(color)
            r_pad_rect = self.r_pad.draw(color)
        if ball == True:
            ball_rect = self.ball.draw(color)
        return l_sc_rect, r_sc_rect, l_pad_rect, r_pad_rect, ball_rect

    def check_user_inputs(self, keys):
        """
        Check user inputs (keyboards / mouse).
        Logic implemented with Ness controller
        ---------------------------------------------------------------
        Ness controller - Keyboard       - Explanation
        Button A        - Keyboard C     - Close / Calibrate
        Button B        - Keyboard B     - Simple mapping
        Button Start    - Keyboard R     - Restart game / Reboot
        Button Select   - Keyboard Space - No particular meaning
        ---------------------------------------------------------------
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        if keys[pygame.K_SPACE] \
        and keys[pygame.K_b] \
        and keys[pygame.K_r]:
            os.system("sudo reboot") # Raspberry reboot immediately
        elif keys[pygame.K_SPACE] \
        and keys[pygame.K_b] \
        and keys[pygame.K_c]:
            os.system("shutdown now") # Raspberry shuts down immediately
        elif keys[pygame.K_ESCAPE]:
            sys.exit()
        elif keys[pygame.K_c]:
            pygame.event.clear()
            self.game_status = skt_cst.SCENE_CALIBRATION_REQUESTED
            # Will only have effect if return statement in game code
        elif keys[pygame.K_r]:
            self.game_status = skt_cst.SCENE_WAITING_PLAYERS
            # Will only have effect if return statement in game code

    def detect_goal(self, goal_to_be):
        """
        Handles when goals are scored, and updates scores.
        """
        goal = False
        if self.ball.rect.left < 0:
            self.r_score += 1
            vx_dir_aft_goal = 1
            goal = True
        elif self.ball.rect.right > self.win_w:
            self.l_score += 1
            vx_dir_aft_goal = -1
            goal = True
        if goal == True:
            self.ball.reset()
            self.ball.vx = self.ball.vx_straight * vx_dir_aft_goal
            goal_to_be = False

        return goal_to_be

    def handle_walls_coll(self):
        """
        Handles collision between ball and top or bottom walls.
        """
        # Bottom wall
        if (self.ball.rect.bottom >= self.win_h):
            y_mod = self.win_h - self.ball.r
        # Top wall
        elif (self.ball.rect.top <= 0):
            y_mod = self.ball.r
        x_mod = int(self.ball.rect.centerx - ((self.ball.vx * \
                (self.ball.rect.centery - y_mod)) / self.ball.vy))
        self.ball.rect.center = (x_mod, y_mod)
        self.ball.vy *= -1

    def handle_l_coll(self, goal_to_be):
        """
        Handles collision between ball and left paddle.
        """
        if self.ball.rect.left <= self.l_pad.rect.right:
            x_mod = self.l_pad.rect.right + self.ball.r
            y_mod = int(self.ball.rect.centery \
                    - (self.ball.rect.centerx - x_mod) \
                    * self.ball.vy / self.ball.vx)
            # If ball colliding with paddle:
            if (y_mod + self.ball.r >= self.l_pad.rect.top \
            and y_mod - self.ball.r <= self.l_pad.rect.bottom):
                y_pad_mid = self.l_pad.rect.centery
                # Bounce angle calculation
                if (y_mod < (y_pad_mid + self.PAD_FLAT_BOUNCE_RATIO * self.win_h / 2) \
                and y_mod > (y_pad_mid - self.PAD_FLAT_BOUNCE_RATIO * self.win_h / 2)):
                    self.ball.vx = self.ball.vx_straight
                    self.ball.vy = 0
                else:
                    angle = int((abs(y_mod - y_pad_mid) - (self.PAD_FLAT_BOUNCE_RATIO * self.win_h / 2)) \
                       / ((self.r_pad.h + self.ball.r - self.PAD_FLAT_BOUNCE_RATIO * self.win_h) / 2) * self.BALL_ANGLE_MAX)
                    if y_mod > y_pad_mid:
                        vy = int(self.ball.vx_straight \
                                 * math.tan(math.radians(angle)))
                    else:
                        vy = -int(self.ball.vx_straight \
                                  * math.tan(math.radians(angle)))
                    self.ball.vx *= -1
                    self.ball.vy = vy
                self.ball.rect.center = (x_mod, y_mod)
            else:
                goal_to_be = True
        return goal_to_be

    def handle_r_coll(self, goal_to_be):
        """
        Handles collision between ball and right paddle.
        """
        if self.ball.rect.right >= self.r_pad.rect.left:
            x_mod = self.r_pad.rect.left - self.ball.r
            y_mod = int(self.ball.rect.centery \
                    - (self.ball.rect.centerx - x_mod) \
                    * self.ball.vy / self.ball.vx)
            # If ball colliding with paddle:
            if y_mod + self.ball.r >= self.r_pad.rect.top \
            and y_mod - self.ball.r <= self.r_pad.rect.bottom:
                y_pad_mid = self.r_pad.rect.centery
                # Bounce angle calculation
                if (y_mod < (y_pad_mid + self.PAD_FLAT_BOUNCE_RATIO * self.win_h / 2) \
                and y_mod > (y_pad_mid - self.PAD_FLAT_BOUNCE_RATIO * self.win_h / 2)):
                    self.ball.vx = -self.ball.vx_straight
                    self.ball.vy = 0
                else:
                    angle = int((abs(y_mod - y_pad_mid) - (self.PAD_FLAT_BOUNCE_RATIO * self.win_h / 2)) \
                    / ((self.r_pad.h + self.ball.r - self.PAD_FLAT_BOUNCE_RATIO * self.win_h) / 2) * self.BALL_ANGLE_MAX)
                    if y_mod > y_pad_mid:
                        vy = int(self.ball.vx_straight \
                        * math.tan(math.radians(angle)))
                    else:
                        vy = -int(self.ball.vx_straight \
                        * math.tan(math.radians(angle)))
                    # Keeping vx constant all the time
                    self.ball.vx *= -1
                    self.ball.vy = vy
                self.ball.rect.center = (x_mod, y_mod)
            else:
                goal_to_be = True
        return goal_to_be

    def check_collision(self):
        """
        Detects possible collisions between ball and walls or pads.
        """
        bot_coll = False
        top_coll = False
        l_coll = False
        r_coll = False
        if (self.ball.rect.bottom >= self.win_h):
            bot_coll = True
        elif (self.ball.rect.top <= 0):
            top_coll = True
        if ((self.ball.vx < 0) \
        and (self.ball.rect.left <= self.l_pad.rect.right)):
            l_coll = True
        elif ((self.ball.vx > 0) \
        and (self.ball.rect.right >= self.r_pad.rect.left)):
            r_coll = True

        return bot_coll, top_coll, l_coll, r_coll

    def handle_collision(self, goal_to_be):
        """
        Handles ball collision with paddles and top/bottom walls.

        - Calculates ball horizontal and vertical velocities.
        - Calculates ball angle after collision with paddle depending.
        ...on the collision point.
        """

        bot_coll, top_coll, l_coll, r_coll = self.check_collision()

        # Left paddle possible collision case
        if (l_coll and goal_to_be == False):
            # Ball also colliding with bottom wall
            if bot_coll:
                y_mod = self.win_h - self.ball.r
            # Ball also colliding with top wall
            elif top_coll:
                y_mod = self.ball.r
            # Which collision first: top/bottom wall or left paddle ?
            if bot_coll or top_coll:
                x_mod = int(self.ball.rect.centerx - ((self.ball.vx * \
                     (self.ball.rect.centery - y_mod)) / self.ball.vy))
                # Top/bottom wall collision first :
                if x_mod > (self.l_pad.rect.right):
                    self.handle_walls_coll()
                # Left padlle collision first if paddle well positioned
                else:
                    goal_to_be = self.handle_l_coll(goal_to_be)
                    # If left pad not well positioned, goal will happen,
                    # but still needs to manage bouncing on walls
                    if goal_to_be:
                        self.handle_walls_coll()
            # Left paddle collision possible and no wall collision
            else:
                goal_to_be = self.handle_l_coll(goal_to_be)

        # Right paddle possible collision case
        elif (r_coll and goal_to_be == False):
            # Ball also colliding with bottom wall
            if bot_coll:
                y_mod = self.win_h - self.ball.r
            # Ball also colliding with top wall
            elif top_coll:
                y_mod = self.ball.r
            # Which collision first: top/bottom wall or right paddle ?
            if bot_coll or top_coll:
                x_mod = int(self.ball.rect.centerx - ((self.ball.vx * \
                     (self.ball.rect.centery - y_mod)) / self.ball.vy))
                # Top/bottom wall collision first :
                if x_mod < self.r_pad.x:
                    self.handle_walls_coll()
               # Right padlle collision first if paddle well positioned
                else:
                    goal_to_be = self.handle_r_coll(goal_to_be)
                    # If right pad not well positioned, goal will happen
                    # but still needs to manage bouncing on walls
                    if goal_to_be:
                        self.handle_walls_coll()
            # Right paddle collision possible and no wall collision
            else:
                goal_to_be = self.handle_r_coll(goal_to_be)

        # No possible collision with pads, but wall collision possible
        elif (bot_coll or top_coll):
            self.handle_walls_coll()

        return goal_to_be

    #-------------------------------------------------------------------
    # GAME STATES
    #-------------------------------------------------------------------

    def welcome(self):
        """
        Displays splash screen for a certain duration at program start.
        """
        start_time = time.time()
        current_time = time.time()

        # Managing display:
        """
        Try loop added to bypass display error that occurs sometines \
        at startup when display resolution needs to be reduced.
        """
        try:
            self.win.fill(skt_cst.BLACK)
            r = int(self.WELCOME_RADIUS_RATIO * self.win_h)
            pygame.draw.circle(self.win, skt_cst.WHITE, \
                            (self.x_dic["0.50"], self.y_dic["0.50"]), r)
            txt = "SKATEPONG"
            skt_tls.draw_text(self.win, self.FT_NM, \
                              self.ft_dic["0.10"], txt, \
                              self.x_dic["0.50"], self.y_dic["0.50"], \
                              skt_cst.BLACK)
            pygame.display.update()
        except:
            print ("Reinitializing display...")
            self.win, self.win_w, self.win_h = self.create_window()
            self.welcome()

        while current_time - start_time < self.DELAY_WELCOME:
            self.clock.tick(self.FPS)
            # Checking requests for closing game window / rebooting/shutting down RPI:
            # Note: Restarting game / calibrating requests have no impact
            keys = pygame.key.get_pressed()
            self.check_user_inputs(keys)
            # Updating current time
            current_time = time.time()
        self.game_status = skt_cst.SCENE_WAITING_GYROS

    def wait_gyros(self):
        """
        Game does not start until both skateboards are connected.
        """
        status = 0
        loop_nb = 1
        l_gyro_connected = False
        r_gyro_connected = False
        txt_fr_1 = "VEUILLEZ CONNECTER LA PLANCHE GAUCHE"
        txt_en_1 = "PLEASE CONNECT LEFT SKATEBOARD"
        txt_fr_2 = "VEUILLEZ CONNECTER LA PLANCHE DROITE"
        txt_en_2 = "PLEASE CONNECT RIGHT SKATEBOARD"
        txt_fr_3 = "VEUILLEZ CONNECTER LES PLANCHES"
        txt_en_3 = "PLEASE CONNECT SKATEBOARDS"
        max_w_txt_fr = skt_tls.get_max_w_txt(self.FT_NM, \
                      self.ft_dic["0.10"], txt_fr_1, txt_fr_2, txt_fr_3)
        max_w_txt_en = skt_tls.get_max_w_txt(self.FT_NM, \
                      self.ft_dic["0.10"], txt_en_1, txt_en_2, txt_en_3)
        # Reinitializing display:
        self.win.fill(skt_cst.BLACK)

        while not (l_gyro_connected and r_gyro_connected):

            self.clock.tick(self.FPS)

            l_gyro_connected = False
            r_gyro_connected = False
            prev_status = status

            # Checking user requests :
            # -> closing game window / rebooting / shutting down RPI
            # Note: Restarting game / calibrating not available here
            keys = pygame.key.get_pressed()
            self.check_user_inputs(keys)

            # Left gyro test :
            try:
                self.l_gyro = skt_gyro.Gyro_one_axis( \
                              skt_gyro.Gyro_one_axis.I2C_ADDRESS_1, \
                              'y', self.GYRO_SENSITIVITY)
            except IOError:
                l_gyro_connected = False
            else:
                l_gyro_connected = True
            # Right gyro test :
            try:
                self.r_gyro = skt_gyro.Gyro_one_axis( \
                              skt_gyro.Gyro_one_axis.I2C_ADDRESS_2, \
                              'y', self.GYRO_SENSITIVITY)
            except IOError:
                r_gyro_connected = False
            else:
                r_gyro_connected = True
            # Status summary :
            if not (l_gyro_connected and r_gyro_connected):
                if r_gyro_connected == True:
                    status = 1
                elif l_gyro_connected == True:
                    status = 2
                else:
                    status = 3
            # Updating display if status has changed :
            if status != prev_status:
                if status == 1:
                    txt_fr = txt_fr_1
                    txt_en = txt_en_1
                elif status == 2:
                    txt_fr = txt_fr_2
                    txt_en = txt_en_2
                elif status == 3:
                    txt_fr = txt_fr_3
                    txt_en = txt_en_3
                # Black rect above max text area + new text displayed.
                txt_fr_max_rect = pygame.Rect(0, 0, max_w_txt_fr, self.ft_dic["0.10"])
                txt_en_max_rect = pygame.Rect(0, 0, max_w_txt_en, self.ft_dic["0.10"])
                txt_fr_max_rect.center = (self.x_dic["0.50"], self.y_dic["0.40"])
                txt_en_max_rect.center = (self.x_dic["0.50"], self.y_dic["0.60"])
                txt_fr_max_rect = pygame.draw.rect(self.win, skt_cst.BLACK, txt_fr_max_rect)
                txt_en_max_rect = pygame.draw.rect(self.win, skt_cst.BLACK, txt_en_max_rect)
                txt_fr_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], txt_fr, \
                                  self.x_dic["0.50"], self.y_dic["0.40"], skt_cst.WHITE)
                txt_en_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], txt_en, \
                                  self.x_dic["0.50"], self.y_dic["0.60"], skt_cst.GREY)
                if loop_nb == 1:
                    pygame.display.update()
                    loop_nb += 1
                else:
                    pygame.display.update([txt_fr_max_rect, \
                                           txt_en_max_rect, \
                                           txt_fr_rect, txt_en_rect])

        self.game_status = skt_cst.SCENE_WAITING_PLAYERS

    def wait_players(self):
        """
        Standby before detection of active players on each skateboard.
        Note : paddles active.
        """
        moving_time = time.time()
        current_time = time.time()
        status = 0
        left_player_ready = False
        right_player_ready = False
        self.ball.reset()
        loop_nb = 1
        pygame.event.get() # Solves pad calib done twice consecutively

        txt_fr_0 = "PIVOTEZ LES PLANCHES POUR DEBUTER LA PARTIE"
        txt_en_0 = "MOVE SKATES TO START GAME"
        txt_fr_1 = "EN ATTENTE DU JOUEUR GAUCHE"
        txt_en_1 = "WAITING FOR LEFT PLAYER"
        txt_fr_2 = "EN ATTENTE DU JOUEUR DROIT"
        txt_en_2 = "WAITING FOR RIGHT PLAYER"
        txt_fr_3 = "EN ATTENTE DES JOUEURS"
        txt_en_3 = "WAITING FOR PLAYERS"

        max_w_txt_fr = skt_tls.get_max_w_txt(self.FT_NM, \
                      self.ft_dic["0.10"], txt_fr_1, txt_fr_2, txt_fr_3)
        max_w_txt_en = skt_tls.get_max_w_txt(self.FT_NM, \
                      self.ft_dic["0.10"], txt_en_1, txt_en_2, txt_en_3)

        # Reinitializing display:
        self.win.fill(skt_cst.BLACK)
        # The message below is always displayed until players are ready:
        txt_fr_0_rect = skt_tls.draw_text(self.win, self.FT_NM, \
                     self.ft_dic["0.05"], txt_fr_0, self.x_dic["0.50"],\
                     self.y_dic["0.30"], skt_cst.WHITE)
        txt_en_0_rect = skt_tls.draw_text(self.win, self.FT_NM, \
                     self.ft_dic["0.05"], txt_en_0, self.x_dic["0.50"],\
                     self.y_dic["0.80"], skt_cst.GREY)

        while not (left_player_ready and right_player_ready):

            self.clock.tick(self.FPS)
            prev_status = status

            # Checking user requests :
            # -> closing game window / rebooting / shutting down RPI
            # Note: Restarting game / calibrating not available here
            keys = pygame.key.get_pressed()
            self.check_user_inputs(keys)

            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            # Going to paddles calibration scene upon user request:
            if self.game_status == skt_cst.SCENE_CALIBRATION_REQUESTED:
                return

            if not (left_player_ready and right_player_ready):
                if right_player_ready == True:
                    status = 1
                elif left_player_ready == True:
                    status = 2
                else:
                    status = 3
            # Updating display if status has changed :
            if status != prev_status:
                if status == 1:
                    txt_fr = txt_fr_1
                    txt_en = txt_en_1
                elif status == 2:
                    txt_fr = txt_fr_2
                    txt_en = txt_en_2
                elif status == 3:
                    txt_fr = txt_fr_3
                    txt_en = txt_en_3
                # Black rect above max text area + new text displayed.
                txt_fr_max_rect = pygame.Rect(0, 0, max_w_txt_fr, self.ft_dic["0.10"])
                txt_en_max_rect = pygame.Rect(0, 0, max_w_txt_en, self.ft_dic["0.10"])
                txt_fr_max_rect.center = (self.x_dic["0.50"], self.y_dic["0.20"])
                txt_en_max_rect.center = (self.x_dic["0.50"], self.y_dic["0.70"])
                txt_fr_max_rect = pygame.draw.rect(self.win, skt_cst.BLACK, txt_fr_max_rect)
                txt_en_max_rect = pygame.draw.rect(self.win, skt_cst.BLACK, txt_en_max_rect)
                txt_fr_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], txt_fr, \
                                  self.x_dic["0.50"], self.y_dic["0.20"], skt_cst.WHITE)
                txt_en_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], txt_en, \
                                  self.x_dic["0.50"], self.y_dic["0.70"], skt_cst.GREY)
                if loop_nb == 1:
                    pass
                else:
                    pygame.display.update([txt_fr_max_rect, \
                                           txt_en_max_rect, \
                                           txt_fr_rect, txt_en_rect])

            # Erasing from display objects previous positions:
            l_score_rect_old, r_score_rect_old, l_pad_rect_old, \
            r_pad_rect_old, ball_rect_old = self.erase_game_objects( \
                                            color = skt_cst.BLACK, \
                                            pads = True, ball = True, \
                                            scores = True)
            # Moving objects:
            vy_l_pad, l_gyro_ratio = self.l_pad.move(self.win_h)
            vy_r_pad, r_gyro_ratio = self.r_pad.move(self.win_h)
            # Adding to display objects new positions:
            l_score_rect, r_score_rect, l_pad_rect, r_pad_rect, ball_rect,\
            mid_line_h_rect, mid_line_v_rect = self.draw_game_objects(\
                                               draw_pads = True, \
                                               draw_ball = True, \
                                               draw_scores = False, \
                                               draw_line = False)
            # Updating the necessary parts of the display:
            if loop_nb == 1:
                pygame.display.update()
                loop_nb += 1
            else:
                pygame.display.update([l_pad_rect_old, r_pad_rect_old, \
                                       ball_rect_old, l_pad_rect, \
                                       r_pad_rect, ball_rect])
            
            if abs(l_gyro_ratio) > self.GYRO_ACTIVE_RATIO:
                left_player_ready = True
                moving_time = time.time()
            if abs(r_gyro_ratio) > self.GYRO_ACTIVE_RATIO:
                right_player_ready = True
                moving_time = time.time()

            current_time = time.time()

            if current_time - moving_time > self.DELAY_INACT_PLAYER:
                left_player_ready = False
                right_player_ready = False

        self.game_status = skt_cst.SCENE_COUNTDOWN

    def countdown(self):
        """
        Starts a countdown before the game actually begins.

        Note : paddles active.
        """
        start_time = time.time()
        current_time = time.time()
        time_before_start = 0
        loop_nb = 1

        # Reinitializing display:
        self.win.fill(skt_cst.BLACK)
        max_w_txt_countdown = skt_tls.get_max_w_txt(self.FT_NM, \
                      self.ft_dic["0.20"], "100")
        while current_time - start_time < self.DELAY_COUNTDOWN:
            prev_time_before_start = time_before_start
            self.clock.tick(self.FPS)

            # Checking user requests :
            # -> closing game window / rebooting / shutting down RPI.
            # Note: Restarting game / calibrating not available here.
            keys = pygame.key.get_pressed()
            self.check_user_inputs(keys)
            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            time_before_start = self.DELAY_COUNTDOWN \
                                - int(current_time - start_time)

            # Updating countdown display if needed :
            if time_before_start != prev_time_before_start:
                countdown_rect_erase =  pygame.Rect(0, 0, max_w_txt_countdown, self.ft_dic["0.20"])
                countdown_rect_erase.center = (self.x_dic["0.50"], self.y_dic["0.25"])
                countdown_rect_erase = pygame.draw.rect(self.win, skt_cst.BLACK, countdown_rect_erase)
                txt = str(time_before_start)
                countdown_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.20"], txt, \
                                  self.x_dic["0.50"], self.y_dic["0.25"], skt_cst.WHITE)
                if loop_nb == 1:
                    pass
                else:
                    pygame.display.update([countdown_rect_erase, \
                                           countdown_rect])

            # Erasing from display objects previous positions:
            l_score_rect_old, r_score_rect_old, l_pad_rect_old, \
            r_pad_rect_old, ball_rect_old = self.erase_game_objects( \
                                            color = skt_cst.BLACK, \
                                            pads = True, \
                                            ball = True, \
                                            scores = False)
            # Moving objects:
            vy_l_pad, l_gyro_ratio = self.l_pad.move(self.win_h)
            vy_r_pad, r_gyro_ratio = self.r_pad.move(self.win_h)
            # Adding to display objects new positions:
            l_score_rect, r_score_rect, l_pad_rect, r_pad_rect, ball_rect, \
            mid_line_h_rect, mid_line_v_rect = self.draw_game_objects( \
                                               draw_pads = True, \
                                               draw_ball = True, \
                                               draw_scores = False, \
                                               draw_line = False)
            # Updating the necessary parts of the display:
            if loop_nb == 1:
                pygame.display.update()
                loop_nb += 1
            else:
                pygame.display.update([l_pad_rect_old, r_pad_rect_old, \
                                       ball_rect_old, l_pad_rect, \
                                       r_pad_rect, ball_rect])

            current_time = time.time()

        self.game_status = skt_cst.SCENE_GAME_ONGOING

    def game_ongoing(self):
        """
        Controls the game itself.
        """
        loop_nb = 1
        self.l_score = 0
        self.r_score = 0
        goal_to_be = False
        random_number = random.randint(1, 2)

        # Reinitializing display:
        self.win.fill(skt_cst.BLACK)

        # Determining ball direction at start.
        if random_number == 1:
            self.ball.vx =  self.ball.vx_straight # To the right
        else:
            self.ball.vx =  -self.ball.vx_straight # To the left

        while self.l_score < self.WINNING_SCORE \
        and self.r_score < self.WINNING_SCORE:

            self.clock.tick(self.FPS)
            # Checking user requests :
            # -> closing game window / rebooting / shutting down RPI.
            # -> Restarting game / calibrating available here.
            keys = pygame.key.get_pressed()
            self.check_user_inputs(keys)

            # Going to paddles calibration scene upon user request:
            if self.game_status == skt_cst.SCENE_CALIBRATION_REQUESTED \
            or self.game_status == skt_cst.SCENE_WAITING_PLAYERS:
                return

            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            # Erasing from display objects previous positions:
            l_score_rect_old, r_score_rect_old, l_pad_rect_old, \
            r_pad_rect_old, ball_rect_old = self.erase_game_objects(\
                                            color = skt_cst.BLACK, \
                                            pads = True, \
                                            ball = True, \
                                            scores = True)
            # Moving objects:
            vy_l_pad, l_gyro_ratio = self.l_pad.move(self.win_h)
            vy_r_pad, r_gyro_ratio = self.r_pad.move(self.win_h)
            self.ball.move()
            goal_to_be = self.handle_collision(goal_to_be)
            goal_to_be = self.detect_goal(goal_to_be)
            # Adding to display objects new positions:
            l_score_rect, r_score_rect, l_pad_rect, r_pad_rect, ball_rect, \
            mid_line_h_rect, mid_line_v_rect = self.draw_game_objects( \
                                               draw_pads = True, \
                                               draw_ball = True, \
                                               draw_scores = True, \
                                               draw_line = True)
            if loop_nb == 1:
                pygame.display.update()
            else:
                pygame.display.update([l_pad_rect_old, r_pad_rect_old,\
                        ball_rect_old, l_score_rect_old, \
                        r_score_rect_old, l_pad_rect, r_pad_rect, \
                        ball_rect, l_score_rect, r_score_rect, \
                        mid_line_h_rect, mid_line_v_rect])

            if self.l_score >= self.WINNING_SCORE \
            or self.r_score >= self.WINNING_SCORE:
                self.game_status = skt_cst.SCENE_GAME_END
                return

    def game_end(self):
        """
        Announces winner + calib. pads once steady skates bef. next game.
        Invites players to get down from skateboards before calibration.
        Note : paddles active.
        """
        start_time = time.time()
        current_time = time.time()
        moving_time = time.time()
        self.ball.reset()
        loop_nb = 1

        # Reinitializing display:
        self.win.fill(skt_cst.BLACK)

        if (self.l_score == self.WINNING_SCORE):
            txt_fr = "VICTOIRE DU JOUEUR DE GAUCHE"
            txt_en = "LEFT PLAYER WON"
        else:
            txt_fr = "VICTOIRE DU JOUEUR DE DROITE"
            txt_en = "RIGHT PLAYER WON"
        
        txt_fr_2 = "CALIBRATION A VENIR - MERCI DE DESCENDRE DES PLANCHES"
        txt_en_2 = "CALIBRATION PENDING - PLEASE GET DOWN FROM SKATEBOARDS"

        # Displaying winner and to get down from skates for calibration:
        txt_fr_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], txt_fr, \
                              self.x_dic["0.50"], self.y_dic["0.25"], skt_cst.WHITE)
        txt_en_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], txt_en, \
                              self.x_dic["0.50"], self.y_dic["0.65"], skt_cst.GREY)

        txt_fr_2_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.05"], \
                          txt_fr_2, self.x_dic["0.50"], self.y_dic["0.35"], skt_cst.WHITE)
        txt_en_2_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.05"], \
                          txt_en_2, self.x_dic["0.50"], self.y_dic["0.75"], skt_cst.GREY)

        # This scene will only exit once both skates are steady for a
        # few seconds or that a maximum time has gone.
        # Once one of the 2 conditions is fulfilled, pads calib. is done
        while ((current_time - start_time < self.DELAY_MAX_GAME_END)
        and (current_time - moving_time < self.DELAY_STEADY_BEF_CALIB)):

            self.clock.tick(self.FPS)

            # Checking user requests :
            # -> closing game window / rebooting / shutting down RPI.
            # -> Restarting game / calibrating not available here.
            keys = pygame.key.get_pressed()
            self.check_user_inputs(keys)

            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            # Erasing from display objects previous positions:
            l_score_rect_old, r_score_rect_old, l_pad_rect_old, \
            r_pad_rect_old, ball_rect_old = self.erase_game_objects(\
                                            color = skt_cst.BLACK, \
                                            pads = True, \
                                            ball = False, \
                                            scores = False)

            vy_l_pad, l_gyro_ratio = self.l_pad.move(self.win_h)
            vy_r_pad, r_gyro_ratio = self.r_pad.move(self.win_h)

            # Adding to display objects new positions:
            l_score_rect, r_score_rect, l_pad_rect, r_pad_rect, ball_rect, \
            mid_line_h_rect, mid_line_v_rect = self.draw_game_objects( \
                                               draw_pads = True, \
                                               draw_ball = True, \
                                               draw_scores = True, \
                                               draw_line = False)
            if loop_nb == 1:
                pygame.display.update()
                loop_nb += 1
            else:
                pygame.display.update([l_pad_rect_old, r_pad_rect_old, \
                        l_pad_rect, r_pad_rect])

            if (abs(l_gyro_ratio) > self.GYRO_STEADY_RATIO
            or abs(r_gyro_ratio) > self.GYRO_STEADY_RATIO):
                moving_time = time.time()
            
            current_time = time.time()
            
         # Paddles repositioned in the center of the screen:
        self.l_pad.move_to_center(self.win_h)
        self.r_pad.move_to_center(self.win_h)   
        self.game_status = skt_cst.SCENE_WAITING_PLAYERS

    def calibrate_pads(self):
        """
        Handles the paddles calibration + offset measurement

        Notes : 
        - No warning indication before calibration is actually started.
        - Displays that calibration is ongoing.
        - Going back to the scene "waiting for players".
        """
        self.ball.reset()
        self.clock.tick(self.FPS)

        # Reinitializing display:
        self.win.fill(skt_cst.BLACK)

        # Displaying that calibration is ongoing:
        txt_fr_1 = "CALIBRATION EN COURS"
        txt_en_1 = "CALIBRATION ONGOING"
        txt_fr_2 = "MAINTENIR LES PLANCHES IMMOBILES EN POSITION NEUTRE"
        txt_en_2 = "GET SKATES STEADY IN THEIR NEUTRAL POSITIONS"

        txt_fr_2_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.05"], \
                          txt_fr_2, self.x_dic["0.50"], self.y_dic["0.30"], skt_cst.WHITE)
        txt_en_2_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.05"], \
                          txt_en_2, self.x_dic["0.50"], self.y_dic["0.80"], skt_cst.GREY)
        txt_fr_1_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], \
                          txt_fr_1, self.x_dic["0.50"], self.y_dic["0.20"], skt_cst.WHITE)
        txt_en_1_rect = skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], \
                          txt_en_1, self.x_dic["0.50"], self.y_dic["0.70"], skt_cst.GREY)

        # Adding to display objects new positions:
        l_score_rect, r_score_rect, l_pad_rect, r_pad_rect, ball_rect, \
        mid_line_h_rect, mid_line_v_rect = self.draw_game_objects( \
                                           draw_pads = True, \
                                           draw_ball = True, \
                                           draw_scores = False, \
                                           draw_line = False)
                                           
        pygame.display.update()

        # Gyroscope offset measurement:
        try:
            self.l_gyro.offset = self.l_gyro.measure_gyro_offset()
        except IOError:
            self.l_gyro.error = True
        try:
            self.r_gyro.offset = self.r_gyro.measure_gyro_offset()
        except IOError:
            self.r_gyro.error = True

        # Erasing from display objects previous positions:
        l_score_rect_old, r_score_rect_old, l_pad_rect_old, \
        r_pad_rect_old, ball_rect_old = self.erase_game_objects( \
                                        color = skt_cst.BLACK, \
                                        pads = True, \
                                        ball = True, \
                                        scores = False)

        # Paddles calibration:
        self.l_pad.move_to_center(self.win_h)
        self.r_pad.move_to_center(self.win_h)

        # Adding to display objects new positions:
        l_score_rect, r_score_rect, l_pad_rect, r_pad_rect, ball_rect, mid_line_h_rect, mid_line_v_rect = \
        self.draw_game_objects(draw_pads = True, draw_ball = True, \
                               draw_scores = False, draw_line = False)

        pygame.display.update([l_pad_rect_old, r_pad_rect_old, \
                                   l_pad_rect, r_pad_rect])

        self.game_status = skt_cst.SCENE_WAITING_PLAYERS

if __name__ == '__main__':
    pass

"""
Copyright © 2023 Quentin BENETHUILLERE. All rights reserved.
"""
