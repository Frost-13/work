"""
gtp_connection.py
Module for playing games of Go using GoTextProtocol
Parts of this code were originally based on the gtp module
in the Deep-Go project by Isaac Henrion and Amos Storkey
at the University of Edinburgh.
"""
import traceback
from sys import stdin, stdout, stderr
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, PASS, \
                       MAXSIZE, coord_to_point, where1d
import numpy as np
import re
import simple_board
class GtpConnection():

    def __init__(self, go_engine, board, debug_mode = False):
        """
        Manage a GTP connection for a Go-playing engine
        Parameters
        ----------
        go_engine:
            a program that can reply to a set of GTP commandsbelow
        board:
            Represents the current board state.
        """
        self._debug_mode = debug_mode #True
        self.go_engine = go_engine
        self.board = board
        self.commands = {
            "protocol_version": self.protocol_version_cmd,
            "quit": self.quit_cmd,
            "name": self.name_cmd,
            "boardsize": self.boardsize_cmd,
            "showboard": self.showboard_cmd,
            "clear_board": self.clear_board_cmd,
            "komi": self.komi_cmd,
            "version": self.version_cmd,
            "known_command": self.known_command_cmd,
            "genmove": self.genmove_cmd,
            "list_commands": self.list_commands_cmd,
            "play": self.play_cmd,
            "legal_moves": self.legal_moves_cmd,
            "gogui-rules_game_id": self.gogui_rules_game_id_cmd,
            "gogui-rules_board_size": self.gogui_rules_board_size_cmd,
            "gogui-rules_legal_moves": self.gogui_rules_legal_moves_cmd,
            "gogui-rules_side_to_move": self.gogui_rules_side_to_move_cmd,
            "gogui-rules_board": self.gogui_rules_board_cmd,
            "gogui-rules_final_result": self.gogui_rules_final_result_cmd,
            "gogui-analyze_commands": self.gogui_analyze_cmd
        }

        # used for argument checking
        # values: (required number of arguments,
        #          error message on argnum failure)
        self.argmap = {
            "boardsize": (1, 'Usage: boardsize INT'),
            "komi": (1, 'Usage: komi FLOAT'),
            "known_command": (1, 'Usage: known_command CMD_NAME'),
            "genmove": (1, 'Usage: genmove {w,b}'),
            "play": (2, 'Usage: play {b,w} MOVE'),
            "legal_moves": (1, 'Usage: legal_moves {w,b}')
        }

    def write(self, data):
        stdout.write(data)

    def flush(self):
        stdout.flush()

    def start_connection(self):
        """
        Start a GTP connection.
        This function continuously monitors standard input for commands.
        """
        line = stdin.readline()
        while line:
            self.get_cmd(line)
            line = stdin.readline()

    def get_cmd(self, command):
        """
        Parse command string and execute it
        """
        if len(command.strip(' \r\t')) == 0:
            return
        if command[0] == '#':
            return
        # Strip leading numbers from regression tests
        if command[0].isdigit():
            command = re.sub("^\d+", "", command).lstrip()

        elements = command.split()
        if not elements:
            return
        command_name = elements[0]; args = elements[1:]
        if self.has_arg_error(command_name, len(args)):
            return
        if command_name in self.commands:
            try:
                self.commands[command_name](args)
            except Exception as e:
                self.debug_msg("Error executing command {}\n".format(str(e)))
                self.debug_msg("Stack Trace:\n{}\n".
                               format(traceback.format_exc()))
                raise e
        else:
            self.debug_msg("Unknown command: {}\n".format(command_name))
            self.error('Unknown command')
            stdout.flush()

    def has_arg_error(self, cmd, argnum):
        """
        Verify the number of arguments of cmd.
        argnum is the number of parsed arguments
        """
        if cmd in self.argmap and self.argmap[cmd][0] != argnum:
            self.error(self.argmap[cmd][1])
            return True
        return False

    def debug_msg(self, msg):
        """ Write msg to the debug stream """
        if self._debug_mode:  #if True: also gougi -verbose
            stderr.write(msg)
            stderr.flush()

    def error(self, error_msg):
        """ Send error msg to stdout """
        stdout.write('? {}\n\n'.format(error_msg))
        stdout.flush()

    def respond(self, response=''):
        """ Send response to stdout """
        stdout.write('= {}\n\n'.format(response))
        stdout.flush()

    def reset(self, size):
        """
        Reset the board to empty board of given size
        """
        self.board.reset(size)

    def board2d(self):
        return str(GoBoardUtil.get_twoD_board(self.board))

    def protocol_version_cmd(self, args):
        """ Return the GTP protocol version being used (always 2) """
        self.respond('2')

    def quit_cmd(self, args):
        """ Quit game and exit the GTP interface """
        self.respond()
        exit()

    def name_cmd(self, args):
        """ Return the name of the Go engine """
        self.respond(self.go_engine.name)

    def version_cmd(self, args):
        """ Return the version of the Go engine """
        self.respond(self.go_engine.version)

    def clear_board_cmd(self, args):
        """ clear the board """
        self.reset(self.board.size)
        self.respond()

    def boardsize_cmd(self, args):
        """
        Reset the game with new boardsize args[0]
        """
        self.reset(int(args[0]))
        self.respond()

    """
    ==========================================================================
    Assignment 1 - game-specific commands start here
    ==========================================================================
    """

    def gogui_analyze_cmd(self, args):
        """ We already implemented this function for Assignment 1 """
        self.respond("pstring/Legal Moves For ToPlay/gogui-rules_legal_moves\n"
                     "pstring/Side to Play/gogui-rules_side_to_move\n"
                     "pstring/Final Result/gogui-rules_final_result\n"
                     "pstring/Board Size/gogui-rules_board_size\n"
                     "pstring/Rules GameID/gogui-rules_game_id\n"
                     "pstring/Show Board/gogui-rules_board\n"
                     )

    def gogui_rules_game_id_cmd(self, args):
        """ We already implemented this function for Assignment 1 """
        self.respond("NoGo")

    def gogui_rules_board_size_cmd(self, args):
        """ We already implemented this function for Assignment 1 """
        self.respond(str(self.board.size))

    def gogui_rules_legal_moves_cmd(self, args):  #--------DONE----------------
        """ Implement this function for Assignment 1
            Produce a list of all legal moves for
            the current player, in alphabetic order. """
        colour = self.board.current_player
        if colour == 1:
            colour = 'b'
        else:
            colour = 'w'
        #print("#############:", colour)
        board_color = colour.lower()
        color = color_to_int(board_color)
        moves = GoBoardUtil.generate_legal_moves(self.board, self.board.current_player)
        gtp_moves = []
        for move in moves:
            # check if a PASS
            if move == "PASS":
                continue
            coords = point_to_coord(move, self.board.size)
            if self.board.board[move] != 0:
                continue
            board_copy = self.board.copy()
            opp_color = GoBoardUtil.opponent(color)
            board_copy.board[move] = color
            capture = False
            single_captures = []
            neighbors = board_copy._neighbors(move)
            No = False
            for nb in neighbors:
                if board_copy.board[nb] == opp_color:
                    single_capture = None
                    opp_block = board_copy._block_of(nb)
                    if not board_copy._has_liberty(opp_block):
                        captures = list(where1d(opp_block))
                        board_copy.board[captures] = 0
                        if len(captures) == 1:
                            single_capture = nb
                        if len(captures) >= 1:
                            No = True
                            break
                    if single_capture != None:
                        # use single captures to detect suicide
                        single_captures.append(single_capture)
            if not No:
                if single_captures != []:
                    continue
                block = board_copy._block_of(move)
                if not board_copy._has_liberty(block):  # undo suicide move
                    continue

                gtp_moves.append(format_point(coords))

        # put it all in a list
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(sorted_moves)


    def gogui_rules_side_to_move_cmd(self, args):
        """ We already implemented this function for Assignment 1 """
        color = "black" if self.board.current_player == BLACK else "white"
        self.respond(color)

    def gogui_rules_board_cmd(self, args):
        """ We already implemented this function for Assignment 1 """
        size = self.board.size
        str = ''
        for row in range(size-1, -1, -1):
            start = self.board.row_start(row + 1)
            for i in range(size):
                #str += '.'
                point = self.board.board[start + i]
                if point == BLACK:
                    str += 'X'
                elif point == WHITE:
                    str += 'O'
                elif point == EMPTY:
                    str += '.'
                else:
                    assert False
            str += '\n'
        self.respond(str)

    def gogui_rules_final_result_cmd(self, args): #----------Done----------------------
        """ Implement this function for Assignment 1
            This command checks if the game is over
            and outputs one of the following game results: """

        result = "unknown"
        colour = self.board.current_player
        if colour == 1:
            colour = 'b'
        else:
            colour = 'w'
        #print("#############:", colour)
        board_color = colour.lower()
        color = color_to_int(board_color)
        moves = GoBoardUtil.generate_legal_moves(self.board, self.board.current_player)
        gtp_moves = []
        for move in moves:
            # check if a PASS
            if move == "PASS":
                continue
            coords = point_to_coord(move, self.board.size)
            if self.board.board[move] != 0:
                continue
            board_copy = self.board.copy()
            opp_color = GoBoardUtil.opponent(color)
            board_copy.board[move] = color
            capture = False
            single_captures = []
            neighbors = board_copy._neighbors(move)
            No = False
            for nb in neighbors:
                if board_copy.board[nb] == opp_color:
                    single_capture = None
                    opp_block = board_copy._block_of(nb)
                    if not board_copy._has_liberty(opp_block):
                        captures = list(where1d(opp_block))
                        board_copy.board[captures] = 0
                        if len(captures) == 1:
                            single_capture = nb
                        if len(captures) >= 1:
                            No = True
                            break
                    if single_capture != None:
                        # use single captures to detect suicide
                        single_captures.append(single_capture)
            if not No:
                if single_captures != []:
                    continue
                block = board_copy._block_of(move)
                if not board_copy._has_liberty(block):  # undo suicide move
                    continue

                gtp_moves.append(format_point(coords))

        if not gtp_moves:
            result = GoBoardUtil.opponent(color)
        if result == 1:
            result = 'black'
        elif result == 2:
            result = 'white'

        self.respond(result)

    def play_cmd(self, args):                   #-----------Done--------------------
        """ Modify this function for Assignment 1
        play a move args[1] for given color args[0] in {'b','w'}
        Check in following order:
        wrong color
        wrong coordinate
        occupied
        capture
        suicide
        """
        try:
            board_color = args[0].lower()
            board_move = args[1]
            color = color_to_int(board_color)

            #wrong color
            self.board.current_player
            if self.board.current_player != color:
                #figure out a way to implement this elegantly
                self.respond("illegal move: \"{}\" wrong color".format(" ".join(args)))
                return

            #Check if move is "PASS"
            if board_move.lower() == "pass":
                #Pass is not allowd so generate Illegal move message
                self.respond("illegal move: \"{}\" wrong coordinate".format(" ".join(args)))
                return
            else:
                coord = move_to_coord(board_move, self.board.size)
                if coord:
                    move = coord_to_point(coord[0], coord[1], self.board.size)

            # check for spot occupation, ex. empty
            if self.board.board[move] != 0:
                self.respond("illegal move: \"{}\" occupied".format(" ".join(args)))
                return

            board_copy = self.board.copy()

            #test for captures, then suicide
            # General case: deal with captures, suicide, and next ko point
            opp_color = GoBoardUtil.opponent(color)
            board_copy.board[move] = color
            capture = False
            single_captures = []
            neighbors = board_copy._neighbors(move)
            for nb in neighbors:
                if board_copy.board[nb] == opp_color:
                    single_capture = None
                    opp_block = board_copy._block_of(nb)
                    if not board_copy._has_liberty(opp_block):
                        captures = list(where1d(opp_block))
                        board_copy.board[captures] = 0
                        if len(captures) == 1:
                            single_capture = nb
                        if len(captures) >= 1:
                            self.respond("illegal move: \"{}\" capture".format(" ".join(args)))
                            return
                    if single_capture != None:
                        # use single captures to detect suicide
                        single_captures.append(single_capture)
            if single_captures != []:
                self.respond("illegal move: \"{}\" capture".format(" ".join(args)))
                return


            block = board_copy._block_of(move)
            if not board_copy._has_liberty(block):  # undo suicide move
                self.respond("illegal move: \"{}\" suicide".format(" ".join(args)))
                return


            # try to playe the move
            if not self.board.play_move(move, color):
                #false, probably the wrong move
                self.respond("Illegal move: {}".format(board_move))
                return

            self.respond()


        except Exception as e:
            # return an error message
            self.respond('Error: {}'.format(str(e)))
            self.respond("illegal Move: \"{}\" wrong coordinate ex".format(" ".join(args)))

    def genmove_cmd(self, args):#------------Done---------------------
        """ Modify this function for Assignment 1 """
        """ generate a move for color args[0] in {'b','w'} """
        board_color = args[0].lower()
        color = color_to_int(board_color)
        move = self.go_engine.get_move(self.board, color)
        move_coord = point_to_coord(move, self.board.size)
        move_as_string = format_point(move_coord)

        # our code
        colour = 1
        if board_color == 'w':
            colour == 2
        elif board_color == 'b':
            colour == 1
        moves = GoBoardUtil.generate_legal_moves(self.board, colour)
        gtp_moves = []
        for Move in moves:
            # check if a PASS
            if Move == "PASS":
                continue
            coords = point_to_coord(Move, self.board.size)
            if self.board.board[Move] != 0:
                continue
            board_copy = self.board.copy()
            opp_color = GoBoardUtil.opponent(color)
            board_copy.board[Move] = color
            capture = False
            single_captures = []
            neighbors = board_copy._neighbors(move)
            No = False
            for nb in neighbors:
                if board_copy.board[nb] == opp_color:
                    single_capture = None
                    opp_block = board_copy._block_of(nb)
                    if not board_copy._has_liberty(opp_block):
                        captures = list(where1d(opp_block))
                        board_copy.board[captures] = 0
                        if len(captures) == 1:
                            single_capture = nb
                        if len(captures) >= 1:
                            No = True
                            break
                    if single_capture != None:
                        # use single captures to detect suicide
                        single_captures.append(single_capture)
            if not No:
                if single_captures != []:
                    continue
                block = board_copy._block_of(Move)
                if not board_copy._has_liberty(block):  # undo suicide move
                    continue

                gtp_moves.append(format_point(coords))

        print(*gtp_moves)
        if not gtp_moves:
            self.respond("resign")
        else:
            if format_point(move_coord) in gtp_moves:
                self.board.play_move(move, color)
                self.respond(move_as_string)
            else:
                self.respond("Illegal move: {}".format(move_as_string))



    """
    ==========================================================================
    Assignment 1 - game-specific commands end here
    ==========================================================================
    """

    def showboard_cmd(self, args):
        self.respond('\n' + self.board2d())

    def komi_cmd(self, args):
        """
        Set the engine's komi to args[0]
        """
        self.go_engine.komi = float(args[0])
        self.respond()

    def known_command_cmd(self, args):
        """
        Check if command args[0] is known to the GTP interface
        """
        if args[0] in self.commands:
            self.respond("true")
        else:
            self.respond("false")

    def list_commands_cmd(self, args):
        """ list all supported GTP commands """
        self.respond(' '.join(list(self.commands.keys())))

    """ Assignment 1: ignore this command, implement
        gogui_rules_legal_moves_cmd  above instead """
    def legal_moves_cmd(self, args):
        """
        List legal moves for color args[0] in {'b','w'}
        """
        board_color = args[0].lower()
        color = color_to_int(board_color)
        moves = GoBoardUtil.generate_legal_moves(self.board, color)
        gtp_moves = []
        for move in moves:
            coords = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(sorted_moves)


def point_to_coord(point, boardsize):
    """
    Transform point given as board array index
    to (row, col) coordinate representation.
    Special case: PASS is not transformed
    """
    if point == PASS:
        return PASS
    else:
        NS = boardsize + 1
        return divmod(point, NS)

def format_point(move):
    """
    Return move coordinates as a string such as 'A1', or 'PASS'.
    """
    column_letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    if move == PASS:
        return "PASS"
    row, col = move
    if not 0 <= row < MAXSIZE or not 0 <= col < MAXSIZE:
        raise ValueError
    return column_letters[col - 1]+ str(row)

def move_to_coord(point_str, board_size):
    """
    Convert a string point_str representing a point, as specified by GTP,
    to a pair of coordinates (row, col) in range 1 .. board_size.
    Raises ValueError if point_str is invalid
    """
    if not 2 <= board_size <= MAXSIZE:
        raise ValueError("board_size out of range")
    s = point_str.lower()
    if s == "pass":
        return PASS
    try:
        col_c = s[0]
        if (not "a" <= col_c <= "z") or col_c == "i":
            raise ValueError
        col = ord(col_c) - ord("a")
        if col_c < "i":
            col += 1
        row = int(s[1:])
        if row < 1:
            raise ValueError
    except (IndexError, ValueError):
        raise ValueError("invalid point: '{}'".format(s))
    if not (col <= board_size and row <= board_size):
        raise ValueError("point off board: '{}'".format(s))
    return row, col

def color_to_int(c):
    """convert character to the appropriate integer code"""
    color_to_int = {"b": BLACK , "w": WHITE, "e": EMPTY,
                    "BORDER": BORDER}
    return color_to_int[c]
