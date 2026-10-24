# BScout agent setup

The project-local `.codex/config.toml` sets session defaults; standalone agent
definitions live in `.codex/agents/*.toml`. These files configure future hosts
that support this format. They do not prove that the current host has loaded or
activated them. Skills under `.agents/skills/` add task instructions and do not
select a model. The model picker under the composer changes the primary model;
a request in chat text can guide a subagent, but does not switch the primary
model.

Default to direct execution in the main Sol chat for clear, small changes. Use
reader for substantial bounded exploration; use a separate coder only for useful
independent implementation. Use reviewer for meaningful risks or explicit review. The main agent owns integration and the
final result. Keep delegated prompts specific and request only necessary paths,
line numbers, decisions, and unresolved risks.

If an agent cannot run with its requested model, surface that fact and ask the user
before choosing a different model. Runtime metadata can help explain execution,
but self-reported model names are not proof of billing. Add optional skills or
tools only when a concrete future workflow needs them; none is required for the
current BScout setup.

## Current roles and example

- bscout_reader: gpt-6-luna / medium, evidence gathering without edits.
- bscout_prompt_master: gpt-6-luna / medium, prepares a brief for the orchestrator.
- bscout_coder: gpt-6.1-sol / low, implementation and focused checks.
- bscout_reviewer: gpt-6.1-sol / medium, optional review without edits.

## Budget-first examples

Small fix: "Fix this error directly and run the relevant checks. No subagents."

Investigation: "Have Luna reader locate the cause of the search filter issue.
Use its findings to implement the fix yourself; avoid a separate coder."

Large task: "Split only independent parts between agents, with separate file
ownership. Use prompt master if the requirements need clarification or a reusable
brief. Integrate and verify the result yourself."

Prompt preparation: "Have prompt master turn this large request and existing reader
findings into a concise brief for the Sol orchestrator. Do not implement it yet."

The main Sol chat remains selected through the composer; these project defaults
only select subagent models. The budget recommendation is Sol 6.1 / low for routine
work, with a reasoned effort change for complex tasks rather than repeated failed
attempts. This is guidance, not a programmatic switch of the current chat.
Do not launch every configured role for each task. Measure results and usage on
real project tasks; no savings percentage is established by these settings.

/subagents inspects running or completed agent threads; it does not install skills
or change the parent model. Skill names can be invoked with $skill-name. Newly
installed skills are available on the next turn; restart if the client misses them.
A role profile is only configuration until the host loads it. In a host without
custom role selection, the orchestrator can read the profile and explicitly pass
its model, effort and instructions, disclosing that fallback.

External coding skills are installed project-locally. Prefer relevant individual
rules rather than loading a whole rulebook. Their upstream guidance is not a reason
to upgrade React/Next or replace React Query, nor to override DESIGN.md or AGENTS.md.
The web-design-guidelines skill fetches its upstream guidelines during review;
that remote content is not pinned by the local skill installation.
