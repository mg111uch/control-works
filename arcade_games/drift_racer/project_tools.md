## Project specific tool usage commands

- **Make Codebase_atlas:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output && conda run -n myenv python -m codebase_atlas.main --project-dir /home/manigupt/Hello/python/control/arcade_games/drift_racer/codebase --output-dir /home/manigupt/Hello/python/control/arcade_games/drift_racer`

- **Add markers:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && python add_markers.py --md_file /home/manigupt/Hello/python/control/arcade_games/drift_racer/code_atlas.md --project_path "/home/manigupt/Hello/python/control/arcade_games/drift_racer"`

- **Codebase size:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && conda run -n myenv python codebase_size.py --directory /home/manigupt/Hello/python/control/arcade_games/drift_racer/codebase --extensions .py .yaml --output-file /home/manigupt/Hello/python/control/arcade_games/drift_racer/code_atlas.md --start-marker "## Codebase size" --end-marker "## End Codebase size"`

- **Make directory:** 
`cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && conda run -n myenv python make_directree.py --reverse --base_path /home/manigupt/Hello/python/control/arcade_games/drift_racer --md_file /home/manigupt/Hello/python/control/arcade_games/drift_racer/code_atlas.md --start_marker '### FILE_MAP Tree' --end_marker '### End Tree'`

- **Copy Content:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && conda run -n myenv python copyContent.py --mode dump --md_file /home/manigupt/Hello/python/control/arcade_games/drift_racer/code_atlas.md --base_path /home/manigupt/Hello/python/control/arcade_games/drift_racer --output_file /home/manigupt/Hello/python/control/arcade_games/drift_racer/code_dump.txt --start_marker '### FILE_MAP Tree' --end_marker '### End Tree'`

- **Count Tokens in file:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && conda run -n myenv python token_count.py /home/manigupt/Hello/python/control/arcade_games/drift_racer/agent_harness.md`

- **Check if file exists:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && conda run -n myenv python path_file_exists.py /home/manigupt/Hello/python/control/arcade_games/drift_racer/code_atlas.md`

- **Record video** `cd /home/manigupt/Hello/python/ai_agent/agent_tools && conda run -n myenv python record_screen.py --x 0 --y 0 --width 600 --height 400 --duration 10 --fps 30 --output /home/manigupt/Hello/python/ai_agent/videos/drift_racer.avi`

- **Start training and abhort** `cd /home/manigupt/Hello/python/ai_agent/agent_tools && conda run -n myenv python run_process.py --script "/home/manigupt/Hello/python/control/arcade_games/drift_racer/codebase/training/train_nn.py --headless=False --num_envs 1" --duration 10`

- **Run and Record** `cd /home/manigupt/Hello/python/control/arcade_games/drift_racer && conda run -n myenv python run_and_record.py --duration 15 --y 65`

- **Ask Gemini** `cd /home/manigupt/Hello/python/ai_agent/agent_tools && export $(cat .env | xargs) && conda run -n myenv python reason_video.py --video_file /home/manigupt/Hello/python/ai_agent/videos/drift_racer.avi --response_file /home/manigupt/Hello/python/control/arcade_games/drift_racer/video_test.md`

- **Execute in order:** `cd /home/manigupt/Hello/python/ai_agent/atlas_output/tools && python run_cmds.py /home/manigupt/Hello/python/control/arcade_games/drift_racer/project_tools.md "Make Codebase_atlas" "Add markers" "Codebase size" "Make directory" "Count Tokens in file"`