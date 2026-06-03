#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

tmpdir=$(make_tmpdir)
home_dir="$tmpdir/home"
bin_dir="$tmpdir/bin"
mkdir -p "$home_dir/.codex"
prepare_codex_installer_bin "$bin_dir"
write_stub_curl "$bin_dir" "# T-skills Routing\n\nrouting table body\n"

# Claude Code target drops the rule into ~/.claude/rules/ as a standalone file
# (same path used by english / anti-patterns). Marker label override keeps the
# Codex block name as <!-- T-skills Routing --> instead of <!-- T-skills T-skills Routing -->.
PATH="$bin_dir" HOME="$home_dir" /bin/bash "$ROOT/scripts/setup-rule.sh" t-skills-routing claude-code >"$tmpdir/claude.out"
grep -q 'routing table body' "$home_dir/.claude/rules/t-skills-routing.md"

# Codex target uses marker injection. Idempotent on re-run.
PATH="$bin_dir" HOME="$home_dir" /bin/bash "$ROOT/scripts/setup-rule.sh" t-skills-routing codex >"$tmpdir/codex1.out"
PATH="$bin_dir" HOME="$home_dir" /bin/bash "$ROOT/scripts/setup-rule.sh" t-skills-routing codex >"$tmpdir/codex2.out"
test "$(grep -c '<!-- T-skills Routing: start -->' "$home_dir/.codex/AGENTS.md")" -eq 1
grep -q 'routing table body' "$home_dir/.codex/AGENTS.md"

echo "T-skills Routing installer smoke: ok"
