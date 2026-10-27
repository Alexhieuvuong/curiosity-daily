# The Risk You Keep vs. the Risk You Sell: Why Self-Insurance Is a Bet on Your Own Balance Sheet

> Every premium you pay is partly a fee for someone else to hold your fear — so what happens when you decide to hold it yourself?

## Why this is interesting
Insurance looks like a simple trade: a small certain payment today for protection against a large uncertain loss tomorrow [2]. But that trade bundles two very different things — the *risk itself* and the *cost of carrying it*. Self-insurance is the act of unbundling them: keeping the risk, and refusing to pay someone else to carry it [3]. Once you see the premium as a price for *carrying*, not just for *covering*, the whole question of who should hold which risk becomes a balance-sheet puzzle rather than a matter of prudence.

## First principles
Start with the irreducible mechanic. A policyholder assumes "a guaranteed, known, and relatively small loss" (the premium) in exchange for the insurer's promise to compensate a covered loss [2]. The insurer, in turn, can offload part of that exposure through reinsurance when a risk is "too large for it to carry" [2]. Now flip it: self-insurance is the same logic run in reverse — an organization "that is liable for some risk does not take out any third-party insurance, but rather chooses to bear the risk itself," setting aside money using "actuarial and insurance information and the law of large numbers" so the reserve resembles a premium [3]. The core insight is that *carrying* a risk has a cost, and that cost can either be paid to an insurer or absorbed internally. Pricing, at bottom, is the act of putting a number on that carrying cost — which is exactly what the academic literature on "pricing financial and insurance risks" tries to formalize [4][5].

## Break it into pieces
- **What exactly are you buying when you buy insurance?** Coverage of the loss, or the *transfer* of the burden of carrying it? The two are separable [2][3].
- **When does keeping the risk beat selling it?** Self-insurance is framed as cheaper because it eliminates "the carrying-costs that commercial insurers are obliged to pass on" [3] — but cheaper for whom, and under what assumptions?
- **Why don't individuals self-insure more?** The source says individuals "rarely have the funds to cover large uncertain risks" and rarely save enough on premiums to justify it [3]. So scale and capital, not intelligence, may be the real gate.
- **What forces you to buy anyway?** Legal mandates like compulsory third-party car insurance can override the self-insurance calculation entirely [3].
- **How do you price a risk you keep?** The framework papers treat pricing of traded vs. non-traded risks and even "fair values of insurance liabilities" as a unified problem [4][5].

## Follow the incentives
The self-insuring organization profits by avoiding the premium *and* the insurer's carrying costs [3] — but it now bears the downside itself, paying claims "from captive or on-balance sheet financial provisions" [3]. The commercial insurer, by contrast, earns its margin precisely by holding risk others don't want to carry, and can further lay off what's "too large for it to carry" via reinsurance [2]. Notice the asymmetry of incentives: the self-insurer is betting its own assets that its actuarial estimate is right, while the insurer can pass extreme exposures upward through reinsurance [2][3]. The risk doesn't vanish at any layer — it just changes hands, and each hand charges (or saves) a price for holding it.

## How it echoes elsewhere
The same "carry vs. transfer" mechanic shows up in **systemic risk**: the source defines it as risk from "interlinkages and interdependencies" where "the failure of a single entity or cluster of entities can cause a cascading failure" [1]. When many institutions each decide to self-insure — to keep risk on their own books rather than transfer it — the aggregate exposure concentrates in ways no single balance sheet sees. It also echoes **capital allocation inside firms**: the pricing framework explicitly extends to "prescribe capital allocations within insurance companies" [4], meaning the same logic that decides whether to buy insurance decides where capital sits.

## A real-world case
The sources give the mechanic but not a named corporate example, so here is a clearly labeled simplification. **Illustrative:** a mid-sized firm faces a recurring, moderate risk of equipment breakdown. A commercial insurer would charge a premium that includes the insurer's own carrying costs [3]. The firm instead runs the numbers with actuarial methods and the law of large numbers, sets aside a reserve sized like a premium, and pays claims from that reserve [3]. If its estimate is sound, it saves the carrying-cost margin; if a cluster of losses arrives at once, its own assets absorb the hit — the mirror image of the cascading-failure logic in [1].

## Second-order effects
If self-insurance spreads because it looks cheaper, more risk stays on individual balance sheets rather than being diversified across a pool — which, following the systemic-risk definition, could raise the chance that one entity's bad estimate becomes a cluster failure [1][3]. Conversely, mandatory-insurance rules [3] act as a counterweight, forcing risk into pools whether or not self-insurance would be cheaper. And the very existence of a pricing framework for "non-traded" risks [4] suggests the boundary between "insurable" and "self-insured" is a modeling choice as much as a financial one.

## A question to sit with
If self-insurance is cheaper mainly because it strips out the insurer's carrying costs [3], is that a genuine efficiency — or just a transfer of risk to whoever ultimately can't afford to hold it?

## Go deeper
- Compare the "law of large numbers" reserve logic in self-insurance [3] with how reinsurance lets a primary insurer shed risk "too large for it to carry" [2] — same math, opposite direction.
- Explore how the distortion-operator and universal-framework papers [4][5] turn "carrying cost" into an actual number, and what assumptions they must make about non-traded risk.
- Trace the systemic-risk thread [1]: at what point does many firms self-insuring become a system-level fragility rather than individual prudence?

## Sources

[1] [Systemic risk](https://en.wikipedia.org/wiki/Systemic_risk) — Wikipedia
[2] [Insurance](https://en.wikipedia.org/wiki/Insurance) — Wikipedia
[3] [Self-insurance](https://en.wikipedia.org/wiki/Self-insurance) — Wikipedia
[4] [A Universal Framework for Pricing Financial and Insurance Risks (2002)](https://doi.org/10.2143/ast.32.2.1027) — academic paper
[5] [A Class of Distortion Operators for Pricing Financial and Insurance Risks (2000)](https://doi.org/10.2307/253675) — academic paper

## Vocabulary Builder
1. **contingent** — (adjective, /kənˈtɪndʒənt/) — dependent on something uncertain happening. _Example: Insurance protects against a contingent loss that may or may not occur._
2. **premium** — (noun, /ˈpriːmiəm/) — the payment a policyholder makes to an insurer for coverage. _Example: The premium is the small certain cost traded for protection._
3. **deductible** — (noun, /dɪˈdʌktəbəl/) — the out-of-pocket amount an insured must pay before the insurer covers a claim. _Example: A higher deductible lowers the premium but raises your own exposure._
4. **reinsurance** — (noun, /ˌriːɪnˈʃʊərəns/) — insurance bought by an insurer to offload part of its risk. _Example: The primary insurer used reinsurance for a risk too large to carry alone._
5. **underwriter** — (noun, /ˈʌndəraɪtər/) — an entity that provides insurance and assesses the risk. _Example: The underwriter decides whether the risk is worth covering._
6. **actuarial** — (adjective, /ˌæktʃuˈeəriəl/) — relating to the statistical calculation of risk and premiums. _Example: Self-insurers rely on actuarial methods to size their reserves._
7. **idiosyncratic** — (adjective, /ˌɪdiəsɪŋˈkrætɪk/) — peculiar to an individual entity rather than the whole system. _Example: Idiosyncratic risk affects one firm; systemic risk spreads across all._
8. **interlinkage** — (noun, /ˌɪntəˈlɪŋkɪdʒ/) — a connection between parts of a system. _Example: Interlinkages let one failure cascade through the market._
9. **cascading** — (adjective, /kæˈskeɪdɪŋ/) — spreading in a chain, each failure triggering the next. _Example: A cascading failure can bring down an entire system._
10. **liability** — (noun, /ˌlaɪəˈbɪləti/) — a legal or financial obligation to pay. _Example: The framework helps determine fair values of insurance liabilities._
11. **prudently** — (adverb, /ˈpruːdəntli/) — with careful judgment about future risk. _Example: Used prudently, self-insurance sets aside enough to cover uncertain losses._
12. **distortion** — (noun, /dɪˈstɔːʃən/) — a change that alters a value or shape from its true form. _Example: Distortion operators reshape a probability distribution for pricing._

---
*Curiosity Daily · 2026-10-27 · grounded & fact-checked · deepseek-chat*
