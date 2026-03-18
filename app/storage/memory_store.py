class MemoryStore:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._store = {}
        return cls._instance
    
    def save(self, game_id, game_state):
        self._store[game_id] = game_state
    
    def load(self, game_id):
        return self._store.get(game_id)
    
    def delete(self, game_id):
        if game_id in self._store:
            del self._store[game_id]
            return True
        return False
    
    def exists(self, game_id):
        return game_id in self._store
    
    def clear(self):
        self._store.clear()
