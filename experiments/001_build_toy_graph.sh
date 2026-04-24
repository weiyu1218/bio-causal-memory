#!/usr/bin/env bash
set -euo pipefail

bcm build-graph \
  --task data/fixtures/transcript_quant_task.json \
  --trace data/runs/transcript_quant_failed_toy.json \
  --out data/graphs/transcript_quant_failed_toy.graph.json
