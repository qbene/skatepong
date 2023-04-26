#!usr/bin/python3

import pygame
import time
import math
import random
import sys
from mpu6050 import mpu6050
import skatepong.gyro
import skatepong.tools
import skatepong.game_objects

class Game():

    #------------------------------------------------------------------------------
    # GAME PARAMETERS
    #------------------------------------------------------------------------------
    
    WINNING_SCORE = 3 # Number of goals to win the game
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
    GYRO_SENSITIVITY = mpu6050.GYRO_RANGE_500DEG
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

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GREY = (127, 127, 127)    

    def __init__(self, game_status = 0, l_score = 0, r_score = 0, dev_mode = False):
        #self.clock = clock
        pygame.init()
        self.clock = pygame.time.Clock()
        self.game_status = game_status
        self.l_score = l_score
        self.r_score = r_score
        self.dev_mode = dev_mode
        self.win, self.win_w, self.win_h = self.create_window()

    #------------------------------------------------------------------------------
    # SIDE FUNCTIONS
    #------------------------------------------------------------------------------
        
    def create_window(self):
        """
        Initializes game window, and adjusts size to display resolution.
        """
        disp_w = pygame.display.Info().current_w # Display width (in pixels)
        disp_h = pygame.display.Info().current_h # Display height (in pixels)
        if self.dev_mode == True:
            win = pygame.display.set_mode([disp_w, disp_h-100])
            pygame.display.set_caption("Skatepong")         
        else:
            win = pygame.display.set_mode([0, 0], pygame.FULLSCREEN)
        win_w , win_h = pygame.display.get_surface().get_size()
        return win, win_w, win_h # Capital letters for WIN to identify main window

    def compute_elements_sizes(self):
        """
        Computes game elements sizes/speeds based on display resolution.
        """
        pad_w = int(self.win_w * self.PAD_WIDTH_RATIO)
        pad_h = int(self.win_h * self.PAD_HEIGHT_RATIO)
        ball_r = min(int(self.win_w * self.BALL_RADIUS_RATIO), int(self.win_h * self.BALL_RADIUS_RATIO))
        ball_vx_straight = int(self.win_w * self.BALL_V_RATIO)
        return pad_w, pad_h, ball_r, ball_vx_straight

    def create_game_elements(self):
        """
        Creates game objects at program start.
        """
        # Creating game objects:
        # - Both paddles are centered vertically
        # - The ball is created in the center of the display
        pad_w, pad_h, ball_r, ball_vx_straight = self.compute_elements_sizes()
        l_pad_x =  int(self.win_w * self.PAD_X_OFFSET_RATIO)
        r_pad_x = self.win_w - int(self.PAD_X_OFFSET_RATIO * self.win_w) - pad_w
        pad_y = (self.win_h - pad_h) // 2
        self.l_pad = skatepong.game_objects.Paddle(self.win, l_pad_x, pad_y, pad_w, pad_h, self.WHITE, self.l_gyro)
        self.r_pad = skatepong.game_objects.Paddle(self.win, r_pad_x, pad_y, pad_w, pad_h, self.WHITE, self.r_gyro)
        self.ball = skatepong.game_objects.Ball(self.win, self.win_w // 2, self.win_h // 2, ball_r, self.WHITE, ball_vx_straight, 0, 0)

    def reinitialize_gyro_if_needed(self):
        """
        Recreate gyroscopes objects following deconnections.
        """
        if self.l_gyro.error == True and self.l_gyro.ready_for_reinit == True:
            try:
                self.l_gyro = skatepong.gyro.Gyro_one_axis(skatepong.gyro.Gyro_one_axis.I2C_ADDRESS_1, 'y', self.GYRO_SENSITIVITY)
            except IOError:
                pass
        if self.r_gyro.error == True and self.r_gyro.ready_for_reinit == True:
            try:
                self.r_gyro = skatepong.gyro.Gyro_one_axis(skatepong.gyro.Gyro_one_axis.I2C_ADDRESS_2, 'y', self.GYRO_SENSITIVITY)
            except IOError:
                pass

    def draw_game_objects(self, draw_pads = False, draw_ball = False, draw_scores = False, draw_line = False):
        """
        Draws on a surface the desired game elements (pads / ball / scores)
        
        Note : Each scene of the game do not require every single game object 
        """
        if draw_scores == True:
            skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_1 * self.win_h), str(self.l_score), self.win_w // 4, int(self.FONT_RATIO_0_1 * self.win_h), self.WHITE)
            skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_1 * self.win_h), str(self.r_score), (self.win_w * 3) // 4, int(self.FONT_RATIO_0_1 * self.win_h), self.WHITE)
        if draw_line == True:        
            skatepong.tools.draw_mid_line(self.win, self.win_w, self.win_h, int(self.win_w * self.MID_LINE_WIDTH_RATIO), self.CENTER_CROSS_MULTIPLIER, self.WHITE)
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
            vx_direction_after_goal = 1
            goal = True
        elif self.ball.rect.right > self.win_w:
            self.l_score += 1
            vx_direction_after_goal = -1
            goal = True
        if goal == True:
            self.ball.reset()
            self.ball.vx = self.ball.vx_straight * vx_direction_after_goal
            goal_to_be = False

        return goal_to_be

    def handle_top_bottom_collision(self):
        """ Collision with top or bottom wall"""
        # Bottom wall
        if (self.ball.rect.bottom >= self.win_h):
            y_mod = self.win_h - self.ball.r  
        # Top wall
        elif (self.ball.rect.top <= 0):
            y_mod = self.ball.r
        x_mod = int(self.ball.rect.centerx - ((self.ball.vx * (self.ball.rect.centery - y_mod)) / self.ball.vy))
        self.ball.rect.center = (x_mod, y_mod)
        self.ball.vy *= -1
        
    def handle_left_collision(self, goal_to_be):
        #goal_to_be = False
        if self.ball.rect.left <= self.l_pad.rect.right:
            x_mod = self.l_pad.rect.right + self.ball.r
            y_mod = int(self.ball.rect.centery - (self.ball.rect.centerx - x_mod) * self.ball.vy / self.ball.vx)            
            # If ball colliding with paddle:
            if y_mod >= self.l_pad.rect.top and y_mod <= self.l_pad.rect.bottom:            
                y_pad_mid = self.l_pad.rect.centery
                # Bounce angle calculation
                if (y_mod < (y_pad_mid + self.PAD_FLAT_BOUNCE_RATIO * self.win_w) and y_mod > (y_pad_mid - self.PAD_FLAT_BOUNCE_RATIO * self.win_w)):
                    self.ball.vx = self.ball.vx_straight                    
                else:
                    angle = round((y_mod - y_pad_mid) / (self.l_pad.h / 2) * self.BALL_ANGLE_MAX)
                    # Constant speed
                    #vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_w)
                    #vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_w)
                    # Faster when there is an angle to compensate for longer distance
                    vx = round(math.cos(math.radians(angle)) * self.ball.vx_straight) * (self.VELOCITY_ANGLE_FACTOR - math.cos(math.radians(angle)))
                    vy = round(math.sin(math.radians(angle)) * self.ball.vx_straight) * (self.VELOCITY_ANGLE_FACTOR - math.cos(math.radians(angle)))                    
                    self.ball.vy = vy
                    self.ball.vx = vx
                self.ball.rect.center = (x_mod, y_mod)
            else:
                goal_to_be = True
        return goal_to_be

    def handle_right_collision(self, goal_to_be):
        #goal_to_be = False
        if self.ball.rect.right >= self.r_pad.rect.left:
            x_mod = self.r_pad.rect.left - self.ball.r
            y_mod = int(self.ball.rect.centery - (self.ball.rect.centerx - x_mod) * self.ball.vy / self.ball.vx)            
            # If ball colliding with paddle:
            if y_mod >= self.r_pad.rect.top and y_mod <= self.r_pad.rect.bottom:            
                y_pad_mid = self.r_pad.rect.centery
                # Bounce angle calculation
                if (y_mod < (y_pad_mid + self.PAD_FLAT_BOUNCE_RATIO * self.win_w) and y_mod > (y_pad_mid - self.PAD_FLAT_BOUNCE_RATIO * self.win_w)):
                    self.ball.vx = -self.ball.vx_straight
                else:
                    angle = round((y_mod - y_pad_mid) / (self.r_pad.h / 2) * self.BALL_ANGLE_MAX)
                    #angle = round((ball.y - y_pad_mid) / (r_pad.h / 2) * BALL_ANGLE_MAX)
                    # Constant speed
                    #vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_w)
                    #vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_w)
                    # Faster when there is an angle to compensate for longer distance
                    vx = round(math.cos(math.radians(angle)) * self.ball.vx_straight) * (self.VELOCITY_ANGLE_FACTOR - math.cos(math.radians(angle)))
                    vy = round(math.sin(math.radians(angle)) * self.ball.vx_straight) * (self.VELOCITY_ANGLE_FACTOR - math.cos(math.radians(angle)))                    
                    self.ball.vy = vy
                    self.ball.vx = -vx
                self.ball.rect.center = (x_mod, y_mod)
            else:
                goal_to_be = True
        return goal_to_be

    def check_collision(self):
        
        bottom_collision = False
        top_collision = False
        left_collision = False
        right_collision = False
        if (self.ball.rect.bottom >= self.win_h):
            bottom_collision = True
        elif (self.ball.rect.top <= 0):
            top_collision = True
        if ((self.ball.vx < 0) and (self.ball.rect.left <= self.l_pad.rect.right)):
            left_collision = True
        elif ((self.ball.vx > 0) and (self.ball.rect.right >= self.r_pad.rect.left)):
            right_collision = True
                
        return bottom_collision, top_collision, left_collision, right_collision

    def handle_collision(self, goal_to_be):
        """
        Handles ball collision with paddles and top/bottom walls.
        
        - Calculates ball horizontal and vertical velocities.
        - Calculates ball angle after collision with paddle depending
        ...on the collision point.
        """
        
        bottom_collision, top_collision, left_collision, right_collision = self.check_collision()
        
        # Left paddle possible collision case
        if (left_collision and goal_to_be == False):
            # Ball also colliding with bottom wall
            if bottom_collision:
                y_mod = self.win_h - self.ball.r  
            # Ball also colliding with top wall
            elif top_collision:
                y_mod = self.ball.r
            # Neef to determine which collision would arrive first: top/bottom wall or left paddle ?
            if bottom_collision or top_collision:
                x_mod = int(self.ball.rect.centerx - ((self.ball.vx * (self.ball.rect.centery - y_mod)) / self.ball.vy))
                # Top/bottom wall collision first :
                if x_mod > (self.l_pad.rect.right):
                    self.handle_top_bottom_collision(self.ball, self.win_h)
                # Left padlle collision would arrive first if paddle well positioned
                else:
                    goal_to_be = self.handle_left_collision(goal_to_be)
                    # If left paddle not well positioned, a goal will hapen, but still needs to manage boucing on top/bottom wall
                    if goal_to_be:
                        self.handle_top_bottom_collision()
            # Left paddle collision possible and no collision with top/bottom walls
            else:
                goal_to_be = self.handle_left_collision(goal_to_be)

        # Right paddle possible collision case
        elif (right_collision and goal_to_be == False):
            # Ball also colliding with bottom wall
            if bottom_collision:
                y_mod = self.win_h - self.ball.r  
            # Ball also colliding with top wall
            elif top_collision:
                y_mod = self.ball.r
            # Neef to determine which collision would arrive first: top/bottom wall or right paddle ?
            if bottom_collision or top_collision:
                x_mod = int(self.ball.rect.centerx - ((self.ball.vx * (self.ball.rect.centery - y_mod)) / self.ball.vy))
                # Top/bottom wall collision first :
                if x_mod < self.r_pad.x:
                    handle_top_bottom_collision(ball, win_h)
                # Right padlle collision would arrive first if paddle well positioned
                else:        
                    goal_to_be = self.handle_right_collision(goal_to_be)
                    # If right paddle not well positioned, a goal will hapen, but still needs to manage boucing on top/bottom wall
                    if goal_to_be:
                        self.handle_top_bottom_collision()
            # Right paddle collision possible and no collision with top/bottom walls
            else:
                goal_to_be = self.handle_right_collision(goal_to_be)
        
        # No possible collision with paddles, but just with top or bottom walls
        elif (bottom_collision or top_collision):
            self.handle_top_bottom_collision()

        return goal_to_be

    #------------------------------------------------------------------------------
    # GAME STATES
    #------------------------------------------------------------------------------    

    def welcome(self):
        """
        Displays a welcome screen for a certain duration at program start.
        """
        start_time = time.time()
        
        # Managing display:
        self.win.fill(self.BLACK)
        pygame.draw.circle(self.win, self.WHITE, (self.win_w//2, self.win_h//2), self.WELCOME_RADIUS_RATIO * self.win_h)
        skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_1 * self.win_h), "SKATEPONG", self.win_w // 2, self.win_h // 2, self.BLACK)
        pygame.display.update()
        
        current_time = time.time()
        while current_time - start_time < 3:

            self.clock.tick(self.FPS)

            # Closing game window if red cross clicked or ESCAPE pressed:
            keys = pygame.key.get_pressed()
            self.check_user_inputs(keys)
            #check_exit_game(keys)
            # Updating current time
            current_time = time.time()
            
        self.game_status = self.SCENE_WAITING_GYROS
            
    def wait_gyros(self):
        """
        Game does not start if both skateboards are not connected at startup.
        """
        
        both_gyros_connected = False
        while both_gyros_connected != True:
            
            try:
                l_gyro = skatepong.gyro.Gyro_one_axis(skatepong.gyro.Gyro_one_axis.I2C_ADDRESS_1, 'y', self.GYRO_SENSITIVITY)
            except IOError:
                l_gyro_connected = False
            else:
                l_gyro_connected = True
            
            try:
                r_gyro = skatepong.gyro.Gyro_one_axis(skatepong.gyro.Gyro_one_axis.I2C_ADDRESS_2, 'y', self.GYRO_SENSITIVITY)
            except IOError:
                r_gyro_connected = False
            else:
                r_gyro_connected = True
            
            if l_gyro_connected and r_gyro_connected:
                both_gyros_connected = True
            
            if both_gyros_connected == False:
                # Managing display:
                self.win.fill(self.BLACK)
                if l_gyro_connected == True and r_gyro_connected == False:
                    message = "Right skateboard NOT connected"
                elif l_gyro_connected == False and r_gyro_connected == True:
                    message = "Left skateboard NOT connected"
                else:
                    message = "Please connect skateboards"
                skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_1 * self.win_h), message, self.win_w // 2, self.win_h // 2, self.WHITE)
                pygame.display.update()
        
        self.l_gyro = l_gyro
        self.r_gyro = r_gyro
        self.game_status = self.SCENE_WAITING_PLAYERS

    def wait_players(self):
        """
        Enters 'standby' state before detection of actives players on each skateboard.
        
        Note : paddles active.
        """
        moving_time = time.time()
        current_time = time.time()
        left_player_ready = False
        right_player_ready = False
        self.ball.reset()
        
        while ((left_player_ready == False) or (right_player_ready == False)):

            self.clock.tick(self.FPS)

            # Closing game window if red cross clicked or ESCAPE pressed:        
            keys = pygame.key.get_pressed()
            self.check_user_inputs(keys)
            #check_exit_game(keys)

            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            # Going to paddles calibration scene upon user request:
            #game_status = check_for_pads_calib(keys, game_status)
            if self.game_status == self.SCENE_CALIBRATION:
                return

            if ((left_player_ready == False) and (right_player_ready == False)):
                message = "WAITING FOR PLAYERS"
            elif ((left_player_ready == False) and (right_player_ready == True)):
                message = "LEFT PLAYER MISSING"
            elif ((left_player_ready == True) and (right_player_ready == False)):
                message = "RIGHT PLAYER MISSING"
            
            # Managing display:
            self.win.fill(self.BLACK)
            skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_1 * self.win_h), message, self.win_w // 2, self.win_h // 4, self.WHITE)
            skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_05 * self.win_h), "MOVE SKATES TO START", self.win_w // 2, (self.win_h * 3) // 4, self.WHITE)
            self.draw_game_objects(draw_pads = True, draw_ball = True, draw_scores = False, draw_line = False)
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
                left_player_ready = 0
                right_player_ready = 0

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
            
            # Closing game window if red cross clicked or ESCAPE pressed:
            keys = pygame.key.get_pressed()
            #check_exit_game(keys)
            self.game_status = self.check_user_inputs(keys)
            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            time_before_start = self.DELAY_COUNTDOWN - int(current_time - start_time) 

            vy_l_pad = self.l_pad.move(self.win_h)
            vy_r_pad = self.r_pad.move(self.win_h)

            # Managing display:
            self.win.fill(self.BLACK)
            skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_2 * self.win_h), str(time_before_start), self.win_w // 2, self.win_h // 4, self.WHITE)
            self.draw_game_objects(draw_pads = True, draw_ball = True, draw_scores = False, draw_line = False)
            pygame.display.update()

            current_time = time.time()
       
        self.game_status = self.SCENE_GAME_ONGOING

    def game_ongoing(self):
        """
        Controls the game itself.
        
        1 point each time a player shoots the ball inside the oponent's zone.
        """
        
        self.l_score = 0
        self.r_score = 0
        goal_to_be = False
        random_number = random.randint(1, 2)
        
        if random_number == 1:
            self.ball.vx =  self.ball.vx_straight # Ball going to the right at start
        else:
            self.ball.vx =  -self.ball.vx_straight # Ball going to the left at start
            
        while (self.l_score < self.WINNING_SCORE and self.r_score < self.WINNING_SCORE):

            self.clock.tick(self.FPS)
            # Closing game window if red cross clicked or ESCAPE pressed:
            keys = pygame.key.get_pressed()
            self.game_status = self.check_user_inputs(keys)
            
            # Going to paddles calibration scene upon user request:
            if self.game_status == self.SCENE_CALIBRATION  or self.game_status == self.SCENE_WAITING_PLAYERS:
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
            self.draw_game_objects(draw_pads = True, draw_ball = True, draw_scores = True, draw_line = True)
            pygame.display.update()   

            if (self.l_score >= self.WINNING_SCORE or self.r_score >= self.WINNING_SCORE):
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
            message = "LEFT PLAYER WON"
        else:
            message = "RIGHT PLAYER WON"
        
        while current_time - start_time < self.DELAY_GAME_END:
            
            self.clock.tick(self.FPS)

            # Closing game window if red cross clicked or ESCAPE pressed:
            keys = pygame.key.get_pressed()
            self.game_status = self.check_user_inputs(keys)
            #check_exit_game(keys)

            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            vy_l_pad = self.l_pad.move(self.win_h)
            vy_r_pad = self.r_pad.move(self.win_h)

            # Managing display:
            self.win.fill(self.BLACK)
            self.draw_game_objects(draw_pads = True, draw_ball = False, draw_scores = True, draw_line = False)
            skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_15 * self.win_h), message, self.win_w // 2, self.win_h // 2, self.WHITE)
            pygame.display.update()

            current_time = time.time()
        
        self.game_status = self.SCENE_WAITING_PLAYERS   

    def calibrate_pads(self):
        """
        Handles the paddles calibration.
        
        - A first screen indicates that calibration will take place after countdown
        => Indic
        - A second screen allows user to test the new calibration for a given time
        - Then, going back to the scene "waiting for players".
        """
        start_time = time.time()
        current_time = time.time()
        self.ball.reset()
        
        # Announcing that calibration is about to take place
        while current_time - start_time < self.DELAY_BEF_PAD_CALIB:

            self.clock.tick(self.FPS)

            # Closing game window if red cross clicked or ESCAPE pressed:
            keys = pygame.key.get_pressed()
            #check_exit_game(keys)
            self.game_status = self.check_user_inputs(keys)

            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            time_before_start = self.DELAY_BEF_PAD_CALIB - int(current_time - start_time)
           
            vy_l_pad = self.l_pad.move(self.win_h)
            vy_r_pad = self.r_pad.move(self.win_h)
            
            # Managing display:
            self.win.fill(self.BLACK)
            skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_1 * self.win_h), "CALIBRATION IS ABOUT TO START", self.win_w // 2, self.win_h // 4, self.WHITE)
            skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_05 * self.win_h), "GET SKATES STEADY IN THEIR NEUTRAL POSITIONS", self.win_w // 2, (self.win_h * 3) // 4, self.WHITE)
            skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_2 * self.win_h), str(time_before_start), self.win_w // 2, self.win_h // 2, self.WHITE)
            self.draw_game_objects(draw_pads = True, draw_ball = False, draw_scores = False, draw_line = False)
            pygame.display.update()
            
            current_time = time.time()
        
        self.clock.tick(self.FPS)
        
        # Managing display:
        self.win.fill(self.BLACK)
        skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_1 * self.win_h), "CALIBRATION ONGOING...", self.win_w // 2, self.win_h // 4, self.WHITE)
        skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_05 * self.win_h), "GET SKATES STEADY IN THEIR NEUTRAL POSITIONS", self.win_w // 2, (self.win_h * 3) // 4, self.WHITE)
        self.draw_game_objects(draw_pads = True, draw_ball = False, draw_scores = False)
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

            # Closing game window if red cross clicked or ESCAPE pressed:
            keys = pygame.key.get_pressed()
            #check_exit_game(keys)
            self.game_status = self.check_user_inputs(keys)

            # Reinitializing gyro if necessary (after i2c deconnection)
            self.reinitialize_gyro_if_needed()

            time_before_start = self.DELAY_AFT_PAD_CALIB - int(current_time - start_time)

            vy_l_pad = self.l_pad.move(win_h)
            vy_r_pad = self.r_pad.move(win_h)
            
            # Managing display:
            self.win.fill(self.BLACK)
            skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_1 * self.win_h), "CALIBRATION DONE", self.win_w // 2, self.win_h // 4, self.WHITE)
            skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_05 * self.win_h), "MOVE SKATES TO TEST CALIBRATION", self.win_w // 2, (self.win_h * 3) // 4, self.WHITE)
            skatepong.tools.draw_text(self.win, self.FONT_NAME, int(self.FONT_RATIO_0_2 *self. win_h), str(time_before_start), self.win_w // 2, self.win_h // 2, self.WHITE)
            self.draw_game_objects(draw_pads = True, draw_ball = False, draw_scores = False)
            pygame.display.update()
            
            current_time = time.time()
        
        self.game_status = self.SCENE_WAITING_PLAYERS
        
if __name__ == '__main__':
    print("Hello")
