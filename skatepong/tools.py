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
        if txt_w > max_w_txt:
            max_w_txt = txt_w
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
    mid_line_h_rect = pygame.draw.rect(win, color, horiz_rect)
    mid_line_v_rect = pygame.draw.rect(win, color, vert_rect)
    return mid_line_h_rect, mid_line_v_rect

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
             "0.05": int(win_w * 0.05), \
             "0.10": int(win_w * 0.10), \
             "0.15": int(win_w * 0.15), \
             "0.20": int(win_w * 0.20), \
             "0.25": int(win_w * 0.25), \
             "0.30": int(win_w * 0.30), \
             "0.35": int(win_w * 0.35), \
             "0.40": int(win_w * 0.40), \
             "0.45": int(win_w * 0.45), \
             "0.50": int(win_w * 0.50), \
             "0.55": int(win_w * 0.55), \
             "0.60": int(win_w * 0.60), \
             "0.65": int(win_w * 0.65), \
             "0.70": int(win_w * 0.70), \
             "0.75": int(win_w * 0.75), \
             "0.80": int(win_w * 0.80), \
             "0.85": int(win_w * 0.85), \
             "0.90": int(win_w * 0.90), \
             "0.95": int(win_w * 0.95) \
             }
    y_dic = {
             "0.05": int(win_h * 0.05), \
             "0.10": int(win_h * 0.10), \
             "0.15": int(win_h * 0.15), \
             "0.20": int(win_h * 0.20), \
             "0.25": int(win_h * 0.25), \
             "0.30": int(win_h * 0.30), \
             "0.35": int(win_h * 0.35), \
             "0.40": int(win_h * 0.40), \
             "0.45": int(win_h * 0.45), \
             "0.50": int(win_h * 0.50), \
             "0.55": int(win_h * 0.55), \
             "0.60": int(win_h * 0.60), \
             "0.65": int(win_h * 0.65), \
             "0.70": int(win_h * 0.70), \
             "0.75": int(win_h * 0.75), \
             "0.80": int(win_h * 0.80), \
             "0.85": int(win_h * 0.85), \
             "0.90": int(win_h * 0.90), \
             "0.95": int(win_h * 0.95) \
             }
    return x_dic, y_dic
    
def get_cpu_revision():
    """
    Returns cpu revision information
    -------------------------------------------------------------------
    3 Model B -> a02082 / a22082 / a32082
    3 Model B+ -> a020d3
    4 Model B (1Go) -> a03111 
    4 Model B (2Go) -> b03111 / b03112 / b03114 / b03115
    4 Model B (4Go) -> c03111 / c03112 / c03114 / c03115
    4 Model B (8Go) -> d03114 / d03115
    -------------------------------------------------------------------
    """
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line [0:8] == "Revision":
                cpu_rev = line[11:17]
        f.close()
    except:
        cpu_rev = "not found"
    print ("cpu revision:", cpu_rev)
    return (cpu_rev)
    
def is_rpi_4b(cpu_rev):
    """
    Returns cpu revision information
    -------------------------------------------------------------------
    3 Model B -> a02082 / a22082 / a32082
    3 Model B+ -> a020d3
    4 Model B (1Go) -> a03111 
    4 Model B (2Go) -> b03111 / b03112 / b03114 / b03115
    4 Model B (4Go) -> c03111 / c03112 / c03114 / c03115
    4 Model B (8Go) -> d03114 / d03115
    -------------------------------------------------------------------
    """
    rpi_4b = False
    list_rpi_4b = ["a03111", \
                   "b03111", "b03112", "b03114", "b03115", \
                   "c03111", "c03112", "c03114", "c03115", \
                   "d03114" , "d03115"]
    for rev in list_rpi_4b:
        if cpu_rev == rev:
            rpi_4b = True
            break
    print ("Raspberry Pi 4 :", rpi_4b)
    return rpi_4b

def main():
    """
    Function for test purposes only
    """
    cpu_rev = get_cpu_revision()
    is_rpi_4b(cpu_rev)
    is_rpi_4b("a020d3")

if __name__ == '__main__':
    main()
