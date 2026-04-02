# Lessons Learned from Upgrading InScope and our Suite of Plugins

## Overview

This past quarter we upgraded our internal developer portal and all of its plugins to the latest versions. Along the way we hit framework-level bugs, discovered upstream breaking changes, and figured out a better process for doing this kind of work going forward. This was also the first project where I used an AI-powered work journal — logging progress, blockers, and resolutions conversationally through Claude Code instead of writing them up manually.

Here's what we learned.

---

## 1. Delegate, Collaborate, and Welcome New Perspectives

This project moved faster because I didn't try to do everything myself, and because the people who jumped in brought fresh thinking. Three things stood out:

**Collaboration increases throughput.** Upgrading 13 plugins is inherently parallelizable — each plugin is its own repo with its own tests and deployment. When teammates picked up plugins, we completed the entire development phase within the first week. The work lent itself to delegation, and we took advantage of that.

**New perspectives improve the process.** When I asked the team for help, one teammate tried a completely different approach to upgrading: instead of bumping dependency versions and ironing out the resulting bugs, he used AI to rebootstrap the plugins from scratch — starting with a fresh, fully updated Backstage environment and bringing the actual plugin code on top. This wasn't just faster; it was fundamentally better. It ensured parity between ephemeral and local dev environments, kept everything up to date by default, and set a new standard for how we do plugin upgrades going forward. Everyone has blind spots, and bringing in more teammates means more perspectives on the problem. What seems like an obvious approach to one person might not even occur to another — and that's exactly the point.

**Know when to call in the experts.** Weeks into the project, we hit a bug in stage that we couldn't resolve on our own. After a couple days of troubleshooting, I escalated to the RHDH team. They confirmed it was a framework-level issue on their end. Knowing when to stop debugging and hand it upstream saved us from spinning our wheels — and as I noted in my journal: "Big relief — takes the mental burden off our team."

## 2. Keep a Work Journal (and Let AI Do the Writing)

I've always known a work journal would be valuable — but I also knew I'd never keep up with one manually. You get busy, you get lazy, and the journal quietly dies within a week. The details that matter most (the dead ends, the root causes, the things you tried) are exactly the things that fade fastest, and they're the last thing you want to reconstruct at the end of a long day. So I didn't try to solve that with discipline. I solved it with AI.

The journal lives in a git repo as markdown files, and I interact with it entirely through a /journal Claude skill. I don't sit down and write up what I did. Instead, the journaling happens naturally as part of the work itself. When I'm debugging an issue in a Claude Code session, I can say "add this to my progress" or "mark that task done" and the journal updates. When I hit a blocker, I mention it in conversation and it gets recorded. When I resolve something, the resolution gets captured alongside the original problem — because Claude Code has the context of what I just fixed and why.

Designing the journal this way from the start — with AI as the primary interface — meant the barrier to entry was low enough that I actually used it. Not just during this project, but as a general part of my workflow. The plugin upgrade was where it proved its value most dramatically, but the habit stuck because it never felt like extra work.

Specific moments where this paid off during the plugin upgrade:

- **A plugin broken in production** — Early in the project I noticed one of our plugins was failing in production. I started debugging and captured my findings as I went. Weeks later when I circled back to it, my notes gave me the full context immediately — what I'd tried, what I'd ruled out, and where I'd left off. Without the journal, I'd have started the investigation over from scratch.

- **A config issue that came back** — While working on the platform upgrade, I discovered that a plugin's configuration needed to live in a specific file to work correctly. When the same issue resurfaced after deploying to stage, I already knew exactly where to look and what the fix was — because the original discovery was recorded with enough detail to act on immediately.

- **Understanding *why* something broke upstream** — The platform upgrade removed a set of plugins we depended on. I tracked down the upstream PR and documented not just what was removed but *why* — the maintainers were reducing their support burden. Weeks later, when it came time to fix it, the journal gave me the full picture and understanding the motivation made the solution obvious.

The bottom line: the journal was valuable because it was *actually maintained*, and it was actually maintained because AI removed the friction. Less context lost to forgetting means lessons can actually be learned from a project instead of just surviving it.

## 3. Document Follow-Up Work as You Go

During the project, we identified several improvements that weren't blocking the upgrade but would make future work smoother. Instead of trusting ourselves to remember them later, we documented them immediately:

- Automate dependency updates, keeping updates incremental instead of larger undertakings
- Streamline the release process with automated artifact creation
- Improve plugin UX for edge cases discovered during testing
- Flesh out test environment coverage for plugins that had gaps

These are the kinds of things that slip through the cracks after a big project wraps up and everyone moves on. Writing them down while the context is fresh means they actually make it onto the backlog.

---

## Conclusion

The thread running through all of this is that big projects don't succeed on technical skill alone. Asking for help — and being open when someone brings a better approach — got us a fundamentally improved upgrade process. Keeping a journal meant we could build on what we learned each day instead of rediscovering it. And documenting follow-ups in the journal while the context was fresh meant the work that came *after* the project didn't fall through the cracks.

A team effort upgraded 13 plugins and a major platform version in just a quarter. The work was possible because we stayed organized, stayed open to new ideas, and wrote things down.
