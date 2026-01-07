# Operation Log

## Phase 1: Initial Setup
- Analyzed `01-Worklist-Plates-Matched-Original.csv`.
- Created `extract_triples.py` to handle basic triple extraction.
- Rules implemented:
  - `Title_Description` -> `Head`
  - `Title_QID` -> `Head_QID`
  - `Artist` -> `created_by` -> `Tail`
  - `Location` -> `located_at` -> `Tail`
  - Provenance extraction (e.g., "from the collection of...").

## Phase 2: Deep Extraction
- Enhanced `extract_triples.py` to handle `embedded_location` (e.g., "Facade of St. Peter's").
- Output saved to `03-Worklist-Triples-Deep.csv`.

## Phase 3: Refinement (Current)
- Addressed complex titles with multiple embedded relations.
- New rules implemented:
  - **Location Suffixes**: Handles ", Rome" or ", Rome 1642" at the end of titles.
  - **Complex Structures**:
    - `with view of X` -> `depicts` X
    - `with portraits of X and Y` -> `depicts` X, `depicts` Y
    - `Modello for X` -> `preparatory_for` X
    - `Frontispiece of X` -> `part_of` X
    - `Final plate of X` -> `part_of` X
    - `from the opera X` -> `part_of` X
    - `Person, Title` -> `depicts` Person, `has_title_role` Title
    - `Author: Title` -> `created_by` Author
  - **Recursive Parsing**: Targets of relations (like the book title in "Frontispiece of Book...") are now recursively parsed to extract their own metadata (e.g., Author, Location, Date).
- Verified against user-reported issues:
  - `Frontispiece of Girolamo Teti...`: Successfully extracted `depicts` (Palazzo), `part_of` (Book), and recursively extracted Book's author/location/date.
  - `Modello for fresco...`: Successfully extracted `preparatory_for` (Fresco) and location.
  - `Paolo Giordano Orsini...`: Successfully extracted `depicts` and `has_title_role`.
  - `The Elysian Fields...`: Successfully extracted `part_of` (Opera).
- Output saved to `04-Worklist-Triples-Refined.csv`.
