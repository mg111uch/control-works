## Project specific tool usage commands

- **Make Codebase_atlas:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output && conda run -n myenv python -m codebase_atlas.main --project-dir /home/manigupt/Hello/python/control/arcade_games/flappy_bird/codebase --output-dir /home/manigupt/Hello/python/control/arcade_games/flappy_bird`

- **Add markers:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && python add_markers.py --md_file /home/manigupt/Hello/python/control/arcade_games/flappy_bird/code_atlas.md --project_path "/home/manigupt/Hello/python/control/arcade_games/flappy_bird"`

- **Codebase size:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && conda run -n myenv python codebase_size.py --directory /home/manigupt/Hello/python/control/arcade_games/flappy_bird/codebase --extensions .py .yaml --output-file /home/manigupt/Hello/python/control/arcade_games/flappy_bird/code_atlas.md --start-marker "## Codebase size" --end-marker "## End Codebase size"`

- **Make directory:** 
`cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && conda run -n myenv python make_directree.py --reverse --base_path /home/manigupt/Hello/python/control/arcade_games/flappy_bird --md_file /home/manigupt/Hello/python/control/arcade_games/flappy_bird/code_atlas.md --start_marker '### FILE_MAP Tree' --end_marker '### End Tree'`

- **Copy Content:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && conda run -n myenv python copyContent.py --mode dump --md_file /home/manigupt/Hello/python/control/arcade_games/flappy_bird/code_atlas.md --base_path /home/manigupt/Hello/python/control/arcade_games/flappy_bird --output_file /home/manigupt/Hello/python/control/arcade_games/flappy_bird/code_dump.txt --start_marker '### FILE_MAP Tree' --end_marker '### End Tree'`

- **Count Tokens in file:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && conda run -n myenv python token_count.py /home/manigupt/Hello/python/control/arcade_games/flappy_bird/agent_harness.md`

- **Check if file exists:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && conda run -n myenv python path_file_exists.py /home/manigupt/Hello/python/control/arcade_games/flappy_bird/code_atlas.md`

- **Execute in order:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && python run_cmds.py /home/manigupt/Hello/python/control/arcade_games/flappy_bird/project_tools.md "Make Codebase_atlas" "Add markers" "Codebase size" "Make directory" "Count Tokens in file"`