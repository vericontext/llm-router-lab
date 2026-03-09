# I Benchmarked 4 LLM Routers From South Korea — Here's Why Edge Infrastructure Matters More Than Routing Logic

## The Claim, Then the Measurement

In yesterday's post "The Orchestration Moat" (ai.contextix.io/2026-03-08-orchestration-moat), I analyzed why multi-model routing is inevitable. The core thesis, drawn from recent industry benchmarks and trends: routing overhead is 20-50ms, cost savings reach 40-60%, and the moat shifts to routing intelligence.

To test these claims, I built llm-router-lab (github.com/vericontext/llm-router-lab), an open-source benchmark framework, and measured 4 LLM routing paths head-to-head: OpenAI Direct, OpenRouter, Portkey, and Cloudflare AI Gateway — all calling the same model (GPT-4o).

**Important context:** All tests were run from South Korea. Every API call crosses the Pacific Ocean. This geographic factor turned out to be the most important variable in the entire benchmark — more important than any routing logic. Readers in the US will likely see a different picture, though the relative patterns (edge infrastructure advantage, tail-latency smoothing) should hold directionally.

**Methodology:** Each overhead test ran N=300 (100 repeats × 3 minimal-prompt cases) per router. No explicit warm-up was performed — cold-start effects are included as they reflect real-world usage. We report p50 and p95 — not p99, which requires N=1000+ to be statistically meaningful. All raw data and code are open-source for independent verification.

**A note on "edge infrastructure":** Throughout this post, "edge" refers to CDN-style network infrastructure — regional TLS termination and connection pooling at PoPs close to the client. The LLM inference itself still runs in centralized data centers. This is not "edge AI" (running models on-device). The edge only handles the network handshake; the model runs where it always does.


## TL;DR — 4 Takeaways

1. **Routing overhead is network topology, not routing logic.** At N=300, the p50 difference between direct and routed calls is ~60ms — noise-level. The "20-50ms fixed overhead" framing is wrong because it assumes overhead is a property of routing. It's a property of the network path between you, the router, and the model provider.
2. **Edge infrastructure is the real moat — but it's two-sided.** Routers with strong client-side edge networks (Cloudflare, Portkey) had the tightest p95 for OpenAI calls. But router-to-provider backend connectivity also matters: the same router showed different overhead for OpenAI vs Gemini, depending on its backend path to each provider.
3. **Streaming and non-streaming have different winners.** Direct connections win streaming TTFT by ~250ms. Routers win non-streaming tail latency. Choose based on your UX pattern.
4. **Model tier cost savings are real but hard.** 90%+ savings are possible by routing simple queries to gpt-4o-mini — and edge-backed routers let you implement multi-tier strategies without adding latency.


## Routing Overhead: It's About the Network, Not the Router

The original analysis assumed routing adds a fixed 20-50ms overhead. Here's what N=300 actually shows on minimal prompts (max_tokens: 1):

| Router | N | p50 | p95 |
|--------|---|-----|-----|
| OpenAI Direct | 300 | 0.487s | 1.021s |
| Portkey | 300 | 0.519s | 0.903s |
| Cloudflare AI GW | 300 | 0.521s | 0.823s |
| OpenRouter | 300 | 0.549s | 1.021s |

All four paths cluster within 62ms at p50 (0.487-0.549s) — noise-level for transpacific traffic. The "routing overhead" is not a meaningful fixed number; network path variance dwarfs it.

At p95, Cloudflare (0.823s) and Portkey (0.903s) are actually the most stable — better than both OpenAI Direct and OpenRouter (both 1.021s). This makes sense: Cloudflare has one of the world's largest edge networks, and Portkey likely routes through infrastructure with good Asia-Pacific coverage.

**Self-correction:** In my initial N=30 test, OpenRouter appeared 23% faster than direct at p50, and Portkey appeared to have catastrophic tail latency of 10.8s. At N=300, the p50 rankings shifted entirely, and Portkey became one of the most stable routers. **If I had published the N=30 results alone, I would have unfairly maligned Portkey and overpraised OpenRouter.** Always be suspicious of N<100 latency comparisons.


## Tail Latency: Where Edge Infrastructure Earns Its Keep

At the median, all four routers are within 62ms of each other. The real differentiation is in the tail:

| Router | p50 | p95 | p50/p95 Ratio |
|--------|-----|-----|---------------|
| Cloudflare AI GW | 0.521s | 0.823s | 1.6x |
| Portkey | 0.519s | 0.903s | 1.7x |
| OpenAI Direct | 0.487s | 1.021s | 2.1x |
| OpenRouter | 0.549s | 1.021s | 1.9x |

**Cloudflare and Portkey have the tightest tail latency** — 20% better than both OpenAI Direct and OpenRouter.

From South Korea, a direct HTTPS request to api.openai.com requires: DNS resolution → TCP handshake across the Pacific → TLS negotiation → HTTP request → response. Any hiccup in the transpacific leg (submarine cable congestion, BGP route change) adds hundreds of milliseconds. Routers with edge PoPs (regional data centers that handle TLS termination and maintain connection pools to upstream APIs) close to the client short-circuit this: your TLS terminates at a nearby PoP, and the gateway relays over pre-established, high-bandwidth connections to the API provider's data center.

**This is an infrastructure argument, not a routing argument.** The same benefit would apply to any CDN or API gateway with strong regional presence. For developers outside the US — which is most of the world — this matters more than any routing intelligence.


## Real Coding Tasks: Does Overhead Matter at Scale?

On actual coding workloads (code completion, bug fixing, code review — N=20 per router, OpenAI Direct vs OpenRouter only):

| Router | Avg | p50 | p95 |
|--------|-----|-----|-----|
| OpenRouter | 4.35s | 4.56s | 9.66s |
| OpenAI Direct | 5.74s | 5.07s | 17.62s |

OpenRouter is 24% faster on average and nearly 2x more stable at p95 (9.66s vs 17.62s). Note: N=20 is still relatively small, so the p95 difference should be interpreted with caution.

The key insight: as response generation time grows from milliseconds to seconds, the fixed overhead of routing becomes proportionally irrelevant. On a 4-second response, even 200ms of routing overhead is only 5%. But the tail-latency smoothing benefit persists — and matters more for interactive use, because a single 17-second hang in a coding session breaks flow state.


## Multi-Provider: The Overhead Varies by Backend Path

Testing the same prompt across 4 models via OpenRouter's single API, plus a direct comparison for Gemini (N=20-30):

| Path | p50 | p95 |
|------|-----|-----|
| Gemini Direct | 1.307s | 1.981s |
| Gemini via OpenRouter | 1.583s | 2.013s |
| **Overhead** | **+276ms** | **+32ms** |

Compare this to the OpenAI overhead measured earlier: +62ms at p50. Why is the Gemini overhead 4x larger?

This reveals an important nuance: **routing overhead isn't just client→router. It's client→router→provider.** OpenRouter's backend path to Google's API (GCP) may traverse different network infrastructure than its path to OpenAI (Azure). The overhead depends on two hops, not one — and different provider backends have different geographic characteristics.

This means the "routing overhead" can't be stated as a single number. It's a function of: (1) client-to-router edge proximity, (2) router-to-provider backend connectivity, and (3) the provider's own infrastructure. Each combination has its own overhead profile.

The multi-provider tax buys you: model experimentation without vendor lock-in, automatic failover, single billing, and a unified API. Key insight: Gemini Flash delivers 63% more tokens than GPT-4o while being only 16% slower. You discover this when switching models is a config change, not a codebase migration.


## Model Tier Cost-Latency Tradeoff

Testing the three-tier approach (fast/default/large) via OpenRouter (N=10-20):

| Model (Tier) | Avg | p50 | Completion Tokens | Est. Cost/1K calls |
|--------------|-----|-----|-------------------|--------------------|
| gpt-4o-mini (fast) | 7.58s | 7.04s | 403 | ~$0.10 |
| claude-sonnet (default) | 9.14s | 9.20s | 583 | ~$12.25 |
| claude-opus (large) | 10.66s | 9.70s | 596 | ~$48.35 |

The tier gap is mostly in cost, not latency. mini→sonnet: +31% latency but ~150x cost. sonnet→opus: +5% latency but ~4x cost. The latency curve flattens while the cost curve explodes.

If you can reliably classify 60% of queries as "simple," the savings are 90%+ on those queries — far exceeding the original 40-60% claim. The hard part is classification accuracy. Edge-backed routers make this strategy practical: you get multi-tier model routing without adding network latency, since the router's edge PoP handles the extra hop at negligible cost.


## Streaming TTFT: Direct Wins Here

For coding agents, time-to-first-token (TTFT) matters more than total latency. Measured with streaming enabled (N=60):

| Router | TTFT | p50 Total | p95 Total |
|--------|------|-----------|-----------|
| OpenAI Direct | 0.569s | 5.49s | 10.58s |
| OpenRouter | 0.820s | 7.24s | 25.67s |

TTFT overhead for OpenRouter is +251ms. This is the one scenario where direct connections clearly win. Hypothesis: the router's streaming proxy introduces buffering latency that doesn't exist in non-streaming mode.

**For coding agents:** if perceived responsiveness (first character appearing) is your priority, direct API connections have a measurable edge. If you're doing non-streaming batch work, the tail-latency smoothing of routers may be more valuable.


## Tool Calling: Small Per-Turn Tax, Smoother Sessions

Coding agents call tools (read_file, write_file) on nearly every turn (N=40):

| Router | p50 | p95 |
|--------|-----|-----|
| OpenAI Direct | 0.699s | 1.187s |
| OpenRouter | 0.780s | 1.261s |

The per-call overhead is +81ms. In a 50-turn session, that compounds to ~4 extra seconds total. But the worst-case behavior favors the router — fewer outlier spikes means a smoother interactive experience. For autonomous agent loops that may run 100+ tool calls, consistent per-turn latency matters more than shaving 81ms off the median.


---

**Methodology:** llm-router-lab (github.com/vericontext/llm-router-lab), fully open-source. **Client:** South Korea — all results are shaped by transpacific routing. US/EU testers will see different patterns, though relative trends (edge advantage, tail smoothing) should hold directionally. **Sample sizes:** Overhead: N=300 (all 4 routers). Coding tasks: N=20. Multi-provider: N=20-30. Streaming: N=60. Tool calling: N=40. **Statistics:** We report p50 and p95. p99 is omitted as it requires N=1000+ for reliability. **Models:** gpt-4o, gpt-4o-mini, claude-sonnet-4, claude-opus-4.5, gemini-2.5-flash, llama-3.1-70b. **Invitation:** If you're in the US/EU and want to run the same benchmark, the repo has everything you need. I'd love to see how geography changes these results.
