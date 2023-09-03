# textual-game-of-life 

An implementation of Conway's game of life (cellular automata) in the terminal using textual.

[textual-game-of-life](https://github.com/thomascrha/textual-game-of-life/assets/5226462/66dd4153-d286-4680-ac73-8fd63e60c00e)

## install

```bash
git clone textual-game-of-life # ;)
pip3 install -r requirements.txt
```
## usage

```bash
python3 main.py
```

## todo

- [ ] add toggle for starting/stopping the game. 
- [ ] add a command line interface for all the options and settings.
- [ ] make cursor black when on a white cell and white when on a black cell.
- [ ] add a way to save/load the current state of the game.
- [ ] add shift_+ and shift_- to change the horizontal width of the canvas.
- [ ] add ctrl_+ and ctrl_- to change the vertical width of the canvas.
- [ ] add alt_+ and alt_- to change the size of the pixels.
- [ ] add a way to change the speed of the game.

This will most likely spun into there own project.
- [ ] look into using [textual-canvas](https://github.com/davep/textual-canvas) for the canvas - seems to have far smaller pixels. 
- [ ] implement more automata rules. I may create a more general version of this program that can be used to implement any cellular automata.
