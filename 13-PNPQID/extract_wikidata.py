import json
import csv
import time
import random
import logging
import requests
import argparse
import os
import re
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Set, Any

# --- Configuration ---
class Config:
    WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Bot/1.0 (Research project; contact@example.com)"
    ]
    MAX_RETRIES = 3
    BATCH_SIZE = 50  # Number of QIDs per SPARQL query
    MIN_DELAY = 1.5
    MAX_DELAY = 3.0
    TIMEOUT = 30
    OUTPUT_FILE = os.path.join("output", "sponsor_painter_kg.jsonl")
    CHECKPOINT_FILE = os.path.join("output", "checkpoint.json")
    LOG_FILE = os.path.join("logs", "extraction.log")

# --- Logger Setup ---
def setup_logger():
    logger = logging.getLogger("WikidataExtractor")
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()

# --- Checkpoint Manager ---
class CheckpointManager:
    def __init__(self, filepath):
        self.filepath = filepath
        self.processed_qids = set()
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_qids = set(data.get("processed_qids", []))
                logger.info(f"Loaded checkpoint. {len(self.processed_qids)} QIDs already processed.")
            except Exception as e:
                logger.error(f"Failed to load checkpoint: {e}")

    def save(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump({"processed_qids": list(self.processed_qids)}, f)
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def add(self, qids: List[str]):
        self.processed_qids.update(qids)
        self.save()

    def is_processed(self, qid):
        return qid in self.processed_qids

# --- Data Loader ---
class DataLoader:
    def __init__(self, filepath):
        self.filepath = filepath
    
    def load_data(self, limit=None) -> List[Dict[str, str]]:
        data = []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'Original-QID' in row and row['Original-QID'] and row['Original-QID'].startswith('Q'):
                        data.append(row)
            
            logger.info(f"Loaded {len(data)} records from {self.filepath}")
            
            if limit:
                data = data[:limit]
                logger.info(f"Limited to first {limit} records for testing.")
                
            return data
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

# --- Wikidata Fetcher ---
class WikidataFetcher:
    def __init__(self):
        self.session = requests.Session()
    
    def get_random_user_agent(self):
        return random.choice(Config.USER_AGENTS)
    
    def fetch_batch(self, qids: List[str]) -> List[Dict]:
        if not qids:
            return []
            
        sparql_query = self._build_query(qids)
        headers = {'User-Agent': self.get_random_user_agent(), 'Accept': 'application/json'}
        
        for attempt in range(Config.MAX_RETRIES):
            try:
                time.sleep(random.uniform(Config.MIN_DELAY, Config.MAX_DELAY))
                response = self.session.get(
                    Config.WIKIDATA_ENDPOINT, 
                    params={'query': sparql_query, 'format': 'json'}, 
                    headers=headers,
                    timeout=Config.TIMEOUT
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return data.get('results', {}).get('bindings', [])
                    except json.JSONDecodeError:
                        logger.error("JSON Decode Error")
                        continue
                elif response.status_code == 429:
                    wait_time = (2 ** attempt) * 5
                    logger.warning(f"Rate limited (429). Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP {response.status_code}: {response.text[:100]}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                
        logger.error(f"Failed to fetch batch after {Config.MAX_RETRIES} attempts.")
        return []

    def _build_query(self, qids: List[str]) -> str:
        values = " ".join([f"wd:{qid}" for qid in qids])
        # We fetch:
        # - Item Label (via service)
        # - Property (p)
        # - Value (o)
        # - Value Label (oLabel via service)
        # We filter for direct claims (wdt:) or labels/descriptions to keep it clean,
        # but the requirement is "complete", so we'll grab ?p ?o and filter in post-processing.
        # However, getting *everything* might be too huge.
        # Let's focus on Direct Claims (wdt:*) and rdfs:label/schema:description
        
        query = f"""
        SELECT ?item ?itemLabel ?p ?o ?oLabel WHERE {{
          VALUES ?item {{ {values} }}
          ?item ?p ?o .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,zh". }}
        }}
        """
        return query

# --- Data Processor ---
class DataProcessor:
    @staticmethod
    def process_results(raw_results: List[Dict], input_map: Dict[str, Dict]) -> List[Dict]:
        """
        raw_results: List of bindings from SPARQL
        input_map: Map of QID -> Input CSV Row Data (for merging metadata)
        """
        grouped = defaultdict(lambda: {
            "id": "", 
            "labels": {}, 
            "descriptions": {}, 
            "properties": defaultdict(list),
            "dataset_info": {}
        })
        
        for binding in raw_results:
            qid_uri = binding['item']['value']
            qid = qid_uri.split('/')[-1]
            
            if qid not in grouped:
                grouped[qid]["id"] = qid
                if qid in input_map:
                    grouped[qid]["dataset_info"] = input_map[qid]
            
            # Item Label (from Service)
            if 'itemLabel' in binding:
                # This is usually the English label or fallback due to serviceParam
                # We can store it as a primary label
                grouped[qid]["primary_label"] = binding['itemLabel']['value']

            p_uri = binding['p']['value']
            o_val = binding['o']['value']
            o_type = binding['o']['type']
            o_label = binding['oLabel']['value'] if 'oLabel' in binding else None
            
            # Normalize Date
            if o_type == 'literal' and 'datatype' in binding['o'] and binding['o']['datatype'] == 'http://www.w3.org/2001/XMLSchema#dateTime':
                 try:
                     # Wikidata dates are ISO 8601 like 1794-01-01T00:00:00Z
                     # Sometimes they are +1794-01-01T00:00:00Z
                     o_val = o_val.lstrip('+')
                 except:
                     pass

            # Classify Property
            if "prop/direct/" in p_uri:
                pid = p_uri.split("/")[-1]
                prop_data = {"value": o_val, "type": o_type}
                if o_label and o_label != o_val:
                    prop_data["label"] = o_label
                grouped[qid]["properties"][pid].append(prop_data)
            
            elif "http://www.w3.org/2000/01/rdf-schema#label" in p_uri:
                lang = binding['o'].get('xml:lang', 'unknown')
                grouped[qid]["labels"][lang] = o_val
                
            elif "http://schema.org/description" in p_uri:
                lang = binding['o'].get('xml:lang', 'unknown')
                grouped[qid]["descriptions"][lang] = o_val

        # Final Cleanup
        output_list = []
        for qid, data in grouped.items():
            # Convert defaultdict to dict
            data["properties"] = dict(data["properties"])
            
            # Metadata
            data["metadata"] = {
                "extracted_at": datetime.utcnow().isoformat() + "Z",
                "source": "Wikidata"
            }
            output_list.append(data)
            
        return output_list

# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(description="Extract Wikidata KG for Patrons and Painters")
    parser.add_argument("--test", action="store_true", help="Run in test mode (limit to 5 records)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of records to process")
    args = parser.parse_args()

    limit = 5 if args.test else args.limit
    
    # 1. Load Data
    loader = DataLoader("01-Merged_Dataset.csv")
    try:
        raw_data = loader.load_data(limit=limit)
    except FileNotFoundError:
        logger.error("Input file not found!")
        return

    # Map QID to Input Data for easy merging
    input_map = {row['Original-QID']: row for row in raw_data}
    all_qids = list(input_map.keys())
    
    # 2. Checkpoint
    checkpoint = CheckpointManager(Config.CHECKPOINT_FILE)
    qids_to_process = [qid for qid in all_qids if not checkpoint.is_processed(qid)]
    
    logger.info(f"Total QIDs: {len(all_qids)}, Remaining: {len(qids_to_process)}")
    
    # 3. Process in Batches
    fetcher = WikidataFetcher()
    processor = DataProcessor()
    
    total_processed = 0
    
    with open(Config.OUTPUT_FILE, 'a', encoding='utf-8') as f_out:
        for i in range(0, len(qids_to_process), Config.BATCH_SIZE):
            batch_qids = qids_to_process[i : i + Config.BATCH_SIZE]
            logger.info(f"Processing batch {i//Config.BATCH_SIZE + 1} ({len(batch_qids)} QIDs)...")
            
            # Fetch
            raw_results = fetcher.fetch_batch(batch_qids)
            
            if not raw_results:
                logger.warning(f"No results for batch starting with {batch_qids[0]}")
                # We still mark them as processed to avoid infinite loop on broken IDs? 
                # Or we just skip. Let's skip updating checkpoint if failed completely.
                # But fetcher returns empty on failure after retries.
                # If it's empty, maybe the QIDs are invalid. We should log them.
                pass
            
            # Process
            clean_data = processor.process_results(raw_results, input_map)
            
            # Write
            for item in clean_data:
                f_out.write(json.dumps(item, ensure_ascii=False) + "\n")
                
            # Update Checkpoint
            # Note: We mark the whole batch as processed, even if some QIDs returned no data (deleted/invalid)
            checkpoint.add(batch_qids)
            total_processed += len(batch_qids)
            
            logger.info(f"Saved {len(clean_data)} items. Total processed: {total_processed}")

if __name__ == "__main__":
    main()
