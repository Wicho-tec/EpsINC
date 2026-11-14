"""
EpsInc - Map Definitions
Contains 5 colorful, original LEGO-inspired maps with corridors, corners, intersections and open arenas.
"""
from typing import Dict, List, Tuple
from server.models import MapDefinition, WallRect

LEGO_COLORS = {
    "red": "#E52521",
    "blue": "#0055BF",
    "yellow": "#F6D000",
    "green": "#009640",
    "orange": "#FF6B00",
    "purple": "#9B30FF",
    "cyan": "#00C3E3",
    "lime": "#78D64B",
    "white": "#FFFFFF",
    "dark_blue": "#001D6E"
}

def create_boundary(width: int, height: int, thickness: int = 40, color: str = "#E52521") -> List[WallRect]:
    """Generates standard outer boundary walls."""
    return [
        WallRect(x=0, y=0, w=width, h=thickness, color=color),                     # Top
        WallRect(x=0, y=height - thickness, w=width, h=thickness, color=color),     # Bottom
        WallRect(x=0, y=0, w=thickness, h=height, color=color),                     # Left
        WallRect(x=width - thickness, y=0, w=thickness, h=height, color=color)      # Right
    ]

# ---------------- MAP 1: Ciudad de Bloques (2400 x 1800) ----------------
def get_map_ciudad_bloques() -> MapDefinition:
    w, h = 2400, 1800
    walls = create_boundary(w, h, 40, LEGO_COLORS["blue"])
    
    # Central Plaza Buildings
    walls.extend([
        # Central square dividers
        WallRect(x=1050, y=750, w=300, h=40, color=LEGO_COLORS["yellow"]),
        WallRect(x=1050, y=1010, w=300, h=40, color=LEGO_COLORS["yellow"]),
        WallRect(x=1050, y=750, w=40, h=300, color=LEGO_COLORS["red"]),
        WallRect(x=1310, y=750, w=40, h=300, color=LEGO_COLORS["red"]),
        
        # Northwest quadrant
        WallRect(x=300, y=300, w=400, h=50, color=LEGO_COLORS["green"]),
        WallRect(x=300, y=300, w=50, h=350, color=LEGO_COLORS["orange"]),
        WallRect(x=550, y=500, w=250, h=50, color=LEGO_COLORS["yellow"]),
        WallRect(x=800, y=200, w=50, h=350, color=LEGO_COLORS["red"]),
        
        # Northeast quadrant
        WallRect(x=1500, y=300, w=500, h=50, color=LEGO_COLORS["green"]),
        WallRect(x=1950, y=300, w=50, h=400, color=LEGO_COLORS["purple"]),
        WallRect(x=1500, y=450, w=300, h=50, color=LEGO_COLORS["orange"]),
        WallRect(x=1300, y=200, w=50, h=350, color=LEGO_COLORS["blue"]),
        
        # Southwest quadrant
        WallRect(x=300, y=1450, w=450, h=50, color=LEGO_COLORS["purple"]),
        WallRect(x=300, y=1100, w=50, h=400, color=LEGO_COLORS["cyan"]),
        WallRect(x=500, y=1250, w=350, h=50, color=LEGO_COLORS["lime"]),
        WallRect(x=750, y=950, w=50, h=350, color=LEGO_COLORS["yellow"]),
        
        # Southeast quadrant
        WallRect(x=1600, y=1450, w=450, h=50, color=LEGO_COLORS["red"]),
        WallRect(x=2000, y=1100, w=50, h=400, color=LEGO_COLORS["blue"]),
        WallRect(x=1400, y=1250, w=450, h=50, color=LEGO_COLORS["green"]),
        WallRect(x=1400, y=950, w=50, h=350, color=LEGO_COLORS["orange"]),
        
        # Bouncing baffle pillars (LEGO brick pillars)
        WallRect(x=600, y=900, w=80, h=80, color=LEGO_COLORS["red"]),
        WallRect(x=1720, y=900, w=80, h=80, color=LEGO_COLORS["blue"]),
        WallRect(x=1160, y=400, w=80, h=80, color=LEGO_COLORS["yellow"]),
        WallRect(x=1160, y=1400, w=80, h=80, color=LEGO_COLORS["green"]),
    ])
    
    spawns = [
        (200, 200), (450, 200), (950, 200), (1450, 200), (2200, 200),
        (200, 800), (450, 750), (1950, 750), (2200, 800),
        (200, 1600), (550, 1600), (950, 1600), (1450, 1600), (2200, 1600),
        (900, 600), (1500, 600), (900, 1150), (1500, 1150), (1180, 880), (1180, 200)
    ]
    
    powerups = [
        (1180, 880), (600, 400), (1800, 400), (600, 1350), (1800, 1350),
        (350, 900), (2050, 900), (1180, 550), (1180, 1250)
    ]
    
    return MapDefinition(
        id="ciudad_bloques",
        name="Ciudad de Bloques",
        width=w,
        height=h,
        theme="lego_classic",
        background_color="#18233C",
        walls=walls,
        spawn_points=spawns,
        powerup_spawns=powerups
    )

# ---------------- MAP 2: Laberinto Neón (2600 x 2000) ----------------
def get_map_laberinto_neon() -> MapDefinition:
    w, h = 2600, 2000
    walls = create_boundary(w, h, 40, LEGO_COLORS["purple"])
    
    # Maze corridors with vibrant cyan, yellow, pink, and lime
    walls.extend([
        # Outer ring hallways
        WallRect(x=200, y=200, w=1000, h=40, color=LEGO_COLORS["cyan"]),
        WallRect(x=1400, y=200, w=1000, h=40, color=LEGO_COLORS["lime"]),
        WallRect(x=200, y=200, w=40, h=700, color=LEGO_COLORS["yellow"]),
        WallRect(x=2360, y=200, w=40, h=700, color=LEGO_COLORS["orange"]),
        
        WallRect(x=200, y=1100, w=40, h=700, color=LEGO_COLORS["lime"]),
        WallRect(x=2360, y=1100, w=40, h=700, color=LEGO_COLORS["cyan"]),
        WallRect(x=200, y=1760, w=1000, h=40, color=LEGO_COLORS["red"]),
        WallRect(x=1400, y=1760, w=1000, h=40, color=LEGO_COLORS["yellow"]),
        
        # Zig-zag corridors
        WallRect(x=450, y=450, w=600, h=40, color=LEGO_COLORS["yellow"]),
        WallRect(x=1050, y=450, w=40, h=400, color=LEGO_COLORS["red"]),
        WallRect(x=650, y=700, w=400, h=40, color=LEGO_COLORS["purple"]),
        
        WallRect(x=1550, y=450, w=600, h=40, color=LEGO_COLORS["orange"]),
        WallRect(x=1510, y=450, w=40, h=400, color=LEGO_COLORS["cyan"]),
        WallRect(x=1550, y=700, w=400, h=40, color=LEGO_COLORS["lime"]),
        
        WallRect(x=450, y=1510, w=600, h=40, color=LEGO_COLORS["cyan"]),
        WallRect(x=1050, y=1150, w=40, h=400, color=LEGO_COLORS["lime"]),
        WallRect(x=650, y=1250, w=400, h=40, color=LEGO_COLORS["yellow"]),
        
        WallRect(x=1550, y=1510, w=600, h=40, color=LEGO_COLORS["purple"]),
        WallRect(x=1510, y=1150, w=40, h=400, color=LEGO_COLORS["red"]),
        WallRect(x=1550, y=1250, w=400, h=40, color=LEGO_COLORS["cyan"]),
        
        # Center Chamber with 4 entry chutes
        WallRect(x=1150, y=850, w=300, h=40, color=LEGO_COLORS["yellow"]),
        WallRect(x=1150, y=1110, w=300, h=40, color=LEGO_COLORS["yellow"]),
        WallRect(x=1150, y=850, w=40, h=100, color=LEGO_COLORS["cyan"]),
        WallRect(x=1150, y=1050, w=40, h=100, color=LEGO_COLORS["cyan"]),
        WallRect(x=1410, y=850, w=40, h=100, color=LEGO_COLORS["lime"]),
        WallRect(x=1410, y=1050, w=40, h=100, color=LEGO_COLORS["lime"]),
        
        # Angled bounce studs
        WallRect(x=850, y=960, w=80, h=80, color=LEGO_COLORS["red"]),
        WallRect(x=1670, y=960, w=80, h=80, color=LEGO_COLORS["blue"]),
        WallRect(x=1260, y=550, w=80, h=80, color=LEGO_COLORS["orange"]),
        WallRect(x=1260, y=1370, w=80, h=80, color=LEGO_COLORS["purple"]),
    ])
    
    spawns = [
        (100, 100), (1300, 100), (2500, 100), (100, 950), (2500, 950),
        (100, 1900), (1300, 1900), (2500, 1900), (320, 320), (2280, 320),
        (320, 1680), (2280, 1680), (850, 550), (1750, 550), (850, 1450),
        (1750, 1450), (1300, 1000), (550, 950), (2050, 950), (1300, 400)
    ]
    
    powerups = [
        (1300, 1000), (750, 320), (1850, 320), (750, 1680), (1850, 1680),
        (350, 950), (2250, 950), (1300, 680), (1300, 1320), (850, 1100)
    ]
    
    return MapDefinition(
        id="laberinto_neon",
        name="Laberinto Neón",
        width=w,
        height=h,
        theme="cyber_lego",
        background_color="#0F1123",
        walls=walls,
        spawn_points=spawns,
        powerup_spawns=powerups
    )

# ---------------- MAP 3: Cruces de Juguete (2500 x 2500) ----------------
def get_map_cruces_juguete() -> MapDefinition:
    w, h = 2500, 2500
    walls = create_boundary(w, h, 45, LEGO_COLORS["red"])
    
    # Quad cross pattern
    cx, cy = w // 2, h // 2
    
    # 4 Grand Crossbars with openings
    walls.extend([
        # Central Horizontal dividers with center gateway
        WallRect(x=200, y=cy - 25, w=850, h=50, color=LEGO_COLORS["blue"]),
        WallRect(x=w - 1050, y=cy - 25, w=850, h=50, color=LEGO_COLORS["blue"]),
        
        # Central Vertical dividers with center gateway
        WallRect(x=cx - 25, y=200, w=50, h=850, color=LEGO_COLORS["yellow"]),
        WallRect(x=cx - 25, y=h - 1050, w=50, h=850, color=LEGO_COLORS["yellow"]),
        
        # 4 Diamond Corner Fortresses
        # Top-left fort
        WallRect(x=500, y=500, w=350, h=50, color=LEGO_COLORS["green"]),
        WallRect(x=500, y=500, w=50, h=350, color=LEGO_COLORS["orange"]),
        WallRect(x=650, y=650, w=200, h=50, color=LEGO_COLORS["purple"]),
        
        # Top-right fort
        WallRect(x=1650, y=500, w=350, h=50, color=LEGO_COLORS["green"]),
        WallRect(x=1950, y=500, w=50, h=350, color=LEGO_COLORS["orange"]),
        WallRect(x=1650, y=650, w=200, h=50, color=LEGO_COLORS["purple"]),
        
        # Bottom-left fort
        WallRect(x=500, y=1950, w=350, h=50, color=LEGO_COLORS["cyan"]),
        WallRect(x=500, y=1650, w=50, h=350, color=LEGO_COLORS["lime"]),
        WallRect(x=650, y=1800, w=200, h=50, color=LEGO_COLORS["red"]),
        
        # Bottom-right fort
        WallRect(x=1650, y=1950, w=350, h=50, color=LEGO_COLORS["cyan"]),
        WallRect(x=1950, y=1650, w=50, h=350, color=LEGO_COLORS["lime"]),
        WallRect(x=1650, y=1800, w=200, h=50, color=LEGO_COLORS["red"]),
        
        # Central roundabout obstacle blocks
        WallRect(x=cx - 150, y=cy - 150, w=70, h=70, color=LEGO_COLORS["red"]),
        WallRect(x=cx + 80, y=cy - 150, w=70, h=70, color=LEGO_COLORS["yellow"]),
        WallRect(x=cx - 150, y=cy + 80, w=70, h=70, color=LEGO_COLORS["green"]),
        WallRect(x=cx + 80, y=cy + 80, w=70, h=70, color=LEGO_COLORS["blue"]),
    ])
    
    spawns = [
        (250, 250), (cx, 120), (w - 250, 250),
        (250, cy), (w - 250, cy),
        (250, h - 250), (cx, h - 120), (w - 250, h - 250),
        (800, 300), (1700, 300), (800, 2200), (1700, 2200),
        (300, 800), (2200, 800), (300, 1700), (2200, 1700),
        (cx - 300, cy - 300), (cx + 300, cy - 300),
        (cx - 300, cy + 300), (cx + 300, cy + 300)
    ]
    
    powerups = [
        (cx, cy), (700, 700), (1800, 700), (700, 1800), (1800, 1800),
        (cx, 450), (cx, 2050), (450, cy), (2050, cy)
    ]
    
    return MapDefinition(
        id="cruces_juguete",
        name="Cruces de Juguete",
        width=w,
        height=h,
        theme="toy_junction",
        background_color="#1E2A38",
        walls=walls,
        spawn_points=spawns,
        powerup_spawns=powerups
    )

# ---------------- MAP 4: Fortaleza Pastel (2600 x 1800) ----------------
def get_map_fortaleza_pastel() -> MapDefinition:
    w, h = 2600, 1800
    walls = create_boundary(w, h, 40, "#FF69B4") # Pastel hot pink outer wall
    
    PASTEL = {
        "pink": "#FF8DA1",
        "mint": "#84E1BC",
        "lemon": "#FDF074",
        "lavender": "#C084FC",
        "peach": "#FDBA74",
        "sky": "#7DD3FC"
    }
    
    walls.extend([
        # Twin Castle Keeps (Left and Right)
        # Left Castle
        WallRect(x=400, y=400, w=500, h=50, color=PASTEL["mint"]),
        WallRect(x=400, y=1350, w=500, h=50, color=PASTEL["mint"]),
        WallRect(x=400, y=400, w=50, h=350, color=PASTEL["lavender"]),
        WallRect(x=400, y=1050, w=50, h=350, color=PASTEL["lavender"]),
        WallRect(x=850, y=400, w=50, h=300, color=PASTEL["pink"]),
        WallRect(x=850, y=1100, w=50, h=300, color=PASTEL["pink"]),
        
        # Right Castle
        WallRect(x=1700, y=400, w=500, h=50, color=PASTEL["peach"]),
        WallRect(x=1700, y=1350, w=500, h=50, color=PASTEL["peach"]),
        WallRect(x=1700, y=400, w=50, h=300, color=PASTEL["sky"]),
        WallRect(x=1700, y=1100, w=50, h=300, color=PASTEL["sky"]),
        WallRect(x=2150, y=400, w=50, h=350, color=PASTEL["lemon"]),
        WallRect(x=2150, y=1050, w=50, h=350, color=PASTEL["lemon"]),
        
        # Central Moat / Bridge Walkways
        WallRect(x=1100, y=250, w=400, h=50, color=PASTEL["lemon"]),
        WallRect(x=1100, y=1500, w=400, h=50, color=PASTEL["lemon"]),
        WallRect(x=1150, y=600, w=50, h=600, color=PASTEL["sky"]),
        WallRect(x=1400, y=600, w=50, h=600, color=PASTEL["lavender"]),
        
        # Castle Turret Pillars
        WallRect(x=625, y=875, w=60, h=60, color=PASTEL["pink"]),
        WallRect(x=1925, y=875, w=60, h=60, color=PASTEL["lemon"]),
        WallRect(x=1275, y=875, w=50, h=50, color=PASTEL["mint"]),
    ])
    
    spawns = [
        (150, 150), (1300, 150), (2450, 150),
        (625, 600), (625, 1200), (1925, 600), (1925, 1200),
        (150, 900), (2450, 900),
        (150, 1650), (1300, 1650), (2450, 1650),
        (300, 500), (2300, 500), (300, 1300), (2300, 1300),
        (1000, 900), (1600, 900), (1300, 450), (1300, 1350)
    ]
    
    powerups = [
        (1275, 900), (625, 900), (1925, 900), (1300, 300), (1300, 1500),
        (250, 900), (2350, 900), (625, 1300), (1925, 500)
    ]
    
    return MapDefinition(
        id="fortaleza_pastel",
        name="Fortaleza Pastel",
        width=w,
        height=h,
        theme="pastel_bricks",
        background_color="#231730",
        walls=walls,
        spawn_points=spawns,
        powerup_spawns=powerups
    )

# ---------------- MAP 5: Arena Caos 360 (2800 x 2200) ----------------
def get_map_coliseo_360() -> MapDefinition:
    w, h = 2800, 2200
    walls = create_boundary(w, h, 45, LEGO_COLORS["yellow"])
    
    cx, cy = w // 2, h // 2
    
    # Octagonal & Circular-feeling concentric rings of LEGO blocks
    walls.extend([
        # Outer Ring Barriers
        WallRect(x=500, y=300, w=600, h=50, color=LEGO_COLORS["red"]),
        WallRect(x=1700, y=300, w=600, h=50, color=LEGO_COLORS["blue"]),
        WallRect(x=500, y=1850, w=600, h=50, color=LEGO_COLORS["blue"]),
        WallRect(x=1700, y=1850, w=600, h=50, color=LEGO_COLORS["red"]),
        
        WallRect(x=300, y=600, w=50, h=400, color=LEGO_COLORS["green"]),
        WallRect(x=300, y=1200, w=50, h=400, color=LEGO_COLORS["orange"]),
        WallRect(x=2450, y=600, w=50, h=400, color=LEGO_COLORS["orange"]),
        WallRect(x=2450, y=1200, w=50, h=400, color=LEGO_COLORS["green"]),
        
        # Mid Ring segmented defenses
        WallRect(x=800, y=700, w=350, h=50, color=LEGO_COLORS["yellow"]),
        WallRect(x=1650, y=700, w=350, h=50, color=LEGO_COLORS["yellow"]),
        WallRect(x=800, y=1450, w=350, h=50, color=LEGO_COLORS["cyan"]),
        WallRect(x=1650, y=1450, w=350, h=50, color=LEGO_COLORS["cyan"]),
        
        WallRect(x=700, y=850, w=50, h=500, color=LEGO_COLORS["purple"]),
        WallRect(x=2050, y=850, w=50, h=500, color=LEGO_COLORS["purple"]),
        
        # Central Battle Hub
        WallRect(x=cx - 200, y=cy - 200, w=120, h=40, color=LEGO_COLORS["red"]),
        WallRect(x=cx + 80, y=cy - 200, w=120, h=40, color=LEGO_COLORS["red"]),
        WallRect(x=cx - 200, y=cy + 160, w=120, h=40, color=LEGO_COLORS["blue"]),
        WallRect(x=cx + 80, y=cy + 160, w=120, h=40, color=LEGO_COLORS["blue"]),
        
        # 4 Core Columns
        WallRect(x=cx - 80, y=cy - 80, w=160, h=160, color=LEGO_COLORS["lime"]),
    ])
    
    spawns = [
        (150, 150), (cx, 150), (w - 150, 150),
        (150, cy), (w - 150, cy),
        (150, h - 150), (cx, h - 150), (w - 150, h - 150),
        (550, 550), (2250, 550), (550, 1650), (2250, 1650),
        (1100, 500), (1700, 500), (1100, 1700), (1700, 1700),
        (900, cy), (1900, cy), (cx, cy - 450), (cx, cy + 450)
    ]
    
    powerups = [
        (cx, cy - 300), (cx, cy + 300), (cx - 400, cy), (cx + 400, cy),
        (550, 450), (2250, 450), (550, 1750), (2250, 1750),
        (cx, 150), (cx, h - 150)
    ]
    
    return MapDefinition(
        id="coliseo_360",
        name="Arena Caos 360",
        width=w,
        height=h,
        theme="gladiator_lego",
        background_color="#121824",
        walls=walls,
        spawn_points=spawns,
        powerup_spawns=powerups
    )

ALL_MAPS: Dict[str, MapDefinition] = {
    "ciudad_bloques": get_map_ciudad_bloques(),
    "laberinto_neon": get_map_laberinto_neon(),
    "cruces_juguete": get_map_cruces_juguete(),
    "fortaleza_pastel": get_map_fortaleza_pastel(),
    "coliseo_360": get_map_coliseo_360()
}

def get_map(map_id: str) -> MapDefinition:
    return ALL_MAPS.get(map_id, ALL_MAPS["ciudad_bloques"])
