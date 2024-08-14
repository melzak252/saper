import time
from typing import List, Tuple
from typing import List, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import asyncio
from concurrent.futures import ThreadPoolExecutor

class LostException(Exception):
    pass

class WinException(Exception):
    pass

class MinesweeperSolver:
    def __init__(self, board, board_size, driver, mines: int):
        self.driver = driver
        self.raw_board: List[List[WebElement]] = board
        self.board: List[List[int | None]] = []
        self.mines = mines
        self.mines_found = 0
        self.board_rows, self.board_cols = board_size
        tiles = self.board_rows * self.board_cols
        self.perc_board: List[List[float | None]] = [[mines / tiles for _ in range(self.board_cols)] for _ in range(self.board_rows)]
        self.reset()
        
    def reset(self):
        for i in range(self.board_rows):
            self.board.append([])
            for j in range(self.board_cols):
                self.board[i].append(None)


    def find_safe_moves(self):
        save_moves = set()
        for i, row in enumerate(self.board):
            for j, val in enumerate(row):
                if val is not None and val > 0:
                    num, moves = self.surrounding(i, j)

                    if num > 0 and num == len(moves):
                        for r, c in moves:
                            self.board[r][c] = -1
                            self.mines_found += 1
                    elif num == 0:
                        save_moves = save_moves | set(moves)

        # self.save_state()
        
        return save_moves
    
    def get_unmarked(self):
        return [(i, j) for i, row in enumerate(self.board) for j, col in enumerate(row) if col is None]
    
    def surrounding(self, row, col) -> Tuple[int, List[Tuple[int, int]]]:
        num = self.board[row][col]
        possible_moves = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if (i == 0 and j == 0) or not (0 <= (row + i) < self.board_rows) or not (0 <= (col + j) < self.board_cols):
                    continue
                
                val = self.board[row + i][col + j]
                if val is None:
                    possible_moves.append((row + i, col + j))

                if val == -1:
                    num -= 1
                    
        return num, possible_moves   
    
        
    def surrounding_prob(self, row, col) -> Tuple[int, List[Tuple[int, int]]]:
        num = self.board[row][col]
        possible_moves = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if (i == 0 and j == 0) or not (0 <= (row + i) < self.board_rows) or not (0 <= (col + j) < self.board_cols):
                    continue
                
                val = self.board[row + i][col + j]
                if val is None:
                    possible_moves.append((row + i, col + j))

                if val == -1:
                    num -= 1
                    
        return num, possible_moves 
    
    def probability(self):
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for i, row in enumerate(self.board):
            for j, val in enumerate(row):
                if val is not None:
                    self.perc_board[i][j] = None
                    continue
                
                bomb_count = 0
                unknown_count = 0
                for dr, dc in directions:
                    nr, nc = i + dr, j + dc
                    if not (0 <= nr < self.board_rows and 0 <= nc < self.board_cols) or self.board[nr][nc] is None or self.board[nr][nc] <= 0:
                        continue
                    
                    n, moves = self.surrounding(nr, nc)
                    bomb_count += n
                    
                    unknown_count += len(moves)
                        
                self.perc_board[i][j] = bomb_count / unknown_count if unknown_count else 1

        min_prob = float('inf')
        min_indices = []

        for r, row in enumerate(self.perc_board):
            for c, val in enumerate(row):
                if val is not None and val < min_prob:
                    min_prob = val
                    min_indices = [(r, c)]
                elif val == min_prob:
                    min_indices.append((r, c))

        return min_indices

    async def update_board(self):
        executor = ThreadPoolExecutor(max_workers=20)  # Adjust as necessary
        script = """
            var elements = arguments[0];
            var attrs = [];
            for (var i = 0; i < elements.length; i++) {
                attrs.push(elements[i].getAttribute('src'));
            }
            return attrs;
        """
        try:
            # Fetch all elements at once
            all_elements = [val for i, row in enumerate(self.raw_board) for j, val in enumerate(row) if self.board[i][j] is None]
            loop = asyncio.get_running_loop()
            attributes = await loop.run_in_executor(
                executor, lambda: self.driver.execute_script(script, all_elements))

            my_iter = iter(attributes)
            # Process the attributes
            for i, row in enumerate(self.raw_board):
                for j, _ in enumerate(row):
                    a = self.board[i][j]
                    if a is not None:
                        continue                    
                    
                    src = next(my_iter)

                    if src.endswith("ptaszek.jpd"):
                        raise WinException("Wygrana!")
                    elif src.endswith("mineszary.jpg"):
                        raise LostException("Juz po grze")
                    elif src.endswith("flagziel.jpg"):
                        raise LostException("Juz po grze")
                    elif src.endswith("flag.jpg"):
                        a = -1
                    elif src.endswith("0.jpg"):
                        a = 0
                    elif src.endswith("1.jpg"):
                        a = 1
                    elif src.endswith("2.jpg"):
                        a = 2
                    elif src.endswith("3.jpg"):
                        a = 3
                    elif src.endswith("4.jpg"):
                        a = 4
                    elif src.endswith("5.jpg"):
                        a = 5
                    elif src.endswith("6.jpg"):
                        a = 6
                    elif src.endswith("7.jpg"):
                        a = 7
                    elif src.endswith("8.jpg"):
                        a = 8
                    elif src.endswith("9.jpg"):
                        raise LostException("Mina!!!")
                    
                    self.board[i][j] = a
        except WinException as e:
            raise e
        except LostException as e:
            raise e
        except Exception as e:
            print(e)
            raise LostException(e)

    async def get_attribute_async(self, executor, element, attribute, i, j):
        loop = asyncio.get_running_loop()
        src = await loop.run_in_executor(executor, element.get_attribute, attribute)
        return i, j, src

    def click(self, row, col):
        self.raw_board[row][col].click() 

    def save_state(self, filename: str = "state.txt"):
        with open(filename, "w") as f:
            for row in self.board:
                for val in row:
                    a = ""
                    if val is None:
                        a = "E" 
                    elif 0 < val < 9:
                        a = f"{val}"
                    elif val == 0:
                        a = " "
                    elif val == -1:
                        a = "X"
                    f.write(f"{a} ")

                f.write("\n")
            