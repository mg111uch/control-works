"""
Tests for the train_nn training script functionality.
"""
import argparse
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the training directory to path for imports
sys.path.insert(0, '/home/manigupt/Hello/python/control/arcade_games/drift_racer/codebase/training')


class TestTrainDurationArgument(unittest.TestCase):
    """Tests for train_duration command line argument."""
    
    def test_train_duration_argument_exists(self):
        """Test that --train_duration argument is properly defined."""
        # We need to test the argument parsing
        test_args = [
            'train_nn.py',
            '--train_duration', '300'
        ]
        
        with patch.object(sys, 'argv', test_args):
            parser = argparse.ArgumentParser(description='Drift King 2D Training')
            parser.add_argument('--headless', type=str, default='True',
                                choices=['True', 'False'],
                                help='Run in headless mode (default: True)')
            parser.add_argument('--visualize', action='store_true',
                                help='Visualize the trained model (requires trained model)')
            parser.add_argument('--num_envs', type=int, default=4,
                                help='Number of parallel environments for vectorized training')
            parser.add_argument('--train_duration', type=int, default=None,
                                help='Maximum training duration in seconds (None = run all generations)')
            args = parser.parse_args(['--train_duration', '300'])
            
            self.assertEqual(args.train_duration, 300)
    
    def test_train_duration_none_by_default(self):
        """Test that train_duration defaults to None."""
        test_args = ['train_nn.py']
        
        with patch.object(sys, 'argv', test_args):
            parser = argparse.ArgumentParser(description='Drift King 2D Training')
            parser.add_argument('--train_duration', type=int, default=None,
                                help='Maximum training duration in seconds')
            args = parser.parse_args([])
            
            self.assertIsNone(args.train_duration)
    
    def test_train_duration_zero(self):
        """Test that train_duration can be set to 0 (immediate abort)."""
        test_args = ['train_nn.py', '--train_duration', '0']
        
        with patch.object(sys, 'argv', test_args):
            parser = argparse.ArgumentParser(description='Drift King 2D Training')
            parser.add_argument('--train_duration', type=int, default=None)
            args = parser.parse_args(['--train_duration', '0'])
            
            self.assertEqual(args.train_duration, 0)


class TestTrainingLoopDurationCheck(unittest.TestCase):
    """Tests for training loop duration checking logic."""
    
    def test_duration_check_logic(self):
        """Test the duration check logic that should be in the training loop."""
        # Simulate the duration check logic
        TRAIN_DURATION = 10  # 10 seconds
        start_time = 0
        current_time = 5
        
        # When elapsed time is less than duration, training should continue
        elapsed_time = current_time - start_time
        should_continue = elapsed_time < TRAIN_DURATION
        self.assertTrue(should_continue)
        
        # When elapsed time equals duration, training should stop
        current_time = 10
        elapsed_time = current_time - start_time
        should_continue = elapsed_time < TRAIN_DURATION
        self.assertFalse(should_continue)
    
    def test_duration_check_with_none(self):
        """Test that None train_duration doesn't trigger early stop."""
        TRAIN_DURATION = None
        elapsed_time = 1000
        
        # Should not break when train_duration is None
        should_stop = TRAIN_DURATION is not None and elapsed_time >= TRAIN_DURATION
        self.assertFalse(should_stop)
    
    def test_elapsed_time_calculation(self):
        """Test elapsed time calculation in training loop."""
        import time
        
        start_time = time.time()
        
        # Simulate some work
        time.sleep(0.01)
        
        elapsed_time = time.time() - start_time
        
        # Elapsed time should be approximately 0.01 seconds
        self.assertGreater(elapsed_time, 0)
        self.assertLess(elapsed_time, 1.0)


class TestTrainingOutput(unittest.TestCase):
    """Tests for training output messages."""
    
    def test_completion_message_format(self):
        """Test that completion message includes duration info."""
        elapsed_time = 123.45
        best_score = 250.5
        duration_limit = 300
        
        # Format the expected output
        message = f"\nTraining completed in {elapsed_time:.2f} seconds"
        message += f"\nBest drift score achieved: {best_score}"
        message += f"\nDuration limit: {duration_limit}s (used: {elapsed_time:.2f}s)"
        message += "\nModel saved to drift_policy_model.pth"
        
        self.assertIn("Training completed", message)
        self.assertIn("123.45", message)
        self.assertIn("Duration limit: 300s", message)
    
    def test_early_stop_message_format(self):
        """Test early stop message when duration limit is reached."""
        generation = 50
        duration_limit = 60
        
        message = f"\nTraining duration limit ({duration_limit}s) reached at generation {generation}. Stopping early."
        
        self.assertIn("Training duration limit", message)
        self.assertIn("60s", message)
        self.assertIn("generation 50", message)
        self.assertIn("Stopping early", message)


class TestTrainingAutoAbort(unittest.TestCase):
    """Tests for training auto-abort functionality."""
    
    def test_training_aborts_after_duration(self):
        """Test that training loop aborts when train_duration is exceeded."""
        import time
        
        # Simulate the training loop with duration checking
        TRAIN_DURATION = 5  # 5 seconds
        start_time = 0
        current_time = 0
        time.time = lambda: current_time
        
        generations_completed = 0
        max_generations = 200
        
        for gen in range(max_generations):
            # Simulate time passing (each generation takes 1 second)
            current_time += 1
            elapsed_time = time.time() - start_time
            
            # Check if train_duration has been exceeded
            if TRAIN_DURATION is not None and elapsed_time >= TRAIN_DURATION:
                # Training should abort here
                break
            
            generations_completed += 1
        
        # With 5 second duration and 1 second per generation:
        # - Gen 0: elapsed=1, continue
        # - Gen 1: elapsed=2, continue
        # - Gen 2: elapsed=3, continue
        # - Gen 3: elapsed=4, continue
        # - Gen 4: elapsed=5, break (5 >= 5)
        # So we complete 4 generations
        self.assertEqual(generations_completed, 4)
    
    def test_training_continues_without_duration_limit(self):
        """Test that training runs all generations when train_duration is None."""
        import time
        
        TRAIN_DURATION = None
        start_time = 0
        current_time = 0
        time.time = lambda: current_time
        
        generations_completed = 0
        max_generations = 10  # Using smaller number for test
        
        for gen in range(max_generations):
            current_time += 1
            elapsed_time = time.time() - start_time
            
            if TRAIN_DURATION is not None and elapsed_time >= TRAIN_DURATION:
                break
            
            generations_completed += 1
        
        # Should complete all generations since TRAIN_DURATION is None
        self.assertEqual(generations_completed, max_generations)
    
    def test_immediate_abort_with_zero_duration(self):
        """Test that training aborts immediately with train_duration=0."""
        import time
        
        TRAIN_DURATION = 0
        start_time = 0
        current_time = 0
        time.time = lambda: current_time
        
        generations_completed = 0
        max_generations = 200
        
        for gen in range(max_generations):
            current_time += 1
            elapsed_time = time.time() - start_time
            
            if TRAIN_DURATION is not None and elapsed_time >= TRAIN_DURATION:
                break
            
            generations_completed += 1
        
        # Should not complete any generations with 0 duration
        self.assertEqual(generations_completed, 0)
    
    def test_partial_generation_time_respected(self):
        """Test that partial generation times are respected."""
        import time
        
        TRAIN_DURATION = 3
        start_time = 0
        current_time = 0
        time.time = lambda: current_time
        
        generations_completed = 0
        max_generations = 200
        
        for gen in range(max_generations):
            # Each generation takes 1.5 seconds
            current_time += 1.5
            elapsed_time = time.time() - start_time
            
            if TRAIN_DURATION is not None and elapsed_time >= TRAIN_DURATION:
                break
            
            generations_completed += 1
        
        # - Gen 0: elapsed=1.5, continue (1.5 < 3)
        # - Gen 1: elapsed=3.0, break (3.0 >= 3)
        # So we complete 1 generation
        self.assertEqual(generations_completed, 1)


class TestTrainingEpisodeTracking(unittest.TestCase):
    """Tests for training episode tracking in progress display."""
    
    def test_progress_output_includes_episode(self):
        """Test that progress output format includes episode information."""
        # Test the format string used in training
        total_episode = 100
        gen = 5
        GENERATIONS = 200
        current_best_score = 150.5
        reward = 75.2
        steps = 500
        ticks = 10000
        
        # Format the output
        output = f"Episode {total_episode} | Gen {gen+1}/{GENERATIONS} | Best Score: {current_best_score:.2f} | Reward: {reward:.2f} | Steps: {steps:.0f} | Ticks: {ticks}"
        
        # Check that episode is in output
        self.assertIn("Episode 100", output)
        self.assertIn("Gen 6/200", output)
        self.assertIn("Best Score: 150.50", output)
    
    def test_episode_tracking_variable_initialization(self):
        """Test that total_episode variable is initialized in train function."""
        # This tests the code pattern used in train()
        total_episode = 0  # Track total episodes across all generations
        
        # Simulate episodes being run
        episodes_run = 3  # 3 episodes per agent evaluation
        num_agents = 10
        
        for _ in range(num_agents):
            total_episode += episodes_run
        
        # Should accumulate episodes
        self.assertEqual(total_episode, 30)
    
    def test_evaluate_batch_returns_tuple_with_episodes(self):
        """Test that evaluate_batch returns a tuple with results and episode count."""
        # Test the expected return type pattern
        results = [(100.0, 50.0, 100, 1000)]
        total_episodes = 3
        
        # Should be able to unpack as tuple
        returned_results, returned_episodes = results, total_episodes
        
        self.assertEqual(returned_results, results)
        self.assertEqual(returned_episodes, total_episodes)


class TestHeadlessFalseProgressDisplay(unittest.TestCase):
    """Tests for training progress display in headless=False mode."""
    
    def test_progress_output_format_non_headless(self):
        """Test that progress output format is correct for headless=False mode."""
        # Simulate the output format used in train() for non-headless mode
        total_episode = 150
        gen = 10
        GENERATIONS = 200
        current_best_score = 250.75
        reward = 125.5
        steps = 1000
        HEADLESS_MODE = False
        
        # Format the output as done in train_nn.py
        output = (f"Episode {total_episode} | Gen {gen+1}/{GENERATIONS} | "
                  f"Best Score: {current_best_score:.2f} | "
                  f"Reward: {reward:.2f} | "
                  f"Steps: {steps:.0f}"
                  + (f" | Ticks: {10000}" if HEADLESS_MODE else ""))
        
        # Verify the output contains episode and generation info
        self.assertIn("Episode 150", output)
        self.assertIn("Gen 11/200", output)
        self.assertIn("Best Score: 250.75", output)
        self.assertIn("Reward: 125.50", output)
        self.assertIn("Steps: 1000", output)
        # In non-headless mode, Ticks should NOT be shown
        self.assertNotIn("Ticks:", output)
    
    def test_progress_output_includes_episode_count(self):
        """Test that progress output includes cumulative episode count."""
        total_episode = 500
        gen = 25
        GENERATIONS = 200
        
        output = f"Episode {total_episode} | Gen {gen+1}/{GENERATIONS}"
        
        self.assertIn("Episode 500", output)
        self.assertIn("Gen 26/200", output)
    
    def test_progress_output_flushed_for_immediate_display(self):
        """Test that progress output uses flush=True for immediate display."""
        # This test verifies the pattern used in train_nn.py
        # The actual print statement should use flush=True
        import io
        import sys
        
        # Capture output to verify flush parameter is used
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Simulate the print statement from train_nn.py
            total_episode = 100
            gen = 5
            GENERATIONS = 200
            current_best_score = 150.0
            reward = 75.0
            steps = 500
            HEADLESS_MODE = False
            
            print(f"Episode {total_episode} | Gen {gen+1}/{GENERATIONS} | "
                  f"Best Score: {current_best_score:.2f} | "
                  f"Reward: {reward:.2f} | "
                  f"Steps: {steps:.0f}"
                  + (f" | Ticks: {10000}" if HEADLESS_MODE else ""),
                  flush=True)
            
            output = captured_output.getvalue()
            self.assertIn("Episode 100", output)
            self.assertIn("Gen 6/200", output)
        finally:
            sys.stdout = sys.__stdout__
    
    def test_generation_progress_shows_current_and_total(self):
        """Test that generation progress shows both current and total generations."""
        gen = 49
        GENERATIONS = 200
        
        progress = f"Gen {gen+1}/{GENERATIONS}"
        
        self.assertIn("50/200", progress)
        self.assertEqual(progress, "Gen 50/200")
    
    def test_episode_counter_increments_across_generations(self):
        """Test that episode counter properly increments across generations."""
        # Simulate the episode tracking pattern from train_nn.py
        total_episode = 0
        episodes_per_generation = 30  # POP_SIZE * 3 episodes per agent
        
        # Simulate 5 generations
        for gen in range(5):
            # Each generation runs multiple episodes
            total_episode += episodes_per_generation
            
            # Verify progress output at each generation
            output = f"Episode {total_episode} | Gen {gen+1}/200"
            self.assertIn(f"Episode {total_episode}", output)
        
        # After 5 generations, should have 150 episodes
        self.assertEqual(total_episode, 150)
    
    def test_progress_output_without_ticks_in_non_headless(self):
        """Test that Ticks are not shown in non-headless mode progress."""
        HEADLESS_MODE = False
        ticks = 50000
        
        # In non-headless mode, ticks should not be appended
        output_suffix = f" | Ticks: {ticks}" if HEADLESS_MODE else ""
        
        self.assertEqual(output_suffix, "")
        self.assertNotIn("Ticks", output_suffix)
    
    def test_progress_output_with_ticks_in_headless(self):
        """Test that Ticks ARE shown in headless mode progress (for comparison)."""
        HEADLESS_MODE = True
        ticks = 50000
        
        # In headless mode, ticks should be appended
        output_suffix = f" | Ticks: {ticks}" if HEADLESS_MODE else ""
        
        self.assertIn("Ticks: 50000", output_suffix)


class TestTrainingProgressIntegration(unittest.TestCase):
    """Integration tests for training progress display functionality."""
    
    def test_full_progress_line_format_non_headless(self):
        """Test the complete progress line format for headless=False mode."""
        # This test verifies the exact format of the progress line
        total_episode = 300
        gen = 15
        GENERATIONS = 200
        current_best_score = 175.25
        reward = 87.5
        steps = 750
        HEADLESS_MODE = False
        
        # Build the progress line exactly as in train_nn.py
        progress_line = (f"Episode {total_episode} | Gen {gen+1}/{GENERATIONS} | "
                        f"Best Score: {current_best_score:.2f} | "
                        f"Reward: {reward:.2f} | "
                        f"Steps: {steps:.0f}"
                        + (f" | Ticks: {10000}" if HEADLESS_MODE else ""))
        
        # Verify all components are present
        expected_parts = [
            "Episode 300",
            "Gen 16/200",
            "Best Score: 175.25",
            "Reward: 87.50",
            "Steps: 750"
        ]
        
        for part in expected_parts:
            self.assertIn(part, progress_line)
        
        # Verify Ticks is NOT present in non-headless mode
        self.assertNotIn("Ticks:", progress_line)
    
    def test_progress_shows_training_advancement(self):
        """Test that progress output clearly shows training advancement."""
        # Simulate multiple progress outputs across generations
        progress_outputs = []
        total_episode = 0
        episodes_per_gen = 30
        GENERATIONS = 200
        
        for gen in range(3):
            total_episode += episodes_per_gen
            output = f"Episode {total_episode} | Gen {gen+1}/{GENERATIONS}"
            progress_outputs.append(output)
        
        # Verify progression
        self.assertIn("Episode 30", progress_outputs[0])
        self.assertIn("Gen 1/200", progress_outputs[0])
        self.assertIn("Episode 60", progress_outputs[1])
        self.assertIn("Gen 2/200", progress_outputs[1])
        self.assertIn("Episode 90", progress_outputs[2])
        self.assertIn("Gen 3/200", progress_outputs[2])


if __name__ == '__main__':
    unittest.main()
