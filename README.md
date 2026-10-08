<div align="center">
  <h1>🐯 T-skills</h1>
  <p><b>Engineering habits you already know, turned into skills AI agents can run.</b></p>
</div>

<br/>

## What

T-skills is a personal collection of eight skills for Claude Code and Codex. Each one drills a single engineering habit, sets a clear goal and the constraints that matter, then lets the model do what it does best. Every skill output starts with a 🐯 marker so you can tell at a glance which skill is running.

## Skills

| Skill | When | What it does |
| :--- | :--- | :--- |
| `/think` | Before building anything new | Pressure-tests the design and produces a decision-complete plan. |
| `/design` | Building frontend interfaces | Produces distinctive UI with a committed direction, not generic defaults. |
| `/check` | After a task, before merging or release | Reviews the diff, extracts project constraints, handles release follow-through. |
| `/hunt` | Any bug, regression, or unexpected behavior | Systematic debugging; root cause confirmed before any fix. |
| `/write` | Writing or editing prose | Rewrites prose to sound natural in Chinese and English. |
| `/learn` | Diving into an unfamiliar domain | Six-phase research workflow: collect, digest, outline, fill in, refine, publish. |
| `/read` | Any URL or PDF | Fetches content with platform-specific routing; summary or clean Markdown. |
| `/health` | Auditing agent health | Checks Claude/Codex/Pi config, verifier output, and AI maintainability. |

## Install

**Claude Code**

```bash
npx skills add tanglei168/T-skills -a claude-code -g -y
```

Install just one with `npx skills add tanglei168/T-skills --skill think -a claude-code -g -y`.

**Codex**

```bash
npx skills add tanglei168/T-skills -a codex -g -y
```

**Update**

```bash
npx skills update -g -y
```

## Personal video skills

[家庭手账记录片](personal-skills/family-scrapbook-video/SKILL.md) preserves the approved family video style: clear activity themes, complete original framing, scrapbook cards and doodles, cheerful music, and full children’s greetings and birthday moments. The directory contains reusable instructions, design assets, and a scaffold helper; family footage and music are kept locally.

Install this optional skill for Codex:

```bash
npx skills add https://github.com/tanglei168/T-skills/tree/main/personal-skills/family-scrapbook-video --skill family-scrapbook-video -a codex -g -y
```

[Manus 风格产品发布片](personal-skills/manus-style-launch-video/SKILL.md) (v2.1.0) turns product facts and real interfaces into an editable HyperFrames project and MP4. It includes English copy and UI checks, continuous music phrasing, Muse/Skillry reference comparisons, and helpers for timeline validation, local rendering, and soundtrack replacement. This is an independently authored workflow; third-party music and machine-specific runtime paths are excluded.

Install this optional skill for Codex:

```bash
npx skills add https://github.com/tanglei168/T-skills/tree/main/personal-skills/manus-style-launch-video --skill manus-style-launch-video -a codex -g -y
```

`metadata.internal: true` keeps these optional skills out of the default eight-skill engineering install; selecting one by name includes it. They are maintained separately from the engineering release ZIP.

## Credits

T-skills is derived from [Waza](https://github.com/tw93/Waza) by Tw93, used under the MIT License. The skill set, validation, codegen, and packaging machinery originate there; see `LICENSE` for attribution. Thanks to the original author.

## License

MIT License. See [LICENSE](LICENSE).
