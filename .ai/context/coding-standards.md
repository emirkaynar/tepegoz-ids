# Coding Standards

## Priority

Performance first, then clarity, then extensibility.

## Rules

- Minimize allocations and unnecessary object churn.
- Batch writes and expensive I/O whenever possible.
- Keep capture, processing, and storage paths lean.
- Avoid payload inspection and deep packet analysis.
- Prefer deterministic logic for Tier 1.
- Measure before introducing complexity.

## Code Shape

- Keep interfaces small and explicit.
- Use clear data structures for flows, alerts, and rule inputs. Use `__slots__` for classes in the hot path to save memory and speed up attribute access.
- Prefer direct transformations over layered abstraction when performance matters.

## Python & Scapy Performance Traps

_(To meet the 100Mbps / 60% CPU budget)_

1. **Never store packets in memory:** Always use `sniff(..., store=False, prn=handler)`. Storing packets will OOM the system in seconds.
2. **Avoid deep dissection:** Do not let Scapy parse layers you don't need. Extract `Ether`, `IP`, `TCP`/`UDP` headers and avoid touching the `payload` to prevent expensive recursive parsing.
3. **Use Kernel BPF Filters:** Drop irrelevant traffic in the kernel (e.g., `sniff(filter="tcp or udp")`) before it crosses into Python userspace.
4. **Amortize cleanup:** Do not sweep the flow table for expired flows on every packet. Run cleanup every $N$ packets or on a separate timer (amortized $O(1)$).
5. **Minimize GC Churn:** Do not create new dicts, lists, or string concatenations inside the per-packet `handler` loop. Update values in place and prefer standard tuples over classes for transient internal state.

## Review Check

Any new code should explain why it is efficient enough for the current hardware and traffic assumptions.

## Frontend (Grafana App Plugin) Rules

- **Native UI Only:** Build forms and configuration surfaces using `@grafana/ui` components to ensure a native aesthetic. Do not introduce generic CSS frameworks (Tailwind, Bootstrap).
- **Strict Typing:** All React frontend code must use TypeScript with `strict` mode enabled.
- **Proxy Routing:** Frontend HTTP POST/GET requests must be routed via Grafana's data proxy or data source proxy to reach the Headless FastAPI backend securely. Do not make direct browser-to-FastAPI requests.
