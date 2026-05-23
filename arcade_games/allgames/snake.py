#!/usr/bin/env python3
"""Minimal file based snake game.
Asks the gemini agent for a plan to reach the food. Auto-runs until the snake eats the food.
The game uses AI to control the snake automatically based on the gemini agent's plan.

Script loop:
Write (game state + question) → run agent → get complete plan
Execute plan tick by tick (update game state in file, don't call agent)
Food eaten → spawn new food → go to step 1 (call agent again)
"""

'''
Prompt: Modify this script so that script follows this loop. 
1. At the start the initial game state is written to `/home/manigupt/Hello/python/ai_agent/utils/ask_response.md` file under the `## Game State` header along with the question under '## Reasoning Question' which must be asked to the gemini agent so that snake reaches the food. 
2. Then this script runs the command `cd /home/manigupt/Hello/python/ai_agent/agent_tools && conda run -n myenv python ask_gemini.py --response_file /home/manigupt/Hello/python/ai_agent/utils/ask_response.md` which writes the plan.  
3. Then this script should read the answer written by agent under `## Reasoning Answer` header in response file without erasing the answer.
4. Then this game should autorun the answer plan tick by tick which changes only the game state in ask_response.md file until it snake eats the food using that plan and next food appears. 
5. Goes to 1. Then again game state along with reasoning question is written in ask_response.md which must be send to agent for the plan to reaching next food. 
Do not change this prompt.
'''

import random
import time
import os
import subprocess
import re
import sys
import tty
import termios
import select

RESPONSE_FILE = "/home/manigupt/Hello/python/ai_agent/utils/ask_response.md"

# Manual mode flag - set to True to control snake with arrow keys
MANUAL_MODE = False

# Game tick constants (seconds between ticks)
MANUAL_TICK = 0.5  # Faster for manual mode
AUTO_TICK = 5      # Slower for AI mode

QUESTION = """Based on the game state provided below, analyze and provide a plan (sequence of moves) for the snake to reach and eat the food (X). 
Respond with direction choices only, one per line, using only: UP, DOWN, LEFT, or RIGHT. No other text.
Consider avoiding walls and self-collision while trying to eat the food (X)."""

def get_game_state_str(snake, food_y, food_x, score, game_height, game_width, direction):
    """Generate a string describing the current game state."""
    direction_names = {(-1, 0): "UP", (1, 0): "DOWN", (0, -1): "LEFT", (0, 1): "RIGHT"}
    dir_name = direction_names.get(tuple(direction), "RIGHT")
    
    # Create a simple ASCII representation of the game board with borders
    board = []
    for y in range(game_height):
        row = ""
        for x in range(game_width):
            # Border
            if y == 0 or y == game_height - 1 or x == 0 or x == game_width - 1:
                row += "|"
            elif [y, x] == [food_y, food_x]:
                row += "X"
            elif [y, x] == snake[0]:
                row += "O"
            elif [y, x] in snake:
                row += "#"
            else:
                row += " "
        board.append(row)
    
    board_str = "\n".join(board)
    
    state = f"""Game Board ({game_height}x{game_width}):
{board_str}

Snake head: {snake[0]} (direction: {dir_name})
Snake length: {len(snake)}
Food position: ({food_y}, {food_x})
Current score: {score}
"""
    return state

def write_to_file(game_state_str, question):
    """Write game state and question to the response file."""
    content = f"""## Reasoning Question

{question}

## Game State

{game_state_str}

## Reasoning Answer
"""
    
    with open(RESPONSE_FILE, "w") as f:
        f.write(content)

def update_game_state_only(game_state_str, question):
    """Update only the game state in the response file (keep question and answer sections)."""
    try:
        with open(RESPONSE_FILE, "r") as f:
            content = f.read()
        
        # Rebuild with updated game state between Reasoning Question and Reasoning Answer
        new_content = f"## Reasoning Question\n\n{question}\n\n## Game State\n\n{game_state_str}\n\n## Reasoning Answer\n"
        
        # Try to preserve existing answer if any
        if "## Reasoning Answer" in content:
            answer_match = content.split("## Reasoning Answer")
            if len(answer_match) > 1 and answer_match[1].strip():
                new_content += answer_match[1].strip()
        
        with open(RESPONSE_FILE, "w") as f:
            f.write(new_content)
    except Exception as e:
        print(f"Error updating game state: {e}")

def run_gemini_agent():
    """Run the gemini agent to get the plan."""
    cmd = "cd /home/manigupt/Hello/python/ai_agent/agent_tools && conda run -n myenv python ask_gemini.py --response_file /home/manigupt/Hello/python/ai_agent/utils/ask_response.md"
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    return result.returncode == 0

def read_answer_from_file():
    """Read the answer from the response file."""
    try:
        with open(RESPONSE_FILE, "r") as f:
            content = f.read()
        
        # Find the ## Reasoning Answer section
        if "## Reasoning Answer" in content:
            answer_section = content.split("## Reasoning Answer")[1].strip()
            return answer_section
        return None
    except Exception as e:
        print(f"Error reading response file: {e}")
        return None

def parse_directions(answer):
    """Parse all directions from the answer."""
    directions = []
    valid_dirs = {"UP": [-1, 0], "DOWN": [1, 0], "LEFT": [0, -1], "RIGHT": [0, 1]}
    
    for line in answer.strip().split("\n"):
        line = line.strip().upper()
        if line in valid_dirs:
            directions.append(valid_dirs[line])
    
    return directions

def get_key_input(timeout=0.1):
    """Get keyboard input without blocking. Returns direction or None."""
    try:
        # Check if there's input available
        if select.select([sys.stdin], [], [], timeout)[0]:
            char = sys.stdin.read(1)
            if char == '\x1b':  # ESC sequence start
                next_char = sys.stdin.read(1)
                if next_char == '[':
                    direction_char = sys.stdin.read(1)
                    if direction_char == 'A':  # UP
                        return [-1, 0]
                    elif direction_char == 'B':  # DOWN
                        return [1, 0]
                    elif direction_char == 'C':  # RIGHT
                        return [0, 1]
                    elif direction_char == 'D':  # LEFT
                        return [0, -1]
            elif char.upper() == 'W':  # Alternative WASD
                return [-1, 0]
            elif char.upper() == 'S':
                return [1, 0]
            elif char.upper() == 'A':
                return [0, -1]
            elif char.upper() == 'D':
                return [0, 1]
    except:
        pass
    return None

def run_manual_mode(game_height, game_width, snake, direction, score, food_y, food_x):
    """Run the game in manual mode with keyboard controls."""
    # Setup terminal for raw input
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    
    try:
        while True:
            # Print game state
            os.system('clear' if os.name == 'posix' else 'cls')
            print(get_game_state_str(snake, food_y, food_x, score, game_height, game_width, direction))
            print("Use arrow keys or WASD to move. Press Ctrl+C to quit.")
            
            # Get input with timeout
            new_direction = get_key_input(timeout=MANUAL_TICK)
            
            if new_direction:
                # Prevent 180-degree turns
                if (new_direction[0] != -direction[0] or new_direction[1] != -direction[1]):
                    direction = new_direction
            
            # Move snake
            new_head = [snake[0][0] + direction[0], snake[0][1] + direction[1]]
            
            # Check collision with walls
            if (new_head[0] < 1 or new_head[0] > game_height - 2 or
                new_head[1] < 1 or new_head[1] > game_width - 2):
                print("Game Over! Snake hit wall.")
                break
            
            # Check collision with self
            if new_head in snake:
                print("Game Over! Snake hit itself.")
                break
            
            snake.insert(0, new_head)
            
            # Check food
            if new_head == [food_y, food_x]:
                score += 1
                print(f"Score: {score}")
                
                # Spawn new food
                while True:
                    food_y = random.randint(1, game_height - 2)
                    food_x = random.randint(1, game_width - 2)
                    if [food_y, food_x] not in snake:
                        break
            else:
                snake.pop()
                
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
    return score

def main():
    # Setup - don't display in terminal, just update file
    # Flush output immediately
    sys.stdout.flush()
    
    # Game area (10x14 playable, 12x16 with borders)
    game_height = 12
    game_width = 16
    
    # Snake initial position (center) - head and one body segment
    snake = [[game_height // 2, game_width // 2], [game_height // 2, game_width // 2 - 1]]
    direction = [0, 1]  # Moving right
    score = 0
    
    # Run in manual mode if flag is set
    if MANUAL_MODE:
        # Food position (ensure not on snake)
        while True:
            food_y = random.randint(1, game_height - 2)
            food_x = random.randint(1, game_width - 2)
            if [food_y, food_x] not in snake:
                break
        final_score = run_manual_mode(game_height, game_width, snake, direction, score, food_y, food_x)
        print(f"Final Score: {final_score}")
        return
    
    # Use AUTO_TICK for AI mode
    game_tick = AUTO_TICK
    
    # Main game loop with AI agent
    while True:
        
        # Food position (ensure not on snake)
        while True:
            food_y = random.randint(1, game_height - 2)
            food_x = random.randint(1, game_width - 2)
            if [food_y, food_x] not in snake:
                break
        
        # Step 1: Write game state and question to file
        game_state = get_game_state_str(snake, food_y, food_x, score, game_height, game_width, direction)
        write_to_file(game_state, QUESTION)
        
        # Step 2: Run gemini agent (only once per food)
        if not run_gemini_agent():
            print("Failed to run gemini agent")
            break
        
        # Step 3: Read answer - this contains the full plan
        answer = read_answer_from_file()
        if not answer:
            print("No answer from agent")
            break
        
        # Step 4: Parse all directions from the plan
        plan = parse_directions(answer)
        if not plan:
            print("No valid directions in plan")
            break
        
        print(f"Got plan with {len(plan)} moves")
        
        # Step 5: Execute the plan tick by tick (update game state in file, but don't call agent)
        for move_idx, new_direction in enumerate(plan):
            # Move snake
            direction = new_direction
            new_head = [snake[0][0] + direction[0], snake[0][1] + direction[1]]
            
            # Check collision with walls
            if (new_head[0] < 1 or new_head[0] > game_height - 2 or
                new_head[1] < 1 or new_head[1] > game_width - 2):
                print("Snake hit wall - plan failed")
                break
            
            # Check collision with self
            if new_head in snake:
                print("Snake hit itself - plan failed")
                break
            
            snake.insert(0, new_head)
            
            # Check food
            if new_head == [food_y, food_x]:
                score += 1
                print(f"Score: {score}")
                
                # Spawn new food at random position (not on snake)
                while True:
                    food_y = random.randint(1, game_height - 2)
                    food_x = random.randint(1, game_width - 2)
                    if [food_y, food_x] not in snake:
                        break
                
                # Update game state in file to reflect new food position
                game_state = get_game_state_str(snake, food_y, food_x, score, game_height, game_width, direction)
                update_game_state_only(game_state, QUESTION)
                
                # Food eaten - ask agent again for plan to reach new food
                break
            
            snake.pop()
            
            # Update game state in file (but don't call agent)
            game_state = get_game_state_str(snake, food_y, food_x, score, game_height, game_width, direction)
            update_game_state_only(game_state, QUESTION)
            
            time.sleep(AUTO_TICK)
        
        # Loop back - new food will be spawned and agent will be called again
        continue

if __name__ == "__main__":
    main()
