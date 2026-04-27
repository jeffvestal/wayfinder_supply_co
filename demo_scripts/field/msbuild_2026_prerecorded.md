# MS Build 2026 Session — Pre-Recorded Backup Plan

**Purpose:** If conference wifi fails, the Elastic Workflow is down, or the agent stalls live, switch to this script and play the pre-recorded demo over the PA.

---

## Recording Capture Order

Record the full live flow from `msbuild_2026_25min.md` with these caps:

| Segment | Length cap | Notes |
|---|---|---|
| Open PR (Scene 3) | 1:30 | Cut the PR-create network roundtrip — jump cut |
| Agent comment appears (Scene 4) | 2:00 | Edit out the wait; show create → cut → comment |
| VS Code trace query (Scene 5) | 2:30 | Keep the MCP tool call visible in the UI |
| Fix applied + saved (Scene 5) | 1:00 | Show the diff before/after in a single frame |
| Concurrency proof (Scene 6) | 1:00 | Clean terminal, readable font size |

Target total: ~8 min. Record at 1920×1080, 60fps. Export MP4 H.264.

---

## Fallback Triggers

Switch to pre-recorded if any of these happen on stage:

- Agent comment does not appear within 3 minutes of PR open.
- `gh pr create` returns 5xx or times out twice.
- Copilot Agent Mode returns no content for either prompt.
- Wifi drops (any request fails with DNS/timeout).
- Harness L1 fails mid-demo.

---

## On-Stage Script When Switching to Backup

1. **Stop whatever is failing.** Do not keep retrying live.
2. Say: "Let me show you this from a recording I made earlier — same system, same agent, same result."
3. Start the MP4.
4. **Narrate over it.** Do not re-read the 25-min script verbatim — summarize each beat in 1-2 sentences as it plays. This is the segment of the talk where your narration, not the live system, carries the story.
5. After the recording ends, jump to Scene 7 (Close) of the live script.

Do not attempt to recover the live demo mid-session. One attempt, one fallback — clean cut.

---

## Pre-Flight for the Backup Itself

Day-of:
- [ ] MP4 mirrored on laptop + USB + cloud.
- [ ] Audio levels tested on the conference PA.
- [ ] Playback tested at full-screen on the actual stage monitor (not the confidence monitor).
- [ ] Captions burned in (not sidecar .srt) — room projectors often strip subtitle tracks.
