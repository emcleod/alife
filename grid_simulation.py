import tkinter as tk
from tkinter import ttk
import random
import time
from typing import List
from lifeform import Lifeform, GridSquare


class GridSimulation:
    """Grid-based artificial life simulation with tkinter GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Grid Life Simulation")
        self.root.geometry("900x700")
        
        # Random number generators with fixed seeds for reproducibility
        self.habitat_rng = random.Random(12345)    # For habitat generation
        self.food_rng = random.Random(54321)       # For food behavior
        self.lifeform_rng = random.Random(98765)   # For lifeform behavior
        self.combat_rng = random.Random(13579)     # For combat decisions
        self.movement_rng = random.Random(24680)   # For movement decisions
        
        # Simulation parameters
        self.grid_size = 10
        self.initial_population = 5
        self.grid: List[List[GridSquare]] = []
        self.lifeforms: List[Lifeform] = []
        self.running = False
        self.last_update = time.time()
        self.time_period = 0  # Track time periods for seasons
        self.speed_multiplier = 1.0  # Speed control
        
        # GUI elements
        self.canvas = None
        self.square_size = 40
        
        self.setup_gui()
        self.create_grid()
        
    def setup_gui(self):
        """Create the GUI interface"""
        # Control frame
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10)
        
        # Grid size dropdown
        ttk.Label(control_frame, text="Grid Size:").pack(side=tk.LEFT, padx=5)
        self.grid_size_var = tk.StringVar(value="10")
        grid_dropdown = ttk.Combobox(control_frame, textvariable=self.grid_size_var, 
                                   values=["5", "10", "15", "20", "25"], width=5)
        grid_dropdown.pack(side=tk.LEFT, padx=5)
        grid_dropdown.bind("<<ComboboxSelected>>", self.on_grid_size_change)
        
        # Population spinner
        ttk.Label(control_frame, text="Initial Population:").pack(side=tk.LEFT, padx=(20,5))
        self.population_var = tk.StringVar(value="5")
        population_spin = ttk.Spinbox(control_frame, from_=1, to=50, width=5,
                                    textvariable=self.population_var)
        population_spin.pack(side=tk.LEFT, padx=5)
        
        # Speed control
        ttk.Label(control_frame, text="Speed:").pack(side=tk.LEFT, padx=(20,5))
        self.speed_var = tk.StringVar(value="1.0")
        speed_dropdown = ttk.Combobox(control_frame, textvariable=self.speed_var,
                                    values=["0.1", "0.25", "0.5", "1.0", "2.0", "5.0", "10.0"], 
                                    width=6)
        speed_dropdown.pack(side=tk.LEFT, padx=5)
        speed_dropdown.bind("<<ComboboxSelected>>", self.on_speed_change)
        
        # Buttons
        self.start_button = ttk.Button(control_frame, text="Start", command=self.start_simulation)
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_simulation)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Reset", command=self.reset_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        # Stats frame
        stats_frame = ttk.Frame(self.root)
        stats_frame.pack(pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="Population: 0 | Avg Health: 0.0")
        self.stats_label.pack()
        
        # Canvas for grid
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(pady=10, expand=True, fill=tk.BOTH)
        
        self.canvas = tk.Canvas(canvas_frame, bg='black')
        self.canvas.pack(expand=True, fill=tk.BOTH)
        
    def on_grid_size_change(self, event=None):
        """Handle grid size change"""
        self.grid_size = int(self.grid_size_var.get())
        self.square_size = min(40, 600 // self.grid_size)  # Adjust square size for screen
        self.reset_simulation()
        
    def on_speed_change(self, event=None):
        """Handle speed change"""
        self.speed_multiplier = float(self.speed_var.get())
        
    def create_grid(self):
        """Create the grid of squares"""
        self.grid = []
        for x in range(self.grid_size):
            column = []
            for y in range(self.grid_size):
                # Create a separate RNG for each square's food behavior
                square_seed = self.food_rng.randint(1, 1000000)
                square_rng = random.Random(square_seed)
                column.append(GridSquare(square_rng))
            self.grid.append(column)
        
        # Initialize habitat after creating grid
        self.initialize_habitat()
            
    def initialize_habitat(self):
        """Initialize food maximum values with clumped distribution for richer/poorer habitats"""
        # First pass: set base max food values and regeneration rates
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                # Start with moderate base values
                self.grid[x][y].max_food = self.habitat_rng.uniform(20, 35)
                self.grid[x][y].base_regen_rate = self.grid[x][y].regen_rate  # Store original
        
        # Second pass: create clumps by adjusting neighbors
        num_rich_patches = self.habitat_rng.randint(2, 4)  # 2-4 rich areas
        num_poor_patches = self.habitat_rng.randint(1, 3)  # 1-3 poor areas
        
        # Create rich patches
        for _ in range(num_rich_patches):
            center_x = self.habitat_rng.randint(2, self.grid_size - 3)  # More margin for 5x5
            center_y = self.habitat_rng.randint(2, self.grid_size - 3)
            
            # Enhance food in 5x5 area around center
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    nx, ny = center_x + dx, center_y + dy
                    if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                        # Manhattan distance from center for linear drop-off
                        distance = abs(dx) + abs(dy)
                        # Linear drop-off: max effect at center (distance 0), min at corners (distance 4)
                        enhancement = max(0, 25 - (distance * 5))  # 25, 20, 15, 10, 5
                        self.grid[nx][ny].max_food += enhancement
                        # Regeneration boost with linear drop-off
                        regen_boost = 1.0 + max(0, 0.8 - (distance * 0.15))  # 1.8x to 1.2x to 1.0x
                        self.grid[nx][ny].regen_rate = self.grid[nx][ny].base_regen_rate * regen_boost
                        # Cap at reasonable maximum
                        if self.grid[nx][ny].max_food > 70:
                            self.grid[nx][ny].max_food = 70
        
        # Create poor patches
        for _ in range(num_poor_patches):
            center_x = self.habitat_rng.randint(2, self.grid_size - 3)  # More margin for 5x5
            center_y = self.habitat_rng.randint(2, self.grid_size - 3)
            
            # Reduce food in 5x5 area around center
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    nx, ny = center_x + dx, center_y + dy
                    if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                        # Manhattan distance from center for linear drop-off
                        distance = abs(dx) + abs(dy)
                        # Linear drop-off: max reduction at center, min at corners
                        reduction = max(0, 20 - (distance * 4))  # 20, 16, 12, 8, 4
                        self.grid[nx][ny].max_food -= reduction
                        # Regeneration reduction with linear drop-off
                        regen_reduction = 0.2 + (distance * 0.15)  # 0.2x to 0.8x (worse to better)
                        self.grid[nx][ny].regen_rate = self.grid[nx][ny].base_regen_rate * regen_reduction
                        # Cap at reasonable minimum
                        if self.grid[nx][ny].max_food < 3:
                            self.grid[nx][ny].max_food = 3
        
        # Set initial food amounts to random portion of max food
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                self.grid[x][y].food_amount = self.habitat_rng.uniform(0.2, 0.6) * self.grid[x][y].max_food
                
    def place_initial_population(self):
        """Randomly place initial lifeforms on the grid"""
        self.lifeforms = []
        population_size = int(self.population_var.get())
        
        for _ in range(population_size):
            # Find random empty position
            attempts = 0
            while attempts < 100:  # Prevent infinite loop
                x = self.lifeform_rng.randint(0, self.grid_size - 1)
                y = self.lifeform_rng.randint(0, self.grid_size - 1)
                
                # Check if square has room (less than 4 lifeforms)
                current_count = sum(1 for lf in self.lifeforms if lf.grid_x == x and lf.grid_y == y and lf.alive)
                
                if current_count < 4:
                    lifeform = Lifeform(x, y, self.lifeform_rng, self.grid_size, self.grid_size)
                    self.lifeforms.append(lifeform)
                    break
                    
                attempts += 1
                
    def start_simulation(self):
        """Start the simulation"""
        self.running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.last_update = time.time()
        self.update_loop()
        
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        
    def reset_simulation(self):
        """Reset the simulation"""
        self.stop_simulation()
        self.time_period = 0
        self.create_grid()
        self.place_initial_population()
        self.draw_grid()
        
    def update_simulation(self, dt: float):
        """Update simulation logic"""
        # Apply speed multiplier to dt
        adjusted_dt = dt * self.speed_multiplier
        
        # Update grid squares (food regeneration with seasonal effects)
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                self.grid[x][y].regenerate_food(adjusted_dt, self.time_period)
        
        # Update lifeforms
        for lifeform in self.lifeforms:
            if lifeform.alive:
                # Let lifeform eat from current square
                current_square = self.grid[lifeform.grid_x][lifeform.grid_y]
                lifeform.update(adjusted_dt, current_square)
            else:
                # Update death timer for fading
                lifeform.death_timer += adjusted_dt
        
        # Remove fully faded lifeforms
        self.lifeforms = [lf for lf in self.lifeforms if lf.alive or lf.death_timer < 7.0]
        
        # Increment time period
        self.time_period += adjusted_dt * 0.1  # Adjust this rate as needed
        
    def try_move_lifeform(self, lifeform):
        #lifeform will move to an adjacent square
        pass

    def draw_grid(self):
        """Draw the grid on canvas"""
        # Force canvas to update its size first
        self.canvas.update_idletasks()
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Calculate grid positioning - center the grid
        grid_pixel_size = self.grid_size * self.square_size
        start_x = max(0, (canvas_width - grid_pixel_size) // 2)
        start_y = max(0, (canvas_height - grid_pixel_size) // 2)
        
        # Store all rectangles to create, then create them all at once
        rectangles_to_create = []
        
        # Prepare food squares (background)
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                x1 = start_x + x * self.square_size
                y1 = start_y + y * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                
                # Get food background color
                food_color = self.grid[x][y].get_color()
                food_color_hex = f"#{food_color[0]:02x}{food_color[1]:02x}{food_color[2]:02x}"
                
                rectangles_to_create.append((x1, y1, x2, y2, food_color_hex))
        
        # Now clear and redraw all at once
        self.canvas.delete("all")
        
        for x1, y1, x2, y2, color_hex in rectangles_to_create:
            self.canvas.create_rectangle(x1, y1, x2, y2, 
                                       fill=color_hex, outline="gray")
        
        # Draw lifeforms as circles on top
        for lifeform in self.lifeforms:
            if lifeform.alive or lifeform.death_timer < 7.0:  # Show until fully faded
                # Get position within grid
                grid_x1 = start_x + lifeform.grid_x * self.square_size
                grid_y1 = start_y + lifeform.grid_y * self.square_size
                
                # Count lifeforms in this square to determine position
                lifeforms_in_square = [lf for lf in self.lifeforms 
                                     if lf.grid_x == lifeform.grid_x and lf.grid_y == lifeform.grid_y 
                                     and (lf.alive or lf.death_timer < 7.0)]
                
                try:
                    position_index = lifeforms_in_square.index(lifeform)
                except ValueError:
                    position_index = 0
                
                # Position in 2x2 grid within square
                positions = [
                    (0.25, 0.25),  # Top-left
                    (0.75, 0.25),  # Top-right  
                    (0.25, 0.75),  # Bottom-left
                    (0.75, 0.75)   # Bottom-right
                ]
                
                if position_index < len(positions):
                    rel_x, rel_y = positions[position_index]
                    
                    # Calculate circle position and size
                    circle_size = self.square_size * 0.3  # 30% of square size
                    center_x = grid_x1 + (self.square_size * rel_x)
                    center_y = grid_y1 + (self.square_size * rel_y)
                    
                    circle_x1 = center_x - circle_size // 2
                    circle_y1 = center_y - circle_size // 2
                    circle_x2 = center_x + circle_size // 2
                    circle_y2 = center_y + circle_size // 2
                    
                    # Get lifeform color and transparency
                    lifeform_color = lifeform.get_color()
                    
                    # Apply transparency for dead lifeforms
                    if not lifeform.alive:
                        fade_progress = lifeform.death_timer / 7.0  # 0 to 1
                        # Fade to background by mixing with food color
                        food_color = self.grid[lifeform.grid_x][lifeform.grid_y].get_color()
                        
                        # Linear interpolation between lifeform and food color
                        mixed_color = (
                            int(lifeform_color[0] * (1 - fade_progress) + food_color[0] * fade_progress),
                            int(lifeform_color[1] * (1 - fade_progress) + food_color[1] * fade_progress),
                            int(lifeform_color[2] * (1 - fade_progress) + food_color[2] * fade_progress)
                        )
                        lifeform_color = mixed_color
                    
                    lifeform_color_hex = f"#{lifeform_color[0]:02x}{lifeform_color[1]:02x}{lifeform_color[2]:02x}"
                    
                    self.canvas.create_oval(circle_x1, circle_y1, circle_x2, circle_y2,
                                          fill=lifeform_color_hex, outline="black", width=1)
                
    def update_stats(self):
        """Update statistics display"""
        alive_lifeforms = [lf for lf in self.lifeforms if lf.alive]
        
        if alive_lifeforms:
            avg_health = sum(lf.health for lf in alive_lifeforms) / len(alive_lifeforms)
            stats_text = f"Population: {len(alive_lifeforms)} | Avg Health: {avg_health:.1f}"
        else:
            stats_text = "Population: 0 | All lifeforms extinct!"
            
        # Add seasonal information
        season_names = ["Winter", "Spring", "Summer", "Autumn"]
        season_index = int((self.time_period % 52) / 13)
        current_season = season_names[season_index]
        stats_text += f" | Season: {current_season} ({self.time_period:.1f})"
            
        self.stats_label.config(text=stats_text)
        
    def update_loop(self):
        """Main update loop"""
        if self.running:
            current_time = time.time()
            dt = current_time - self.last_update
            self.last_update = current_time
            
            self.update_simulation(dt)
            self.draw_grid()
            self.update_stats()
            
            # Schedule next update
            self.root.after(500, self.update_loop)  # Update every 500ms (slower)
            
    def run(self):
        """Start the GUI"""
        self.reset_simulation()
        self.root.mainloop()

        
if __name__ == "__main__":
    sim = GridSimulation()
    sim.run()