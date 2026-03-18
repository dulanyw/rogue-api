class Config:
    DEBUG = False
    STORAGE_TYPE = "sqlite"
    DATABASE_URL = "sqlite:///rogue.db"
    MAX_GAMES = 1000
    INVENTORY_LIMIT = 26
    MAP_WIDTH = 80
    MAP_HEIGHT = 24
    VISION_RADIUS = 5
    FOG_OF_WAR = True
