Scope

- Projekt rieši iba endpointy explicitne uvedené v endpoints.json.
- Neregistrované služby sa cez tento projekt nesmú kontrolovať, reštartovať ani meniť.

Watchdog

- watchdog.py je deterministický health checker.
- Pri zdravom stave nesmie volať LLM.
- LLM sa spúšťa iba pri novej chybe endpointu.
- Stav a report watchdogu zostávajú lokálne v tomto projekte.

Diagnostika a opravy

- Pred každou opravou vykonaj read-only diagnostiku a získaj konkrétne dôkazy.
- Reštart povoľ iba cez allowlist príkazov v endpoints.json a helper repair.py.
- Nevymýšľaj nové restartovacie príkazy a počas incidentu nerozširuj allowlist.
- Po reštarte endpoint znovu over a zaznamenaj výsledok.

Hermes profil

- Incidenty rieši profil laurincov-pes.
- Model qwen-prisma sa používa iba na analýzu incidentov.
- Nemeň cron plánovanie, model, credentials ani oprávnenia profilu.
- Do reportov, logov a dashboardu nezapisuj secrets.

Zakázané akcie

- Žiadne deštruktívne príkazy.
- Žiadne sudo, rm, prune, rebuild alebo zmeny firewallu.
- Nemeň Docker Compose, sieť, disky ani registry endpointov počas incidentu.
- Qwen Prisma sa nepokúšaj opravovať cez samotný Qwen, ak je nedostupný.

Výstup

Reportuj stručne po slovensky vo formáte PASS/FAIL:

- príčina,
- dôkaz,
- vykonaná akcia,
- výsledok po akcii,
- otvorené riziká.
