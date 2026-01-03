import json
import csv
import time
import random
import logging
import requests
import argparse
import os
from collections import defaultdict
from typing import List, Dict, Set, Any

# --- Configuration ---
class Config:
    WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Bot/1.0 (Research project; contact@example.com)"
    ]
    MAX_RETRIES = 3
    BATCH_SIZE = 50
    MIN_DELAY = 1.5
    MAX_DELAY = 3.0
    TIMEOUT = 45
    OUTPUT_FILE = os.path.join("output", "sponsor_painter_kg.jsonld")
    LOG_FILE = os.path.join("logs", "kg_extraction.log")

# --- Logger ---
def setup_logger():
    logger = logging.getLogger("WikidataKG")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    if not os.path.exists("logs"):
        os.makedirs("logs")
        
    file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()

# --- Fetcher ---
class WikidataFetcher:
    def __init__(self):
        self.session = requests.Session()
    
    def _get_headers(self):
        return {'User-Agent': random.choice(Config.USER_AGENTS), 'Accept': 'application/json'}

    def execute_query(self, query: str) -> List[Dict]:
        for attempt in range(Config.MAX_RETRIES):
            try:
                time.sleep(random.uniform(Config.MIN_DELAY, Config.MAX_DELAY))
                response = self.session.get(
                    Config.WIKIDATA_ENDPOINT, 
                    params={'query': query, 'format': 'json'}, 
                    headers=self._get_headers(),
                    timeout=Config.TIMEOUT
                )
                
                if response.status_code == 200:
                    return response.json().get('results', {}).get('bindings', [])
                elif response.status_code == 429:
                    wait = (2 ** attempt) * 5
                    logger.warning(f"Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"HTTP {response.status_code}: {response.text[:100]}")
            except Exception as e:
                logger.error(f"Request failed: {e}")
        return []

# --- Logic ---
class KGExtractor:
    def __init__(self, input_file):
        self.input_file = input_file
        self.fetcher = WikidataFetcher()
        self.all_properties = set()
        self.entities = {} # Map QID -> Node Data
        self.property_labels = {} # Map PID -> Labels

    def load_input_qids(self, limit=None) -> List[Dict]:
        qids = []
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('Original-QID', '').startswith('Q'):
                        qids.append(row)
            logger.info(f"Loaded {len(qids)} records.")
            return qids[:limit] if limit else qids
        except Exception as e:
            logger.error(f"Error loading input: {e}")
            return []

    def fetch_entity_data(self, input_data: List[Dict]):
        qids = [row['Original-QID'] for row in input_data]
        input_map = {row['Original-QID']: row for row in input_data}
        
        # Process in batches
        for i in range(0, len(qids), Config.BATCH_SIZE):
            batch = qids[i : i + Config.BATCH_SIZE]
            logger.info(f"Fetching batch {i} - {i+len(batch)}...")
            
            # SPARQL: Get all direct properties (wdt:), values, and labels
            # We fetch ?item ?itemLabel ?p ?o ?oLabel
            # Note: ?p will be a URI like http://www.wikidata.org/prop/direct/P31
            values_clause = " ".join([f"wd:{qid}" for qid in batch])
            query = f"""
            SELECT ?item ?itemLabel ?p ?o ?oLabel WHERE {{
              VALUES ?item {{ {values_clause} }}
              ?item ?p ?o .
              FILTER(STRSTARTS(STR(?p), "http://www.wikidata.org/prop/direct/"))
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,zh". }}
            }}
            """
            
            results = self.fetcher.execute_query(query)
            self._process_batch_results(results, input_map)

    def _process_batch_results(self, results, input_map):
        for binding in results:
            item_uri = binding['item']['value']
            qid = item_uri.split('/')[-1]
            
            # Init Entity Node
            if qid not in self.entities:
                label = binding.get('itemLabel', {}).get('value')
                self.entities[qid] = {
                    "@id": f"wd:{qid}",
                    "@type": "wd:Item",
                    "rdfs:label": label,
                    "ex:originalInfo": input_map.get(qid, {})
                }
            
            # Process Property
            p_uri = binding['p']['value']
            pid = p_uri.split('/')[-1] # e.g. P31
            self.all_properties.add(pid)
            
            # Process Object
            o_val = binding['o']['value']
            o_type = binding['o']['type']
            o_label = binding.get('oLabel', {}).get('value')
            
            prop_key = f"wdt:{pid}"
            
            # Create Value Node (Framing)
            value_node = None
            if o_type == 'uri' and 'entity' in o_val:
                # It's a Wikidata Item
                o_qid = o_val.split('/')[-1]
                value_node = {
                    "@id": f"wd:{o_qid}",
                    "rdfs:label": o_label
                }
            elif o_type == 'literal':
                # Literal value (date, string, number)
                # Check datatype
                datatype = binding['o'].get('datatype')
                if datatype:
                    value_node = {
                        "@value": o_val,
                        "@type": datatype
                    }
                else:
                    value_node = o_val
            else:
                # Fallback
                value_node = o_val

            # Add to entity
            if prop_key not in self.entities[qid]:
                self.entities[qid][prop_key] = []
            
            # Avoid duplicates if possible (simple check)
            if value_node not in self.entities[qid][prop_key]:
                self.entities[qid][prop_key].append(value_node)

    def fetch_property_labels(self):
        if not self.all_properties:
            return

        logger.info(f"Fetching labels for {len(self.all_properties)} properties...")
        pids = list(self.all_properties)
        
        # Batch fetch property labels
        for i in range(0, len(pids), Config.BATCH_SIZE):
            batch = pids[i : i + Config.BATCH_SIZE]
            values_clause = " ".join([f"wd:{pid}" for pid in batch])
            
            query = f"""
            SELECT ?prop ?propLabel WHERE {{
              VALUES ?prop {{ {values_clause} }}
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,zh". }}
            }}
            """
            results = self.fetcher.execute_query(query)
            
            for binding in results:
                p_uri = binding['prop']['value']
                pid = p_uri.split('/')[-1]
                label = binding.get('propLabel', {}).get('value')
                self.property_labels[pid] = label

    def save_jsonld(self):
        graph = []
        
        # 1. Add Entities
        for qid, data in self.entities.items():
            # Flatten single-item lists for cleaner JSON
            clean_data = {}
            for k, v in data.items():
                if isinstance(v, list) and len(v) == 1:
                    clean_data[k] = v[0]
                else:
                    clean_data[k] = v
            graph.append(clean_data)
            
        # 2. Add Properties
        for pid, label in self.property_labels.items():
            graph.append({
                "@id": f"wdt:{pid}",
                "@type": "rdf:Property",
                "rdfs:label": label
            })
            
        # 3. Construct Final Object
        output = {
            "@context": {
                "wd": "http://www.wikidata.org/entity/",
                "wdt": "http://www.wikidata.org/prop/direct/",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "schema": "http://schema.org/",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "ex": "http://example.org/ontology/"
            },
            "@graph": graph
        }
        
        with open(Config.OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved JSON-LD to {Config.OUTPUT_FILE}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run with 5 records")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    
    limit = 5 if args.test else args.limit
    
    extractor = KGExtractor("01-Merged_Dataset.csv")
    
    # 1. Load QIDs
    input_data = extractor.load_input_qids(limit)
    if not input_data:
        return
        
    # 2. Fetch Entity Data (and collect used Properties)
    extractor.fetch_entity_data(input_data)
    
    # 3. Fetch Property Labels
    extractor.fetch_property_labels()
    
    # 4. Save
    extractor.save_jsonld()

if __name__ == "__main__":
    main()
