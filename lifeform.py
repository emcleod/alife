import random
from typing import Tuple

class Lifeform:
    """Simple lifeform that lives on a grid square"""
    
    def __init__(self, grid_x: int, grid_y: int):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.health = 50  # Initial health (1-50 scale)
        self.max_health = 50
        self.alive = True
        self.movement_threshold = 10  # Can't move below this energy
        self.low_energy_timer = 0  # How long below threshold
        self.low_energy_limit = 5.0  # Seconds before max health drops
        
    def update(self, dt: float, food_available: float):
        """Update lifeform state"""
        if not self.alive:
            return
            
        # Gain health from food, lose health without food
        if food_available > 0:
            self.health = min(self.max_health, self.health + 1)
            self.low_energy_timer = 0  # Reset timer when eating
        else:
            self.health = max(0, self.health - 1)
            
        # Track low energy time
        if self.health < 20:  # Below 20 is "low energy"
            self.low_energy_timer += dt
            # Drop max health if low energy too long
            if self.low_energy_timer >= self.low_energy_limit and self.max_health > 25:
                self.max_health -= 1
                self.low_energy_timer = 0
        else:
            self.low_energy_timer = 0
            
        # Die if health reaches 0
        if self.health <= 0:
            self.alive = False
            
    def can_move(self) -> bool:
        """Check if lifeform has enough energy to move"""
        return self.health >= self.movement_threshold
        
    def move_to(self, new_x: int, new_y: int):
        """Move to new grid position"""
        if self.can_move():
            self.grid_x = new_x
            self.grid_y = new_y
            
    def fight(self, other: 'Lifeform') -> 'Lifeform':
        """Fight another lifeform, return winner"""
        if self.health > other.health:
            # Self wins but loses energy
            self.health = max(1, self.health - 5)
            other.alive = False
            return self
        else:
            # Other wins
            other.health = max(1, other.health - 5)
            self.alive = False
            return other
            
    def get_color(self) -> Tuple[int, int, int]:
        """Get color based on health (green=max, red=min)"""
        if not self.alive:
            return (100, 100, 100)  # Gray for dead
            
        # Interpolate between red and green based on health
        health_ratio = self.health / 50.0
        red = int(255 * (1 - health_ratio))
        green = int(255 * health_ratio)
        blue = 0
        return (red, green, blue)

class GridSquare:
    """A square on the grid that can contain food and lifeforms"""
    
    def __init__(self):
        self.food_amount = random.uniform(10, 30)  # Random initial food
        self.max_food = random.uniform(25, 40)     # Random max capacity
        self.regen_rate = random.uniform(0.5, 2.0) # Random regen rate per second
        self.lifeform = None
        
    def update(self, dt: float):
        """Update food regeneration"""
        if self.food_amount < self.max_food:
            self.food_amount = min(self.max_food, self.food_amount + self.regen_rate * dt)
            
    def consume_food(self, amount: float = 2.0) -> float:
        """Consume food from this square, return amount actually consumed"""
        consumed = min(self.food_amount, amount)
        self.food_amount -= consumed
        return consumed
        
    def has_food(self) -> bool:
        """Check if square has food available"""
        return self.food_amount > 1.0
        
    def place_lifeform(self, lifeform: Lifeform):
        """Place a lifeform on this square"""
        self.lifeform = lifeform
        
    def remove_lifeform(self):
        """Remove lifeform from this square"""
        self.lifeform = None
        
    def get_color(self) -> Tuple[int, int, int]:
        """Get background color based on food amount"""
        if self.lifeform and self.lifeform.alive:
            return self.lifeform.get_color()
        else:
            # Show food amount as green intensity
            food_ratio = self.food_amount / 40.0  # Assuming max possible is ~40
            green_intensity = int(50 + 100 * food_ratio)  # Base green + food green
            return (20, green_intensity, 20)