# Conversion of interchunk dependencies to intrachunk dependencies in SSF
# Run 3 programs in sequential manner
- Adding posn and name features
  * works both at file and folder level  python add_posn_and_name_features.py --input Sample-Input-Inter --output Sample-Input-With-Posn-Name
- Computing Head
  * works both at file and folder level  python head_computation.py --input Sample-Input-With-Posn-Name --output Sample-Input-Head-Computed --json chunkHeadMapping.json
- Conversion into Intrachunk using POS tags
  * works both at file and folder level  python convert_inter_chunk_to_intra_chunk.py --input Sample-Input-Head-Computed --output Sample-Input-Intra