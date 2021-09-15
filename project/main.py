from controller import Controller
import sys
if __name__ == '__main__':
    c = Controller()
    while c.running:
        c.curr_menu.display_menu()
        if c.playing:
            c.kill()
            c.stateList[c.state]()
        c.reset()
    c.kill()
    sys.exit()

