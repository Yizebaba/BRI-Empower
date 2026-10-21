[中文](README.md) | **English**

# Belt and Road Full-Scope Foresight

Website: https://yizebaba.github.io/BRI-Full-Scope-Foresight/ · Docs: https://yizebaba.github.io/BRI-Full-Scope-Foresight/about.html

> What if you could see the futures that might unfold? What if the future could be rehearsed in advance? How much more often would your decisions win?

Public data on the 150 Belt and Road partner countries, plus the user's own documents, feed an AI swarm-intelligence engine. Its agents — governments, companies, media, local residents and others — react to a decision in a simulated society, and the output is a report plus the full process data.

## Features

| Feature | Details |
|---|---|
| Simulate (default tab) | Pick 0–5 countries, tick seed documents, upload your own files (PDF/Markdown/TXT; up to 20, 50 MB each, 100 MB total), write your own prompt and run it with your own model key. Rounds default to auto. |
| Results | Read on the page; download PDF, Word, Markdown and HTML reports and CSV process data. Every file carries a "simulation, not fact" label and disclaimer. |
| Countries | Conflict, hazards, outages, news, travel advice, overview, military, research, trade (97 industries) and Chinese-financed projects for 150 countries; sea, air, rail and road chokepoints and every land border. |
| Seed documents | 5–8 per country, generated automatically, readable and downloadable. |
| Sources / Examples | Licence, refresh rate and use of every source; completed example simulations; seed data accuracy check. |
| Languages | Full Chinese/English switch. |
| Custom simulation | "Custom simulation ✉" opens a pre-filled email (yizebaba@gmail.com); urgency levels: standard, priority, express, emergency. |

## Data refresh

| Workflow | Frequency | Content |
|---|---|---|
| `scan.yml` | Every 30 min | Earthquakes, hazard alerts, natural events, travel advice, news near key projects; regenerates seed documents |
| World Monitor scheduled task | Daily | Conflict, top stories, outages, outbreaks, airports → `data/wm.json` |
| `logistics.yml` | Twice daily | IMF PortWatch ports and maritime chokepoints |
| `chokepoints.yml` | Twice daily | Air, rail and road chokepoints and land borders |
| `trade.yml` | Mondays | UN Comtrade trade; World Bank economic, military (SIPRI) and research indicators; Wikidata institutions, leaders and award winners; OpenAlex papers |
| `docs.yml` | Wednesdays | Wikipedia, World Bank Documents & Reports, OpenAlex papers (ReliefWeb pending approval) |
| `pages.yml` | On site changes | Publishes `site/` to GitHub Pages |

## How a run works

The page submits the prompt, selected seed documents, uploaded files and the user's own model and Zep keys to the EVEREST platform's Cloudflare Worker queue. In the EVEREST repository (Yizebaba/EVEREST-), `mirofish-queue.yml` dispatches jobs every 5 minutes and `mirofish.yml` claims them with a GitHub OIDC identity (keys and files are deleted from the server once claimed), runs the simulation and stores results and exports on its `events` branch under `mirofish-bri/`. This repository needs no secrets and visitors need no GitHub token.

Note: self-service prompts and reports appear in the public run list.

## Data and licences

Sources, licences and citations are in `data/sources.json` (the "Sources" tab on the site). The simulation engine is the open-source MiroFish (github.com/666ghj/MiroFish, AGPL-3.0), fetched at a pinned version at run time; this repository neither contains nor modifies its code.

Simulation results are simulations, not facts or forecasts, and are not investment, legal or security advice.

## Related

EVEREST platform: https://github.com/Yizebaba/EVEREST- — maintained separately.
