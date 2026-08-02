<!-- profile cards updated: 2026-08-02 -->
<!-- Cards: python3 tools/generate_profile_cards.py && python3 tools/render_cards.py -->

<div align="center">

<img src="./profile/hero.png" width="880" alt="Zhu (Leo) Zhi — Cornell CS '28, GPA 4.0 / 4.0. Software Engineer, Machine Learning Engineer, Robotics Engineer. However the technical landscape shifts, engineering keeps returning to one origin: making things that solve real problems — with a coherent mind and a practice that never stops improving.">

<a href="mailto:zhizhu0730@gmail.com"><img src="https://img.shields.io/badge/Email-zhizhu0730@gmail.com-2563eb?style=flat-square&logo=gmail&logoColor=ffffff&labelColor=121212" alt="Email zhizhu0730 at gmail dot com"></a>
<a href="mailto:zz766@cornell.edu"><img src="https://img.shields.io/badge/Cornell-zz766@cornell.edu-333333?style=flat-square&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI%2BPHBhdGggZmlsbD0iI2I0YjRiNCIgZD0iTTEyIDMgMSA5bDExIDYgOS00LjkxVjE3aDJWOUwxMiAzek01IDEzLjE4djRMMTIgMjFsNy0zLjgydi00TDEyIDE3bC03LTMuODJ6Ii8%2BPC9zdmc%2B&labelColor=121212" alt="Cornell email zz766 at cornell dot edu"></a>
<a href="https://linkedin.com/in/zhu-zhi-506499376"><img src="https://img.shields.io/badge/LinkedIn-Zhu_Zhi-333333?style=flat-square&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI%2BPHBhdGggZmlsbD0iI2I0YjRiNCIgZD0iTTIwIDNINGEyIDIgMCAwIDAtMiAydjE0YTIgMiAwIDAgMCAyIDJoMTZhMiAyIDAgMCAwIDItMlY1YTIgMiAwIDAgMC0yLTJ6bS04IDRhMi41IDIuNSAwIDEgMSAwIDUgMi41IDIuNSAwIDAgMSAwLTV6bTUgMTFIN3YtMWMwLTEuNjYgMy4zMy0yLjUgNS0yLjVzNSAuODQgNSAyLjV2MXoiLz48L3N2Zz4%3D&labelColor=121212" alt="LinkedIn profile, Zhu Zhi"></a>

</div>

---

<div align="center">
<img src="./profile/impact.png" width="880" alt="Improvement factor per workload on a log scale, largest first. City-scale simulation run, Unity raycasting over Manhattan: 30 hours to 11 minutes, 161x faster. PostGIS spatial query after index and memory retune: 2,000 ms to 25 ms, 80x faster. Agent context overhead per LLM call: 10k tokens to about 300, 33x less. AUV steady-state error, 6-DoF controller: baseline to 20%, 5x less. Web interaction latency, INP in the chat workspace: 140 ms to 40 ms, 3.5x faster. Fleet data uploaded per vehicle per day: 100% to 30%, 3.3x less.">
</div>

---

<img src="./profile/card-bonsai.png" width="880" alt="On-vehicle data curation pipeline, v2. On the vehicle: sensor stream of MCAP recordings, to frame embeddings from an on-vehicle encoder, to a window score measured as distance to characteristic vectors, to a race-free upload gate, to the cloud. Off the vehicle, a remote fleet server makes a periodic pass over the full uploaded dataset and sends refreshed characteristic vectors back down to the scoring stage, closing the loop. 70% less upload volume, 8x usable score spread, under 3% latency cost for a distilled vision-language model, 287k frames embedded on Ray.">

<sub>Private company repo, so there is no link — this is the part I can describe.</sub>

- A fleet records far more than the network can carry home. The pipeline scores every recording window **on the vehicle** and uploads only the informative ones, cutting upload volume **~70%**. Merged to main and running on every vehicle.
- **v1** scored each frame on four orthogonal signals — spatial density, semantic composition, anomalous detections, temporal motion — collapsing them into one window score. Retuning the thresholds and formulas against real field data widened the usable score spread **8×** (σ 0.021 → 0.169), so short bursts of interest survive long stretches of ordinary driving.
- **v2** replaces those hand-tuned scorers with embedding-based scoring, and closes the loop: a remote fleet server makes a periodic pass over the full uploaded dataset and pushes refreshed characteristic vectors down to every vehicle, which then scores each window by its distance to them. What counts as interesting stops being a constant someone tuned and starts tracking what the fleet has already seen.
- Re-architected critical uploads around an explicit boundary between the **data layer** (recorder-owned MCAP files) and the **annotation layer** (pipeline-owned time windows), and closed the open-recording race by parking windows whose tail extends into the active file, then finalizing them when a covering file closes.
- Distilling image–language ability from TIPSv2 into the production BEV perception backbone for **under 3%** added latency, verified against the teacher on a 24,471-pair benchmark I designed.
- Made the team's shared embedding package encoder-agnostic (registry + factory) and embedded **287k frames** through CLIP, TIPSv2 and SigLIP2 on an autoscaling Anyscale Ray GPU cluster.

<img src="./profile/card-langalpha.png" width="880" alt="LangAlpha architecture: web, Slack and CLI into an agent core with programmatic tool calling and a subagent swarm, into a Daytona sandbox, durable Postgres and Redis state, and 30+ native and MCP tools. 10k fewer tokens per agent call, interaction latency 140 to 40 ms, 1.6k GitHub stars.">

<sub>

[**Repository**](https://github.com/ginlix-ai/LangAlpha) · [**langalpha.ai**](https://langalpha.ai) · 1.6k stars · 5,000+ users

</sub>

- Rebuilt chat as a **persistent workspace** so users can stop and resume mid-task: Daytona-sandboxed tool execution, PostgreSQL/Redis-backed conversation state, subagent dispatch, memory compaction and durable file storage.
- Traced **~10k tokens per call** of pure overhead to unused tool schemas shipping on every request, and replaced the static manifest with on-demand tool discovery.
- Cut Interaction to Next Paint from **140 ms to 40 ms** by moving fetch state into TanStack Query.
- Routed queries between in-context lookups (SEC filings) and sandboxed bulk processing across **30+ native and MCP tools**, so large jobs never exhaust the context window.
- Own the production release lifecycle end to end — CI/CD, schema migrations, incident response.

<img src="./profile/card-sunlightcity.png" width="880" alt="SunlightCity pipeline: Unity Manhattan mesh to a headless IL2CPP raycaster to 54 Kubernetes workers to a 9-shard PostGIS cluster, finishing in 11 minutes 9 seconds. 161x faster than one machine, 16M rows per second into Postgres, spatial queries from 2000 ms to 25 ms.">

<sub>

[**Repository**](https://github.com/leo-Zhizhu/SunlightCity------Large-Scale-Simulation-Data-Pipeline) · 7.89B measurements · 500 GB · 11m 09s

</sub>

- The question, asked 7.89 billion times: *at this spot on this street, at 09:03 on 15 June — sun, or shadow?* Unity's physics engine answers one instance by casting a ray at the sun; **54 Kubernetes workers** and a **9-instance PostgreSQL cluster** answer all of them and land 500 GB in **11m 09s**. The same work takes **30 hours** on one machine.
- The fleet size and the shard count were not guessed. Both are **derived from a 15-minute deadline** by a capacity model that ships in the repo and re-runs in one command.
- Containerized the physics engine as a headless Linux IL2CPP build and MapReduce-partitioned the workload, after converting unstructured Unity city models into a routable graph via procedural mesh-to-graph extraction.
- Diagnosed database I/O as the ingestion bottleneck and retuned PostGIS spatial indexing, memory allocation and bulk-insert chunk sizing — queries dropped from **~2000 ms to ~25 ms**.

---

<div align="center">
<img src="./profile/stack.png" width="880" alt="Stack grouped by area. Languages: Python, C++, Java, Go, Kotlin, C#, TypeScript, JavaScript, SQL, Bash. ML and perception: PyTorch, NumPy, Pandas, OpenCV, YOLOv7, CLIP, SigLIP2, TIPSv2, BEV perception, knowledge distillation, vision-language models, embedding pipelines, benchmark design, adaptive thresholding. Agents and LLM systems: LangGraph, LangChain, MCP, FastMCP, RAG, programmatic tool calling, subagent orchestration, context engineering, memory compaction, sandboxed execution, SSE streaming, tool routing. Robotics and control: ROS 2, MCAP, 6-DoF control, system identification, controller tuning, state machines, sensor fusion, LiDAR and camera, real-time on-vehicle, field-data iteration. Backend and web: Spring Boot, FastAPI, Node.js, React, TanStack Query, Jetpack Compose, Room, Retrofit and OkHttp, REST APIs, WebSocket, session auth, stale-while-revalidate. Data and storage: PostgreSQL, PostGIS, Redis, Elasticsearch, SQLite, sharding, spatial indexing, query tuning, bulk ingest, schema migration, caching strategy. Infrastructure and scale: Docker, Kubernetes, AWS with RDS, ECR and App Runner, Ray and Anyscale, Unity headless, IL2CPP, MapReduce, autoscaling, capacity planning, CI/CD, GitHub Actions, Linux. Foundations: machine learning, algorithms and data structures, databases, computer organization, cryptography, probability, linear algebra, distributed systems.">
</div>

---

<div align="center">
<img src="./profile/shelf.png" width="880" alt="Also on the shelf. GroceryManager, Spring Boot with React on AWS App Runner: search moved to Elasticsearch, about 400 ms faster and typo-tolerant. Pixel Social, React with Go and Elasticsearch and DALL-E 3: Go backend over an Elasticsearch index with generative image creation in the upload flow. PaperChat, Node.js with React, LangChain and MCP: retrieval and live search share one answer path so citations stay attached to what was read. MiniSpotify, Kotlin with ExoPlayer and Jetpack Compose: Room and Kotlin Flows stale-while-revalidate cache, about 80% faster returning-user load, backoff cut failed requests 25%. Cornell AUV, ROS 2 with YOLOv7: nonlinear models fit to 6-DoF pool-test data found controller parameters hand-tuning missed, 80% less steady-state error.">
</div>

<sub>

[GroceryManager](https://github.com/leo-Zhizhu/GroceryManager) · [Pixel Social](https://github.com/leo-Zhizhu/Pixel-Social) · [PaperChat](https://github.com/leo-Zhizhu/PaperChat) · [MiniSpotify](https://github.com/leo-Zhizhu/MiniSpotify) · [Cornell AUV](https://cuauv.org)

</sub>

---

<div align="center">

<img src="./profile/github.png" width="880" alt="GitHub at a glance: 1.6k stars earned, 12 public repos, 13 followers, 11 languages in use, with a language mix bar led by Python and TypeScript.">

<img src="./assets/snake.svg" width="880" alt="Contribution graph rendered as a snake eating the commit squares">

</div>

---

<div align="center">
<img src="./profile/principles.png" width="880" alt="How I think about the work. Tradeoffs, not perfect solutions: clarity over cleverness, observability over magic, iteration over over-design, user needs over technical ego. The real world is the test: a feature is cheap, a feature that holds under load, bad networks and odd inputs is the job. Humans stay in the loop: the user should understand why the system produced an answer, not just what the answer was. Currently learning: reliable agent orchestration, AI infrastructure, robotics control powered by ML, system design at scale.">
</div>

<div align="center">
<br>

**Open to internships, coffee chats, collaboration, research, and interesting challenges.**

<sub><i>Software is not just logic — it's a contract with reality.</i></sub>

</div>
