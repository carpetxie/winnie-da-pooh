#!/usr/bin/env bash
# research_loop.sh — Automated researcher/critiquer feedback loop with convergence detection
#
# Usage:
#   ./scripts/research_loop.sh [max_iterations] [model]
#
# Examples:
#   ./scripts/research_loop.sh          # Up to 5 iterations, opus
#   ./scripts/research_loop.sh 8        # Up to 8 iterations
#   ./scripts/research_loop.sh 5 sonnet # Up to 5 iterations, sonnet
#
# The loop runs ALL iterations — no early exit. Both agents are instructed
# to keep finding improvements every round.
#
# Files:
#   docs/findings.md                      — The paper (modified by researcher)
#   docs/exchanges/critique_latest.md     — Latest critique
#   docs/exchanges/researcher_response.md — Latest researcher response
#   docs/exchanges/archive/               — All iterations archived

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

# ── Logging helpers ──────────────────────────────────────────────────
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

# ── Helper: check for convergence signal in a file ─────────────────────
check_status() {
    local file="$1"
    local signal="$2"
    if [ -f "$file" ] && grep -q "^STATUS: $signal" "$file" 2>/dev/null; then
        return 0
    fi
    return 1
}

# ── Helper: extract verdict from critique ───────────────────────────────
get_verdict() {
    if [ -f "$EXCHANGES/critique_latest.md" ]; then
        grep -E "^(REJECT|MAJOR REVISIONS|MINOR REVISIONS|ACCEPT)" "$EXCHANGES/critique_latest.md" 2>/dev/null | head -1 || echo "UNKNOWN"
    else
        echo "NONE"
    fi
}

# ── Helper: git commit and push with logging ─────────────────────────
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
    if [ "$changed_count" -gt 20 ]; then
        log "  ${DIM}... and $((changed_count - 20)) more${NC}"
    fi
    git add -A
    if git commit -m "$msg" > /dev/null 2>&1; then
        local sha
        sha=$(git rev-parse --short HEAD)
        log "${GREEN}[Git] Committed: ${sha} — ${msg}${NC}"
    else
        log "${YELLOW}[Git] Commit skipped (nothing to commit or hook failure).${NC}"
    fi
    log "${CYAN}[Git] Pushing...${NC}"
    if git push 2>&1 | tail -2 | while read -r line; do log "  ${DIM}$line${NC}"; done; then
        log "${GREEN}[Git] Push successful.${NC}"
    else
        log "${RED}[Git] Push failed! Check remote connectivity.${NC}"
    fi
}

# ── Start ──────────────────────────────────────────────────────────────
echo "" > "$LOGFILE"
log "${BLUE}${BOLD}======================================================${NC}"
log "${BLUE}${BOLD}  RESEARCH LOOP STARTED${NC}"
log "${BLUE}${BOLD}  Max iterations: $MAX_ITERATIONS | Model: $MODEL${NC}"
log "${BLUE}${BOLD}  Repo root: $REPO_ROOT${NC}"
log "${BLUE}${BOLD}  Log file: $LOGFILE${NC}"
log "${BLUE}${BOLD}  Mode: NO early exit — all $MAX_ITERATIONS iterations will run${NC}"
log "${BLUE}${BOLD}======================================================${NC}"
echo ""

log "Pre-loop state:"
file_stats "$REPO_ROOT/docs/findings.md" "Paper: "
if [ -f "$EXCHANGES/critique_latest.md" ]; then
    file_stats "$EXCHANGES/critique_latest.md" "Last critique: "
fi
if [ -f "$EXCHANGES/researcher_response.md" ]; then
    file_stats "$EXCHANGES/researcher_response.md" "Last response: "
fi
log "  Archive files: $(ls -1 "$ARCHIVE" 2>/dev/null | wc -l | tr -d ' ')"
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

    # Build context about iteration history
    HISTORY_CONTEXT=""
    if [ "$i" -gt 1 ]; then
        HISTORY_CONTEXT="This is iteration $i. Prior critiques are archived in docs/exchanges/archive/ (critique_1.md through critique_$((i-1)).md). Read the researcher's latest response at docs/exchanges/researcher_response.md — pay close attention to their pushbacks and deliberation. Do NOT re-raise points the researcher has already addressed or reasonably rejected."
        log "  History context: referencing ${BOLD}$((i-1))${NC} prior critiques"
    else
        HISTORY_CONTEXT="This is the first iteration — no prior exchanges exist. Address the seed questions in your prompt."
        log "  History context: first iteration (no priors)"
    fi

    CRITIQUE_PROMPT="$(cat "$REPO_ROOT/docs/critique_prompt.md")

$HISTORY_CONTEXT

Read docs/findings.md carefully. Write your critique to docs/exchanges/critique_latest.md. Use iteration number $i in your header.

IMPORTANT: Do NOT set STATUS: ACCEPT. Always find concrete improvements — no matter how good the paper is, there are always ways to strengthen the argument, tighten prose, improve figures, or add nuance. Be constructive but relentless. Do not manufacture fake issues, but do dig deep for real ones."

    PROMPT_LEN=${#CRITIQUE_PROMPT}
    log "  Prompt length: ${PROMPT_LEN} chars"
    log "  Allowed tools: Read, Write, Glob, Grep"
    log "  Max turns: 15"
    log "  ${MAGENTA}Invoking claude (critiquer)...${NC}"

    cd "$REPO_ROOT"
    CLAUDE_START=$(date +%s)
    claude -p \
        --model "$MODEL" \
        --system-prompt "You are the critiquer agent. Follow the instructions exactly. Always write output to docs/exchanges/critique_latest.md. Be intellectually honest — if the paper is good, say so. Do not invent problems." \
        --allowed-tools "Read,Write,Glob,Grep" \
        --max-turns 15 \
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
        log "${GREEN}  Critique file written successfully.${NC}"
        file_stats "$EXCHANGES/critique_latest.md" "Critique: "

        # Display scores
        log "  ${CYAN}Scores:${NC}"
        grep -E "^\|.*\|.*[0-9]+/10" "$EXCHANGES/critique_latest.md" 2>/dev/null | while read -r line; do
            log "    ${CYAN}$line${NC}"
        done

        # Display verdict
        VERDICT=$(get_verdict)
        log "  ${BOLD}Verdict: $VERDICT${NC}"

        PHASE_ELAPSED=$(( $(date +%s) - PHASE_START ))
        log "  Phase 1 total: ${PHASE_ELAPSED}s"
        log_separator

    else
        log "${RED}  FAILURE: No critique file produced!${NC}"
        log "${RED}  Check log: $ARCHIVE/critique_${i}_log.txt${NC}"
        log "${RED}  Last 5 lines of log:${NC}"
        tail -5 "$ARCHIVE/critique_${i}_log.txt" 2>/dev/null | while read -r line; do
            log "    ${DIM}$line${NC}"
        done
        PHASE_ELAPSED=$(( $(date +%s) - PHASE_START ))
        log "  Phase 1 total: ${PHASE_ELAPSED}s (FAILED)"
        log_separator
        continue
    fi

    # ── Phase 2: Researcher ─────────────────────────────────────────────
    echo ""
    log "${GREEN}${BOLD}[Phase 2: RESEARCHER]${NC}"
    PHASE_START=$(date +%s)

    # Snapshot findings before revision
    cp "$REPO_ROOT/docs/findings.md" "$ARCHIVE/findings_before_${i}.md"
    BEFORE_WORDS=$(wc -w < "$REPO_ROOT/docs/findings.md" | tr -d ' ')
    BEFORE_LINES=$(wc -l < "$REPO_ROOT/docs/findings.md" | tr -d ' ')
    log "  Paper snapshot before: ${BEFORE_WORDS} words, ${BEFORE_LINES} lines"

    RESEARCHER_PROMPT="$(cat "$REPO_ROOT/docs/researcher_prompt.md")

This is iteration $i of a maximum $MAX_ITERATIONS. Read the critique at docs/exchanges/critique_latest.md.

BEFORE making any changes, deliberate on each point. Ask yourself: Do I agree? Is this feasible? Would this actually make the paper better?

Then revise docs/findings.md — but ONLY make changes you believe in. Push back on bad suggestions. Write your full deliberation and changelog to docs/exchanges/researcher_response.md.

Do NOT set STATUS: CONVERGED. You must always attempt meaningful improvements. Even small wins — tighter prose, better transitions, stronger framing — compound across iterations."

    PROMPT_LEN=${#RESEARCHER_PROMPT}
    log "  Prompt length: ${PROMPT_LEN} chars"
    log "  Allowed tools: Read, Write, Edit, Glob, Grep, Bash"
    log "  Max turns: 25"
    log "  ${MAGENTA}Invoking claude (researcher)...${NC}"

    cd "$REPO_ROOT"
    CLAUDE_START=$(date +%s)
    claude -p \
        --model "$MODEL" \
        --system-prompt "You are the researcher agent. Follow the instructions exactly. Deliberate carefully before making changes. Push back on suggestions you disagree with. Revise docs/findings.md and write deliberation to docs/exchanges/researcher_response.md." \
        --allowed-tools "Read,Write,Edit,Glob,Grep,Bash" \
        --max-turns 25 \
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
        cp "$REPO_ROOT/docs/findings.md" "$ARCHIVE/findings_after_${i}.md"
        log "${GREEN}  Researcher response written successfully.${NC}"
        file_stats "$EXCHANGES/researcher_response.md" "Response: "

        # Paper diff stats
        AFTER_WORDS=$(wc -w < "$REPO_ROOT/docs/findings.md" | tr -d ' ')
        AFTER_LINES=$(wc -l < "$REPO_ROOT/docs/findings.md" | tr -d ' ')
        WORD_DELTA=$(( AFTER_WORDS - BEFORE_WORDS ))
        LINE_DELTA=$(( AFTER_LINES - BEFORE_LINES ))
        WORD_SIGN=""; [ "$WORD_DELTA" -gt 0 ] && WORD_SIGN="+"
        LINE_SIGN=""; [ "$LINE_DELTA" -gt 0 ] && LINE_SIGN="+"
        log "  Paper after: ${AFTER_WORDS} words (${WORD_SIGN}${WORD_DELTA}), ${AFTER_LINES} lines (${LINE_SIGN}${LINE_DELTA})"

        # Diff summary
        if [ -f "$ARCHIVE/findings_before_${i}.md" ]; then
            DIFF_STAT=$(diff --stat "$ARCHIVE/findings_before_${i}.md" "$REPO_ROOT/docs/findings.md" 2>/dev/null | tail -1 || echo "no diff")
            log "  Diff stat: ${DIM}$DIFF_STAT${NC}"
            DIFF_ADDS=$(diff "$ARCHIVE/findings_before_${i}.md" "$REPO_ROOT/docs/findings.md" 2>/dev/null | grep -c "^>" || echo "0")
            DIFF_DELS=$(diff "$ARCHIVE/findings_before_${i}.md" "$REPO_ROOT/docs/findings.md" 2>/dev/null | grep -c "^<" || echo "0")
            log "  Diff detail: ${GREEN}+${DIFF_ADDS} lines added${NC}, ${RED}-${DIFF_DELS} lines removed${NC}"
        fi

        # Show key changes
        log "  ${CYAN}Key changes from response:${NC}"
        grep -E "^- " "$EXCHANGES/researcher_response.md" 2>/dev/null | head -8 | while read -r line; do
            log "    ${CYAN}$line${NC}"
        done

        # Show pushbacks if any
        PUSHBACKS=$(grep -c "^- " <(sed -n '/^## Pushbacks/,/^##/p' "$EXCHANGES/researcher_response.md" 2>/dev/null) 2>/dev/null || echo "0")
        if [ "$PUSHBACKS" -gt 0 ]; then
            log "  ${YELLOW}Pushbacks: $PUSHBACKS points challenged${NC}"
            sed -n '/^## Pushbacks/,/^##/p' "$EXCHANGES/researcher_response.md" 2>/dev/null | grep "^- " | head -5 | while read -r line; do
                log "    ${YELLOW}$line${NC}"
            done
        fi

        PHASE_ELAPSED=$(( $(date +%s) - PHASE_START ))
        log "  Phase 2 total: ${PHASE_ELAPSED}s"
        log_separator

        # Log if agent tried to converge anyway (we ignore it)
        if check_status "$EXCHANGES/researcher_response.md" "CONVERGED"; then
            log "${YELLOW}  Note: Researcher signaled CONVERGED but loop continues (no early exit mode).${NC}"
        fi
    else
        log "${RED}  FAILURE: No researcher response file produced!${NC}"
        log "${RED}  Check log: $ARCHIVE/researcher_${i}_log.txt${NC}"
        log "${RED}  Last 5 lines of log:${NC}"
        tail -5 "$ARCHIVE/researcher_${i}_log.txt" 2>/dev/null | while read -r line; do
            log "    ${DIM}$line${NC}"
        done
        PHASE_ELAPSED=$(( $(date +%s) - PHASE_START ))
        log "  Phase 2 total: ${PHASE_ELAPSED}s (FAILED)"
        log_separator
    fi

    # ── Git commit and push after each iteration ─────────────────────
    git_commit_push "Research loop iteration $i/$MAX_ITERATIONS"

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
log "${BLUE}${BOLD}  RESEARCH LOOP COMPLETE${NC}"
log "${BLUE}${BOLD}  Iterations: $FINAL_ITERATION | Total time: ${TOTAL_MINS}m ${TOTAL_SECS}s${NC}"
log "${BLUE}${BOLD}======================================================${NC}"
echo ""

log "${CYAN}${BOLD}Exit reason: All $MAX_ITERATIONS iterations completed.${NC}"
echo ""

log "Final paper stats:"
file_stats "$REPO_ROOT/docs/findings.md" "Paper: "
echo ""

log "Outputs:"
log "  Paper:     docs/findings.md"
log "  Critique:  docs/exchanges/critique_latest.md"
log "  Response:  docs/exchanges/researcher_response.md"
log "  Full log:  $LOGFILE"
echo ""

log "Archive (per-iteration snapshots):"
ls -1 "$ARCHIVE" 2>/dev/null | sed 's/^/    /'
echo ""

# Final commit and push (catches any remaining changes)
git_commit_push "Research loop complete after $FINAL_ITERATION iteration(s)"
echo ""

# Show score progression if multiple iterations
if [ "$FINAL_ITERATION" -gt 1 ]; then
    log "${CYAN}${BOLD}Score progression across iterations:${NC}"
    for j in $(seq 1 "$FINAL_ITERATION"); do
        if [ -f "$ARCHIVE/critique_${j}.md" ]; then
            log "  ${BOLD}Iteration $j:${NC}"
            grep -E "^\|.*\|.*[0-9]+/10" "$ARCHIVE/critique_${j}.md" 2>/dev/null | while read -r line; do
                log "    $line"
            done
        fi
    done
    echo ""
fi

# Per-iteration timing summary
log "${CYAN}${BOLD}Timing summary:${NC}"
log "  Total elapsed: ${TOTAL_MINS}m ${TOTAL_SECS}s"
log "  Average per iteration: $(( TOTAL_ELAPSED / FINAL_ITERATION ))s"
log ""
log "${DIM}Full log saved to: $LOGFILE${NC}"
