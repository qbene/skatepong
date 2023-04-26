#!usr/bin/python3

import pygame
from pygame.locals import *

class Ball():
    

    def __init__(self, win, x, y, r, color, vx_straight, vx = 0, vy = 0):
        self.win = win
        self.x = self.original_x = x # Ball center - horizontal axis
        self.y = self.original_y = y # Ball center - vertical axis
        self.color = color
        self.r = r # Ball radius (px)
        self.vx_straight = vx_straight # Ball velocity when going horizontally (px)
        self.vx = self.original_vx = vx # Ball velocity - horizontal axis (px)
        self.vy = self.original_vy = vy # Ball velocity - vertical axis (px)

    def draw(self):
        pygame.draw.circle(self.win, self.color, (self.x, self.y), self.r)
        #self.rect = pygame.draw.circle(self.win, self.color, (self.x, self.y), self.r)
        #self.rect = ball_obj.get_rect()
        
    def move(self):
        self.x += self.vx
        self.y += self.vy
    
    def reset(self):
        self.x = self.original_x
        self.y = self.original_y
        self.vx = self.original_vx
        self.vy = self.original_vy
        
class Paddle():
    
    def __init__(self, win, x, y, w, h, color, gyro):
        self.win = win
        self.x = self.original_x = x # Top left hand corner - horizontal axis
        self.y = self.original_y = y # Top left hand corner - vertical axis
        self.w = w # Paddle width (in pixels)
        self.h = h # Paddle height (in pixels)
        self.color = color
        self.gyro = gyro # Gyroscope that controls the paddle displacement
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self):
        
        pygame.draw.rect(self.win, self.color, self.rect)

    def compute_pad_velocity(self):
        
        # Handling gyroscope i2c deconnection
        try:
            gyro_raw = self.gyro.get_data()
        except IOError:
            print("i2c communication with gyroscope failed")
            self.gyro.error = True
            self.gyro.ready_for_reinit = False
            vy = 0
        # Computing pad velocity if gyroscope is connected
        else:
            self.gyro.ready_for_reinit = True
            #gyro_raw = self.gyro.get_data()
            gyro_calib = gyro_raw - self.gyro.offset
            if gyro_calib < -200:
                vy = -30
            elif  (gyro_calib >= -200 and gyro_calib < -50):
                vy = -20
            elif (gyro_calib >= -50 and gyro_calib < -10): 
                vy = -10    
            elif (gyro_calib >= -10 and gyro_calib < 10):
                vy = 0
            elif (gyro_calib >= 10 and gyro_calib < 50):
                vy = 10
            elif (gyro_calib >= 50 and gyro_calib < 200):
                vy = 20
            elif gyro_calib >= 200:
                vy = 30
            else:
                vy = 5
            #print("Gyro (" + self.gyro.axis + " axis) => Raw data :", str(round(gyro_raw,2)), "/ Calibrated data :", str(round(gyro_calib,2)))
        return vy

    def move(self, win_h):
        vy_pad = self.compute_pad_velocity()        
        if self.rect.top + vy_pad < 0:
            self.rect.top = 0
        elif self.rect.bottom + vy_pad > win_h:
            self.rect.bottom = win_h
        else:
            self.rect.move_ip(0,vy_pad)
        return vy_pad
    
    def move_to_center(self, win_h):
        self.rect.centery = win_h // 2
