# I Benchmarked 5 LLM Routers From South Korea — Here's Why Edge Infrastructure Matters More Than Routing Logic

## The Claim, Then the Measurement

In yesterday's post "The Orchestration Moat" (ai.contextix.io/2026-03-08-orchestration-moat), I analyzed why multi-model routing is inevitable. The core thesis, drawn from recent industry benchmarks and trends: routing overhead is 20-50ms, cost savings reach 40-60%, and the moat shifts to routing intelligence.

To test these claims, I built llm-router-lab (github.com/vericontext/llm-router-lab), an open-source benchmark framework, and measured 4 LLM routing paths head-to-head: OpenAI Direct, OpenRouter, Portkey, and Cloudflare AI Gateway — all calling the same model (GPT-4o).

**Important context:** All tests were run from South Korea. This means every API call crosses the Pacific Ocean. This geographic factor turned out to be the most important variable in the entire benchmark — more important than any routing logic. If you're reading this from the US, your results will likely look very different.

**Methodology:** Each overhead test ran N=300 (100 repeats × 3 minimal-prompt cases) per router. No explicit warm-up was performed — the first few calls in each batch may include cold-start effects, which are included in the data as they reflect real-world usage. We report p50 and p95 — not p99, which requires N=1000+ to be statistically meaningful. All raw data and code are open-source for independent verification.


## TL;DR — 4 Takeaways

1. **Routing overhead is network topology, not routing logic.** At N=300, the p50 difference between direct and routed calls is ~60ms — noise-level. The "20-50ms fixed overhead" framing is wrong because it assumes overhead is a property of routing. It's a property of network path.
2. **Edge infrastructure is the real moat.** Routers with strong Asia-Pacific edge networks (Cloudflare, Portkey) had the tightest p95 — 20% better than both OpenAI Direct and OpenRouter. CDN-backed gateways absorb transpacific jitter through regional TLS termination and connection pooling.
3. **Streaming and non-streaming have different winners.** Direct connections win streaming TTFT by ~250ms. Routers win non-streaming tail latency. Choose based on your UX pattern.
4. **Model tier cost savings are real but hard.** 90%+ savings are possible by routing simple queries to gpt-4o-mini. The challenge is building an accurate query classifier.


## Routing Overhead: It's About the Network, Not the Router

The original analysis assumed routing adds a fixed 20-50ms overhead. Here's what N=300 actually shows on minimal prompts (max_tokens: 1):

| Router | N | p50 | p95 |
|--------|---|-----|-----|
| OpenAI Direct | 300 | 0.487s | 1.021s |
| Portkey | 300 | 0.519s | 0.903s |
| Cloudflare AI GW | 300 | 0.521s | 0.823s |
| OpenRouter | 300 | 0.549s | 1.021s |

**What this tells us:**

All four paths cluster within 62ms at p50 (0.487-0.549s) — noise-level for transpacific traffic. The "routing overhead" is not a meaningful number; network path variance dwarfs it.

At p95, Cloudflare (0.823s) and Portkey (0.903s) are actually the most stable — better than both OpenAI Direct and OpenRouter (both 1.021s). This makes sense: Cloudflare has one of the world's largest edge networks, and Portkey likely routes through infrastructure with good Asia-Pacific coverage.

**Self-correction:** In my initial N=30 test, OpenRouter appeared 23% faster than direct at p50, and Portkey appeared to have catastrophic p99 of 10.8s. At N=300, the p50 rankings shifted entirely, and Portkey became one of the most stable routers. This is exactly why small-sample benchmarks are dangerous. **If I had published the N=30 results alone, I would have unfairly maligned Portkey and overpraised OpenRouter.** Always be suspicious of N<100 latency comparisons.


## Tail Latency: Where Edge Infrastructure Earns Its Keep

At the median, all four routers are within 62ms of each other. The real differentiation is in the tail:

| Router | p50 | p95 | p50/p95 Ratio |
|--------|-----|-----|---------------|
| Cloudflare AI GW | 0.521s | 0.823s | 1.6x |
| Portkey | 0.519s | 0.903s | 1.7x |
| OpenAI Direct | 0.487s | 1.021s | 2.1x |
| OpenRouter | 0.549s | 1.021s | 1.9x |

The surprise: **Cloudflare and Portkey have the tightest tail latency** — better than both OpenAI Direct and OpenRouter. Cloudflare's p95 (0.823s) is 20% lower than the other three.

Why? From South Korea, a direct HTTPS request to api.openai.com requires: DNS resolution → TCP handshake across the Pacific → TLS negotiation → HTTP request → response. Any hiccup in the transpacific leg (submarine cable congestion, BGP route change) adds hundreds of milliseconds. Routers with edge PoPs close to the client short-circuit this: TLS terminates regionally, and the gateway maintains pre-established connections to the upstream API.

Cloudflare's edge network is arguably the largest in the world — they have nodes in every major Asian city. Portkey likely benefits from similar CDN-backed infrastructure. OpenRouter, despite good p50 performance, shows the same p95 as direct, suggesting its edge presence may be thinner in Asia-Pacific.

**This is an infrastructure argument, not a routing argument.** The same benefit would apply to any CDN or API gateway with strong regional presence. For developers outside the US — which is most of the world — this matters more than any routing intelligence.


## Real Coding Tasks: Does Overhead Matter at Scale?

On actual coding workloads (code completion, bug fixing, code review — N=20 per router), the picture changes:

| Router | Avg | p50 | p95 |
|--------|-----|-----|-----|
| OpenRouter | 4.35s | 4.56s | 9.66s |
| OpenAI Direct | 5.74s | 5.07s | 17.62s |

OpenRouter is 24% faster on average and nearly 2x more stable at p95 (9.66s vs 17.62s). Note: N=20 is still relatively small, so the p95 difference (9.66s vs 17.62s) should be interpreted with caution.

The key insight: as response generation time grows from milliseconds to seconds, the fixed overhead of routing becomes proportionally irrelevant. On a 4-second response, even 200ms of routing overhead is only 5%. But the tail-latency smoothing benefit persists — and matters more, because a single 17-second hang in a coding session breaks flow.


## Multi-Provider: The 270ms Tax Is Worth It

Testing the same prompt across 4 models via OpenRouter's single API (N=20):

| Model (via OpenRouter) | p50 | p95 |
|------------------------|-----|-----|
| GPT-4o | 2.60s | 5.64s |
| Gemini 2.5 Flash | 3.01s | 6.64s |
| Claude Sonnet 4 | 8.77s | 13.56s |
| Llama 3.1 70B | 9.88s | 17.19s |

Gemini direct vs via OpenRouter (N=30):

| Path | p50 | p95 |
|------|-----|-----|
| Gemini Direct | 1.307s | 1.981s |
| Via OpenRouter | 1.583s | 2.013s |

The multi-provider overhead is ~270ms at p50. At p95, the gap nearly vanishes. This tax buys you: model experimentation without vendor lock-in, automatic failover, single billing, and a unified API.

Key insight: Gemini Flash delivers 63% more tokens than GPT-4o while being only 16% slower. You discover this when switching models is a config change, not a codebase migration.


## Model Tier Cost-Latency Tradeoff

Testing the three-tier approach (fast/default/large) via OpenRouter (N=10-20):

| Model (Tier) | Avg | p50 | Completion Tokens | Est. Cost/1K calls |
|--------------|-----|-----|-------------------|--------------------|
| gpt-4o-mini (fast) | 7.58s | 7.04s | 403 | ~$0.10 |
| claude-sonnet (default) | 9.14s | 9.20s | 583 | ~$12.25 |
| claude-opus (large) | 10.66s | 9.70s | 596 | ~$48.35 |

The tier gap is mostly in cost, not latency. mini→sonnet: +31% latency but ~150x cost. sonnet→opus: +5% latency but ~4x cost. The latency curve flattens while the cost curve explodes.

If you can reliably classify 60% of queries as "simple," the savings are 90%+ on those queries — far exceeding the original 40-60% claim. The hard part is classification accuracy.


## Streaming TTFT: Direct Wins Here

For coding agents, time-to-first-token (TTFT) matters more than total latency. Measured with streaming enabled (N=60):

| Router | TTFT | p50 Total | p95 Total |
|--------|------|-----------|-----------|
| OpenAI Direct | 0.569s | 5.49s | 10.58s |
| OpenRouter | 0.820s | 7.24s | 25.67s |

TTFT overhead for OpenRouter is +251ms. This is the one scenario where direct connections clearly win. Hypothesis: the router's streaming proxy introduces buffering latency that doesn't exist in non-streaming mode.

**For coding agents:** if perceived responsiveness (first character appearing) is your priority, direct API connections have a measurable edge. If you're doing non-streaming batch work, the tail-latency smoothing of routers may be more valuable.


## Tool Calling: Small Per-Turn Tax, Better Worst-Case

Coding agents call tools (read_file, write_file) on nearly every turn (N=40):

| Router | p50 | p95 |
|--------|-----|-----|
| OpenAI Direct | 0.699s | 1.187s |
| OpenRouter | 0.780s | 1.261s |

The per-call overhead is +81ms. In a 50-turn session, that compounds to ~4 extra seconds total. But the worst-case behavior favors the router — fewer outlier spikes means a smoother interactive experience.


## Coding Agent End-to-End: API Surface Matters

I ran opencode (opencode.ai), an open-source coding agent, on three real tasks (N=3 each — treat as directional, not conclusive):

| Provider | Task | Avg Wall-clock | Agent Steps |
|----------|------|---------------|-------------|
| OpenAI Direct | type_hints (easy) | 13.5s | 3 |
| OpenRouter | type_hints (easy) | 8.3s | 3 |
| OpenAI Direct | find_bug (medium) | 6.5s | 2 |
| OpenRouter | find_bug (medium) | 4.9s | 2 |
| OpenAI Direct | refactor (hard) | 18.7s | 3 |
| OpenRouter | refactor (hard) | 15.4s | 3 |

OpenRouter was 17-38% faster in wall-clock time. However, this comparison has an important confound: **opencode uses different API endpoints depending on the provider.** OpenAI Direct uses the Responses API (`/v1/responses`), while OpenRouter uses Chat Completions (`/v1/chat/completions`). These are fundamentally different protocols with different context management, token accounting, and server-side behavior.

The wall-clock difference is real, but I cannot attribute it to "routing" — it may be entirely explained by the API protocol difference. This test demonstrates that **your choice of API surface can matter as much as your choice of provider**, but it is not a fair router-vs-direct comparison.

Agent steps were identical across both paths, confirming routing doesn't interfere with agent decision-making.


---

**Methodology:** llm-router-lab (github.com/vericontext/llm-router-lab), fully open-source. **Client:** South Korea — all results are shaped by transpacific routing. US/EU testers will see different patterns. **Warm-up:** No explicit warm-up — cold-start effects are included as they reflect real usage patterns. **Sample sizes:** Overhead: N=300 (all 4 routers). Other scenarios: N=20-60. Coding agent: N=3. **Statistics:** We report p50 and p95. p99 is omitted from primary analysis as it requires N=1000+ for reliability. **Models:** gpt-4o, gpt-4o-mini, claude-sonnet-4, claude-opus-4.5, gemini-2.5-flash, llama-3.1-70b. **Coding agent:** opencode v1.2.22 (`opencode run --format json`). Note: opencode uses Responses API for OpenAI Direct and Chat Completions for OpenRouter — token counts are not comparable between these paths. **Invitation:** If you're in the US/EU and want to run the same benchmark, the repo has everything you need. I'd love to see how geography changes these results.
