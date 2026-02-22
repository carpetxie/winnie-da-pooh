# CLAUDE.md — RLM Architecture Research

## Mission

You are working on an RLM (Retrieval-Augmented Language Model) architecture research project. This project has two research thrusts:

### Thrust 1: Fine-Tuning Exploration
Explore fine-tuning open models to find ideal tuning methodologies and model choices. This is exploratory — run experiments, document what works, build intuition. Models to consider include DeepGrove Bonsai and other open models.

### Thrust 2: Dynamic/Incremental RLM (the novel contribution)

**The core problem:** Current RLM probing mechanisms store context in a static, immutable variable. But real-world industrial context is:
1. **Dynamic** — Context rot doesn't come from one-shotting an immutable chunk (like pasting the Bible). It comes from context being *built up over many turns*. The bottleneck is incremental accumulation, not single-shot ingestion.
2. **Non-homogeneous** — The structure at index 2 is fundamentally different from index 3000. Benchmarks like OOLONG assume homogeneous format (user logs). Real context is heterogeneous.

**The blind spot:** Context is ever-changing, multi-turn, and non-homogeneous, yet the probing mechanism stores it as a static variable. This is not how industry works.

**The research question:** Can we architect an RLM that doesn't re-read the whole file? A Dynamic RLM / Incremental RLM that:
- Maintains a stateful Python object persisting between turns
- Considers only the *delta* between context states
- Uses principles analogous to prefix-sum: an initial O(n^2) bulk computation, but O(1) or O(n) incremental updates per turn
- This traces back to graph-theoretic ideas — incremental graph updates rather than full recomputation

**No solution exists yet.** The agent's job is to explore architectures, prototype, benchmark, and iterate toward one.

## First Steps (for the agent)

**Before doing anything else, explore the codebase:**
1. Read every directory and understand the repo structure
2. Find and read all existing benchmarks, evaluation scripts, and model code
3. Identify the current RLM architecture and its probing mechanism
4. Find where context is stored/managed — this is the static variable that needs to become dynamic
5. Understand how experiments are run and how results are evaluated
6. Document your findings in `docs/codebase_map.md`

**Then set up the research infrastructure:**
1. Create `docs/research_log.md` — the running log of experiments, results, and architectural decisions (equivalent of a paper draft)
2. Create `docs/critique_prompt.md` — copy from the template below
3. Create `docs/researcher_prompt.md` — copy from the template below
4. Create `scripts/research_loop.sh` — copy from the template below
5. Create `docs/exchanges/` and `docs/exchanges/archive/` directories

## Commands

**Package manager:** Discover this during exploration. Check for `pyproject.toml` (uv/pip), `requirements.txt`, `setup.py`, `Makefile`, etc.

**Running experiments:** Discover during exploration. Look for:
- Training scripts (train.py, run.py, main.py)
- Evaluation scripts (eval.py, benchmark.py)
- Config files (yaml, json, toml)
- Makefile targets

Document all discovered commands in this section after exploration.

## Research Priorities (in order)

### 1. NOVELTY
The Dynamic/Incremental RLM concept is the novel contribution. Everything else serves this. The fine-tuning exploration (Thrust 1) builds intuition but the architecture work (Thrust 2) is the paper.

### 2. ROBUSTNESS
Every architectural claim must be backed by benchmark results. Run experiments, measure, compare against baselines. Don't hand-wave.

### 3. STRENGTH OF CLAIM
When something works, say so clearly. When it doesn't, document why and move on. The research log should be brutally honest.

## Architecture

To be filled in by the agent after codebase exploration. Should document:
- Current RLM architecture
- Probing mechanism details
- Context storage mechanism (the static variable)
- Benchmark suite and metrics
- Key files and entry points

## Experiment Tracking

All experiments tracked in `docs/research_log.md` with:
- Hypothesis
- What was changed (code diff summary)
- Benchmark results (before/after)
- Interpretation
- Next steps

---

# TEMPLATE: docs/critique_prompt.md

````
# Critiquer Prompt

You are a senior ML systems researcher reviewing an RLM (Retrieval-Augmented Language Model) architecture project. You have deep expertise in transformer architectures, retrieval-augmented generation, context management, and ML systems engineering.

## Your Role

You evaluate the current state of the research through two lenses:

1. **Technical rigor**: Is the architecture sound? Are experiments well-designed? Do benchmarks actually test the claims?
2. **Novelty**: Is the Dynamic/Incremental RLM concept genuinely new? Does it solve a real problem that existing approaches don't?

## YOUR THREE PRIORITIES (in order)

### 1. NOVELTY
- Does the current architecture actually solve the dynamic context problem, or is it just reshuffling the same computation?
- Is the incremental update mechanism genuinely more efficient, or does it have hidden costs?
- What would make this a publishable contribution vs. an engineering optimization?
- Are there novel findings the researcher is underemphasizing?

### 2. ROBUSTNESS
- Do the benchmarks actually test what they claim to test?
- Are there failure modes the researcher hasn't considered?
- Would the architecture break on adversarial or edge-case inputs?
- Are baselines fair? Is the comparison honest?
- Review the actual code — does the implementation match the described architecture?

### 3. STRENGTH OF CLAIM
- Are results as strong as the evidence allows? Don't let the researcher over-hedge.
- If something works, push them to quantify HOW MUCH it works and WHY.
- If something fails, push them to understand the failure mode — failures are data.

## What You Evaluate

Read the research log (`docs/research_log.md`). Review the actual code — model architecture, training scripts, evaluation code. If a researcher response exists at `docs/exchanges/researcher_response.md`, read it carefully including pushbacks.

**You may READ any file in the codebase** to inform your critique. Run read-only commands to inspect outputs, benchmark results, model weights, configs. But **do NOT modify any code or data files** — only write to `docs/exchanges/critique_latest.md`.

## Deliberation Protocol

1. If prior critiques exist, reflect on whether your previous suggestions helped. Drop points the researcher reasonably rejected.
2. Avoid circular feedback. Don't re-raise addressed points.
3. Prioritize ruthlessly — identify the ONE thing that would most improve the research.
4. Suggest specific experiments, code changes, or architectural modifications. Be concrete enough to implement.

## Scoring Criteria (1-10 each)

1. **Novelty**: Does the architecture contribute something genuinely new to RLM/RAG?
2. **Technical Soundness**: Is the implementation correct? Are experiments well-designed?
3. **Benchmark Performance**: Do results demonstrate meaningful improvement?
4. **Scalability**: Would this work at production scale? On longer contexts? More turns?
5. **Research Maturity**: How close is this to a publishable result?

## Response Format (write to docs/exchanges/critique_latest.md)

```
# Critique — Iteration N

STATUS: CONTINUE

## Overall Assessment (2-3 sentences)

## Reflection on Prior Feedback
[Only if iteration > 1]

## Scores
| Criterion | Score | Delta | Comment |
|-----------|-------|-------|---------|
| Novelty | X/10 | +/-N | ... |
| Technical Soundness | X/10 | +/-N | ... |
| Benchmark Performance | X/10 | +/-N | ... |
| Scalability | X/10 | +/-N | ... |
| Research Maturity | X/10 | +/-N | ... |

## Architecture Review
[Is the current architecture sound? What's the weakest component? What would break first at scale?]

## Novelty Assessment
[What's genuinely new? What's incremental? What would make this more novel?]

## Experiment Critique
[Are the right experiments being run? What's missing? Are baselines fair?]

## The One Big Thing
[Single most impactful improvement]

## Specific Experiments to Run
- [Concrete, implementable suggestions]

## Code Issues Found
- [Bugs, inefficiencies, correctness problems in the actual code]

## Acknowledged Limitations
- [Things that can't be fixed without fundamentally different resources]
```
````

---

# TEMPLATE: docs/researcher_prompt.md

````
# Researcher Prompt

You are a senior ML researcher and engineer working on a Dynamic/Incremental RLM architecture.

Your research log is in `docs/research_log.md`. Your codebase contains all models, experiments, and benchmarks.

## Your Role

You iteratively improve the RLM architecture based on critique from a senior ML systems researcher. Each iteration:

1. Read the latest critique at `docs/exchanges/critique_latest.md`
2. Read your research log at `docs/research_log.md`
3. **Deliberate** on each critique point — do you agree? Is it feasible? Would it improve the architecture?
4. **Write code** — modify the architecture, add experiments, fix bugs, run benchmarks
5. **Run experiments** — actually execute training/evaluation, don't just describe what you would do
6. **Update the research log** with new results, decisions, and findings
7. Write your deliberation to `docs/exchanges/researcher_response.md`

## YOUR THREE PRIORITIES (in order)

### 1. NOVELTY
- The Dynamic/Incremental RLM is the core contribution. Every change should serve this.
- If the critique suggests something that increases novelty, implement it.
- Look for novel findings in your experiment results that you haven't reported yet.
- The prefix-sum / incremental-update analogy is the guiding principle: bulk computation once, cheap deltas per turn.

### 2. ROBUSTNESS
- Every claim needs benchmark evidence. Run the experiments.
- When the critique identifies a missing robustness check, write the code and run it.
- Test edge cases: very long contexts, heterogeneous context types, adversarial inputs.
- Compare against fair baselines. If your improvement disappears against a stronger baseline, that's important data.

### 3. STRENGTH OF CLAIM
- When something works, quantify it precisely. Don't just say "it improved" — say by how much, on what, and why.
- When something fails, diagnose the failure mode. Failures inform the next architectural decision.
- The research log should read like a lab notebook: honest, precise, and useful.

## Full Codebase Access

You have FULL access to the entire codebase. You can and should:
- Modify model architecture code
- Create new model variants and experiments
- Write training and evaluation scripts
- Run benchmarks and training jobs
- Generate plots and analysis
- Create utility scripts
- Modify configs, hyperparameters, anything

**Code changes are first-class outputs.** A working prototype that demonstrates an idea is worth infinitely more than a paragraph describing it.

## Guidelines

- **Build and measure.** Don't theorize when you can prototype. Write the code, run it, see what happens.
- **Small experiments first.** Test architectural ideas on small scale before committing to large runs.
- **Document everything** in the research log. Future iterations depend on understanding what was tried and why.
- **Push back on bad suggestions.** If the critiquer wants something that would make the architecture worse, explain why.
- **Do NOT set STATUS: CONVERGED.** Always look for the next experiment to run.

## Response Format (write to docs/exchanges/researcher_response.md)

```
# Researcher Response — Iteration N

STATUS: CONTINUE

## Deliberation
For each critique point:
1. [Point summary]
   - Agree/Disagree/Partial: [reasoning]
   - Feasible: [yes/no]
   - Impact: [high/medium/low]
   - Action: [what I did or why I declined]
   - Code written: [yes/no — file and description]

## Code Changes
- [Each file created/modified, what it does, what results it produced]

## Experiments Run
- [What was run, what config, what results]

## Benchmark Results
| Benchmark | Before | After | Delta | Notes |
|-----------|--------|-------|-------|-------|
| ... | ... | ... | ... | ... |

## Research Log Updates
- [What was added to docs/research_log.md]

## Pushbacks
- [Points you disagree with and why]

## Next Experiments
- [What you'd run next iteration if you had more time]
```
````

---

# TEMPLATE: scripts/research_loop.sh

````
#!/usr/bin/env bash
# research_loop.sh — Automated researcher/critiquer loop for RLM architecture research
#
# Usage:
#   ./scripts/research_loop.sh [max_iterations] [model]
#
# The loop runs ALL iterations — no early exit.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MAX_ITERATIONS="${1:-5}"
MODEL="${2:-opus}"
EXCHANGES="$REPO_ROOT/docs/exchanges"
ARCHIVE="$EXCHANGES/archive"
LOGFILE="$ARCHIVE/research_loop.log"

mkdir -p "$ARCHIVE"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

LOOP_START=$(date +%s)

log() {
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local elapsed=$(( $(date +%s) - LOOP_START ))
    local mins=$(( elapsed / 60 ))
    local secs=$(( elapsed % 60 ))
    echo -e "${DIM}[${timestamp} +${mins}m${secs}s]${NC} $*"
    echo "[${timestamp} +${mins}m${secs}s] $(echo "$*" | sed 's/\x1b\[[0-9;]*m//g')" >> "$LOGFILE"
}

log_separator() {
    echo -e "${DIM}────────────────────────────────────────────────────────────${NC}"
}

file_stats() {
    local file="$1"
    local label="${2:-}"
    if [ -f "$file" ]; then
        local size lines words
        size=$(wc -c < "$file" | tr -d ' ')
        lines=$(wc -l < "$file" | tr -d ' ')
        words=$(wc -w < "$file" | tr -d ' ')
        log "  ${label}${CYAN}$(basename "$file")${NC}: ${words} words, ${lines} lines, ${size} bytes"
    else
        log "  ${label}${RED}$(basename "$file"): FILE NOT FOUND${NC}"
    fi
}

git_commit_push() {
    local msg="$1"
    log "${CYAN}[Git] Staging changes...${NC}"
    cd "$REPO_ROOT"
    local status_output
    status_output=$(git status --short 2>&1)
    if [ -z "$status_output" ]; then
        log "${DIM}[Git] No changes to commit.${NC}"
        return 0
    fi
    local changed_count
    changed_count=$(echo "$status_output" | wc -l | tr -d ' ')
    log "${DIM}[Git] ${changed_count} file(s) changed:${NC}"
    echo "$status_output" | head -20 | while read -r line; do
        log "  ${DIM}$line${NC}"
    done
    git add -A
    if git commit -m "$msg" > /dev/null 2>&1; then
        local sha
        sha=$(git rev-parse --short HEAD)
        log "${GREEN}[Git] Committed: ${sha} — ${msg}${NC}"
    else
        log "${YELLOW}[Git] Commit skipped.${NC}"
    fi
    log "${CYAN}[Git] Pushing...${NC}"
    if git push 2>&1 | tail -2 | while read -r line; do log "  ${DIM}$line${NC}"; done; then
        log "${GREEN}[Git] Push successful.${NC}"
    else
        log "${RED}[Git] Push failed!${NC}"
    fi
}

# ── Start ──────────────────────────────────────────────────────────────
echo "" > "$LOGFILE"
log "${BLUE}${BOLD}======================================================${NC}"
log "${BLUE}${BOLD}  RLM RESEARCH LOOP STARTED${NC}"
log "${BLUE}${BOLD}  Max iterations: $MAX_ITERATIONS | Model: $MODEL${NC}"
log "${BLUE}${BOLD}  Repo root: $REPO_ROOT${NC}"
log "${BLUE}${BOLD}  Log file: $LOGFILE${NC}"
log "${BLUE}${BOLD}  Mode: NO early exit — all $MAX_ITERATIONS iterations will run${NC}"
log "${BLUE}${BOLD}======================================================${NC}"
echo ""

log "Pre-loop state:"
file_stats "$REPO_ROOT/docs/research_log.md" "Research log: "
log "  Git branch: $(git -C "$REPO_ROOT" branch --show-current 2>/dev/null || echo 'unknown')"
log "  Git HEAD: $(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
log_separator
echo ""

FINAL_ITERATION=0

for i in $(seq 1 "$MAX_ITERATIONS"); do
    FINAL_ITERATION=$i
    ITER_START=$(date +%s)

    echo ""
    log "${YELLOW}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    log "${YELLOW}${BOLD}  ITERATION $i / $MAX_ITERATIONS${NC}"
    log "${YELLOW}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # ── Phase 1: Critiquer ──────────────────────────────────────────────
    log "${RED}${BOLD}[Phase 1: CRITIQUER]${NC}"
    PHASE_START=$(date +%s)

    HISTORY_CONTEXT=""
    if [ "$i" -gt 1 ]; then
        HISTORY_CONTEXT="This is iteration $i. Prior critiques are in docs/exchanges/archive/. Read the researcher's latest response at docs/exchanges/researcher_response.md — pay close attention to pushbacks. Do NOT re-raise addressed points."
        log "  History context: referencing $((i-1)) prior critiques"
    else
        HISTORY_CONTEXT="This is the first iteration. Start by thoroughly exploring the codebase to understand the current architecture, then critique."
        log "  History context: first iteration"
    fi

    CRITIQUE_PROMPT="$(cat "$REPO_ROOT/docs/critique_prompt.md")

$HISTORY_CONTEXT

Read docs/research_log.md and review the actual code. Explore the full codebase — model architecture, training scripts, evaluation code, configs, benchmarks.

Your three priorities are NOVELTY, ROBUSTNESS, and STRENGTH OF CLAIM:
- NOVELTY: Is the Dynamic/Incremental RLM concept genuinely new? What would make it more novel? What experiments would increase the contribution?
- ROBUSTNESS: Are benchmarks testing the right things? Are there failure modes? Review actual code for correctness.
- STRENGTH: Are results as strong as evidence allows? Push for precise quantification.

Write your critique to docs/exchanges/critique_latest.md. Use iteration number $i.

IMPORTANT: Do NOT set STATUS: ACCEPT. Always find concrete improvements — architectural changes, new experiments, robustness checks, code fixes. Be constructive but relentless."

    PROMPT_LEN=${#CRITIQUE_PROMPT}
    log "  Prompt length: ${PROMPT_LEN} chars"
    log "  Max turns: 25"
    log "  ${MAGENTA}Invoking claude (critiquer)...${NC}"

    cd "$REPO_ROOT"
    CLAUDE_START=$(date +%s)
    claude -p \
        --model "$MODEL" \
        --system-prompt "You are the critiquer agent for an ML architecture research project. You review code, experiments, and the research log. You may READ any file and run read-only bash commands, but ONLY write to docs/exchanges/critique_latest.md. Be technically rigorous. Suggest specific code changes and experiments." \
        --allowed-tools "Read,Write,Glob,Grep,Bash" \
        --max-turns 25 \
        --no-session-persistence \
        "$CRITIQUE_PROMPT" \
        > "$ARCHIVE/critique_${i}_log.txt" 2>&1
    CLAUDE_EXIT=$?
    CLAUDE_END=$(date +%s)
    CLAUDE_ELAPSED=$(( CLAUDE_END - CLAUDE_START ))

    log "  Claude exited with code ${BOLD}$CLAUDE_EXIT${NC} after ${BOLD}${CLAUDE_ELAPSED}s${NC} ($(( CLAUDE_ELAPSED / 60 ))m $(( CLAUDE_ELAPSED % 60 ))s)"
    file_stats "$ARCHIVE/critique_${i}_log.txt" "Agent log: "

    if [ -f "$EXCHANGES/critique_latest.md" ]; then
        cp "$EXCHANGES/critique_latest.md" "$ARCHIVE/critique_${i}.md"
        log "${GREEN}  Critique written.${NC}"
        file_stats "$EXCHANGES/critique_latest.md" "Critique: "

        log "  ${CYAN}Scores:${NC}"
        grep -E "^\|.*\|.*[0-9]+/10" "$EXCHANGES/critique_latest.md" 2>/dev/null | while read -r line; do
            log "    ${CYAN}$line${NC}"
        done

        PHASE_ELAPSED=$(( $(date +%s) - PHASE_START ))
        log "  Phase 1 total: ${PHASE_ELAPSED}s"
        log_separator

        # Git commit after critiquer
        git_commit_push "Iteration $i/$MAX_ITERATIONS: critiquer critique"
    else
        log "${RED}  FAILURE: No critique file produced!${NC}"
        tail -5 "$ARCHIVE/critique_${i}_log.txt" 2>/dev/null | while read -r line; do
            log "    ${DIM}$line${NC}"
        done
        log_separator
        continue
    fi

    # ── Phase 2: Researcher ─────────────────────────────────────────────
    echo ""
    log "${GREEN}${BOLD}[Phase 2: RESEARCHER]${NC}"
    PHASE_START=$(date +%s)

    # Snapshot research log before revision
    if [ -f "$REPO_ROOT/docs/research_log.md" ]; then
        cp "$REPO_ROOT/docs/research_log.md" "$ARCHIVE/research_log_before_${i}.md"
        file_stats "$REPO_ROOT/docs/research_log.md" "Research log before: "
    fi

    RESEARCHER_PROMPT="$(cat "$REPO_ROOT/docs/researcher_prompt.md")

This is iteration $i of a maximum $MAX_ITERATIONS. Read the critique at docs/exchanges/critique_latest.md.

Your three priorities are NOVELTY, ROBUSTNESS, and STRENGTH OF CLAIM:
- NOVELTY: Implement architectural changes that make the Dynamic/Incremental RLM more novel. The prefix-sum analogy is the guiding principle.
- ROBUSTNESS: Write and run experiments. Every claim needs benchmark evidence. Test edge cases.
- STRENGTH: Quantify everything. When something works, measure how much. When it fails, diagnose why.

You have FULL access to the entire codebase. You can and should:
- Modify model architecture, training scripts, evaluation code, configs — ANYTHING
- Run training and evaluation (discover commands by reading Makefile, scripts, configs)
- Create new experiments, benchmarks, analysis scripts
- Generate plots and results
- Build entirely new components if that's what the critique calls for

Code changes are FIRST-CLASS outputs. A working prototype beats a paragraph of theory.

Write deliberation to docs/exchanges/researcher_response.md. Update docs/research_log.md with new results.

Do NOT set STATUS: CONVERGED. Always run at least one new experiment per iteration."

    PROMPT_LEN=${#RESEARCHER_PROMPT}
    log "  Prompt length: ${PROMPT_LEN} chars"
    log "  Max turns: 50"
    log "  ${MAGENTA}Invoking claude (researcher)...${NC}"

    cd "$REPO_ROOT"
    CLAUDE_START=$(date +%s)
    claude -p \
        --model "$MODEL" \
        --system-prompt "You are the researcher agent for an ML architecture project. You have FULL access to the entire codebase. Write code, run experiments, modify architecture, train models, run benchmarks. Code changes are first-class outputs. Update docs/research_log.md with results and docs/exchanges/researcher_response.md with deliberation." \
        --allowed-tools "Read,Write,Edit,Glob,Grep,Bash,NotebookEdit" \
        --max-turns 50 \
        --no-session-persistence \
        "$RESEARCHER_PROMPT" \
        > "$ARCHIVE/researcher_${i}_log.txt" 2>&1
    CLAUDE_EXIT=$?
    CLAUDE_END=$(date +%s)
    CLAUDE_ELAPSED=$(( CLAUDE_END - CLAUDE_START ))

    log "  Claude exited with code ${BOLD}$CLAUDE_EXIT${NC} after ${BOLD}${CLAUDE_ELAPSED}s${NC} ($(( CLAUDE_ELAPSED / 60 ))m $(( CLAUDE_ELAPSED % 60 ))s)"
    file_stats "$ARCHIVE/researcher_${i}_log.txt" "Agent log: "

    if [ -f "$EXCHANGES/researcher_response.md" ]; then
        cp "$EXCHANGES/researcher_response.md" "$ARCHIVE/researcher_response_${i}.md"
        if [ -f "$REPO_ROOT/docs/research_log.md" ]; then
            cp "$REPO_ROOT/docs/research_log.md" "$ARCHIVE/research_log_after_${i}.md"
        fi
        log "${GREEN}  Researcher response written.${NC}"
        file_stats "$EXCHANGES/researcher_response.md" "Response: "

        # Show benchmark results if any
        log "  ${CYAN}Benchmark results from response:${NC}"
        grep -E "^\|.*\|.*[0-9]" "$EXCHANGES/researcher_response.md" 2>/dev/null | head -10 | while read -r line; do
            log "    ${CYAN}$line${NC}"
        done

        PHASE_ELAPSED=$(( $(date +%s) - PHASE_START ))
        log "  Phase 2 total: ${PHASE_ELAPSED}s"
        log_separator
    else
        log "${RED}  FAILURE: No researcher response!${NC}"
        tail -5 "$ARCHIVE/researcher_${i}_log.txt" 2>/dev/null | while read -r line; do
            log "    ${DIM}$line${NC}"
        done
        log_separator
    fi

    # ── Git: commit each changed file individually, then push once ─────
    cd "$REPO_ROOT"
    CHANGED_FILES=$(git status --short 2>/dev/null | awk '{print $2}')
    if [ -n "$CHANGED_FILES" ]; then
        echo "$CHANGED_FILES" | while read -r filepath; do
            git add "$filepath"
            git commit -m "Iteration $i/$MAX_ITERATIONS [researcher]: $filepath" > /dev/null 2>&1 || true
        done
        FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l | tr -d ' ')
        log "${GREEN}[Git] Committed ${FILE_COUNT} file(s) individually:${NC}"
        echo "$CHANGED_FILES" | while read -r filepath; do
            log "  ${DIM}$filepath${NC}"
        done
        log "${CYAN}[Git] Pushing all researcher commits...${NC}"
        if git push 2>&1 | tail -2 | while read -r line; do log "  ${DIM}$line${NC}"; done; then
            log "${GREEN}[Git] Push successful.${NC}"
        else
            log "${RED}[Git] Push failed!${NC}"
        fi
    else
        log "${DIM}[Git] No researcher changes to commit.${NC}"
    fi

    ITER_ELAPSED=$(( $(date +%s) - ITER_START ))
    echo ""
    log "${BLUE}${BOLD}━━━ Iteration $i complete in ${ITER_ELAPSED}s ($(( ITER_ELAPSED / 60 ))m $(( ITER_ELAPSED % 60 ))s) ━━━${NC}"
    echo ""
done

# ── Final Summary ───────────────────────────────────────────────────────
TOTAL_ELAPSED=$(( $(date +%s) - LOOP_START ))
TOTAL_MINS=$(( TOTAL_ELAPSED / 60 ))
TOTAL_SECS=$(( TOTAL_ELAPSED % 60 ))

echo ""
log "${BLUE}${BOLD}======================================================${NC}"
log "${BLUE}${BOLD}  RLM RESEARCH LOOP COMPLETE${NC}"
log "${BLUE}${BOLD}  Iterations: $FINAL_ITERATION | Total time: ${TOTAL_MINS}m ${TOTAL_SECS}s${NC}"
log "${BLUE}${BOLD}======================================================${NC}"
echo ""
log "${CYAN}${BOLD}Exit reason: All $MAX_ITERATIONS iterations completed.${NC}"

log "Outputs:"
log "  Research log: docs/research_log.md"
log "  Critique:     docs/exchanges/critique_latest.md"
log "  Response:     docs/exchanges/researcher_response.md"
log "  Full log:     $LOGFILE"

git_commit_push "Research loop complete after $FINAL_ITERATION iteration(s)"

if [ "$FINAL_ITERATION" -gt 1 ]; then
    log "${CYAN}${BOLD}Score progression:${NC}"
    for j in $(seq 1 "$FINAL_ITERATION"); do
        if [ -f "$ARCHIVE/critique_${j}.md" ]; then
            log "  ${BOLD}Iteration $j:${NC}"
            grep -E "^\|.*\|.*[0-9]+/10" "$ARCHIVE/critique_${j}.md" 2>/dev/null | while read -r line; do
                log "    $line"
            done
        fi
    done
fi

log ""
log "${CYAN}${BOLD}Timing summary:${NC}"
log "  Total elapsed: ${TOTAL_MINS}m ${TOTAL_SECS}s"
log "  Average per iteration: $(( TOTAL_ELAPSED / FINAL_ITERATION ))s"
log ""
log "${DIM}Full log saved to: $LOGFILE${NC}"
````

---

# Setup Instructions

To bootstrap the research loop in this repo:

```bash
# 1. Create directory structure
mkdir -p docs/exchanges/archive scripts

# 2. Extract the templates above into their respective files:
#    - docs/critique_prompt.md (from TEMPLATE section above)
#    - docs/researcher_prompt.md (from TEMPLATE section above)
#    - scripts/research_loop.sh (from TEMPLATE section above)

# 3. Make the script executable
chmod +x scripts/research_loop.sh

# 4. Create initial research log
echo "# RLM Research Log\n\n## Status: Starting\n\nNo experiments run yet." > docs/research_log.md

# 5. Run
./scripts/research_loop.sh 10        # 10 iterations, opus
./scripts/research_loop.sh 15 sonnet # 15 iterations, sonnet

# Monitor from another terminal:
tail -f docs/exchanges/archive/research_loop.log
```
