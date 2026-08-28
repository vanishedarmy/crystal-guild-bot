# Crystal Guild v1.2 Beta 1 — Expedition Balance Simulation

Fixed seeds: `1201` + `2201`  
Runs per scenario: **40**  
Total simulated Expeditions: **3000**

Simulation uses a Warrior at the representative level for each region, level-appropriate shop gear, persistent HP/resources between stages, basic Attack combat, and automatic Expedition Camp at 42% HP or lower. This is intentionally a conservative baseline: player-chosen abilities and battle items should improve survival. Standard runs begin at 50% regional exploration; contract runs use the required unlock state.

## Standard route/depth matrix

| Band | Lv | Region | Depth | Route | Complete | Defeat | Combat | Hazard | Rare | Camp | Travel min | XP | Gil | Seals | Finish HP |
|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Starter | 8.0 | emerald_wilds | scout | safe | 100.0% | 0.0% | 0.65 | 0.10 | 0.00 | 0.00 | 11.9 | 78 | 150 | 2.0 | 91% |
| Starter | 8.0 | emerald_wilds | scout | unknown | 100.0% | 0.0% | 0.70 | 0.30 | 0.12 | 0.03 | 12.0 | 96 | 159 | 2.0 | 84% |
| Starter | 8.0 | emerald_wilds | scout | deep | 100.0% | 0.0% | 0.85 | 0.15 | 0.23 | 0.03 | 11.9 | 181 | 311 | 2.0 | 80% |
| Starter | 8.0 | emerald_wilds | journey | safe | 100.0% | 0.0% | 1.05 | 0.33 | 0.15 | 0.00 | 29.8 | 179 | 380 | 4.0 | 82% |
| Starter | 8.0 | emerald_wilds | journey | unknown | 100.0% | 0.0% | 1.43 | 0.42 | 0.25 | 0.12 | 30.0 | 214 | 267 | 4.0 | 61% |
| Starter | 8.0 | emerald_wilds | journey | deep | 100.0% | 0.0% | 1.20 | 0.40 | 0.42 | 0.20 | 30.2 | 192 | 307 | 4.0 | 76% |
| Starter | 8.0 | emerald_wilds | deep | safe | 100.0% | 0.0% | 2.23 | 0.28 | 0.33 | 0.15 | 63.7 | 363 | 694 | 7.0 | 71% |
| Starter | 8.0 | emerald_wilds | deep | unknown | 100.0% | 0.0% | 1.85 | 1.00 | 0.53 | 0.42 | 64.1 | 338 | 656 | 7.0 | 68% |
| Starter | 8.0 | emerald_wilds | deep | deep | 97.5% | 2.5% | 2.33 | 0.47 | 0.68 | 0.62 | 64.2 | 565 | 987 | 6.8 | 59% |
| Early | 16.0 | ashen_highlands | scout | safe | 100.0% | 0.0% | 1.07 | 0.33 | 0.07 | 0.00 | 11.9 | 297 | 305 | 2.0 | 76% |
| Early | 16.0 | ashen_highlands | scout | unknown | 100.0% | 0.0% | 1.10 | 0.40 | 0.28 | 0.07 | 12.1 | 345 | 405 | 2.0 | 71% |
| Early | 16.0 | ashen_highlands | scout | deep | 100.0% | 0.0% | 1.07 | 0.33 | 0.20 | 0.05 | 12.1 | 396 | 404 | 2.0 | 65% |
| Early | 16.0 | ashen_highlands | journey | safe | 100.0% | 0.0% | 1.85 | 0.45 | 0.20 | 0.15 | 30.1 | 584 | 645 | 4.0 | 64% |
| Early | 16.0 | ashen_highlands | journey | unknown | 100.0% | 0.0% | 2.00 | 0.45 | 0.17 | 0.20 | 30.2 | 705 | 730 | 4.0 | 57% |
| Early | 16.0 | ashen_highlands | journey | deep | 95.0% | 5.0% | 1.82 | 0.60 | 0.33 | 0.38 | 30.1 | 790 | 808 | 3.8 | 47% |
| Early | 16.0 | ashen_highlands | deep | safe | 100.0% | 0.0% | 2.85 | 0.85 | 0.23 | 0.53 | 64.7 | 1080 | 1278 | 7.0 | 55% |
| Early | 16.0 | ashen_highlands | deep | unknown | 100.0% | 0.0% | 2.92 | 0.78 | 0.40 | 0.82 | 65.1 | 1319 | 1668 | 7.0 | 53% |
| Early | 16.0 | ashen_highlands | deep | deep | 77.5% | 22.5% | 2.70 | 0.88 | 0.60 | 1.07 | 61.9 | 1240 | 1286 | 5.4 | 42% |
| Mid | 24.0 | mistfen_marshes | scout | safe | 100.0% | 0.0% | 0.78 | 0.70 | 0.12 | 0.03 | 11.9 | 249 | 182 | 2.0 | 80% |
| Mid | 24.0 | mistfen_marshes | scout | unknown | 100.0% | 0.0% | 1.02 | 0.70 | 0.12 | 0.05 | 12.0 | 381 | 282 | 2.0 | 70% |
| Mid | 24.0 | mistfen_marshes | scout | deep | 100.0% | 0.0% | 0.88 | 0.75 | 0.25 | 0.00 | 11.9 | 349 | 262 | 2.0 | 69% |
| Mid | 24.0 | mistfen_marshes | journey | safe | 100.0% | 0.0% | 1.38 | 1.23 | 0.10 | 0.05 | 29.8 | 543 | 388 | 4.0 | 63% |
| Mid | 24.0 | mistfen_marshes | journey | unknown | 100.0% | 0.0% | 1.35 | 1.43 | 0.12 | 0.23 | 30.0 | 534 | 408 | 4.0 | 66% |
| Mid | 24.0 | mistfen_marshes | journey | deep | 100.0% | 0.0% | 1.20 | 1.07 | 0.53 | 0.25 | 30.3 | 580 | 474 | 4.0 | 70% |
| Mid | 24.0 | mistfen_marshes | deep | safe | 100.0% | 0.0% | 2.55 | 1.68 | 0.05 | 0.62 | 64.5 | 1085 | 779 | 7.0 | 60% |
| Mid | 24.0 | mistfen_marshes | deep | unknown | 100.0% | 0.0% | 2.30 | 2.00 | 0.47 | 0.60 | 64.4 | 1038 | 835 | 7.0 | 53% |
| Mid | 24.0 | mistfen_marshes | deep | deep | 97.5% | 2.5% | 2.48 | 1.73 | 0.57 | 0.88 | 65.0 | 1373 | 1110 | 6.8 | 51% |
| Late | 34.0 | frostveil_reach | scout | safe | 100.0% | 0.0% | 0.93 | 0.50 | 0.05 | 0.10 | 12.1 | 525 | 308 | 2.0 | 68% |
| Late | 34.0 | frostveil_reach | scout | unknown | 100.0% | 0.0% | 1.27 | 0.55 | 0.07 | 0.17 | 12.2 | 801 | 448 | 2.0 | 54% |
| Late | 34.0 | frostveil_reach | scout | deep | 97.5% | 2.5% | 0.88 | 0.70 | 0.17 | 0.20 | 12.1 | 677 | 440 | 1.9 | 60% |
| Late | 34.0 | frostveil_reach | journey | safe | 100.0% | 0.0% | 1.60 | 0.85 | 0.20 | 0.50 | 30.6 | 1068 | 630 | 4.0 | 60% |
| Late | 34.0 | frostveil_reach | journey | unknown | 97.5% | 2.5% | 1.65 | 1.25 | 0.12 | 0.47 | 30.3 | 1142 | 692 | 3.9 | 51% |
| Late | 34.0 | frostveil_reach | journey | deep | 77.5% | 22.5% | 1.60 | 0.85 | 0.30 | 0.53 | 28.5 | 1183 | 740 | 3.1 | 43% |
| Late | 34.0 | frostveil_reach | deep | safe | 100.0% | 0.0% | 2.58 | 1.48 | 0.15 | 1.10 | 65.0 | 1904 | 1144 | 7.0 | 51% |
| Late | 34.0 | frostveil_reach | deep | unknown | 95.0% | 5.0% | 2.65 | 1.82 | 0.47 | 1.40 | 64.6 | 2087 | 1252 | 6.7 | 48% |
| Late | 34.0 | frostveil_reach | deep | deep | 47.5% | 52.5% | 2.30 | 1.40 | 0.60 | 0.97 | 54.0 | 1588 | 1035 | 3.3 | 22% |
| Endgame | 45.0 | astral_scar | scout | safe | 97.5% | 2.5% | 0.97 | 0.38 | 0.17 | 0.30 | 12.4 | 1163 | 787 | 1.9 | 59% |
| Endgame | 45.0 | astral_scar | scout | unknown | 97.5% | 2.5% | 1.00 | 0.50 | 0.15 | 0.30 | 12.5 | 1173 | 755 | 1.9 | 57% |
| Endgame | 45.0 | astral_scar | scout | deep | 80.0% | 20.0% | 0.80 | 0.47 | 0.17 | 0.17 | 11.9 | 784 | 531 | 1.6 | 55% |
| Endgame | 45.0 | astral_scar | journey | safe | 85.0% | 15.0% | 1.62 | 0.75 | 0.20 | 0.70 | 29.5 | 1909 | 1196 | 3.4 | 45% |
| Endgame | 45.0 | astral_scar | journey | unknown | 77.5% | 22.5% | 1.88 | 0.93 | 0.15 | 0.97 | 29.9 | 2232 | 1346 | 3.1 | 37% |
| Endgame | 45.0 | astral_scar | journey | deep | 55.0% | 45.0% | 1.50 | 0.90 | 0.35 | 0.72 | 28.2 | 1506 | 966 | 2.2 | 29% |
| Endgame | 45.0 | astral_scar | deep | safe | 82.5% | 17.5% | 2.58 | 0.85 | 0.10 | 1.40 | 62.0 | 3367 | 2155 | 5.8 | 39% |
| Endgame | 45.0 | astral_scar | deep | unknown | 50.0% | 50.0% | 2.33 | 1.07 | 0.35 | 1.32 | 55.6 | 2552 | 1601 | 3.5 | 25% |
| Endgame | 45.0 | astral_scar | deep | deep | 27.5% | 72.5% | 1.93 | 1.10 | 0.45 | 0.78 | 48.0 | 1697 | 1171 | 1.9 | 13% |

## Regional and Legendary contracts

| Region | Lv | Contract | Route | Complete | Defeat | Combat | Hazard | Travel min | XP | Gil | Seals | Finish HP |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| emerald_wilds | 14.0 | boss | safe | 97.5% | 2.5% | 1.90 | 0.20 | 19.7 | 413 | 317 | 9.8 | 28% |
| emerald_wilds | 14.0 | boss | unknown | 77.5% | 22.5% | 1.77 | 0.23 | 19.8 | 353 | 297 | 7.8 | 19% |
| emerald_wilds | 14.0 | boss | deep | 55.0% | 45.0% | 1.52 | 0.33 | 19.9 | 295 | 280 | 5.5 | 9% |
| emerald_wilds | 14.0 | legendary | safe | 60.0% | 40.0% | 1.93 | 0.23 | 29.6 | 360 | 368 | 9.0 | 8% |
| emerald_wilds | 14.0 | legendary | unknown | 20.0% | 80.0% | 1.93 | 0.30 | 29.6 | 214 | 242 | 3.0 | 2% |
| emerald_wilds | 14.0 | legendary | deep | 12.5% | 87.5% | 2.05 | 0.30 | 29.7 | 236 | 292 | 1.9 | 1% |
| ashen_highlands | 24.0 | boss | safe | 100.0% | 0.0% | 2.10 | 0.45 | 23.8 | 752 | 419 | 10.0 | 36% |
| ashen_highlands | 24.0 | boss | unknown | 92.5% | 7.5% | 2.08 | 0.20 | 23.9 | 866 | 576 | 9.2 | 28% |
| ashen_highlands | 24.0 | boss | deep | 75.0% | 25.0% | 2.20 | 0.28 | 23.9 | 794 | 502 | 7.5 | 18% |
| ashen_highlands | 24.0 | legendary | safe | 90.0% | 10.0% | 2.23 | 0.42 | 35.6 | 837 | 520 | 13.5 | 16% |
| ashen_highlands | 24.0 | legendary | unknown | 50.0% | 50.0% | 2.45 | 0.45 | 35.7 | 675 | 542 | 7.5 | 6% |
| ashen_highlands | 24.0 | legendary | deep | 25.0% | 75.0% | 2.50 | 0.62 | 35.9 | 507 | 384 | 3.8 | 2% |
| mistfen_marshes | 32.0 | boss | safe | 97.5% | 2.5% | 1.98 | 0.60 | 25.7 | 1411 | 787 | 9.8 | 22% |
| mistfen_marshes | 32.0 | boss | unknown | 72.5% | 27.5% | 1.75 | 0.82 | 25.7 | 1148 | 682 | 7.2 | 13% |
| mistfen_marshes | 32.0 | boss | deep | 45.0% | 55.0% | 1.75 | 0.68 | 25.8 | 889 | 553 | 4.5 | 6% |
| mistfen_marshes | 32.0 | legendary | safe | 52.5% | 47.5% | 2.08 | 0.93 | 38.5 | 1060 | 640 | 7.9 | 6% |
| mistfen_marshes | 32.0 | legendary | unknown | 10.0% | 90.0% | 2.12 | 0.93 | 38.5 | 450 | 367 | 1.5 | 2% |
| mistfen_marshes | 32.0 | legendary | deep | 2.5% | 97.5% | 2.25 | 0.93 | 38.7 | 426 | 366 | 0.4 | 1% |
| frostveil_reach | 42.0 | boss | safe | 5.0% | 95.0% | 1.95 | 0.68 | 27.4 | 611 | 410 | 0.5 | 0% |
| frostveil_reach | 42.0 | boss | unknown | 0.0% | 100.0% | 1.65 | 0.90 | 27.6 | 359 | 251 | 0.0 | 0% |
| frostveil_reach | 42.0 | boss | deep | 0.0% | 100.0% | 2.05 | 0.65 | 27.7 | 674 | 469 | 0.0 | 0% |
| frostveil_reach | 42.0 | legendary | safe | 0.0% | 100.0% | 2.17 | 1.02 | 41.6 | 654 | 434 | 0.0 | 0% |
| frostveil_reach | 42.0 | legendary | unknown | 0.0% | 100.0% | 2.25 | 0.95 | 41.4 | 914 | 612 | 0.0 | 0% |
| frostveil_reach | 42.0 | legendary | deep | 0.0% | 100.0% | 2.10 | 1.05 | 41.6 | 871 | 603 | 0.0 | 0% |
| astral_scar | 50.0 | boss | safe | 82.5% | 17.5% | 1.77 | 0.45 | 30.5 | 5170 | 3499 | 8.2 | 28% |
| astral_scar | 50.0 | boss | unknown | 57.5% | 42.5% | 1.77 | 0.42 | 28.5 | 4512 | 3066 | 5.8 | 15% |
| astral_scar | 50.0 | boss | deep | 47.5% | 52.5% | 1.50 | 0.40 | 26.4 | 3644 | 2436 | 4.8 | 14% |
| astral_scar | 50.0 | legendary | safe | 57.5% | 42.5% | 1.82 | 0.55 | 42.4 | 5321 | 3663 | 8.6 | 10% |
| astral_scar | 50.0 | legendary | unknown | 22.5% | 77.5% | 1.77 | 0.53 | 40.7 | 3619 | 2671 | 3.4 | 4% |
| astral_scar | 50.0 | legendary | deep | 27.5% | 72.5% | 1.43 | 0.72 | 34.8 | 2935 | 2130 | 4.1 | 3% |
