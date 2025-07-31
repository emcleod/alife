import random
import math
from typing import Tuple, Optional
import itertools

counter = itertools.count()

#TODO everything that's uniform should be Gaussian
class GridSquare:
    """A square on the grid that can contain food and lifeforms"""
    
    def __init__(self, food_rng: random.Random):
        self.food_rng = food_rng  # Dedicated RNG for this square's food behavior
        self.food_amount = food_rng.uniform(10, 30)  # Random initial food
        self.max_food = food_rng.uniform(25, 70)     # Random max capacity  
        # Increase regen rate if there's more food in the first place      
        self.regen_rate = food_rng.uniform(1.0, 12 * self.max_food / 70) # Random regen rate per second
        self.base_regen_rate = self.regen_rate       # Store original for habitat modifications
        self.lifeform = None
        
    def get_seasonal_multiplier(self, time_period: float) -> float:
        """Calculate seasonal food multiplier based on current time period"""
        # Convert time periods to seasonal cycle (0 to 2π over 52 periods)
        seasonal_angle = (time_period % 52) * (2 * math.pi / 52)
        
        # Create seasonal curve: 0.4 in winter, 1.6 in summer
        # Using cosine shifted so winter is at angle 0 (time_period 0 and 52)
        base_multiplier = 1.0 + 0.6 * math.cos(seasonal_angle - math.pi)
        
        return base_multiplier
        
    def regenerate_food(self, dt: float, time_period: float):
        """Regenerate or decrease food over time with random variation and seasonal effects"""
        # Check if we should start a depletion period
        if not hasattr(self, 'depletion_timer'):
            self.depletion_timer = 0
            self.depletion_duration = 0
        
        # Randomly start depletion (small chance each update)
        if self.depletion_timer <= 0 and self.food_rng.random() < 0.02:  # 2% chance per update
            self.depletion_timer = self.food_rng.uniform(6.0, 10.0)  # 6-10 seconds of depletion
            self.depletion_duration = self.depletion_timer
        
        # Get seasonal multiplier for this square
        seasonal_multiplier = self.get_seasonal_multiplier(time_period)
        
        # Apply seasonal effect to regeneration rate
        seasonal_regen_rate = self.regen_rate * seasonal_multiplier
        
        # Apply food change based on current state
        if self.depletion_timer > 0:
            # Decrease food during depletion period (less affected by seasons)
            depletion_rate = seasonal_regen_rate * 0.7  # Slightly slower than regeneration
            self.food_amount -= depletion_rate * dt
            if self.food_amount < 0:
                self.food_amount = 0
            self.depletion_timer -= dt
        else:
            # Seasonal regeneration
            seasonal_max = self.max_food * seasonal_multiplier
            if self.food_amount < seasonal_max:
                self.food_amount += seasonal_regen_rate * dt
                # Cap at seasonal maximum
                if self.food_amount > seasonal_max:
                    self.food_amount = seasonal_max
            elif seasonal_multiplier < 1.0 and self.food_amount > seasonal_max:
                # In winter, food decays to lower seasonal maximum
                self.food_amount -= (self.regen_rate * 0.3) * dt
                if self.food_amount < seasonal_max:
                    self.food_amount = seasonal_max
            
    def consume_food(self, amount: float = 2.0) -> float:
        actual_consumed = min(amount, self.food_amount)
        self.food_amount -= actual_consumed
        return actual_consumed
        
    def has_food(self) -> bool:
        """Check if square has any food available"""
        return self.food_amount > 50.0  # Higher threshold - need substantial food
        
    def place_lifeform(self, lifeform):
        pass

    def remove_lifeform(self):
        pass
        
    def get_color(self) -> Tuple[int, int, int]:
        """Get background color based on food amount"""
        # Calculate ratio from 0.0 (no food) to 1.0 (max food)
        food_ratio = self.food_amount / self.max_food
        
        # Define colors
        muted_green = (85, 107, 47)    # Max food color (DarkOliveGreen)
        light_brown = (205, 133, 63)   # Min food color (Peru)
        
        # Linear interpolation between light brown and muted green
        r = int(light_brown[0] + (muted_green[0] - light_brown[0]) * food_ratio)
        g = int(light_brown[1] + (muted_green[1] - light_brown[1]) * food_ratio)
        b = int(light_brown[2] + (muted_green[2] - light_brown[2]) * food_ratio)
        
        return (r, g, b)


class Lifeform:
    """Simple lifeform that lives on a grid square"""
    
    # Class variables for future breeding
    fade_time = 7.0  # Time for dead lifeforms to fade away
    movement_cost = 3.0  # Health cost for moving
    
    def __init__(self, grid_x: int, grid_y: int, lifeform_rng: random.Random, max_x: int, max_y: int, 
                 max_health: float = -1, movement_threshold: float = -1):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.lifeform_rng = lifeform_rng
        
        # Random properties for each individual
        # Max health varies or is inherited from parent
        self.max_health = lifeform_rng.uniform(40, 60) if max_health < 0 else max_health 
        # Start at full health
        self.health = self.max_health  
        # Movement threshold varies or is inherited from parent
        self.movement_threshold = lifeform_rng.uniform(8, 15) if movement_threshold < 0 else movement_threshold
        # Food required per second
        self.food_per_second = int(lifeform_rng.uniform(2, 7))
        self.alive = True
        self.death_timer = -1.0  # Time since death (for displaying fade)
        self.id = next(counter)
        self.max_x = max_x
        self.max_y = max_y

    def reproduce(self, current_square: GridSquare, grid_x: int, grid_y: int, max_x: int, max_y: int) -> Optional['Lifeform']:
        # chance of reproduction if lifeform is healthy depends on amount of food
        reproduction_chance = 1 - (0.025 * current_square.food_amount / 700)
        # if it's healthy it will reproduce by chance
        if self.health > self.max_health * 0.8 and self.lifeform_rng.uniform(0, 1) > reproduction_chance: 
            # Inherit health and stamina from parent
            max_health = self.max_health * self.lifeform_rng.uniform(0.85, 1.15)
            movement_threshold = self.movement_threshold * self.lifeform_rng.uniform(0.85, 1.15)
            return Lifeform(grid_x, grid_y, self.lifeform_rng, max_x, max_y, max_health, movement_threshold)
        return None


    def update(self, dt: float, time_period: float, current_square: GridSquare):
        """Update lifeform behavior"""
        if not self.alive:
            return

        if current_square.has_food():
            # Consume food and convert to health
            food_consumed = current_square.consume_food(self.food_per_second * dt)  
            health_gained = food_consumed * 2.0  # Convert food to health (2:1 ratio)
            
            self.health += health_gained
            # Cap at max health
            if self.health > self.max_health:
                self.health = self.max_health
        else:
            move_list = [-1, 0, 1]
            dx = random.choice(move_list)
            dy = random.choice(move_list)
            if dx + self.grid_x < 0:
                dx = 1
            elif dx + self.grid_x >= self.max_x:
                dx = -1
            if dy + self.grid_y < 0:
                dy = 1
            elif dy + self.grid_y >= self.max_y:
                dy = -1
            has_moved = self.move_to(dx + self.grid_x, dy + self.grid_y, time_period) 
            if not has_moved:
                self.alive = False
                self.death_timer = 0
                return

        # Basic health decay over time (hunger)
        hunger_rate = 1.0  # Health lost per second when not eating
        self.health -= hunger_rate * dt
        
        # Check if died from health loss
        if self.health <= 0:
            self.alive = False
            self.death_timer = 0

    def can_move(self, time_period: float = 0) -> bool:
        """Check if lifeform has enough health to move"""
        if not self.alive:
            return False
            
        # Calculate seasonal movement cost multiplier
        seasonal_angle = (time_period % 52) * (2 * math.pi / 52)
        # Higher cost in winter (seasonal_angle near 0), normal in summer (seasonal_angle near π)
        seasonal_cost_multiplier = 1.0 + 0.5 * math.cos(seasonal_angle)  # 1.5x in winter, 0.5x in summer
        
        total_movement_cost = self.movement_cost * seasonal_cost_multiplier
        return self.health > self.movement_threshold and self.health >= total_movement_cost

    def move_to(self, new_x: int, new_y: int, time_period: float = 0):        
        """Move to new position and pay movement cost"""
        if not self.can_move(time_period):
            return False
            
        # Calculate seasonal movement cost
        seasonal_angle = (time_period % 52) * (2 * math.pi / 52)
        seasonal_cost_multiplier = 1.0 + 0.5 * math.cos(seasonal_angle)
        total_movement_cost = self.movement_cost * seasonal_cost_multiplier
        
        # Pay movement cost
        self.health -= total_movement_cost
        if self.health < 0:
            self.health = 0
            
        if new_x > 9 or new_y > 9:
            pass
        # Move to new position
        self.grid_x = new_x
        self.grid_y = new_y
        return True

    def fight(self, other: 'Lifeform', time_period: float) -> None:        
        """Fight with another lifeform"""
        # Are they going to fight
        if self.lifeform_rng.uniform(0, 1) > 0.8:
            won_fight = self.start_fighting(other)
            if other.death_timer >= 0:
                # it's dead
                return
            # Where will the other one run to
            if won_fight:
                move_list = [-1, 0, 1]
                dx = random.choice(move_list)
                dy = random.choice(move_list)
                if dx + other.grid_x < 0:
                    dx = 1
                elif dx + other.grid_x >= other.max_x:
                    dx = -1
                if dy + other.grid_y < 0:
                    dy = 1
                elif dy + other.grid_y >= other.max_y:
                    dy = -1
                # other one tries to flee
                has_moved = other.move_to(dx + other.grid_x, dy + other.grid_y, time_period)
                if not has_moved:
                    # Have to carry on fighting
                    self.fight(other, time_period)
            else:
                if self.death_timer >= 0:
                    # it's dead
                    return
                # Where will the lifeform run to
                move_list = [-1, 0, 1]
                dx = random.choice(move_list)
                dy = random.choice(move_list)
                if dx + self.grid_x < 0:
                    dx = 1
                elif dx + self.grid_x >= self.max_x:
                    dx = -1
                if dy + self.grid_y < 0:
                    dy = 1
                elif dy + self.grid_y >= self.max_y:
                    dy = -1
                # try to flee
                has_moved = self.move_to(dx + self.grid_x, dy + self.grid_y, time_period)
                if not has_moved:
                    self.fight(other, time_period)
        return
        
    def start_fighting(self, other: 'Lifeform') -> bool:
        # It will, so find out when it will run away
        life_remaining_before_flee = 0 if self.lifeform_rng.uniform(0, 1) < 0.2 else self.lifeform_rng.uniform(0, 1) * self.health
        other_life_remaining_before_flee = 0 if other.lifeform_rng.uniform(0, 1) < 0.2 else other.lifeform_rng.uniform(0, 1) * other.health
        # start fighting
        while self.health > life_remaining_before_flee and other.health > other_life_remaining_before_flee:
            damage_inflicted = self.lifeform_rng.uniform(0, self.health / self.max_health * 10)
            damage_received = self.lifeform_rng.uniform(0, other.health / other.max_health * 10)
            self.health -= damage_received
            other.health -= damage_inflicted
        if self.health <= 0:
            self.alive = False
            self.death_timer = 0
        if other.health <= 0:
            other.alive = False
            other.death_timer = 0
        # Is it alive and staying on this square
        return self.alive and self.health >= life_remaining_before_flee
            
    def get_color(self) -> Tuple[int, int, int]:
        """Get color based on health: blue (healthy) to grey (unhealthy)"""
        if not self.alive:
            return (128, 128, 128)  # Grey for dead
            
        # Health ratio from 0.0 (dead) to 1.0 (full health)
        health_ratio = max(0.0, min(1.0, self.health / self.max_health))
        
        # Interpolate from grey (unhealthy) to blue (healthy)
        grey = (100, 100, 100)
        blue = (0, 100, 255)
        
        r = int(grey[0] + (blue[0] - grey[0]) * health_ratio)
        g = int(grey[1] + (blue[1] - grey[1]) * health_ratio)
        b = int(grey[2] + (blue[2] - grey[2]) * health_ratio)
        
        return (r, g, b)
    

