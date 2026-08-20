# 🎮 Game Presets & Anticheat Safety Manual

Comprehensive configuration recipes for popular gaming titles and automation scenarios.

---

## 1. Minecraft (PvP / Bridge / PotPvP)

* **Game Engine:** Java / OpenGL
* **Recommended Target:** `left` (Left Mouse Button) or `right` (Right Mouse Button for bridging)
* **Mode:** `rapid`
* **CPS Target:** `16 – 20 CPS` (`delay: 0.05s`)
* **Human Jitter:** **REQUIRED (Enabled)**
* **Dwell Time:** `15ms – 28ms`

### Strategy
Minecraft PvP algorithms cap hit registration at 20 ticks per second (1 tick = 50ms). Setting CPS higher than 20 causes packet waste and triggers anticheat CPS flags (e.g. GrimAC, Watchdog, Vulcan).
The **Human Jitter** feature introduces subtle timing variations that closely replicate physical jitter-clicking / butterfly clicking.

---

## 2. Roblox (Auto-Farming & AFK Grinding)

* **Game Engine:** Custom C++ / DirectInput
* **Recommended Target:** `e` (Interact / Action) or `left` (Weapon Attack)
* **Mode:** `rapid` (Looting) or `hold` (Continuous mining/channeling)
* **CPS Target:** `10 CPS` (`delay: 0.10s`)
* **Human Jitter:** `Enabled`

### Strategy
Roblox games often run client-side sanity checks. Keeping CPS around 10–12 CPS is completely safe for 24/7 AFK grinding while consuming under 8MB of system RAM.

---

## 3. ARPGs (Diablo IV, Path of Exile, Last Epoch)

* **Game Engine:** DirectX 12 / Vulkan
* **Recommended Target:** `f` (Interact / Pick up loot) or `1` / `2` / `3` (Skill rotations)
* **Mode:** `rapid`
* **CPS Target:** `25 – 30 CPS` (`delay: 0.035s – 0.04s`)
* **Human Jitter:** `Disabled` (for fastest item pickup)

### Strategy
Bypasses hand strain during high-density endgame mapping and dungeon crawling. Instantly vacuums all ground loot within proximity in under 100ms.

---

## 4. Tactical FPS Semi-Auto Trigger (CoD, Apex, Rust)

* **Game Engine:** IW Engine / Source / Unity
* **Recommended Target:** `left` (Fire)
* **Mode:** `rapid`
* **CPS Target:** `12 – 14 CPS` (`delay: 0.075s`)
* **Human Jitter:** `Enabled` (±8ms)

### Strategy
Turns semi-automatic pistols, designated marksman rifles (DMRs), and burst weapons into smooth full-auto fire rates without hitting weapon fire-rate buffer locks.
