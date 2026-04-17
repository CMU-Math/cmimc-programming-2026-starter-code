"""
Pygame visualizer for MazeSimulator.

Controls:
    Space       Play / Pause
    Right       Advance one step (while paused)
    R           Reset simulation
    Esc         Quit

Note: If engine.py's initialize() has the visualize_graph() call uncommented,
a matplotlib window will appear once at startup before the pygame window opens.
In the current repo those lines are commented out, so no matplotlib popup occurs.
"""

try:
    import pygame
except ImportError:
    raise ImportError(
        "pygame is required. Install it with:\n"
        "  pip install pygame\n"
        "or (uv project):\n"
        "  uv add pygame"
    )

import math
import time

import networkx as nx

from engine import MazeSimulator

# ── Window / layout ───────────────────────────────────────────────────────────
W, H        = 1280, 800
CTRL_H      = 100
GRAPH_H     = H - CTRL_H        # 700  — graph drawing area
CTRL_Y      = GRAPH_H           # y-coord where control strip begins
GRAPH_PAD   = 45                # padding inside graph area

# ── Sizes ─────────────────────────────────────────────────────────────────────
NODE_R   = 10
SLOT_R   = 14
BOT_R    = 16
GHOST_R  = 16
COIN_R_MIN = 5
COIN_R_MAX = 13

# ── Palette ───────────────────────────────────────────────────────────────────
C_BG        = ( 18,  18,  30)
C_EDGE      = ( 55,  60,  85)
C_NODE      = ( 65,  95, 160)
C_SLOT      = (210, 168,  28)
C_BOT       = ( 50, 130, 240)
C_GHOST     = (220,  60,  60)
C_COIN      = (255, 215,   0)
C_COIN_TEXT = ( 25,  18,   0)
C_FLASH     = (255, 252, 185)
C_HUD       = (210, 215, 225)
C_CTRL_BG   = ( 25,  25,  40)
C_DIVIDER   = ( 45,  50,  72)
C_BTN       = ( 55,  60,  90)
C_BTN_HOV   = ( 82,  88, 128)
C_BTN_DIS   = ( 38,  38,  56)
C_BTN_TXT   = (210, 215, 225)
C_BTN_DTXT  = ( 75,  78,  95)
C_SLD_TRK   = ( 55,  60,  92)
C_SLD_HND   = (120, 145, 220)

FLASH_DUR  = 0.20   # seconds a slot-pull flash lasts
MIN_SPD    = 0.5
MAX_SPD    = 120.0


# ── Helpers ───────────────────────────────────────────────────────────────────

def _t_to_speed(t: float) -> float:
    """Slider position [0, 1] → steps/sec (log scale)."""
    return MIN_SPD * (MAX_SPD / MIN_SPD) ** t


def _speed_to_t(spd: float) -> float:
    """Steps/sec → slider position [0, 1] (log scale)."""
    return math.log(spd / MIN_SPD) / math.log(MAX_SPD / MIN_SPD)


def _build_layout(graph, graph_style: int) -> dict[int, tuple[int, int]]:
    """Compute screen-space node positions using networkx layout."""
    G = nx.Graph()
    for i in range(graph.n):
        G.add_node(i)
    for i, node in enumerate(graph.nodes):
        for j in node.neighbors:
            if i < j:
                G.add_edge(i, j)

    if graph_style in (2, 3):
        raw = nx.kamada_kawai_layout(G)
    else:
        raw = nx.spring_layout(G, seed=42)

    xs = [p[0] for p in raw.values()]
    ys = [p[1] for p in raw.values()]
    span_x = max(max(xs) - min(xs), 1e-9)
    span_y = max(max(ys) - min(ys), 1e-9)
    scale  = min((W - 2 * GRAPH_PAD) / span_x, (GRAPH_H - 2 * GRAPH_PAD) / span_y)
    cx     = W / 2
    cy     = GRAPH_H / 2
    mx     = (max(xs) + min(xs)) / 2
    my     = (max(ys) + min(ys)) / 2

    return {
        nid: (int(cx + (x - mx) * scale), int(cy - (y - my) * scale))
        for nid, (x, y) in raw.items()
    }


def _lerp(a: tuple, b: tuple, t: float) -> tuple[float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _draw_button(surf, font, rect, label, *, hover=False, disabled=False):
    bg  = C_BTN_DIS if disabled else (C_BTN_HOV if hover else C_BTN)
    fg  = C_BTN_DTXT if disabled else C_BTN_TXT
    pygame.draw.rect(surf, bg,  rect, border_radius=6)
    pygame.draw.rect(surf, C_DIVIDER, rect, width=1, border_radius=6)
    txt = font.render(label, True, fg)
    surf.blit(txt, txt.get_rect(center=rect.center))


# ── Main entry point ──────────────────────────────────────────────────────────

def run_visualizer(bot, ghost, graph_style, slots_style, seed, size=100, steps=2000):
    """
    Open an interactive pygame window that lets you watch MazeSimulator run.

    Parameters match MazeSimulator.initialize() exactly.  Speed is adjustable
    at runtime; the simulation can be paused, stepped, or reset.
    """
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("MazeSimulator Visualizer")
    clock = pygame.time.Clock()

    font_hud  = pygame.font.SysFont("monospace", 16)
    font_btn  = pygame.font.SysFont("monospace", 14)
    font_node = pygame.font.SysFont("monospace", 10)
    font_coin = pygame.font.SysFont("monospace", 11, bold=True)
    font_hint = pygame.font.SysFont("monospace", 12)

    show_labels = size <= 40

    # ── Inner helpers ─────────────────────────────────────────────────────────

    def _init_sim() -> MazeSimulator:
        sim = MazeSimulator()
        sim.initialize(bot, ghost, graph_style, slots_style, seed, size, steps)
        return sim

    # ── State (mutable, mutated by closures) ──────────────────────────────────
    sim   = _init_sim()
    npos  = _build_layout(sim.graph, graph_style)   # screen positions

    paused       = True
    done         = False
    error: list[str] = []

    speed    = 10.0
    tick_dur = 1.0 / speed
    tick_acc = 0.0
    frozen_prog = 0.0   # animation progress frozen when paused

    # animation anchors: interpolate from → to over one tick
    bot_fr   = sim.bot_info["pos"]
    bot_to   = sim.bot_info["pos"]
    ghost_fr = sim.ghost_info["pos"]
    ghost_to = sim.ghost_info["pos"]

    flash: dict[int, float] = {}   # node_idx → wall-clock time of last pull

    # ── Control strip geometry ────────────────────────────────────────────────
    SLD_X, SLD_W, SLD_Y = 52, 390, CTRL_Y + 63
    BTN_Y, BTN_H        = CTRL_Y + 32, 36
    btn_pause = pygame.Rect(462, BTN_Y, 110, BTN_H)
    btn_step  = pygame.Rect(582, BTN_Y,  90, BTN_H)
    btn_reset = pygame.Rect(682, BTN_Y,  90, BTN_H)

    slider_t = _speed_to_t(speed)
    dragging = False

    # ── Closures ──────────────────────────────────────────────────────────────

    def _advance() -> None:
        nonlocal bot_fr, bot_to, ghost_fr, ghost_to, done

        if done:
            return

        pb = sim.bot_info["pos"]
        pg = sim.ghost_info["pos"]

        try:
            done = sim.step()
        except Exception as exc:
            error.append(str(exc))
            done = True
            return

        bot_fr,   bot_to   = pb, sim.bot_info["pos"]
        ghost_fr, ghost_to = pg, sim.ghost_info["pos"]

        # Flash nodes where a slot was pulled this tick.
        # A player that stays put at a slot node has spun.
        now = time.perf_counter()
        if bot_to == bot_fr and sim.graph.nodes[bot_fr].slot is not None:
            flash[bot_fr] = now
        if ghost_to == ghost_fr and sim.graph.nodes[ghost_fr].slot is not None:
            flash[ghost_fr] = now

    def _reset() -> None:
        nonlocal sim, npos, paused, done
        nonlocal tick_acc, frozen_prog
        nonlocal bot_fr, bot_to, ghost_fr, ghost_to

        sim   = _init_sim()
        npos  = _build_layout(sim.graph, graph_style)
        paused = True
        done   = False
        error.clear()
        tick_acc = 0.0
        frozen_prog = 0.0
        bot_fr   = sim.bot_info["pos"]
        bot_to   = sim.bot_info["pos"]
        ghost_fr = sim.ghost_info["pos"]
        ghost_to = sim.ghost_info["pos"]
        flash.clear()

    # ── Main loop ─────────────────────────────────────────────────────────────
    last_t  = time.perf_counter()
    running = True

    while running:
        now = time.perf_counter()
        dt  = min(now - last_t, 0.1)   # clamp large gaps (e.g. window drag)
        last_t = now
        mp = pygame.mouse.get_pos()

        # ── Events ────────────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_SPACE:
                    if not done:
                        paused = not paused
                        if paused:
                            frozen_prog = min(1.0, tick_acc / max(tick_dur, 1e-9))
                elif ev.key == pygame.K_RIGHT:
                    if paused and not done:
                        _advance()
                        frozen_prog = 1.0
                elif ev.key == pygame.K_r:
                    _reset()

            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                hx = SLD_X + int(slider_t * SLD_W)
                if abs(mp[0] - hx) <= 13 and abs(mp[1] - SLD_Y) <= 13:
                    dragging = True
                elif btn_pause.collidepoint(mp):
                    if not done:
                        paused = not paused
                        if paused:
                            frozen_prog = min(1.0, tick_acc / max(tick_dur, 1e-9))
                elif btn_step.collidepoint(mp):
                    if paused and not done:
                        _advance()
                        frozen_prog = 1.0
                elif btn_reset.collidepoint(mp):
                    _reset()

            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                dragging = False

            elif ev.type == pygame.MOUSEMOTION and dragging:
                slider_t = max(0.0, min(1.0, (mp[0] - SLD_X) / SLD_W))
                speed    = _t_to_speed(slider_t)
                tick_dur = 1.0 / speed

        # ── Advance simulation ────────────────────────────────────────────────
        if not paused and not done:
            tick_acc += dt
            while tick_acc >= tick_dur and not done:
                _advance()
                tick_acc -= tick_dur

        # Interpolation progress for smooth animation
        if paused:
            prog = frozen_prog
        else:
            prog = min(1.0, tick_acc / max(tick_dur, 1e-9))

        # ── Draw: graph area ──────────────────────────────────────────────────
        screen.fill(C_BG)

        # Edges
        for i, node in enumerate(sim.graph.nodes):
            for j in node.neighbors:
                if i < j:
                    pygame.draw.line(screen, C_EDGE, npos[i], npos[j], 1)

        # Expire old flashes
        expired = [k for k, t0 in flash.items() if now - t0 >= FLASH_DUR]
        for k in expired:
            del flash[k]

        # Nodes
        for i in range(sim.graph.n):
            px, py = npos[i]
            is_slot = sim.graph.nodes[i].slot is not None
            r         = SLOT_R if is_slot else NODE_R
            base_col  = C_SLOT if is_slot else C_NODE

            t0 = flash.get(i)
            if t0 is not None:
                alpha = 1.0 - (now - t0) / FLASH_DUR
                color = tuple(int(b + (f - b) * alpha) for b, f in zip(base_col, C_FLASH))
            else:
                color = base_col

            pygame.draw.circle(screen, color, (px, py), r)

            if show_labels:
                lbl = font_node.render(str(i), True, (200, 200, 210))
                screen.blit(lbl, lbl.get_rect(center=(px, py)))

        # Coins stored at nodes
        for nid, amt in sim.coins_stored.items():
            if amt <= 0:
                continue
            px, py  = npos[nid]
            node_r  = SLOT_R if sim.graph.nodes[nid].slot is not None else NODE_R
            # Visual radius: log-scale, capped
            cr      = min(COIN_R_MIN + int(math.log1p(min(amt, 400)) * 1.8), COIN_R_MAX)
            coin_cy = py - node_r - cr - 4
            pygame.draw.circle(screen, C_COIN, (px, coin_cy), cr)
            lbl = font_coin.render(str(amt), True, C_COIN_TEXT)
            screen.blit(lbl, lbl.get_rect(center=(px, coin_cy)))

        # Bot and Ghost (interpolated, with overlap separation)
        bx, by = _lerp(npos[bot_fr],   npos[bot_to],   prog)
        gx, gy = _lerp(npos[ghost_fr], npos[ghost_to], prog)
        bx, by, gx, gy = int(bx), int(by), int(gx), int(gy)

        dist = math.hypot(bx - gx, by - gy)
        if dist < BOT_R + GHOST_R:
            push = (BOT_R + GHOST_R - dist) / 2 + 3
            bx  -= int(push)
            gx  += int(push)

        pygame.draw.circle(screen, C_BOT,   (bx, by), BOT_R)
        pygame.draw.circle(screen, C_GHOST, (gx, gy), GHOST_R)

        # ── Draw: HUD (top-left) ──────────────────────────────────────────────
        hud_lines = [
            f"Step:  {sim.current_step} / {sim.total_steps}",
            f"Coins: {sim.coins}",
            f"Speed: {speed:.1f} s/s",
        ]
        if paused:
            hud_lines.append("PAUSED")
        if done:
            hud_lines.append("DONE")
        if error:
            hud_lines.append(f"ERROR: {error[-1][:55]}")

        hy = 14
        for line in hud_lines:
            col  = (255, 90, 90) if line.startswith("ERROR") else C_HUD
            surf = font_hud.render(line, True, col)
            screen.blit(surf, (14, hy))
            hy  += 22

        # ── Draw: control strip ───────────────────────────────────────────────
        pygame.draw.rect(screen, C_CTRL_BG, (0, CTRL_Y, W, CTRL_H))
        pygame.draw.line(screen, C_DIVIDER, (0, CTRL_Y), (W, CTRL_Y), 1)

        # Speed slider
        spd_lbl = font_btn.render(f"Speed: {speed:.1f} s/s", True, C_BTN_TXT)
        screen.blit(spd_lbl, (SLD_X, CTRL_Y + 14))
        pygame.draw.rect(screen, C_SLD_TRK, (SLD_X, SLD_Y - 4, SLD_W, 8), border_radius=4)
        hx_px = SLD_X + int(slider_t * SLD_W)
        pygame.draw.circle(screen, C_SLD_HND, (hx_px, SLD_Y), 11)
        for end_label, end_x in [("0.5", SLD_X), ("120", SLD_X + SLD_W - 20)]:
            screen.blit(font_hint.render(end_label, True, (95, 100, 130)), (end_x, SLD_Y + 15))

        # Buttons
        _draw_button(screen, font_btn, btn_pause,
                     "Pause" if not paused else "Resume",
                     hover=btn_pause.collidepoint(mp), disabled=done)
        _draw_button(screen, font_btn, btn_step, "Step >",
                     hover=btn_step.collidepoint(mp), disabled=not paused or done)
        _draw_button(screen, font_btn, btn_reset, "Reset",
                     hover=btn_reset.collidepoint(mp))

        # Keyboard hints
        for hint, ky in [
            ("SPACE   play/pause", CTRL_Y + 18),
            ("→       step",       CTRL_Y + 36),
            ("R       reset",      CTRL_Y + 54),
            ("ESC     quit",       CTRL_Y + 72),
        ]:
            screen.blit(font_hint.render(hint, True, (78, 83, 108)), (810, ky))

        # Color legend
        legend = [(C_BOT, "Bot"), (C_GHOST, "Ghost"), (C_SLOT, "Slot node"), (C_COIN, "Coins")]
        lx, ly = 1060, CTRL_Y + 18
        for col, label in legend:
            pygame.draw.circle(screen, col, (lx, ly + 6), 6)
            screen.blit(font_hint.render(label, True, (155, 160, 180)), (lx + 14, ly))
            ly += 20

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    from submission import SubmissionBot, SubmissionGhost
    run_visualizer(SubmissionBot, SubmissionGhost, graph_style=3, slots_style=1, seed=42)
