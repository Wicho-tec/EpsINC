/**
 * EpsInc - Frontend Game Client (Ultra-Lightweight 1-Life Battle Royale)
 * Features:
 * - 1 Life: No respawn during the round.
 * - When killed, immediately displays "EPSLOSE" text overlay and spectates the killer.
 * - If killed by own bounced bullet, camera spectates a random living player.
 * - If spectated player dies, automatically switches to their killer or another living player.
 * - Last survivor gets triumphant "EPSWIN" victory screen.
 * - Ultra-lightweight LEGO rendering (zero vector stud overhead, zero blur filters).
 * - Smooth camera and responsive 60 FPS controls.
 */

const PALETTE = [
    "#00D2D3", "#FF6B6B", "#FECA57", "#1DD1A1", "#54A0FF",
    "#9B30FF", "#FF9FF3", "#FF9F43", "#48DBFB", "#10AC84"
];

// Color integer cache
const colorIntCache = new Map();
function getHexColor(hexStr, defaultHex = 0xFFE600) {
    if (!hexStr) return defaultHex;
    let cached = colorIntCache.get(hexStr);
    if (cached === undefined) {
        cached = Phaser.Display.Color.HexStringToColor(hexStr).color;
        colorIntCache.set(hexStr, cached);
    }
    return cached;
}

let selectedColor = PALETTE[0];
let selectedRoomId = "arena-1";
let myPlayerId = null;
let myPlayerToken = null;
let isSpectatorMode = false;
let myPlayerAlive = true;
let spectateTargetId = null;
let socket = null;
let phaserGame = null;
let activeScene = null;
let currentMap = null;

const clientEntities = {
    players: new Map(),
    bullets: new Map()
};

const gameState = {
    players: {},
    bullets: [],
    powerups: [],
    leaderboard: [],
    roomStatus: "waiting",
    winner: null
};

let lastInputSentTime = 0;
let lastSentMoveX = 0;
let lastSentMoveY = 0;
let lastSentAngle = 0;
let lastLeaderboardHash = "";

// ==================== LOBBY INITIALIZATION ====================
document.addEventListener("DOMContentLoaded", () => {
    initColorPalette();
    fetchRooms();

    document.getElementById("room-refresh").addEventListener("click", fetchRooms);
    document.getElementById("btn-play").addEventListener("click", () => joinGame(false));
    document.getElementById("btn-spectate").addEventListener("click", () => joinGame(true));
    
    document.getElementById("btn-play-again").addEventListener("click", () => {
        document.getElementById("epswin-overlay").style.display = "none";
        document.getElementById("epslose-overlay").style.display = "none";
        myPlayerAlive = true;
        spectateTargetId = null;
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: "restart_round" }));
        }
    });

    document.getElementById("btn-leave").addEventListener("click", () => {
        if (socket) socket.close();
        location.reload();
    });

    document.getElementById("btn-mute").addEventListener("click", (e) => {
        const isMuted = window.soundFX.toggleMute();
        e.target.textContent = isMuted ? "🔇 Silencio" : "🔊 Sonido";
    });

    document.getElementById("btn-toggle-bots").addEventListener("click", (e) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            const currentOn = e.target.textContent.includes("ON");
            const newStatus = !currentOn;
            e.target.textContent = newStatus ? "🤖 Bots: ON" : "🤖 Bots: OFF";
            socket.send(JSON.stringify({
                type: "toggle_bots",
                enabled: newStatus
            }));
        }
    });
});

function initColorPalette() {
    const container = document.getElementById("color-palette");
    container.innerHTML = "";
    PALETTE.forEach((color, idx) => {
        const dot = document.createElement("div");
        dot.className = "color-dot" + (idx === 0 ? " active" : "");
        dot.style.backgroundColor = color;
        dot.addEventListener("click", () => {
            document.querySelectorAll(".color-dot").forEach(d => d.classList.remove("active"));
            dot.classList.add("active");
            selectedColor = color;
        });
        container.appendChild(dot);
    });
}

async function fetchRooms() {
    try {
        const res = await fetch("/api/rooms");
        const rooms = await res.json();
        const listContainer = document.getElementById("rooms-list");
        listContainer.innerHTML = "";

        rooms.forEach((r) => {
            const card = document.createElement("div");
            card.className = "room-card" + (r.id === selectedRoomId ? " selected" : "");
            card.innerHTML = `
                <div>
                    <div class="room-title">${r.name}</div>
                    <div style="font-size:12px; color:var(--lego-yellow); font-weight:700;">🗺️ ${r.map_name}</div>
                </div>
                <div class="room-meta">
                    <span class="badge-tag">👥 ${r.player_count}/${r.max_players}</span>
                    <span class="badge-tag">${r.bots_enabled ? "🤖 Bots Activos" : "Solo Humanos"}</span>
                </div>
            `;
            card.addEventListener("click", () => {
                document.querySelectorAll(".room-card").forEach(c => c.classList.remove("selected"));
                card.classList.add("selected");
                selectedRoomId = r.id;
            });
            listContainer.appendChild(card);
        });
    } catch (e) {
        console.error("Error fetching rooms:", e);
    }
}

// ==================== NETWORKING & WEBSOCKET ====================
function joinGame(asSpectator = false) {
    isSpectatorMode = asSpectator;
    myPlayerAlive = !asSpectator;
    spectateTargetId = null;
    const playerName = document.getElementById("player-name").value.trim() || "Biberon";

    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${location.host}/ws/${selectedRoomId}`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        socket.send(JSON.stringify({
            name: playerName,
            color: selectedColor,
            is_spectator: isSpectatorMode,
            reconnect_token: myPlayerToken
        }));
    };

    socket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleServerMessage(msg);
    };

    socket.onclose = () => {
        console.log("Desconectado de EpsInc.");
    };

    socket.onerror = (err) => {
        console.error("WebSocket error:", err);
    };
}

function handleServerMessage(msg) {
    if (msg.type === "init_success") {
        myPlayerId = msg.player_id;
        myPlayerToken = msg.reconnect_token;
        currentMap = msg.map;
        myPlayerAlive = !msg.is_spectator;

        document.getElementById("lobby-screen").style.display = "none";
        document.getElementById("hud-overlay").style.display = "block";
        document.getElementById("hud-room-name").textContent = msg.room_name;

        if (msg.is_spectator) {
            document.getElementById("spectator-banner").style.display = "block";
        }

        if (!phaserGame) {
            initPhaserGame(msg.map);
        } else if (activeScene) {
            activeScene.setupMap(msg.map);
        }
    } else if (msg.type === "state_update") {
        gameState.players = msg.players;
        gameState.bullets = msg.bullets;
        gameState.powerups = msg.powerups;
        gameState.leaderboard = msg.leaderboard;
        gameState.roomStatus = msg.status;
        gameState.winner = msg.winner;

        // Check local player alive state
        if (myPlayerId && gameState.players[myPlayerId]) {
            myPlayerAlive = gameState.players[myPlayerId].alive;
        }

        syncInterpolationEntities(msg.players, msg.bullets);
        updateHUD();
        processEvents(msg.events);
    }
}

function syncInterpolationEntities(serverPlayers, serverBullets) {
    const activePids = new Set(Object.keys(serverPlayers));

    for (const [pid, sp] of Object.entries(serverPlayers)) {
        let ep = clientEntities.players.get(pid);
        if (!ep) {
            ep = {
                id: pid,
                name: sp.name,
                renderX: sp.x,
                renderY: sp.y,
                renderAngle: sp.angle,
                targetX: sp.x,
                targetY: sp.y,
                targetAngle: sp.angle,
                colorInt: getHexColor(sp.color),
                alive: sp.alive
            };
            clientEntities.players.set(pid, ep);
        } else {
            ep.name = sp.name;
            ep.targetX = sp.x;
            ep.targetY = sp.y;
            ep.targetAngle = sp.angle;
            ep.alive = sp.alive;
            if (Math.hypot(ep.renderX - sp.x, ep.renderY - sp.y) > 250) {
                ep.renderX = sp.x;
                ep.renderY = sp.y;
                ep.renderAngle = sp.angle;
            }
        }
    }

    for (const pid of clientEntities.players.keys()) {
        if (!activePids.has(pid)) {
            clientEntities.players.delete(pid);
        }
    }

    const activeBids = new Set();
    serverBullets.forEach(b => {
        activeBids.add(b.id);
        let eb = clientEntities.bullets.get(b.id);
        if (!eb) {
            eb = {
                id: b.id,
                renderX: b.x,
                renderY: b.y,
                targetX: b.x,
                targetY: b.y,
                vx: b.vx,
                vy: b.vy,
                colorInt: getHexColor(b.color, 0xFFE600)
            };
            clientEntities.bullets.set(b.id, eb);
        } else {
            eb.targetX = b.x;
            eb.targetY = b.y;
            eb.vx = b.vx;
            eb.vy = b.vy;
        }
    });

    for (const bid of clientEntities.bullets.keys()) {
        if (!activeBids.has(bid)) {
            clientEntities.bullets.delete(bid);
        }
    }
}

function updateHUD() {
    const lbHash = (gameState.leaderboard || []).map(p => `${p.id}:${p.alive}:${p.score}`).join("|");
    if (lbHash !== lastLeaderboardHash) {
        lastLeaderboardHash = lbHash;
        const lbContainer = document.getElementById("leaderboard-items");
        lbContainer.innerHTML = "";
        
        const livingCount = (gameState.leaderboard || []).filter(p => p.alive).length;
        const totalCount = (gameState.leaderboard || []).length;
        document.getElementById("player-count-badge").textContent = `${livingCount} VIVOS / ${totalCount}`;

        gameState.leaderboard.slice(0, 8).forEach((entry) => {
            const item = document.createElement("div");
            item.className = "lb-item" + (entry.id === myPlayerId ? " me" : "") + (!entry.alive ? " dead" : "");
            item.innerHTML = `
                <div style="display:flex; align-items:center; gap:6px;">
                    <span style="color:${entry.alive ? '#10B981' : '#EF4444'}">${entry.alive ? '●' : '✖'}</span>
                    <span style="color:${entry.color}">●</span>
                    <span>${entry.name}</span>
                </div>
                <div style="font-weight:900; color:var(--lego-yellow);">${entry.score} pts</div>
            `;
            lbContainer.appendChild(item);
        });
    }

    const me = gameState.players[myPlayerId];
    const powerHud = document.getElementById("power-hud");
    if (me && me.alive && (me.active_power || me.shield || me.speed_boost || me.multi_bounce)) {
        powerHud.classList.remove("hidden");
        const iconEl = document.getElementById("power-icon");
        const nameEl = document.getElementById("power-name");
        const descEl = document.getElementById("power-desc");

        if (me.shield) {
            iconEl.textContent = "🛡️";
            nameEl.textContent = "ESCUDO";
            descEl.textContent = "Protección contra proyectil";
        } else if (me.speed_boost) {
            iconEl.textContent = "⚡";
            nameEl.textContent = "SPEED BOOST";
            descEl.textContent = "Velocidad +60%";
        } else if (me.multi_bounce) {
            iconEl.textContent = "🔄";
            nameEl.textContent = "MULTI BOUNCE";
            descEl.textContent = "12 rebotes";
        } else if (me.active_power === "MEGA_BEAM") {
            iconEl.textContent = "💥";
            nameEl.textContent = "MEGA BEAM";
            descEl.textContent = "Rayo letal (2s advertencia)";
        } else if (me.active_power === "RAPID_BURST") {
            iconEl.textContent = "🎯";
            nameEl.textContent = "RAPID BURST";
            descEl.textContent = "Ráfaga cuádruple";
        }
    } else {
        powerHud.classList.add("hidden");
    }
}

function processEvents(events) {
    if (!events || !events.length) return;

    events.forEach(evt => {
        if (evt.type === "shoot_sound") {
            window.soundFX.playShoot(evt.rapid);
        } else if (evt.type === "bullet_bounce") {
            window.soundFX.playBounce();
            if (activeScene) activeScene.spawnBounceSparks(evt.x, evt.y);
        } else if (evt.type === "player_killed") {
            window.soundFX.playHit();
            addFeedMessage(`💥 ${evt.killer_name} eliminó a ${evt.victim_name}`);
            if (activeScene) activeScene.spawnExplosion(evt.x, evt.y);

            // Streak banner trigger
            if (evt.killer_id === myPlayerId && evt.streak >= 3) {
                showStreakBanner(evt.streak);
            }

            // === 1 LIFE LOGIC: IF YOU DIE, SHOW "EPSLOSE" AND SPECTATE KILLER ===
            if (evt.victim_id === myPlayerId) {
                myPlayerAlive = false;
                window.soundFX.playLose();

                // Show clean text EPSLOSE banner (requested by user)
                const loseOverlay = document.getElementById("epslose-overlay");
                const spectateLabel = document.getElementById("spectating-label");
                loseOverlay.style.display = "block";

                // Lock camera to killer or random living player
                spectateTargetId = evt.spectate_target_id;
                const targetPlayer = clientEntities.players.get(spectateTargetId);
                const targetName = targetPlayer ? targetPlayer.name : evt.killer_name;
                spectateLabel.textContent = `👁️ Espectando a: ${targetName}`;
            } else if (evt.victim_id === spectateTargetId) {
                // If the player we are spectating dies, switch to their killer or another living player!
                spectateTargetId = evt.spectate_target_id || findRandomLivingPlayerId();
                const targetPlayer = clientEntities.players.get(spectateTargetId);
                const spectateLabel = document.getElementById("spectating-label");
                if (targetPlayer && spectateLabel) {
                    spectateLabel.textContent = `👁️ Espectando a: ${targetPlayer.name}`;
                }
            }
        } else if (evt.type === "match_won") {
            handleMatchEnd(evt.winner_name, evt.winner_id === myPlayerId);
        } else if (evt.type === "match_restarted") {
            myPlayerAlive = true;
            spectateTargetId = null;
            document.getElementById("epslose-overlay").style.display = "none";
            document.getElementById("epswin-overlay").style.display = "none";
            addFeedMessage("🎮 ¡Nueva ronda iniciada! 1 vida para todos.");
        } else if (evt.type === "powerup_collected") {
            window.soundFX.playPowerup();
        } else if (evt.type === "beam_charging") {
            window.soundFX.playBeamCharge();
            if (activeScene) activeScene.showBeamCharging(evt.x, evt.y, evt.angle, evt.duration);
        } else if (evt.type === "mega_beam_fired") {
            window.soundFX.playMegaBeamFire();
            if (activeScene) activeScene.renderMegaBeam(evt.start_x, evt.start_y, evt.end_x, evt.end_y);
        }
    });
}

function findRandomLivingPlayerId() {
    const living = Array.from(clientEntities.players.values()).filter(p => p.alive && p.id !== myPlayerId);
    if (living.length > 0) {
        return living[Math.floor(Math.random() * living.length)].id;
    }
    return null;
}

function showStreakBanner(count) {
    window.soundFX.playStreak(count);
    const banner = document.getElementById("announcement-banner");
    const textEl = document.getElementById("announcement-text");
    textEl.textContent = `EPSTAKILL x${count}`;
    banner.style.display = "block";

    setTimeout(() => {
        banner.style.display = "none";
    }, 2200);
}

function handleMatchEnd(winnerName, didIWin) {
    const winOverlay = document.getElementById("epswin-overlay");
    const winTitle = document.getElementById("epswin-title");
    const winSubtitle = document.getElementById("epswin-subtitle");

    winOverlay.style.display = "block";

    if (didIWin) {
        window.soundFX.playWin();
        winTitle.textContent = "EPSWIN";
        winTitle.style.color = "#F6D000";
        winSubtitle.textContent = "¡ERES EL ÚLTIMO SUPERVIVIENTE EN PIE!";
    } else {
        winTitle.textContent = "EPSWIN";
        winTitle.style.color = "#FECA57";
        winSubtitle.textContent = `Ganador de la partida: ${winnerName}`;
    }
}

function addFeedMessage(text) {
    const feed = document.getElementById("kill-feed");
    const msg = document.createElement("div");
    msg.className = "kill-msg";
    msg.textContent = text;
    feed.appendChild(msg);

    setTimeout(() => {
        msg.remove();
    }, 3500);
}

// ==================== PHASER 3 GAME SCENE ====================
function initPhaserGame(mapData) {
    const config = {
        type: Phaser.AUTO,
        parent: "game-container",
        width: window.innerWidth,
        height: window.innerHeight,
        backgroundColor: mapData.background_color || "#101522",
        fps: {
            target: 60,
            forceSetTimeOut: false
        },
        physics: {
            default: "arcade",
            arcade: { gravity: { y: 0 }, debug: false }
        },
        scene: {
            preload: preloadScene,
            create: createScene,
            update: updateScene
        }
    };

    phaserGame = new Phaser.Game(config);
    window.addEventListener("resize", () => {
        if (phaserGame) {
            phaserGame.scale.resize(window.innerWidth, window.innerHeight);
        }
    });
}

function preloadScene() {}

function createScene() {
    activeScene = this;

    // Single set of graphics layers
    this.mapGraphics = this.add.graphics();
    this.beamGraphics = this.add.graphics();
    this.powerGraphics = this.add.graphics();
    this.bulletGraphics = this.add.graphics();
    this.playerGraphics = this.add.graphics();
    this.effectGraphics = this.add.graphics();

    this.cursors = this.input.keyboard.addKeys({
        up: Phaser.Input.Keyboard.KeyCodes.W,
        down: Phaser.Input.Keyboard.KeyCodes.S,
        left: Phaser.Input.Keyboard.KeyCodes.A,
        right: Phaser.Input.Keyboard.KeyCodes.D
    });

    this.input.on("pointerdown", (pointer) => {
        if (pointer.leftButtonDown() && socket && socket.readyState === WebSocket.OPEN && myPlayerAlive && !isSpectatorMode) {
            window.soundFX.playShoot();
            socket.send(JSON.stringify({
                type: "input",
                move_x: this.lastMoveX || 0,
                move_y: this.lastMoveY || 0,
                angle: this.lastAimAngle || 0,
                shoot: true
            }));
        }
    });

    this.setupMap(currentMap);
}

Phaser.Scene.prototype.setupMap = function(mapData) {
    if (!mapData) return;
    this.currentMap = mapData;
    this.cameras.main.setBounds(0, 0, mapData.width, mapData.height);

    // ULTRA-LIGHTWEIGHT LEGO BRICKS (Solid blocks with 3D bevels, zero vector stud loops)
    this.mapGraphics.clear();

    mapData.walls.forEach(wall => {
        const colorInt = getHexColor(wall.color);
        
        // Base LEGO block
        this.mapGraphics.fillStyle(colorInt, 1);
        this.mapGraphics.fillRect(wall.x, wall.y, wall.w, wall.h);

        // 3D Top Bevel Highlight
        this.mapGraphics.fillStyle(0xFFFFFF, 0.25);
        this.mapGraphics.fillRect(wall.x, wall.y, wall.w, 4);
        this.mapGraphics.fillRect(wall.x, wall.y, 4, wall.h);

        // 3D Bottom Bevel Shadow
        this.mapGraphics.fillStyle(0x000000, 0.35);
        this.mapGraphics.fillRect(wall.x, wall.y + wall.h - 4, wall.w, 4);
        this.mapGraphics.fillRect(wall.x + wall.w - 4, wall.y, 4, wall.h);

        // Lightweight stud accents (at corners/centers only to keep render calls minimal)
        const studStep = Math.max(32, Math.min(wall.w, wall.h) / 2);
        this.mapGraphics.fillStyle(0xFFFFFF, 0.3);
        for (let sx = wall.x + 16; sx < wall.x + wall.w - 8; sx += studStep) {
            for (let sy = wall.y + 16; sy < wall.y + wall.h - 8; sy += studStep) {
                this.mapGraphics.fillCircle(sx, sy, 4);
            }
        }
    });
};

function updateScene(time, delta) {
    if (!activeScene) return;
    const dt = delta * 0.001;

    let moveX = 0;
    let moveY = 0;

    if (myPlayerAlive && !isSpectatorMode) {
        if (this.cursors.left.isDown) moveX -= 1;
        if (this.cursors.right.isDown) moveX += 1;
        if (this.cursors.up.isDown) moveY -= 1;
        if (this.cursors.down.isDown) moveY += 1;
    }

    const worldPointer = this.input.activePointer.positionToCamera(this.cameras.main);
    let aimAngle = 0;

    const me = gameState.players[myPlayerId];
    const myClient = clientEntities.players.get(myPlayerId);

    // Camera following logic:
    // 1. If living: follow self
    // 2. If eliminated: follow killer / spectated target
    // 3. If in spectator mode: follow first living
    if (myPlayerAlive && me && me.alive && myClient) {
        aimAngle = Phaser.Math.Angle.Between(myClient.renderX, myClient.renderY, worldPointer.x, worldPointer.y);
        this.lastAimAngle = aimAngle;
        this.lastMoveX = moveX;
        this.lastMoveY = moveY;

        if (moveX !== 0 || moveY !== 0) {
            const norm = Math.hypot(moveX, moveY);
            const speed = me.speed_boost ? 220.0 * 1.6 : 220.0;
            myClient.renderX += (moveX / norm) * speed * dt;
            myClient.renderY += (moveY / norm) * speed * dt;
        }

        // Soft reconciliation
        myClient.renderX += (myClient.targetX - myClient.renderX) * 0.25;
        myClient.renderY += (myClient.targetY - myClient.renderY) * 0.25;
        myClient.renderAngle = aimAngle;

        this.cameras.main.startFollow({ x: myClient.renderX, y: myClient.renderY }, true, 0.15, 0.15);

        // Network input throttling
        const nowMs = performance.now();
        const inputChanged = (moveX !== lastSentMoveX || moveY !== lastSentMoveY || Math.abs(aimAngle - lastSentAngle) > 0.035);
        if (inputChanged || (nowMs - lastInputSentTime > 32)) {
            if (socket && socket.readyState === WebSocket.OPEN) {
                lastInputSentTime = nowMs;
                lastSentMoveX = moveX;
                lastSentMoveY = moveY;
                lastSentAngle = aimAngle;
                socket.send(JSON.stringify({
                    type: "input",
                    move_x: moveX,
                    move_y: moveY,
                    angle: aimAngle,
                    shoot: false
                }));
            }
        }
    } else {
        // SPECTATE MODE (Either killed or joined as spectator)
        let targetEntity = null;
        if (spectateTargetId && clientEntities.players.has(spectateTargetId)) {
            targetEntity = clientEntities.players.get(spectateTargetId);
            if (!targetEntity.alive) {
                // Find next living
                spectateTargetId = findRandomLivingPlayerId();
                targetEntity = spectateTargetId ? clientEntities.players.get(spectateTargetId) : null;
            }
        } else {
            spectateTargetId = findRandomLivingPlayerId();
            targetEntity = spectateTargetId ? clientEntities.players.get(spectateTargetId) : null;
        }

        if (targetEntity) {
            this.cameras.main.startFollow({ x: targetEntity.renderX, y: targetEntity.renderY }, true, 0.1, 0.1);
        }
    }

    // 2. Render PowerUps
    this.powerGraphics.clear();
    const pulseTime = time * 0.003;
    gameState.powerups.forEach(pu => {
        if (!pu.active) return;
        const pulse = 16 + Math.sin(pulseTime + pu.x) * 2;

        this.powerGraphics.fillStyle(0x00E5FF, 0.25);
        this.powerGraphics.fillCircle(pu.x, pu.y, pulse + 4);

        this.powerGraphics.fillStyle(0xFFD700, 1);
        this.powerGraphics.fillRoundedRect(pu.x - pulse, pu.y - pulse, pulse * 2, pulse * 2, 4);

        this.powerGraphics.fillStyle(0x000000, 0.85);
        this.powerGraphics.fillCircle(pu.x, pu.y, 6);
    });

    // 3. Render Projectiles
    this.bulletGraphics.clear();
    for (const eb of clientEntities.bullets.values()) {
        eb.renderX += (eb.targetX - eb.renderX) * 0.5 + eb.vx * dt * 0.5;
        eb.renderY += (eb.targetY - eb.renderY) * 0.5 + eb.vy * dt * 0.5;

        this.bulletGraphics.fillStyle(eb.colorInt, 0.4);
        this.bulletGraphics.fillCircle(eb.renderX, eb.renderY, 8);

        this.bulletGraphics.fillStyle(0xFFFFFF, 1);
        this.bulletGraphics.fillCircle(eb.renderX, eb.renderY, 4.5);
    }

    // 4. Render Biberones (Only living bottles are rendered)
    this.playerGraphics.clear();
    for (const [pid, ep] of clientEntities.players.entries()) {
        const sp = gameState.players[pid];
        if (!sp || !sp.alive || sp.is_spectator) continue;

        const isMe = pid === myPlayerId;
        
        if (!isMe) {
            ep.renderX += (ep.targetX - ep.renderX) * 0.35;
            ep.renderY += (ep.targetY - ep.renderY) * 0.35;
            ep.renderAngle = Phaser.Math.Angle.RotateTo(ep.renderAngle, ep.targetAngle, 0.35);
        }

        const px = ep.renderX;
        const py = ep.renderY;
        const angle = ep.renderAngle;
        const bottleColor = ep.colorInt || 0x00D2D3;

        const cosA = Math.cos(angle);
        const sinA = Math.sin(angle);

        const rot = (lx, ly) => ({
            x: px + (lx * cosA - ly * sinA),
            y: py + (lx * sinA + ly * cosA)
        });

        // 1. Bottle Body
        this.playerGraphics.fillStyle(0xF0F8FF, 0.95);
        this.playerGraphics.lineStyle(2, 0x94A3B8, 1);
        this.playerGraphics.fillCircle(px - cosA * 4, py - sinA * 4, 18);
        this.playerGraphics.strokeCircle(px - cosA * 4, py - sinA * 4, 18);

        // Liquid
        this.playerGraphics.fillStyle(bottleColor, 0.7);
        this.playerGraphics.fillCircle(px - cosA * 5, py - sinA * 5, 14);

        // 2. Screw Ring Cap
        this.playerGraphics.fillStyle(bottleColor, 1);
        this.playerGraphics.lineStyle(2, 0x1E293B, 1);
        const capCenter = rot(14, 0);
        this.playerGraphics.fillCircle(capCenter.x, capCenter.y, 11);
        this.playerGraphics.strokeCircle(capCenter.x, capCenter.y, 11);

        // 3. Rubber Nipple (Points to aim direction and shoots)
        this.playerGraphics.fillStyle(0xFFD180, 1);
        this.playerGraphics.lineStyle(2, 0xD4A373, 1);
        const nippleBase = rot(24, 0);
        const nippleTip = rot(32, 0);
        this.playerGraphics.fillCircle(nippleBase.x, nippleBase.y, 7);
        this.playerGraphics.fillCircle(nippleTip.x, nippleTip.y, 4.5);
        this.playerGraphics.strokeCircle(nippleTip.x, nippleTip.y, 4.5);

        // Shield Bubble
        if (sp.shield) {
            this.playerGraphics.fillStyle(0x00E5FF, 0.25);
            this.playerGraphics.lineStyle(2, 0x00E5FF, 0.85);
            this.playerGraphics.fillCircle(px, py, 28);
            this.playerGraphics.strokeCircle(px, py, 28);
        }

        // Speed trail
        if (sp.speed_boost) {
            this.playerGraphics.fillStyle(0xFF9100, 0.4);
            const backTrail = rot(-22, 0);
            this.playerGraphics.fillCircle(backTrail.x, backTrail.y, 8);
        }

        // Indicator
        this.playerGraphics.fillStyle(isMe ? 0x00C3E3 : (sp.is_bot ? 0x94A3B8 : 0xF6D000), 1);
        this.playerGraphics.fillCircle(px, py - 26, 4);
    }
}

// Visual Effects
Phaser.Scene.prototype.spawnBounceSparks = function(x, y) {
    if (!this.effectGraphics) return;
    this.effectGraphics.fillStyle(0xFFE600, 0.9);
    for (let i = 0; i < 3; i++) {
        const ox = (Math.random() - 0.5) * 12;
        const oy = (Math.random() - 0.5) * 12;
        this.effectGraphics.fillCircle(x + ox, y + oy, 2.5);
    }
    setTimeout(() => {
        if (this.effectGraphics) this.effectGraphics.clear();
    }, 70);
};

Phaser.Scene.prototype.spawnExplosion = function(x, y) {
    if (!this.effectGraphics) return;
    this.effectGraphics.fillStyle(0xFF3838, 0.85);
    this.effectGraphics.fillCircle(x, y, 28);
    setTimeout(() => {
        if (this.effectGraphics) this.effectGraphics.clear();
    }, 120);
};

Phaser.Scene.prototype.showBeamCharging = function(x, y, angle, duration) {
    let flashes = 0;
    const interval = setInterval(() => {
        if (!this.beamGraphics) return;
        flashes++;
        this.beamGraphics.clear();
        this.beamGraphics.lineStyle(flashes % 2 === 0 ? 3 : 1, 0xFF1744, 0.8);
        const endX = x + Math.cos(angle) * 1800;
        const endY = y + Math.sin(angle) * 1800;
        this.beamGraphics.lineBetween(x, y, endX, endY);
    }, 250);

    setTimeout(() => {
        clearInterval(interval);
        if (this.beamGraphics) this.beamGraphics.clear();
    }, duration * 1000);
};

Phaser.Scene.prototype.renderMegaBeam = function(x1, y1, x2, y2) {
    if (!this.beamGraphics) return;
    this.beamGraphics.clear();
    this.beamGraphics.lineStyle(16, 0xFF5252, 0.95);
    this.beamGraphics.lineBetween(x1, y1, x2, y2);
    this.beamGraphics.lineStyle(5, 0xFFFFFF, 1);
    this.beamGraphics.lineBetween(x1, y1, x2, y2);

    setTimeout(() => {
        if (this.beamGraphics) this.beamGraphics.clear();
    }, 400);
};
