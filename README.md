# MineSweeper Solver

## Project Overview
This Python-based Minesweeper Solver automates playing Minesweeper on saper-online.pl using Selenium. The program can recognize the game state, make strategic decisions, and learn from previous games by documenting states where it lost.

## Tags:
- `Python 3.8+`
- `Selenium`
- `Asyncio`
- `JS`
- `WebScrapping`

## Features
- **Automated Gameplay**: Automatically play Minesweeper using Selenium WebDriver.
- **Multiple Difficulty** Levels: Choose from beginner to expert levels.
- **Error Handling**: Manages wins and losses with custom exceptions.
- **State Logging**: Ability to save and analyze game states.
- **Customizable Player** Settings: Set your nickname and target wins.

## Prerequisites
- `Python 3.8+`
- `Chrome WebDriver`

## Setup
1. Clone the repository:
```bash
git clone [your-repository-url]
cd [repository-name]
```
2. Install the required packages from requirements.txt:
```bash
pip install -r requirements.txt
```
# Usage
Run the solver with the following command:
```bash
python app.py
```

## Configuration
Modify game settings in app.py as desired:

```python
if __name__ == "__main__":
    player = MineSweeperPlayer(game_level=GameLevel.EXPERT, nick="Melzak", wins=10)
    asyncio.run(main())
```
Update game_level, nick, and wins to suit your preferences.
