"""
DPO Data Preparation Pipeline

Processes poll data to create DPO training dataset:
1. Filters meaningless options
2. Augments short texts using Doubao API (multi-threaded)
3. Creates chosen/rejected pairs based on votes
4. Writes results immediately to file
"""

import json
import threading
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from doubao_client import DoubaoClient
from config import (
    MEANINGLESS_KEYWORDS,
    MIN_VOTE_DIFFERENCE,
    MIN_VOTE_COUNT,
    MIN_VOTE_PERCENTAGE_DIFF,
    OUTPUT_FILE,
    INCLUDE_METADATA,
    MAX_WORKERS,
    WRITE_IMMEDIATELY,
)


class DPOPipeline:
    """Pipeline for preparing DPO training data from poll results"""
    
    def __init__(self, input_file: str = "output.json"):
        self.input_file = input_file
        self.client = DoubaoClient()
        self.augmentation_cache = {}  # Cache to avoid re-augmenting same text
        self.cache_lock = threading.Lock()  # Thread-safe cache access
        self.file_lock = threading.Lock()  # Thread-safe file writing
        self.stats = {
            'total_examples': 0,
            'total_chosen_votes': 0,
            'total_rejected_votes': 0,
        }
        self.stats_lock = threading.Lock()
    
    def load_poll_data(self) -> List[Dict[str, Any]]:
        """Load poll data from JSON file"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} polls from {self.input_file}")
        return data
    
    def is_meaningless_option(self, option_text: str) -> bool:
        """
        Check if an option is meaningless (e.g., "路过", "看结果")
        
        Args:
            option_text: The option text to check
            
        Returns:
            True if option is meaningless, False otherwise
        """
        text_lower = option_text.lower().strip()
        
        for keyword in MEANINGLESS_KEYWORDS:
            if keyword in text_lower:
                return True
        
        return False
    
    def get_valid_options(self, options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out meaningless options and those below minimum vote threshold
        
        Args:
            options: List of poll options
            
        Returns:
            List of valid options
        """
        valid_options = []
        
        for option in options:
            # Check if meaningless
            if self.is_meaningless_option(option['text']):
                continue
            
            # Check minimum vote count
            if option['votes'] < MIN_VOTE_COUNT:
                continue
            
            valid_options.append(option)
        
        return valid_options
    
    def create_dpo_pairs(self, poll: Dict[str, Any]) -> List[Tuple[Dict, Dict]]:
        """
        Create chosen/rejected pairs from a poll
        
        Args:
            poll: Poll data containing content and options
            
        Returns:
            List of (chosen, rejected) option pairs
        """
        options = poll.get('options', [])
        valid_options = self.get_valid_options(options)
        
        if len(valid_options) < 2:
            return []
        
        # Sort by votes (descending)
        sorted_options = sorted(valid_options, key=lambda x: x['votes'], reverse=True)
        
        pairs = []
        chosen = sorted_options[0]
        
        # Create pairs with chosen vs each other option
        for rejected in sorted_options[1:]:
            # Check vote difference threshold
            vote_diff = chosen['votes'] - rejected['votes']
            if vote_diff < MIN_VOTE_DIFFERENCE:
                continue
            
            # Check percentage difference threshold
            if chosen['votes'] > 0:
                chosen_pct = float(chosen['percentage'].rstrip('%'))
                rejected_pct = float(rejected['percentage'].rstrip('%'))
                pct_diff = chosen_pct - rejected_pct
                
                if pct_diff < MIN_VOTE_PERCENTAGE_DIFF:
                    continue
            
            pairs.append((chosen, rejected))
        
        return pairs
    
    def process_single_pair(
        self, 
        context: str, 
        chosen: Dict[str, Any], 
        rejected: Dict[str, Any],
        output_file: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single chosen/rejected pair (thread-safe)
        
        Args:
            context: Poll context/question
            chosen: Chosen option
            rejected: Rejected option
            output_file: Output file path
            
        Returns:
            DPO example dict or None if failed
        """
        # Create cache key for this specific pair
        cache_key = f"{chosen['text']}|{rejected['text']}|{context[:50]}"
        
        # Check cache for chosen analysis (thread-safe)
        chosen_cache_key = f"chosen_{cache_key}"
        with self.cache_lock:
            if chosen_cache_key in self.augmentation_cache:
                chosen_analysis = self.augmentation_cache[chosen_cache_key]
            else:
                chosen_analysis = None
        
        if chosen_analysis is None:
            # Generate chosen analysis
            chosen_analysis = self.client.augment_option(
                option_text=chosen['text'],
                context=context,
                chosen_text=chosen['text'],
                rejected_text=rejected['text'],
                chosen_votes=chosen['votes'],
                rejected_votes=rejected['votes'],
                chosen_percentage=chosen['percentage'],
                rejected_percentage=rejected['percentage'],
                is_chosen=True
            )
            
            # Fallback to original if API fails
            if not chosen_analysis:
                chosen_analysis = f"选择{chosen['text']}的理由：获得{chosen['votes']}票（{chosen['percentage']}）"
            
            # Cache result (thread-safe)
            with self.cache_lock:
                self.augmentation_cache[chosen_cache_key] = chosen_analysis
        
        # Check cache for rejected analysis (thread-safe)
        rejected_cache_key = f"rejected_{cache_key}"
        with self.cache_lock:
            if rejected_cache_key in self.augmentation_cache:
                rejected_analysis = self.augmentation_cache[rejected_cache_key]
            else:
                rejected_analysis = None
        
        if rejected_analysis is None:
            # Generate rejected analysis
            rejected_analysis = self.client.augment_option(
                option_text=rejected['text'],
                context=context,
                chosen_text=chosen['text'],
                rejected_text=rejected['text'],
                chosen_votes=chosen['votes'],
                rejected_votes=rejected['votes'],
                chosen_percentage=chosen['percentage'],
                rejected_percentage=rejected['percentage'],
                is_chosen=False
            )
            
            # Fallback to original if API fails
            if not rejected_analysis:
                rejected_analysis = f"不选择{rejected['text']}的理由：仅获得{rejected['votes']}票（{rejected['percentage']}）"
            
            # Cache result (thread-safe)
            with self.cache_lock:
                self.augmentation_cache[rejected_cache_key] = rejected_analysis
        
        example = {
            "prompt": context,
            "chosen": chosen_analysis,
            "rejected": rejected_analysis,
            "chosen_votes": chosen['votes'],
            "rejected_votes": rejected['votes'],
        }
        
        if INCLUDE_METADATA:
            example["metadata"] = {
                "original_chosen": chosen['text'],
                "original_rejected": rejected['text'],
                "chosen_percentage": chosen['percentage'],
                "rejected_percentage": rejected['percentage'],
            }
        
        # Write immediately to file (thread-safe)
        if WRITE_IMMEDIATELY:
            with self.file_lock:
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        # Update statistics (thread-safe)
        with self.stats_lock:
            self.stats['total_examples'] += 1
            self.stats['total_chosen_votes'] += chosen['votes']
            self.stats['total_rejected_votes'] += rejected['votes']
        
        return example
    
    def process_poll(self, poll: Dict[str, Any], poll_index: int, total_polls: int, output_file: str) -> List[Dict[str, Any]]:
        """
        Process a single poll to create DPO training examples (multi-threaded)
        
        Args:
            poll: Poll data
            poll_index: Index of current poll
            total_polls: Total number of polls
            output_file: Output file path
            
        Returns:
            List of DPO training examples
        """
        pairs = self.create_dpo_pairs(poll)
        
        if not pairs:
            return []
        
        context = poll.get('content', '').strip()
        examples = []
        
        # Process pairs concurrently
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for chosen, rejected in pairs:
                future = executor.submit(
                    self.process_single_pair,
                    context,
                    chosen,
                    rejected,
                    output_file
                )
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    example = future.result()
                    if example:
                        examples.append(example)
                except Exception as e:
                    print(f"Error processing pair: {e}")
        
        return examples
    
    def run(self, output_file: Optional[str] = None) -> None:
        """
        Run the full DPO pipeline with multi-threading
        
        Args:
            output_file: Output file path (default from config)
        """
        if output_file is None:
            output_file = OUTPUT_FILE
        
        print("=" * 60)
        print("DPO Data Preparation Pipeline (Multi-threaded)")
        print("=" * 60)
        print(f"Max workers: {MAX_WORKERS}")
        print(f"Write immediately: {WRITE_IMMEDIATELY}")
        print("=" * 60)
        
        # Clear output file if writing immediately
        if WRITE_IMMEDIATELY:
            with open(output_file, 'w', encoding='utf-8') as f:
                pass  # Clear file
        
        # Load data
        polls = self.load_poll_data()
        
        # Process polls
        all_examples = []
        
        for i, poll in enumerate(polls):
            print(f"\nProcessing poll {i + 1}/{len(polls)}...")
            examples = self.process_poll(poll, i, len(polls), output_file)
            
            if examples:
                print(f"  Generated {len(examples)} DPO pair(s)")
                if not WRITE_IMMEDIATELY:
                    all_examples.extend(examples)
            else:
                print(f"  No valid pairs found")
        
        # Save results if not writing immediately
        if not WRITE_IMMEDIATELY:
            print(f"\n{'=' * 60}")
            print(f"Saving to {output_file}...")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for example in all_examples:
                    f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        # Final statistics
        print(f"\n{'=' * 60}")
        print(f"✓ Processing complete!")
        print(f"Total DPO examples generated: {self.stats['total_examples']}")
        print(f"Output file: {output_file}")
        print("=" * 60)
        
        # Statistics
        self._print_statistics()
    
    def _print_statistics(self) -> None:
        """Print statistics about the generated dataset"""
        total_examples = self.stats['total_examples']
        
        if total_examples == 0:
            return
        
        print("\nDataset Statistics:")
        print("-" * 60)
        
        avg_chosen_votes = self.stats['total_chosen_votes'] / total_examples
        avg_rejected_votes = self.stats['total_rejected_votes'] / total_examples
        avg_vote_diff = avg_chosen_votes - avg_rejected_votes
        
        print(f"Total examples: {total_examples}")
        print(f"Average chosen votes: {avg_chosen_votes:.1f}")
        print(f"Average rejected votes: {avg_rejected_votes:.1f}")
        print(f"Average vote difference: {avg_vote_diff:.1f}")
        
        with self.cache_lock:
            print(f"Unique analyses cached: {len(self.augmentation_cache)}")
        
        print("-" * 60)


def main():
    """Main entry point"""
    pipeline = DPOPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
