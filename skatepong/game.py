#!usr/bin/python3

#-----------------------------------------------------------------------
# IMPORTS
#-----------------------------------------------------------------------

import pygame
import time
import math
import random
import sys
from mpu6050 import mpu6050
import skatepong.gyro as skt_gyro
import skatepong.tools as skt_tls
import skatepong.game_objects as skt_obj

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
        GAME_END : Game has ended, the winner is announced.
        CALIBRATION : Allows paddles calibratation upon request.
    """

    #-------------------------------------------------------------------
    # GAME PARAMETERS
    #-------------------------------------------------------------------
    
    # Main game parameters 
    WINNING_SCORE = 3 # Number of goals to win the game
    BALL_ANGLE_MAX = 55 # Max angle after paddle collision (deg) [30-75]
    VELOCITY_ANGLE_FACTOR = 2.5 # Higher ball velocity when angle [2 - 3]
    # Delays
    DELAY_WELCOME = 3 # Splash screen duration (s)
    DELAY_INACT_PLAYER = 5 # Delay before a player becomes inactive (s)
    DELAY_COUNTDOWN = 3 # Countdown before game starts (s)
    DELAY_GAME_END = 5 # Delay after game ends (s)
    DELAY_BEF_PAD_CALIB = 5 # Delay before paddles calib. starts (s)
    DELAY_AFT_PAD_CALIB = 5 # Delay for testing paddles calib. (s)
    # Technical parameters
    FPS = 60 # Max number of frames per second
    GYRO_SENSITIVITY = mpu6050.GYRO_RANGE_500DEG
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
    PAD_FLAT_BOUNCE_RATIO = 0.01 # Rat. disp. w [0.005 - 0.02]
    BALL_V_RATIO = 0.03 # Rat. disp. w [0.01 - 0.035]
    MID_LINE_WIDTH_RATIO = 0.006 # Rat. disp. w [0.005 - 0.01]
    SCORE_Y_OFFSET_RATIO = 0.02 # Rat. disp. h - frame vertical offset
    CENTER_CROSS_MULTIPLIER = 3 # Mid line thikness factor [2 - 5]
    # Text fonts parameters (names and sizes)
    FT_NM = "comicsans" # or 'quicksandmedium'. Font used for texts.

    #-------------------------------------------------------------------
    # CONSTANTS
    #-------------------------------------------------------------------

    # Game scenes (used for game navigation):
    SCENE_WELCOME = 0
    SCENE_WAITING_GYROS = 1
    SCENE_WAITING_PLAYERS = 2
    SCENE_COUNTDOWN = 3
    SCENE_GAME_ONGOING = 4
    SCENE_GAME_END = 5
    SCENE_CALIBRATION = 6
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GREY = (127, 127, 127)    

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
        # Resolution limitation to avoid lags with resolution 1920x1080
        print ("Display resolution :", disp_w, disp_h) 
        if disp_w == 1920 and disp_h == 1080:
            print ("Resolution reduction needed")
            disp_w = 1280
            disp_h = 720
        if self.full_screen == False:
            win = pygame.display.set_mode([disp_w, disp_h - 100])
            pygame.display.set_caption("Skatepong")         
        else:
            #win = pygame.display.set_mode([0, 0], pygame.FULLSCREEN)
            win = pygame.display.set_mode([disp_w, disp_h], pygame.FULLSCREEN)
        time.sleep(1/2)
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
                     pad_y, pad_w, pad_h, self.WHITE, self.l_gyro)
        self.r_pad = skt_obj.Paddle(self.win, self.win_h, r_pad_x, \
                     pad_y, pad_w, pad_h, self.WHITE, self.r_gyro)
        self.ball = skt_obj.Ball(self.win, self.x_dic["1/2"], self.y_dic["1/2"], \
                    ball_r, self.WHITE, ball_vx_straight, 0, 0)

    def reinitialize_gyro_if_needed(self):
        """
        Recreates gyroscopes objects following deconnections.
        """
        if (self.l_gyro.error and self.l_gyro.ready_for_reinit):
            try:
                self.l_gyro = skt_gyro.Gyro_one_axis( \
                            skt_gyro.Gyro_one_axis.I2C_ADDRESS_1,\
                            'y', self.GYRO_SENSITIVITY)
            except IOError:
                pass
        if (self.r_gyro.error and self.r_gyro.ready_for_reinit):
            try:
                self.r_gyro = skt_gyro.Gyro_one_axis( \
                            skt_gyro.Gyro_one_axis.I2C_ADDRESS_2,\
                            'y', self.GYRO_SENSITIVITY)
            except IOError:
                pass

    def draw_game_objects(self, draw_pads = False, draw_ball = False, \
                          draw_scores = False, draw_line = False):
        """
        Draws the desired game elements (pads / ball / scores)
        Note : Each game scene do not require every single game object 
        """
        if draw_scores == True:
            self.FT_NM = self.FT_NM
            y = self.ft_dic["0.10"] # 1 font sz offset
            txt = str(self.l_score)
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], txt, \
                  self.x_dic["1/4"], y, self.WHITE)
            txt = str(self.r_score)
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], txt, \
                              self.x_dic["3/4"], y, self.WHITE)
        if draw_line == True:        
            thick = int(self.win_w * self.MID_LINE_WIDTH_RATIO)
            horiz_w_factor = self.CENTER_CROSS_MULTIPLIER
            skt_tls.draw_mid_line(self.win, self.win_w, self.win_h, \
                                  thick, horiz_w_factor, self.WHITE)
        if draw_pads == True:
            self.l_pad.draw()
            self.r_pad.draw()
        if draw_ball == True:
            self.ball.draw()

    def check_user_inputs(self, keys):
        """
        Check user inputs (keyboards / mouse). 
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        if keys[pygame.K_ESCAPE]:
            sys.exit()
        elif keys[pygame.K_c]:
            self.game_status = self.SCENE_CALIBRATION
        elif keys[pygame.K_s]:
            self.game_status = self.SCENE_WAITING_PLAYERS

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
        x_mod = int(self.ball.rect.centerx - ((self.ball.vx * (self.ball.rect.centery - y_mod)) / self.ball.vy))
        self.ball.rect.center = (x_mod, y_mod)
        self.ball.vy *= -1
        
    def handle_l_coll(self, goal_to_be):
        """
        Handles collision between ball and left paddle.
        """
        if self.ball.rect.left <= self.l_pad.rect.right:
            x_mod = self.l_pad.rect.right + self.ball.r
            y_mod = int(self.ball.rect.centery - (self.ball.rect.centerx - x_mod) * self.ball.vy / self.ball.vx)            
            # If ball colliding with paddle:
            if (y_mod + self.ball.r >= self.l_pad.rect.top \
            and y_mod - self.ball.r <= self.l_pad.rect.bottom):            
                y_pad_mid = self.l_pad.rect.centery
                # Bounce angle calculation
                if (y_mod < (y_pad_mid + self.PAD_FLAT_BOUNCE_RATIO * self.win_w)\
                and y_mod > (y_pad_mid - self.PAD_FLAT_BOUNCE_RATIO * self.win_w)):
                    self.ball.vx = self.ball.vx_straight
                    self.ball.vy = 0
                else:
                    angle = round((y_mod - y_pad_mid) / (self.l_pad.h / 2) * self.BALL_ANGLE_MAX)
                    # Constant speed
                    #vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_w)
                    #vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_w)
                    # Faster when there is an angle to compensate for longer distance
                    vx = round(math.cos(math.radians(angle)) * self.ball.vx_straight) \
                         * (self.VELOCITY_ANGLE_FACTOR - math.cos(math.radians(angle)))
                    vy = round(math.sin(math.radians(angle)) * self.ball.vx_straight) \
                         * (self.VELOCITY_ANGLE_FACTOR - math.cos(math.radians(angle)))                    
                    self.ball.vy = vy
                    self.ball.vx = vx
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
            y_mod = int(self.ball.rect.centery - (self.ball.rect.centerx - x_mod) * self.ball.vy / self.ball.vx)            
            # If ball colliding with paddle:
            if y_mod + self.ball.r >= self.r_pad.rect.top \
            and y_mod - self.ball.r <= self.r_pad.rect.bottom:            
                y_pad_mid = self.r_pad.rect.centery
                # Bounce angle calculation
                if (y_mod < (y_pad_mid + self.PAD_FLAT_BOUNCE_RATIO * self.win_w) \
                and y_mod > (y_pad_mid - self.PAD_FLAT_BOUNCE_RATIO * self.win_w)):
                    self.ball.vx = -self.ball.vx_straight
                    self.ball.vy = 0
                else:
                    angle = round((y_mod - y_pad_mid) / (self.r_pad.h / 2) * self.BALL_ANGLE_MAX)
                    # Constant speed
                    #vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_w)
                    #vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_w)
                    # Faster when there is an angle to compensate for longer distance
                    vx = round(math.cos(math.radians(angle)) * self.ball.vx_straight) \
                         * (self.VELOCITY_ANGLE_FACTOR - math.cos(math.radians(angle)))
                    vy = round(math.sin(math.radians(angle)) * self.ball.vx_straight) \
                         * (self.VELOCITY_ANGLE_FACTOR - math.cos(math.radians(angle)))                    
                    self.ball.vy = vy
                    self.ball.vx = -vx
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
        - Calculates ball angle after collision with paddle depending
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
                    # but still needs to manage boucing on walls
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
                    # If right pad not well positioned, goal will happen, 
                    # but still needs to manage boucing on walls
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
            self.win.fill(self.BLACK)
            r = int(self.WELCOME_RADIUS_RATIO * self.win_h)
            pygame.draw.circle(self.win, self.WHITE, (self.x_dic["1/2"], self.y_dic["1/2"]), r)
            txt = "SKATEPONG"
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], txt, \
                              self.x_dic["1/2"], self.y_dic["1/2"], self.BLACK)
            pygame.display.update()
        except:
            print ("Reinitializing display...")
            self.win, self.win_w, self.win_h = self.create_window()
            self.welcome()
        
        while current_time - start_time < self.DELAY_WELCOME: 
            self.clock.tick(self.FPS)
            # Checking requests for closing / calibrating / restarting:
            keys = pygame.key.get_pressed()
            self.check_user_inputs(keys)
            # Updating current time
            current_time = time.time()
        self.game_status = self.SCENE_WAITING_GYROS
            
    def wait_gyros(self):
        """
        Game does not start until both skateboards are connected.
        """
        l_gyro_connected = False
        r_gyro_connected = False
        self.win.fill(self.BLACK)
        status = 0
        txt_1 = "Right skateboard NOT connected"
        txt_2 = "Left skateboard NOT connected"
        txt_3 = "Please connect skateboards"
        max_w_txt = skt_tls.get_max_w_txt(self.FT_NM, self.ft_dic["0.10"], txt_1, txt_2, txt_3)
        # Reinitializing display:
        self.win.fill(self.BLACK)
        pygame.display.update()
        
        while not (l_gyro_connected and r_gyro_connected):
            prev_status = status
            # Left gyro test :
            try:
                l_gyro = skt_gyro.Gyro_one_axis(skt_gyro.Gyro_one_axis.I2C_ADDRESS_1, \
                        'y', self.GYRO_SENSITIVITY)
            except IOError:
                l_gyro_connected = False
            else:
                l_gyro_connected = True
            # Right gyro test :
            try:
                r_gyro = skt_gyro.Gyro_one_axis(skt_gyro.Gyro_one_axis.I2C_ADDRESS_2, \
                         'y', self.GYRO_SENSITIVITY)
            except IOError:
                r_gyro_connected = False
            else:
                r_gyro_connected = True
            # Status summary :
            if not (l_gyro_connected and r_gyro_connected):
                if l_gyro_connected == True:
                    status = 1
                elif r_gyro_connected == True:
                    status = 2
                else:
                    status = 3
            # If status has changed :
            if status != prev_status:
                if status == 1:
                    txt = txt_1
                elif status == 2:
                    txt = txt_2
                elif status == 3:
                    txt = txt_3
                # Black rect above max text area + new text displayed.
                txt_max_rect = pygame.Rect(0, 0, max_w_txt, self.ft_dic["0.10"])
                txt_max_rect.center = (self.x_dic["1/2"], self.y_dic["1/2"])
                txt_max_rect = pygame.draw.rect(self.win, self.BLACK, txt_max_rect)
                txt_rect = skt_tls.draw_text_2(self.win, self.FT_NM, self.ft_dic["0.10"], txt, \
                                  self.x_dic["1/2"], self.y_dic["1/2"], self.WHITE)
                pygame.display.update([txt_max_rect, txt_rect])
        
        self.l_gyro = l_gyro
        self.r_gyro = r_gyro
        self.game_status = self.SCENE_WAITING_PLAYERS

    def wait_players(self):
        """
        Standby before detection of active players on each skateboard.
        Note : paddles active.
        """
        moving_time = time.time()
        current_time = time.time()
        left_player_ready = False
        right_player_ready = False
        self.ball.reset()
        
        while not (left_player_ready and right_player_ready):

            self.clock.tick(self.FPS)

            # Checking requests for closing / calibrating / restarting:        
            keys = pygame.key.get_pressed()
            self.check_user_inputs(keys)

            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            # Going to paddles calibration scene upon user request:
            #game_status = check_for_pads_calib(keys, game_status)
            if self.game_status == self.SCENE_CALIBRATION:
                return
            
            if not (left_player_ready and right_player_ready):
                if right_player_ready == True:
                    msg = "LEFT PLAYER MISSING"
                elif left_player_ready == True:
                    msg = "RIGHT PLAYER MISSING"
                else:
                    msg = "WAITING FOR PLAYERS"
            
            # Managing display:
            self.win.fill(self.BLACK)
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], msg, \
                              self.x_dic["1/2"], self.y_dic["1/4"], self.WHITE)
            txt = "MOVE SKATES TO START"
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.05"], txt, \
                              self.x_dic["1/2"], self.y_dic["3/4"], self.WHITE)
            self.draw_game_objects(draw_pads = True, draw_ball = True, \
                                draw_scores = False, draw_line = False)
            pygame.display.update()
            
            vy_l_pad = self.l_pad.move(self.win_h)
            vy_r_pad = self.r_pad.move(self.win_h)
            if abs(vy_l_pad) > 25:
                left_player_ready = True
                moving_time = time.time()
            if abs(vy_r_pad) > 25:
                right_player_ready = True
                moving_time = time.time()

            current_time = time.time()

            if current_time - moving_time > self.DELAY_INACT_PLAYER:
                left_player_ready = False
                right_player_ready = False

        self.game_status = self.SCENE_COUNTDOWN

    def countdown(self):
        """
        Starts a countdown before the game actually begins.

        Note : paddles active.
        """
        start_time = time.time()
        current_time = time.time()
        
        while current_time - start_time < self.DELAY_COUNTDOWN:
            
            self.clock.tick(self.FPS)
            
            # Checking requests for closing / calibrating / restarting:
            keys = pygame.key.get_pressed()
            #check_exit_game(keys)
            self.check_user_inputs(keys)
            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            time_before_start = self.DELAY_COUNTDOWN \
                                - int(current_time - start_time) 

            vy_l_pad = self.l_pad.move(self.win_h)
            vy_r_pad = self.r_pad.move(self.win_h)

            # Managing display:
            self.win.fill(self.BLACK)
            txt = str(time_before_start)
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.20"], txt, 
                              self.x_dic["1/2"], self.y_dic["1/4"], self.WHITE)
            self.draw_game_objects(draw_pads = True, draw_ball = True, \
                                draw_scores = False, draw_line = False)
            pygame.display.update()
            
            current_time = time.time()
       
        self.game_status = self.SCENE_GAME_ONGOING

    def game_ongoing(self):
        """
        Controls the game itself.
        """
        
        self.l_score = 0
        self.r_score = 0
        goal_to_be = False
        random_number = random.randint(1, 2)
        
        # Determining ball direction at start.
        if random_number == 1:
            self.ball.vx =  self.ball.vx_straight # To the right
        else:
            self.ball.vx =  -self.ball.vx_straight # To the left
            
        while self.l_score < self.WINNING_SCORE \
        and self.r_score < self.WINNING_SCORE:

            self.clock.tick(self.FPS)
            # Checking requests for closing / calibrating / restarting:
            keys = pygame.key.get_pressed()
            self.check_user_inputs(keys)
            
            # Going to paddles calibration scene upon user request:
            if self.game_status == self.SCENE_CALIBRATION \
            or self.game_status == self.SCENE_WAITING_PLAYERS:
                return
            
            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            vy_l_pad = self.l_pad.move(self.win_h)
            vy_r_pad = self.r_pad.move(self.win_h)

            self.ball.move()
            goal_to_be = self.handle_collision(goal_to_be)
            goal_to_be = self.detect_goal(goal_to_be)        

            # Managing display:
            self.win.fill(self.BLACK)
            self.draw_game_objects(draw_pads = True, draw_ball = True, \
                                   draw_scores = True, draw_line = True)
            pygame.display.update()   

            if self.l_score >= self.WINNING_SCORE \
            or self.r_score >= self.WINNING_SCORE:
                self.game_status = self.SCENE_GAME_END
                return
            
    def game_end(self):
        """
        Announces the winner, with final score.
        Note : paddles active.
        """
        start_time = time.time()
        current_time = time.time()
        self.ball.reset()
        
        if (self.l_score == self.WINNING_SCORE):
            msg = "LEFT PLAYER WON"
        else:
            msg = "RIGHT PLAYER WON"
        
        while current_time - start_time < self.DELAY_GAME_END:
            
            self.clock.tick(self.FPS)

            # Checking requests for closing / calibrating / restarting:
            keys = pygame.key.get_pressed()
            self.check_user_inputs(keys)
            #check_exit_game(keys)

            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            vy_l_pad = self.l_pad.move(self.win_h)
            vy_r_pad = self.r_pad.move(self.win_h)

            # Managing display:
            self.win.fill(self.BLACK)
            self.draw_game_objects(draw_pads = True, draw_ball = False,\
                                  draw_scores = True, draw_line = False)
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.15"], msg, \
                              self.x_dic["1/2"], self.y_dic["1/2"], self.WHITE)
            pygame.display.update()

            current_time = time.time()
        
        self.game_status = self.SCENE_WAITING_PLAYERS   

    def calibrate_pads(self):
        """
        Handles the paddles calibration.
        
        - 1 : indications and coutdown before calibration
        - 2 : gives user some time to test the new calibration
        - 3 : going back to the scene "waiting for players".
        """
        start_time = time.time()
        current_time = time.time()
        self.ball.reset()
        
        # Announcing that calibration is about to take place:
        while current_time - start_time < self.DELAY_BEF_PAD_CALIB:

            self.clock.tick(self.FPS)

            # Checking requests for closing / calibrating / restarting:
            keys = pygame.key.get_pressed()
            #check_exit_game(keys)
            self.check_user_inputs(keys)

            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            time_before_start = self.DELAY_BEF_PAD_CALIB \
                                - int(current_time - start_time)
           
            vy_l_pad = self.l_pad.move(self.win_h)
            vy_r_pad = self.r_pad.move(self.win_h)
            
            # Managing display:
            self.win.fill(self.BLACK)
            txt = "CALIBRATION IS ABOUT TO START"
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], \
                              txt, self.x_dic["1/2"], self.y_dic["1/4"], self.WHITE)
            txt = "GET SKATES STEADY IN THEIR NEUTRAL POSITIONS"                    
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.05"], \
                              txt, self.x_dic["1/2"], self.y_dic["3/4"], self.WHITE)
            txt = str(time_before_start)         
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.20"], \
                              txt, self.x_dic["1/2"], self.y_dic["1/2"], self.WHITE)
            self.draw_game_objects(draw_pads = True, draw_ball = False,\
                                draw_scores = False, draw_line = False)
            pygame.display.update()
            
            current_time = time.time()
        
        self.clock.tick(self.FPS)
        
        # Managing display:
        self.win.fill(self.BLACK)
        
        txt = "CALIBRATION ONGOING..."
        skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], \
                          txt, self.x_dic["1/2"], self.y_dic["1/4"], self.WHITE)
        txt = "GET SKATES STEADY IN THEIR NEUTRAL POSITIONS"                  
        skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.05"], \
                          txt, self.x_dic["1/2"], self.y_dic["3/4"], self.WHITE)
        self.draw_game_objects(draw_pads = True, draw_ball = False, \
                              draw_scores = False, draw_line = False)
        pygame.display.update()
        # Gyroscope offset measurement:
        self.l_gyro.offset = self.l_gyro.measure_gyro_offset()
        self.r_gyro.offset = self.r_gyro.measure_gyro_offset()    
        # Paddles calibration:
        self.l_pad.move_to_center(self.win_h)
        self.r_pad.move_to_center(self.win_h)

        # Annoucing that calibration has been performed :
        start_time = time.time()
        current_time = time.time()

        while current_time - start_time < self.DELAY_AFT_PAD_CALIB:

            self.clock.tick(self.FPS)

            # Checking requests for closing / calibrating / restarting:
            keys = pygame.key.get_pressed()
            #check_exit_game(keys)
            self.check_user_inputs(keys)

            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            time_before_start = self.DELAY_AFT_PAD_CALIB \
                                - int(current_time - start_time)

            vy_l_pad = self.l_pad.move(self.win_h)
            vy_r_pad = self.r_pad.move(self.win_h)
            
            # Managing display:
            self.win.fill(self.BLACK)
            txt = "CALIBRATION DONE"
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.10"], \
                              txt, self.x_dic["1/2"], self.y_dic["1/4"], self.WHITE)
            txt = "MOVE SKATES TO TEST CALIBRATION"            
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.05"], \
                              txt, self.x_dic["1/2"], self.y_dic["3/4"], self.WHITE)
            txt = str(time_before_start)   
            skt_tls.draw_text(self.win, self.FT_NM, self.ft_dic["0.20"], \
                              txt, self.x_dic["1/2"], self.y_dic["1/2"], self.WHITE)
            
            self.draw_game_objects(draw_pads = True, draw_ball = False,\
                                draw_scores = False, draw_line = False)
            pygame.display.update()
            
            current_time = time.time()
        
        self.game_status = self.SCENE_WAITING_PLAYERS
        
if __name__ == '__main__':
    print("Hello")
