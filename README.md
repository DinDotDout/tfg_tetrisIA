# tfg_tetrisIA
Neural net implementation, capable of playing play tetris99

main.py - as the name suggests, this is the main code. It requires two arguments to be passed, the first one being the serial port (e.g., "COM5") and the second one being te capture device index. When choosing to access the nintendo switch you can control the movement with the classic W,A,S,D keys and then use the J,K,L which are mapped to the switch buttons L,B,A. To end the program press 'Q' and to start the auto mode, which begins at the Tetris99 selection screen, press 'Y'.
SwitchController.py - contains all the commands and methods that we use to send what we want to the nintendo switch console.

