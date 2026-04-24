#!/usr/bin/env bash
set -euo pipefail

bcm query \
  --graph data/graphs/transcript_quant_failed_toy.graph.json \
  --question "why did the run fail?"
