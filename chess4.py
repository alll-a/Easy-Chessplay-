import tkinter as tk #tkinter is used to build the graphical window
import random
from dataclasses import dataclass #dataclass is used to create a simple class for storing moves
from typing import List, Optional, Tuple, Dict #typing adds type hints to make the code easier to read

Pos = Tuple[int, int]  # (row, col)

UNICODE_PIECES: Dict[str, str] = {
    "wK": "♔", "wQ": "♕", "wR": "♖", "wB": "♗", "wN": "♘", "wP": "♙",
    "bK": "♚", "bQ": "♛", "bR": "♜", "bB": "♝", "bN": "♞", "bP": "♟",
}

LIGHT = "#EEEED2" #light squares
DARK = "#769656"  #dark squares
SELECT = "#F6F669" #color of the selected piece
MOVE_DOT = "#BACA44" #highlight for normal possible moves
CAPTURE = "#E06C75" #highlight for a square where an opponent’s piece can be captured


@dataclass(frozen=True)
class Move: #This creates a simple object representing one move.
    src: Pos #source square
    dst: Pos #destination square


def initial_board() -> List[List[Optional[str]]]:  #This function creates the starting chess position
    # 8x8, row 0 is top (black side)
    board = [[None for _ in range(8)] for _ in range(8)] #This creates an 8×8 board full of None. None means the square is empty.
    board[0] = ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"] #black back rank
    board[1] = ["bP"] * 8                                       #black pawns
    board[6] = ["wP"] * 8                                       #white pawns
    board[7] = ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"] #white back rank
    return board


def in_bounds(r: int, c: int) -> bool: #This function checks whether a square is inside the 8×8 board.
    return 0 <= r < 8 and 0 <= c < 8

def color_of(piece: str) -> str: #Each piece string starts with its color:"wP" → white	"bK" → black
    return piece[0]  # 'w' or 'b'

def get_all_pseudo_legal_moves(board: List[List[Optional[str]]], turn: str) -> List[Move]:
    all_moves: List[Move] = []

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is not None and color_of(piece) == turn:
                piece_moves = generate_pseudo_legal_moves(board, turn, (r, c))
                all_moves.extend(piece_moves)

    return all_moves



def generate_pseudo_legal_moves(board: List[List[Optional[str]]], turn: str, src: Pos) -> List[Move]:
    """
    This is one of the most important parts of the program.
    It generates possible moves for one selected piece.
    """
    r, c = src  #Check whether the selected square contains the current player’s piece
    piece = board[r][c]
    if not piece or color_of(piece) != turn:
        return []

    kind = piece[1] #Since the piece looks like "wP" or "bK":	piece[0] = color, piece[1] = piece type
    moves: List[Move] = []

    def add(dst_r: int, dst_c: int): #This helper tries to add a move if the destination square is valid.
        if not in_bounds(dst_r, dst_c): #It does three things: 1.	makes sure the square is on the board
            return                                            #	2.	checks the target square
        target = board[dst_r][dst_c]                            #3.	adds the move if the square is empty or contains an enemy piece
        if target is None or color_of(target) != turn:
            moves.append(Move(src=src, dst=(dst_r, dst_c)))

    if kind == "P":
        direction = -1 if turn == "w" else 1 #White pawns move upward in the matrix, so they use -1.Black pawns move downward, so they use +1.
        start_row = 6 if turn == "w" else 1 #White pawns start on row 6. Black pawns start on row 1.

        # 1 step forward                A pawn can move forward by one square if that square is empty.
        nr = r + direction
        if in_bounds(nr, c) and board[nr][c] is None:
            add(nr, c)
            # 2 steps from start      If the pawn is still on its starting row and the path is clear, it may move two squares forward.
            nr2 = r + 2 * direction
            if r == start_row and in_bounds(nr2, c) and board[nr2][c] is None:
                add(nr2, c)

        # captures                   A pawn may capture diagonally left or right if an enemy piece is there.
        for dc in (-1, 1):
            cr, cc = r + direction, c + dc
            if in_bounds(cr, cc) and board[cr][cc] is not None and color_of(board[cr][cc]) != turn:
                moves.append(Move(src=src, dst=(cr, cc)))

    elif kind == "N": #Knights move in an L-shape, so the code checks all 8 possible knight jumps:
        for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
            add(r + dr, c + dc) #Each candidate square is added with add().Knights do not care about pieces in between.

    elif kind in ("B", "R", "Q"): #These pieces move in straight lines.
        directions = []
        if kind in ("B", "Q"):
            directions += [(-1,-1), (-1,1), (1,-1), (1,1)] #Diagonal directions:(-1,-1), (-1,1), (1,-1), (1,1)
        if kind in ("R", "Q"):
            directions += [(-1,0), (1,0), (0,-1), (0,1)] #Straight directions:(-1,0), (1,0), (0,-1), (0,1)The queen gets both sets of directions.

        for dr, dc in directions: #The piece keeps moving square by square until it reaches the edge or hits another piece.
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                target = board[nr][nc]
                if target is None: #If the square is empty. The move is allowed, and the piece can keep going farther.
                    moves.append(Move(src=src, dst=(nr, nc)))
                else: #If the square is occupied : 	if it is an enemy piece, the square is added as a capture,
                    if color_of(target) != turn: #		after that, movement in that direction stops
                        moves.append(Move(src=src, dst=(nr, nc))) #if it is your own piece, movement also stops, but no move is added
                    break
                nr += dr
                nc += dc

    elif kind == "K": #King movement
        for dr in (-1, 0, 1): #The king moves one square in any direction.
            for dc in (-1, 0, 1): #The code checks all combinations of dr and dc from -1 to 1, except (0, 0).
                if dr == 0 and dc == 0:
                    continue
                add(r + dr, c + dc)

        # Рокировку можно добавить позже (опционально)

    return moves #Return all generated moves


class ChessGUI: #This class manages the graphical chess interface. It stores: the board, current turn, selected square, legal moves, buttons representing squares, status text
    def __init__(self, root: tk.Tk): #This method runs when the GUI is created.
        self.root = root
        root.title("Chess (Tkinter)") #The main window is stored and given a title.

        self.board = initial_board() #The board starts in the initial position, and white moves first.
        self.turn = "w"

        self.selected: Optional[Pos] = None #Selection state At first: no square is selected, no legal moves are highlighted
        self.legal_moves: List[Move] = []

        self.status = tk.StringVar(value="White to move") #Status text This stores the status message shown at the top.
        self.frame = tk.Frame(root, bg="#2B2B2B", padx=12, pady=12) #Main frame. This creates the main container for the whole interface.
        self.frame.pack()

        self.ai_enabled = True
        self.ai_color = "b"

        top = tk.Frame(self.frame, bg="#2B2B2B") #Top panel. This row contains the status label and the reset button.
        top.pack(fill="x", pady=(0, 10)) 
            #Status label. This shows whose turn it is.
        tk.Label(top, textvariable=self.status, fg="white", bg="#2B2B2B", font=("Helvetica", 14, "bold")).pack(side="left")
            #Reset button. This creates a button labeled “New game”.
        tk.Button(top, text="New game", command=self.reset, relief="flat").pack(side="right")

        #Board frame. This frame holds the 8×8 grid of board squares.
        self.board_frame = tk.Frame(self.frame, bd=2, relief="solid")
        self.board_frame.pack()

        #Create 64 buttons. The program creates one button for each square of the board.
        self.cells: List[List[tk.Label]] = [[None]*8 for _ in range(8)]
        for r in range(8):
            for c in range(8):
                cell = tk.Label( #Button configuration
                    self.board_frame,
                    width=4,
                    height=2,
                    font=("Helvetica", 20),
                    bd=0,
                    relief="flat",
                    anchor="center",#command=lambda rr=r, cc=c: self.on_click(rr, cc),
                )
                cell.bind("<Button-1>", lambda e, rr=r, cc=c: self.on_click(rr, cc))
                cell.grid(row=r, column=c, sticky="nsew")
                self.cells[r][c] = cell
                

        for i in range(8): #Make rows and columns expandable
            self.board_frame.grid_rowconfigure(i, weight=1)
            self.board_frame.grid_columnconfigure(i, weight=1)

        self.redraw() # First drawing of the board

    def reset(self): #Reset method. This restores the starting position.
        self.board = initial_board() #creates a fresh initial board
        self.turn = "w" #ets turn to white
        self.selected = None #clears the selected square
        self.legal_moves = [] #clears legal moves
        self.status.set("White to move") #	resets the status text
        self.redraw() #redraws the board

    def on_click(self, r: int, c: int): #Handling a click. This method runs whenever the user clicks a board square
        pos = (r, c) #Read the clicked square: pos is the clicked position
        piece = self.board[r][c] #piece is the piece currently on that square, if any

        # If a piece is already selected, try to move it. Если уже выбрали фигуру — пробуем сделать ход
        if self.selected is not None:
            chosen = Move(self.selected, pos)
            if any(m.src == chosen.src and m.dst == chosen.dst for m in self.legal_moves):
                self.make_move(chosen)
                self.root.after(300, self.make_ai_move)
                return

        # Otherwise, try to select a piece. Иначе выбираем фигуру текущего игрока
        if piece is not None and color_of(piece) == self.turn:
            self.selected = pos
            self.legal_moves = generate_pseudo_legal_moves(self.board, self.turn, pos)
            #print("LEGAL MOVES:", self.legal_moves)
        else: #If not, clear the selection
            self.selected = None
            self.legal_moves = []

        self.redraw() #Redraw after every click. The board is updated visually.

    def make_move(self, move: Move): #Making a move.This method updates the board after a valid move.
        sr, sc = move.src #Move the piece. The piece is moved from source to destination.
        dr, dc = move.dst
        self.board[dr][dc] = self.board[sr][sc] #If an enemy piece was on the destination square, it gets overwritten, which means it is captured
        self.board[sr][sc] = None

        # Switch turn. Переключаем ход If white just moved, it becomes black’s turn.
        self.turn = "b" if self.turn == "w" else "w"
        self.status.set("Black to move" if self.turn == "b" else "White to move") # Update status text

        self.selected = None #Clear selection after the move
        self.legal_moves = [] #After a move is made, nothing remains selected.
        self.redraw() # Redraw again. The interface refreshes to show the new position.
    
    def make_ai_move(self):
        if not self.ai_enabled or self.turn != self.ai_color:
            return

        all_moves = get_all_pseudo_legal_moves(self.board, self.turn)

        if not all_moves:
            self.status.set("No moves available")
            return

        capture_moves = []
        for move in all_moves:
            dr, dc = move.dst
            if self.board[dr][dc] is not None:
                capture_moves.append(move)

        if capture_moves:
            move = random.choice(capture_moves)
        else:
            move = random.choice(all_moves)

        self.make_move(move)

    def redraw(self): #Redrawing the board. This method updates all 64 buttons so the board looks correct.
        move_targets = {m.dst for m in self.legal_moves} #Collect all legal move targets
        #print("MOVE TARGETS:", move_targets)
        for r in range(8): #Loop through every square
            for c in range(8): #The program updates the color and text of every square.
                base = LIGHT if (r + c) % 2 == 0 else DARK #Determine the base square color: even sum → light square, odd sum → dark square
                bg = base

                if self.selected == (r, c): #Highlight the selected piece
                    bg = SELECT #If this square is the selected one, it becomes yellow.
                elif (r, c) in move_targets: # Highlight legal target squares
                    # Enemy piece on target. если клетка занята противником — подсветка "взятие"
                    if self.board[r][c] is not None and color_of(self.board[r][c]) != self.turn:
                        bg = CAPTURE
                    else: #Empty square.
                        bg = MOVE_DOT
                #Determine which symbol to display
                piece = self.board[r][c] #If the square contains a piece, the correct Unicode symbol is shown.
                text = UNICODE_PIECES.get(piece, "") if piece else "" #If not, the text is empty.

                cell= self.cells[r][c] #Update the button
                cell.configure(text=text, bg=bg,fg="black")#, activebackground=bg)

        self.root.update_idletasks() #Refresh pending GUI updates. This lets Tkinter process visual updates.


if __name__ == "__main__": #Program entry point
    root = tk.Tk() #Create the main window
    # Чуть приятнее выглядит на Retina
    try: #Optional scaling
        root.tk.call("tk", "scaling", 1.25)
    except Exception:
        pass
    app = ChessGUI(root) #Create the chess app
    root.mainloop() #Start the Tkinter event loop