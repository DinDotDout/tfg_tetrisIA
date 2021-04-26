import pygame


class Menu():
    def __init__(self, controller):
        self.controller = controller
        self.mid_w, self.mid_h = self.controller.DISPLAY_W / 2, self.controller.DISPLAY_H / 2
        self.run_display = True
        
        self.textSize = 40
        self.offset = - 270
        self.cursorX = self.mid_w + self.offset
        
        self.playX, self.playY = self.mid_w, self.mid_h
        self.trainX, self.trainY = self.mid_w, self.playY + self.textSize
        self.testX, self.testY = self.mid_w, self.trainY + self.textSize
        self.switchX, self.switchY = self.mid_w, self.testY + self.textSize

        self.state = 0  # Menu cursor selector
        self.states = 4

        self.cursor_rect = pygame.Rect(0, 0, 20, 20)
        self.cursor_rect.midtop = (self.mid_w, self.mid_h+self.state*self.textSize)

    def display_menu(self):
        self.run_display = True
        while self.run_display:
            self.controller.check_events()
            self.check_input()
            self.controller.display.fill(self.controller.BLACK)
            self.controller.draw_text('Menu', self.textSize, self.controller.DISPLAY_W / 2, self.controller.DISPLAY_H / 2 - 80)
            self.controller.draw_text("Play Tetris", self.textSize, self.playX, self.playY)
            self.controller.draw_text("Train Net", self.textSize, self.trainX, self.trainY)
            self.controller.draw_text("Test Net", self.textSize, self.testX, self.testY)
            self.controller.draw_text("Access Switch", self.textSize, self.switchX, self.switchY)
            self.draw_cursor()
            self.blit_screen()

    def check_input(self):
        self.move_cursor()
        if self.controller.START_KEY:
            self.controller.playing = True
            self.controller.state = self.state
            self.run_display = False

    def draw_cursor(self):
        self.controller.draw_text('*', self.textSize-10, self.cursor_rect.x, self.cursor_rect.y)

    def blit_screen(self):
        self.controller.window.blit(self.controller.display, (0, 0))
        pygame.display.update()
        self.controller.reset_keys()

    def move_cursor(self):
        if self.controller.DOWN_KEY:
            self.state += 1
        elif self.controller.UP_KEY:
            self.state -= 1
        self.state %= self.states
        self.cursor_rect.midtop = (self.cursorX, self.mid_h+self.state*self.textSize)




