<!-- profile cards updated: 2026-08-01 -->
<!-- Cards in ./profile are generated: python3 tools/generate_profile_cards.py -->

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./profile/hero-dark.svg">
  <img src="./profile/hero-light.svg" width="880" alt="Zhu (Leo) Zhi — Cornell CS '28, GPA 4.0 / 4.0. Software Engineer, Machine Learning Engineer, Robotics Engineer. However the technical landscape shifts, engineering keeps returning to one origin: making things that solve real problems — with a coherent mind and a practice that never stops improving.">
</picture>

<a href="mailto:zhizhu0730@gmail.com"><img src="https://img.shields.io/badge/zhizhu0730@gmail.com-0782a2?style=for-the-badge&logo=gmail&logoColor=white" alt="Email zhizhu0730 at gmail dot com"></a>
<a href="mailto:zz766@cornell.edu"><img src="https://img.shields.io/badge/zz766@cornell.edu-b45309?style=for-the-badge&logo=maildotru&logoColor=white" alt="Email zz766 at cornell dot edu"></a>
<a href="https://linkedin.com/in/zhu-zhi-506499376"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"></a>

</div>

---

## Numbers I moved

<div align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./profile/impact-dark.svg">
  <img src="./profile/impact-light.svg" width="880" alt="Improvement factor per workload on a log scale, largest first. City-scale simulation run, Unity raycasting over Manhattan: 30 hours to 11 minutes, 161x faster. PostGIS spatial query after index and memory retune: 2,000 ms to 25 ms, 80x faster. Agent context overhead per LLM call: 10k tokens to about 300, 33x less. AUV steady-state error, 6-DoF controller: baseline to 20%, 5x less. Web interaction latency, INP in the chat workspace: 140 ms to 40 ms, 3.5x faster. Fleet data uploaded per vehicle per day: 100% to 30%, 3.3x less.">
</picture>
</div>

---

## Work worth a closer look

### Bonsai Robotics · Machine Learning Engineering Intern

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./profile/card-bonsai-dark.svg">
  <img src="./profile/card-bonsai-light.svg" width="880" alt="On-vehicle data curation pipeline: sensor stream to four per-frame scorers to a window score to an upload gate to the cloud. 70% less upload volume, 8x usable score spread, under 3% latency cost for a distilled vision-language model, 287k frames embedded on Ray.">
</picture>

<sub>Private company repo, so there is no link — this is the part I can describe.</sub>

- A fleet records far more than the network can carry home. The pipeline scores every recording window **on the vehicle** and uploads only the informative ones, cutting upload volume **~70%**. Merged to main and running on every vehicle.
- Four orthogonal per-frame signals — spatial density, semantic composition, anomalous detections, temporal motion — collapse into one window score. Retuning the thresholds and formulas against real field data widened the usable score spread **8×** (σ 0.021 → 0.169), so short bursts of interest survive long stretches of ordinary driving.
- Re-architected critical uploads around an explicit boundary between the **data layer** (recorder-owned MCAP files) and the **annotation layer** (pipeline-owned time windows), and closed the open-recording race by parking windows whose tail extends into the active file, then finalizing them when a covering file closes.
- Distilling image–language ability from TIPSv2 into the production BEV perception backbone for **under 3%** added latency, verified against the teacher on a 24,471-pair benchmark I designed.
- Made the team's shared embedding package encoder-agnostic (registry + factory) and embedded **287k frames** through CLIP, TIPSv2 and SigLIP2 on an autoscaling Anyscale Ray GPU cluster.

### Ginlix AI · Full-Stack Software Engineer

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./profile/card-langalpha-dark.svg">
  <img src="./profile/card-langalpha-light.svg" width="880" alt="LangAlpha architecture: web, Slack and CLI into an agent core with programmatic tool calling and a subagent swarm, into a Daytona sandbox, durable Postgres and Redis state, and 30+ native and MCP tools. 10k fewer tokens per agent call, interaction latency 140 to 40 ms, 1.6k GitHub stars.">
</picture>

<sub>

[**Repository**](https://github.com/ginlix-ai/LangAlpha) · [**langalpha.ai**](https://langalpha.ai) · 1.6k stars · 5,000+ users

</sub>

- Rebuilt chat as a **persistent workspace** so users can stop and resume mid-task: Daytona-sandboxed tool execution, PostgreSQL/Redis-backed conversation state, subagent dispatch, memory compaction and durable file storage.
- Traced **~10k tokens per call** of pure overhead to unused tool schemas shipping on every request, and replaced the static manifest with on-demand tool discovery.
- Cut Interaction to Next Paint from **140 ms to 40 ms** by moving fetch state into TanStack Query.
- Routed queries between in-context lookups (SEC filings) and sandboxed bulk processing across **30+ native and MCP tools**, so large jobs never exhaust the context window.
- Own the production release lifecycle end to end — CI/CD, schema migrations, incident response.

### Cornell Ezra Systems · Simulation Infrastructure Lead

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./profile/card-sunlightcity-dark.svg">
  <img src="./profile/card-sunlightcity-light.svg" width="880" alt="SunlightCity pipeline: Unity Manhattan mesh to a headless IL2CPP raycaster to 54 Kubernetes workers to a 9-shard PostGIS cluster, finishing in 11 minutes 9 seconds. 161x faster than one machine, 16M rows per second into Postgres, spatial queries from 2000 ms to 25 ms.">
</picture>

<sub>

[**Repository**](https://github.com/leo-Zhizhu/SunlightCity------Large-Scale-Simulation-Data-Pipeline) · 7.89B measurements · 500 GB · 11m 09s

</sub>

- The question, asked 7.89 billion times: *at this spot on this street, at 09:03 on 15 June — sun, or shadow?* Unity's physics engine answers one instance by casting a ray at the sun; **54 Kubernetes workers** and a **9-instance PostgreSQL cluster** answer all of them and land 500 GB in **11m 09s**. The same work takes **30 hours** on one machine.
- The fleet size and the shard count were not guessed. Both are **derived from a 15-minute deadline** by a capacity model that ships in the repo and re-runs in one command.
- Containerized the physics engine as a headless Linux IL2CPP build and MapReduce-partitioned the workload, after converting unstructured Unity city models into a routable graph via procedural mesh-to-graph extraction.
- Diagnosed database I/O as the ingestion bottleneck and retuned PostGIS spatial indexing, memory allocation and bulk-insert chunk sizing — queries dropped from **~2000 ms to ~25 ms**.

---

## Stack

<div align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./profile/stack-dark.svg">
  <img src="./profile/stack-light.svg" width="880" alt="Stack by area. Languages: Python, C++, Java, Go, Kotlin, C#, TypeScript, SQL. ML and agents: PyTorch, ROS 2, OpenCV, LangGraph, LangChain, MCP, Ray and Anyscale. Backend and data: Spring Boot, FastAPI, Node.js, React, PostgreSQL, PostGIS, Redis, Elasticsearch. Infrastructure: Docker, Kubernetes, AWS, Unity headless, CI/CD, Linux.">
</picture>
</div>

---

## Also on the shelf

| Project | What it is | Notable |
|---|---|---|
| **[GroceryManager](https://github.com/leo-Zhizhu/GroceryManager)** | Grocery list service — Spring Boot, React, AWS App Runner | Moved search to Elasticsearch: **~400 ms faster**, typo-tolerant. Shared Redis session store so instances scale without pinning |
| **[Pixel Social](https://github.com/leo-Zhizhu/Pixel-Social)** | Social platform for creating and sharing images and video — React, Go, Elasticsearch, DALL·E 3 | Go backend over an Elasticsearch index, with generative image creation in the upload flow |
| **[PaperChat](https://github.com/leo-Zhizhu/PaperChat)** | RAG + web-search chat over your own PDFs, with voice I/O — Node.js, React, LangChain, MCP | Retrieval and live search share one answer path, so citations stay attached to what was actually read |
| **[MiniSpotify](https://github.com/leo-Zhizhu/MiniSpotify)** | Android music client — Kotlin, ExoPlayer, Jetpack Compose | Room + Kotlin Flows stale-while-revalidate cache: **~80% faster** returning-user load. Retrofit/OkHttp backoff cut failed requests **25%** |
| **[Cornell AUV](https://cuauv.org)** | Autonomous underwater vehicle — perception, control, mission stack | Fit nonlinear models to 6-DoF pool-test data to find controller parameters hand-tuning missed: **80% less** steady-state error. Adaptive thresholding on the YOLOv7 pipeline removed the pre-test manual retune |

---

## GitHub

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./profile/github-dark.svg">
  <img src="./profile/github-light.svg" width="880" alt="GitHub at a glance: 1.6k stars earned, 12 public repos, 13 followers, 11 languages in use, with a language mix bar led by Python and TypeScript.">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/github-contribution-grid-snake-dark.svg">
  <img src="./assets/github-contribution-grid-snake.svg" width="880" alt="Contribution graph rendered as a snake eating the commit squares">
</picture>

</div>

---

## How I think about the work

| | |
|---|---|
| **Tradeoffs, not perfect solutions** | Clarity over cleverness · observability over magic · iteration over over-design |
| **The real world is the test** | A feature is cheap; a feature that holds under load, bad networks and odd inputs is the job |
| **Humans stay in the loop** | The user should understand *why* the system produced an answer, not just what it was |
| **Currently learning** | Reliable agent orchestration · AI infrastructure · robotics control powered by ML · system design at scale |

<div align="center">
<br>

**Open to internships, coffee chats, collaboration, research, and interesting challenges.**

<sub><i>Software is not just logic — it's a contract with reality.</i></sub>

</div>
