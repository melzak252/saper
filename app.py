import asyncio
from enum import Enum
from typing import List, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

# Enable performance logging

import time
import math
from random import choice, sample, choices
from solver import LostException, MinesweeperSolver, WinException

class GameLevel(Enum):
    BEGINNER = 0
    EASY = 1
    ADVANCED = 2
    EXPERT = 3

GAME_LEVEL_SIZE = {
    GameLevel.BEGINNER: (8, 8),
    GameLevel.EASY: (12, 12),
    GameLevel.ADVANCED: (16, 16),
    GameLevel.EXPERT: (16, 30),
}

GAME_LEVEL_MINES = {
    GameLevel.BEGINNER: 10,
    GameLevel.EASY: 22,
    GameLevel.ADVANCED: 40,
    GameLevel.EXPERT: 99,
}



class MineSweeperPlayer:
    URL: str = 'https://saper-online.pl/gra.php'

    def __init__(self, game_level: GameLevel = GameLevel.BEGINNER, nick: str = "Melzak", wins: int = 5) -> None:
        self.game_level = game_level
        self.nick = nick
        self.wins = wins
        self.driver: webdriver.Chrome = None
        self.game: WebElement = None
        self.panels: WebElement = None

        self.solver: MinesweeperSolver = None


    def connect(self):


        ser = Service(ChromeDriverManager().install())
        options = Options()
        options.add_argument("--no-sandbox")

        # options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options, service=ser)
        self.driver.get('https://saper-online.pl/gra.php')

        
    def log_request(self, intercepted_request):
        print(f"URL: {intercepted_request.get('request').get('url')}")
    
    def game_setup(self):
        self.connect()
        
        self.set_login()
        self.select_level()
        self.click_cookies()
        self.game = self.driver.find_element(By.ID, "Gra")
        board = self.to_board()
        self.solver = MinesweeperSolver(board, GAME_LEVEL_SIZE[self.game_level], self.driver)

    def select_level(self):
        select = Select(self.driver.find_element(By.ID, "poziomValue"))
        select.select_by_index(self.game_level.value)
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.F2)
        self.driver.implicitly_wait(1)

    def set_login(self):
        self.driver.implicitly_wait(1)
        divNick = self.driver.find_element(By.ID, "divNick")
        divNick.find_element(By.XPATH,"// span[contains(text(), 'Zmień nazwę')]").click()
        self.driver.implicitly_wait(1)
        login = divNick.find_element(By.ID, "login")
        login.send_keys(Keys.BACKSPACE * 10)
        login.send_keys(self.nick)
        divNick.find_element(By.XPATH,"// span[contains(text(), 'Zmień')]").click()
        self.driver.implicitly_wait(1)

    def to_board(self):
        board: List[List[WebElement]] = []    
        rows, cols = GAME_LEVEL_SIZE[self.game_level]

        for row in range(rows):
            board.append([])
            for col in range(cols):
                panel = self.game.find_element(By.ID, f"{row}-{col}")  
                board[row].append(panel)
        
        return board
    
    def get_time_info(self):
        czas_info = self.driver.find_element(By.ID, "CzasInfo")
        return czas_info.text

    def new_game(self):
        el = self.driver.find_element(By.TAG_NAME, "body")
        el.send_keys(Keys.F2)
    
        self.game = self.driver.find_element(By.ID, "Gra")
        board = self.to_board()
        self.solver = MinesweeperSolver(board, GAME_LEVEL_SIZE[self.game_level], self.driver)
   

    def click_cookies(self):
        self.driver.find_element(By.XPATH,"// span[contains(text(), 'Rozumiem, akceptuję!')]").click()

    def get_optimal_random_moves(self):
        rows, cols = GAME_LEVEL_SIZE[self.game_level]
        mines = GAME_LEVEL_MINES[self.game_level]
        return int(rows * cols / mines)
    
    async def solve(self):
        condition = True
        threshold = 70
        self.game_setup()
        loses = 0
        while condition:
            try:
                r, c = GAME_LEVEL_SIZE[self.game_level]
                self.solver.click(r // 2 - 1, c // 2 - 1)
                # n = self.get_optimal_random_moves()
                self.random_moves(3)

                while True:
                    await self.solver.update_board()
                    moves = self.solver.find_safe_moves()

                    if moves:
                        for r, c in moves:
                            self.solver.click(r, c)
                    else:
                        moves = self.solver.find_safe_moves()

                        if moves:
                            for r, c in moves:
                                self.solver.click(r, c)
                        else:
                                
                            moves = self.solver.get_unmarked()
                            if not moves:
                                time_info = self.get_time_info()
                                raise WinException(f"Wygrana w {time_info}s")

                            r, c = choice(moves)
                            
                            self.solver.click(r, c)

            except WinException as win:
                print(win)
                time_info = float(self.get_time_info())
                if time_info < threshold:
                    self.wins -= 1
                    condition = self.wins > 0
                self.new_game()
            except LostException as e:
                time_info = self.get_time_info()
                print(f"Przegrałem w {time_info}")

                if float(time_info) > 2.0:
                    self.solver.save_state(f"loses/lose_{loses}.txt")
                    loses += 1
                self.new_game()

            except Exception as e:
                print(e)
                           

        self.driver.close()

    def random_moves(self, n: int = 5):
        moves = self.solver.get_unmarked()
        
        if len(moves) < n:
            r, c = choices(moves)
            
            self.solver.click(r, c)
        else:
            chosen = sample(moves, n)
            for r, c in chosen:
                self.solver.click(r, c)


            

async def main():
    player = MineSweeperPlayer(game_level=GameLevel.EXPERT, nick="Melzak", wins=100)

    await player.solve()

if __name__ == "__main__":
    asyncio.run(main())