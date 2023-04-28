#!usr/bin/python3

#-----------------------------------------------------------------------
# IMPORTS
#-----------------------------------------------------------------------

import pygame

#-----------------------------------------------------------------------
# CODE
#-----------------------------------------------------------------------

def draw_text(win, font_nm, font_sz, txt, x, y, color, bg_color = None):
    """
    Draws text on a surface, text center serving as position reference.
    
    bg_color = text background color
    """
    font = pygame.font.SysFont(font_nm, font_sz)
    txt_surf = font.render(txt, True, color, bg_color)
    txt_rect = txt_surf.get_rect()
    txt_rect.center = (x, y)
    win.blit(txt_surf, txt_rect)
    
def draw_text_2(win, font_nm, font_sz, txt, x, y, color, bg_color = None):
    """
    Draws text on a surface, text center serving as position reference.
    
    bg_color = text background color
    """
    font = pygame.font.SysFont(font_nm, font_sz)
    txt_surf = font.render(txt, True, color, bg_color)
    txt_rect = txt_surf.get_rect()
    txt_rect.center = (x, y)
    win.blit(txt_surf, txt_rect)
    return txt_rect
    
def get_max_w_txt(font_nm, font_sz, *txts):
    """
    Returns the maximum width (px) of the texts given as argmuments.
    """
    color = (255,255,255) # text color. Whatever because no display here
    font = pygame.font.SysFont(font_nm, font_sz)
    max_w_txt = 0
    for txt in txts:
        txt_surf = font.render(txt, True, color)
        txt_w = txt_surf.get_width()
        #print (txt_w)
        if txt_w > max_w_txt:
            max_w_txt = txt_w
    #print ("Max text width :", max_w_txt)
    return max_w_txt
    
    
def draw_mid_line(win, win_w, win_h, thick, horiz_w_factor, color):
    """
    Draws vertical and short horizontals line in the mid screen.
    """
    # Straight line, with small center cross
    vert_rect = pygame.Rect(0, 0, thick, win_h)
    horiz_rect = pygame.Rect(0, 0, horiz_w_factor * thick, thick)
    vert_rect.center = (win_w // 2, win_h //2)
    horiz_rect.center = (win_w // 2, win_h //2)
    pygame.draw.rect(win, color, horiz_rect)
    pygame.draw.rect(win, color, vert_rect)

def comp_font_sizes(win_h):
    """
    Creates a dictionnary with different font sizes.
    """
    ft_dic = {
              "0.05" : int(0.05 * win_h), \
              "0.10" : int(0.10 * win_h), \
              "0.15" : int(0.15 * win_h), \
              "0.20" : int(0.20 * win_h), \
              }
    return ft_dic

def comp_common_coordinates(win_w, win_h):
    """
    Creates a dictionnary with commonly used window coordinates.
    """
    x_dic = {
             "1/4": win_w // 4, \
             "1/2": win_w // 2, \
             "3/4": (win_w * 3) // 4 \
             }
    y_dic = {
             "1/4": win_h // 4, \
             "1/2": win_h // 2, \
             "3/4": (win_h * 3) // 4 \
             }
    return x_dic, y_dic
    """         
    self.x_1_2 = self.win_w // 2
    self.x_1_4 = self.win_w // 4
    self.x_3_4 = (self.win_w * 3) // 4
    self.y_1_2 = self.win_h // 2
    self.y_1_4 = self.win_h // 4
    self.y_3_4 = (self.win_h * 3) // 4
    """

def main():
    """
    Function for test purposes only
    """
    pygame.init()
    get_max_w_txt("comicsans", 10, "Hello", "Move Skate", "Left")

if __name__ == '__main__':
    main()
