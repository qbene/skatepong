#!usr/bin/python3

#-----------------------------------------------------------------------------
# IMPORTS
#-----------------------------------------------------------------------------

import pygame
import math

#-----------------------------------------------------------------------------
# INITIALIZATION
#-----------------------------------------------------------------------------

pygame.init()

#-----------------------------------------------------------------------------
# CONSTANTS
#-----------------------------------------------------------------------------

WIN_WIDTH_INIT, WIN_HEIGHT_INIT = 700, 500
PADDLE_WIDTH_RATIO = 0.02 # Ratio to screen width [0.01 - 0.1]
PADDLE_HEIGHT_RATIO = 0.15 # Ratio to screen height [0.05 - 0.2]
BALL_RADIUS_RATIO = 0.02 # Ratio to min screen width/height [0.01 - 0.04]
PADDLE_VY_RATIO = 0.03 # Ratio to screen height [0.005 - 0.04]
BALL_V_RATIO = 0.01 # Ratio to min screen width [0.005 - 0.02]
BALL_ANGLE_MAX = 60 # In degrees [30-75]
MID_LINE_HEIGHT_RATIO = 0.05 # Ratio to screen height  [ideally 1/x -> int]
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SCORE_FONT = pygame.font.SysFont("comicsans", 50)
WINNING_SCORE = 5

#-----------------------------------------------------------------------------
# CODE
#-----------------------------------------------------------------------------

class Paddle:
    COLOR = WHITE

    def __init__(self, x, y, width, height, vy):
        self.x = self.original_x = x
        self.y = self.original_y = y
        self.width = width
        self.height = height
        self.vy = vy

    def draw(self, win):
        pygame.draw.rect(win, self.COLOR, (self.x, self.y, self.width, self.height))

    def move(self, up=True):
        if up:
            self.y -= self.vy
        else:
            self.y += self.vy

class Ball:
    COLOR = WHITE

    def __init__(self, x, y, radius, vx, vy):
        self.x = self.original_x = x
        self.y = self.original_y = y
        self.radius = radius
        self.vx = vx
        self.vy = vy

    def draw(self, win):
        pygame.draw.circle(win, self.COLOR, (self.x, self.y), self.radius)

    def move(self):
        self.x += self.vx
        self.y += self.vy

def draw_game(win, paddles, ball, left_score, right_score, win_width, win_height,mid_line_height_ratio):
    win.fill(BLACK)
    left_score_text = SCORE_FONT.render(f"{left_score}", 1, WHITE)
    right_score_text = SCORE_FONT.render(f"{right_score}", 1, WHITE)
    win.blit(left_score_text, (win_width//4 - left_score_text.get_width()//2, 20))
    win.blit(right_score_text, (int(win_width*(3/4)) - right_score_text.get_width()//2, 20))

    for paddle in paddles:
        paddle.draw(win)

    ball.draw(win)
    draw_mid_line(win, win_width,win_height,mid_line_height_ratio)
    pygame.display.update()

def draw_mid_line(win, win_width,win_height,mid_line_height_ratio):
    line_element_height = round(win_height*mid_line_height_ratio)
    nb_iterations = round(1/mid_line_height_ratio)-1
    for i in range(0, nb_iterations):
        if i % 2 == 1:
            continue
        pygame.draw.rect(win, WHITE, (win_width//2 - 5, i*line_element_height+line_element_height//2, 10, line_element_height))

def draw_victory(win, paddles, left_score, right_score, win_width, win_height, win_text):
    win.fill(BLACK)
    left_score_text = SCORE_FONT.render(f"{left_score}", 1, WHITE)
    right_score_text = SCORE_FONT.render(f"{right_score}", 1, WHITE)
    win.blit(left_score_text, (win_width//4 - left_score_text.get_width()//2, 20))
    win.blit(right_score_text, (int(win_width*(3/4)) - right_score_text.get_width()//2, 20))
    text = SCORE_FONT.render(win_text, 1, WHITE)
    win.blit(text, (win_width//2 - text.get_width() // 2, win_height//2 - text.get_height()//2))
    for paddle in paddles:
        paddle.draw(win)
    pygame.display.update()

def handle_collision(ball, left_paddle, right_paddle, win_width, win_height):
    if ball.y + ball.radius >= win_height:
        ball.vy *= -1
    elif ball.y - ball.radius <= 0:
        ball.vy *= -1

    if ball.vx < 0:
        if ball.y >= left_paddle.y and ball.y <= left_paddle.y + left_paddle.height:
            if ball.x - ball.radius <= left_paddle.x + left_paddle.width:
                y_paddle_mid = left_paddle.y + left_paddle.height // 2
                angle = round((ball.y - y_paddle_mid) / (left_paddle.height / 2) * BALL_ANGLE_MAX)
                vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_width)
                vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_width)
                ball.vy = vy
                ball.vx = vx

    else:
        if ball.y >= right_paddle.y and ball.y <= right_paddle.y + right_paddle.height:
            if ball.x + ball.radius >= right_paddle.x:
                y_paddle_mid = right_paddle.y + right_paddle.height // 2
                angle = round((ball.y - y_paddle_mid) / (right_paddle.height / 2) * BALL_ANGLE_MAX)
                vx = round(math.cos(math.radians(angle)) * BALL_V_RATIO * win_width)
                vy = round(math.sin(math.radians(angle)) * BALL_V_RATIO * win_width)
                ball.vy = vy
                ball.vx = -1*vx

def handle_paddle_movement(keys, left_paddle, right_paddle, win_height):
    if keys[pygame.K_w] and left_paddle.y - left_paddle.vy >= 0:
        left_paddle.move(up=True)
    if keys[pygame.K_s] and left_paddle.y + left_paddle.vy + left_paddle.height <= win_height:
        left_paddle.move(up=False)

    if keys[pygame.K_UP] and right_paddle.y - right_paddle.vy >= 0:
        right_paddle.move(up=True)
    if keys[pygame.K_DOWN] and right_paddle.y + right_paddle.vy + right_paddle.height <= win_height:
        right_paddle.move(up=False)

def create_window(width,height):
    
    WIN = pygame.display.set_mode([width, height], pygame.RESIZABLE)
    pygame.display.set_caption("Pong")
    return WIN

def compute_elements_sizes(win_width, win_height):
    paddle_width = round(win_width*PADDLE_WIDTH_RATIO)
    paddle_height = round(win_height*PADDLE_HEIGHT_RATIO)
    ball_radius = min(round(win_width*BALL_RADIUS_RATIO), round(win_height*BALL_RADIUS_RATIO))
    vy = round(win_height * PADDLE_VY_RATIO)
    ball_vx = round(BALL_V_RATIO*win_width)
    ball_vy = 0
    return paddle_width, paddle_height, ball_radius, vy, ball_vx, ball_vy

def main():
    run = True
    clock = pygame.time.Clock()
    win_width = WIN_WIDTH_INIT
    win_height = WIN_HEIGHT_INIT
    mid_line_height = round(MID_LINE_HEIGHT_RATIO *  win_height)
    paddle_width, paddle_height, ball_radius, vy, ball_vx, ball_vy = compute_elements_sizes(win_width, win_height)
    left_paddle = Paddle(10, win_height//2 - paddle_height // 2, paddle_width, paddle_height,vy)
    right_paddle = Paddle(win_width - 10 - paddle_width, win_height // 2 - paddle_height//2, paddle_width, paddle_height,vy)
    ball = Ball(win_width // 2, win_height // 2, ball_radius, ball_vx, ball_vy)
    WIN = create_window(win_width,win_height)

    left_score = 0
    right_score = 0

    while run:
        clock.tick(FPS)
        draw_game(WIN, [left_paddle, right_paddle], ball, left_score, right_score, win_width, win_height,MID_LINE_HEIGHT_RATIO)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            elif event.type == pygame.VIDEORESIZE:
                win_width = event.w
                win_height = event.h
                paddle_width, paddle_height, ball_radius, vy, ball_vx, ball_vy = compute_elements_sizes(win_width, win_height)
                create_window(win_width,win_height)
                left_paddle = Paddle(10, win_height//2 - paddle_height // 2, paddle_width, paddle_height,vy)
                right_paddle = Paddle(win_width - 10 - paddle_width, win_height // 2 - paddle_height//2, paddle_width, paddle_height,vy)
                ball = Ball(win_width // 2, win_height // 2, ball_radius, ball_vx, ball_vy)
                draw_game(WIN, [left_paddle, right_paddle], ball, left_score, right_score,win_width, win_height,MID_LINE_HEIGHT_RATIO)
                pygame.display.update()

        keys = pygame.key.get_pressed()
        handle_paddle_movement(keys, left_paddle, right_paddle, win_height)

        ball.move()
        handle_collision(ball, left_paddle, right_paddle, win_width, win_height)

        if ball.x < 0:
            right_score += 1
            ball = Ball(win_width // 2, win_height // 2, ball_radius, ball_vx, ball_vy)
            draw_game(WIN, [left_paddle, right_paddle], ball, left_score, right_score, win_width, win_height, mid_line_height)
        elif ball.x > win_width:
            left_score += 1
            ball = Ball(win_width // 2, win_height // 2, ball_radius, -ball_vx, ball_vy)
            draw_game(WIN, [left_paddle, right_paddle], ball, left_score, right_score, win_width, win_height,mid_line_height)

        won = False
        if left_score >= WINNING_SCORE:
            won = True
            win_text = "Left Player Won!"
        elif right_score >= WINNING_SCORE:
            won = True
            win_text = "Right Player Won!"

        if won:
            draw_victory(WIN, [left_paddle, right_paddle], left_score, right_score, win_width, win_height,win_text)
            pygame.time.delay(5000)
            run = False

    pygame.quit()

if __name__ == '__main__':
    main()
