# I Benchmarked 5 LLM Routers — The "Orchestration Moat" Needs Revision

## The Claim, Then the Measurement

In yesterday's post "The Orchestration Moat" (ai.contextix.io/2026-03-08-orchestration-moat), I analyzed why multi-model routing is inevitable. The core thesis, drawn from recent industry benchmarks and trends: routing overhead is 20-50ms, cost savings reach 40-60%, and the moat shifts to routing intelligence.

So I built llm-router-lab (github.com/vericontext/llm-router-lab), an open-source benchmark framework, and measured 5 LLM routers head-to-head: OpenAI Direct, OpenRouter, Portkey, Cloudflare AI Gateway, and Gemini Direct.

Methodology: Each test case ran 20-30 times per router, from a South Korea-based client. We report percentile-based latency (p50, p95, p99), not averages — because averages lie. All tests used gpt-4o as the common model where possible. The full code and raw results are open-source.

The results surprised me. Some of those claims hold up. Others need serious revision.


## TL;DR — 7 Revised Takeaways

1. Routing overhead is not a fixed cost. The 20-50ms claim is wrong. Well-built routers can be faster than direct calls. Poorly-built ones add 10+ seconds at the tail.
2. The moat is intelligence + infrastructure. Connection pooling, health monitoring, geographic optimization matter just as much as routing logic.
3. Latency consistency is the real moat. OpenRouter's p50/p99 ratio is 2.2x. Portkey's is 21.6x. That's a 10x difference in predictability.
4. Multi-provider overhead is acceptable. 200-300ms overhead for multi-provider access. At p95+, it often disappears entirely.
5. Streaming and non-streaming have different winners. Routers win non-streaming; direct wins streaming TTFT (+251ms).
6. Cost savings exceed the original claim. Not 40-60% — it's 90%+ for simple queries routed to mini models. The challenge is classification accuracy.
7. Token efficiency is a hidden moat dimension. The API path changes input token consumption by 3-10x. This compounds faster than model-tier routing.


## "Routing Overhead 20-50ms" Is Wrong

The original analysis assumed routing adds a fixed 20-50ms overhead. Here's what I actually measured on minimal prompts (max_tokens: 1):

[IMAGE: table-1-router-overhead.png]

Three things jump out:

OpenRouter is faster than calling OpenAI directly. Not by a little — 23% faster at p50 (0.539s vs 0.698s). This likely comes from connection pooling, geographic optimization, and endpoint health monitoring. The "overhead" is negative.

Overhead is not a fixed value — it's a distribution. It ranges from negative (OpenRouter) to catastrophic (Portkey p99 = 10.8s). Quoting a single overhead number is misleading.

p99 defines the real user experience. In a 50-call coding session, the probability of hitting at least one Portkey p99 event is ~40%. Nearly half your sessions will include a 10+ second hang. OpenRouter's p99 of 1.2s means users rarely notice anything.


## Performance Reversal in Real Coding Tasks

The overhead scenario uses minimal tokens. What happens with actual coding workloads? I ran the coding_agent scenario (code completion, bug fixing, code review) with 20 repeats:

[IMAGE: table-2-coding-agent.png]

OpenRouter is 24% faster on average and nearly 2x more stable at p95 (9.66s vs 17.62s).

This inverts the conventional wisdom. The moat isn't just "routing intelligence" — it's infrastructure optimization. Connection pooling, request queuing, endpoint health checks — things individual developers cannot replicate by simply calling the API directly.

As generation length increases, any fixed routing overhead becomes proportionally irrelevant. On a 4-second coding response, even 200ms overhead is only 5%.


## Tail Latency Is the Real Metric

The p50/p99 ratio tells you how "surprising" a router can be:

[IMAGE: table-3-tail-latency.png]

p50 is a marketing metric. p99 is an engineering metric.

Portkey's p50 is the best of all routers (0.498s). If you evaluated routers by median latency alone, you'd choose Portkey. That would be a mistake. Its tail latency is 21.6x the median — the worst consistency of any router tested.

OpenRouter has the best combination: fast median and tight tail. This matters enormously for coding agents where you make dozens of calls per session.


## Multi-Provider DX: The 200ms Tax Is Worth It

I tested OpenRouter's multi-provider capability — running the same prompts through 4 different models via a single API:

[IMAGE: table-4-multi-provider.png]

I also compared Gemini direct vs. Gemini via OpenRouter:

[IMAGE: table-5-gemini-comparison.png]

The overhead is ~270ms at p50. But at p95, the gap nearly vanishes — and OpenRouter's p99 (2.042s) is actually tighter than direct (2.510s).

Key insight: Gemini Flash delivers 63% more tokens than GPT-4o while being only 16% slower — the best cost-performance ratio by far. You discover this kind of insight only when switching models is a config change, not a codebase migration.

The 200-300ms multi-provider overhead buys you model experimentation without vendor lock-in, automatic failover, a single billing relationship, and a unified API for heterogeneous models.


## Model Tier Cost-Latency Tradeoff

The original analysis claimed intelligent routing saves 40-60% by sending simple queries to cheaper models. I tested the three-tier approach via OpenRouter:

[IMAGE: table-6-model-tier-cost.png]

gpt-4o-mini is ~150x cheaper than claude-sonnet for coding tasks — but produces 30% fewer tokens. claude-opus vs claude-sonnet: 17% slower, ~4x more expensive, similar output length. The premium buys reasoning quality, not quantity.

The tier gap is mostly in cost, not latency. mini→sonnet is +2.2s (+31%), but sonnet→opus is only +0.5s (+5%). The latency curve flattens while the cost curve explodes.

Verdict: If you can reliably classify 60% of queries as "simple" and route them to gpt-4o-mini, the savings are not 40-60% — they're closer to 90%+ on those queries. The challenge is classification accuracy. A misrouted complex query to mini gives a worse answer AND takes similar time.


## Streaming TTFT: What Developers Actually Feel

Total latency tells you when a response is done. But in coding agents, what matters is when the first token appears. I measured TTFT (Time to First Token) with streaming enabled (60 calls each):

[IMAGE: table-7-streaming-ttft.png]

The TTFT overhead for OpenRouter is +251ms. In a 5-second response, that's 5% of total time — but it's 100% of the "is anything happening?" moment.

This reverses the non-streaming result where OpenRouter was faster. With streaming, the direct connection wins on both TTFT and total latency. Hypothesis: OpenRouter's streaming proxy adds buffering that doesn't exist in non-streaming mode.

For coding agent UX: if your primary concern is perceived responsiveness, direct API connections have a measurable edge in streaming TTFT. If your concern is non-streaming batch throughput, routers can actually be faster.


## Tool Calling Overhead: The Per-Turn Tax

Coding agents call tools on nearly every turn. If routers add overhead to tool call serialization, it compounds across a 50-turn session. Measured with 40 calls each:

[IMAGE: table-8-tool-calling.png]

The routing overhead at p50 is +81ms — trivial for a single call, but in a 50-tool-call session, that's ~4 seconds of cumulative overhead.

But OpenRouter's p99 (1.52s) is half of direct's p99 (3.05s). The router's connection management smooths out worst-case spikes.

For a 50-turn coding session: OpenAI Direct gives ~35s median but ~1 call at 3s+ (noticeable stutter). OpenRouter gives ~39s median (+4s total) but a tight tail (smoother experience).

The 81ms per-turn tax buys you 2x better worst-case behavior. In an interactive coding session, consistency beats raw speed.


## Real-World Coding Agent Sessions

Everything above measures isolated API calls. But a coding agent chains multiple calls in a loop. I ran opencode, an open-source coding agent, on three real tasks against this very codebase, comparing OpenAI Direct vs OpenRouter with GPT-4o. Each task ran 3 times.

[IMAGE: table-9-opencode-agent.png]

OpenRouter wins across all three tasks — 17-38% faster in wall-clock time.

The most striking finding isn't latency — it's the input token difference. OpenAI Direct consumed 3-10x more input tokens for the same tasks. This is likely because opencode uses OpenAI's Responses API when connecting directly, which manages conversation state server-side, while OpenRouter receives full message history via Chat Completions — but with far less context overhead per turn.

Agent steps are provider-agnostic. Both paths took identical numbers of steps, confirming the routing layer doesn't interfere with agent decision-making.

The compound effect is real. On the hardest task, the 3.3-second difference across just 3 steps means ~1.1s saved per step. In a real 20-step refactoring session, that's 22 seconds — the difference between flow state and frustration.

Token efficiency is a hidden moat dimension. If a routing layer can reduce per-turn context overhead, the savings compound faster than any model-tier routing strategy.


---

Methodology: llm-router-lab (github.com/vericontext/llm-router-lab), open-source. Client location: South Korea. 20-30 repeats per test. Percentile-based stats via numpy. Models: gpt-4o, gpt-4o-mini, claude-sonnet-4, claude-opus-4.5, gemini-2.5-flash, llama-3.1-70b. Coding agent: opencode v1.2.22. Results reflect network conditions from South Korea — US/EU clients may see different patterns.
