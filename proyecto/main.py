from controller import Controller

c = Controller()

while c.running:
    c.curr_menu.display_menu()
    if c.playing:
        c.stateList[c.state]()
    c.reset()
