import tkinter as tk
from tkinter import ttk
import random
import time
from typing import List, Optional
from lifeform import Lifeform, GridSquare

class GridSimulation:
    """Grid-based artificial life simulation with tkinter GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Grid Life Simulation")
        self.root.geometry("900x700")
        
        # Simulation parameters
        self.grid_size = 10
        self.initial_population = 5
        self.grid: List[List[GridSquare]] = []
        self.lifeforms: List[Lifeform] = []
        self.running = False
        self.last_update = time.time()
        
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
        
    def create_grid(self):
        """Create the grid of squares"""
        self.grid = []
        for x in range(self.grid_size):
            column = []
            for y in range(self.grid_size):
                column.append(GridSquare())
            self.grid.append(column)
            
    def place_initial_population(self):
        """Randomly place initial lifeforms on the grid"""
        self.lifeforms = []
        population = int(self.population_var.get())
        
        for _ in range(population):
            # Find empty square
            attempts = 0
            while attempts < 100:  # Prevent infinite loop
                x = random.randint(0, self.grid_size - 1)
                y = random.randint(0, self.grid_size - 1)
                
                if self.grid[x][y].lifeform is None:
                    lifeform = Lifeform(x, y)
                    self.grid[x][y].place_lifeform(lifeform)
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
        self.create_grid()
        self.place_initial_population()
        self.draw_grid()
        
    def update_simulation(self, dt: float):
        """Update simulation logic"""
        # Update grid squares (food regeneration)
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                self.grid[x][y].update(dt)
                
        # Update lifeforms
        alive_lifeforms = []
        for lifeform in self.lifeforms:
            if not lifeform.alive:
                # Remove dead lifeform from grid
                self.grid[lifeform.grid_x][lifeform.grid_y].remove_lifeform()
                continue
                
            square = self.grid[lifeform.grid_x][lifeform.grid_y]
            
            # Try to eat food
            food_available = square.consume_food() if square.has_food() else 0
            lifeform.update(dt, food_available)
            
            # Try to move if no food and can move
            if not square.has_food() and lifeform.can_move() and lifeform.alive:
                self.try_move_lifeform(lifeform)
                
            if lifeform.alive:
                alive_lifeforms.append(lifeform)
            else:
                # Remove dead lifeform from grid
                self.grid[lifeform.grid_x][lifeform.grid_y].remove_lifeform()
                
        self.lifeforms = alive_lifeforms
        
    def try_move_lifeform(self, lifeform: Lifeform):
        """Try to move a lifeform to adjacent square"""
        possible_moves = []
        
        # Check all adjacent squares (including diagonals)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                    
                new_x = lifeform.grid_x + dx
                new_y = lifeform.grid_y + dy
                
                # Check bounds
                if 0 <= new_x < self.grid_size and 0 <= new_y < self.grid_size:
                    possible_moves.append((new_x, new_y))
        
        if not possible_moves:
            return
            
        # Choose random move
        new_x, new_y = random.choice(possible_moves)
        target_square = self.grid[new_x][new_y]
        
        # Check if square is occupied
        if target_square.lifeform is not None:
            # Fight!
            winner = lifeform.fight(target_square.lifeform)
            if winner == lifeform:
                # Move to new square
                self.grid[lifeform.grid_x][lifeform.grid_y].remove_lifeform()
                target_square.place_lifeform(lifeform)
                lifeform.move_to(new_x, new_y)
        else:
            # Move to empty square
            self.grid[lifeform.grid_x][lifeform.grid_y].remove_lifeform()
            target_square.place_lifeform(lifeform)
            lifeform.move_to(new_x, new_y)
            
    def draw_grid(self):
        """Draw the grid on canvas"""
        self.canvas.delete("all")
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Calculate grid positioning
        grid_pixel_size = self.grid_size * self.square_size
        start_x = max(0, (canvas_width - grid_pixel_size) // 2)
        start_y = max(0, (canvas_height - grid_pixel_size) // 2)
        
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                x1 = start_x + x * self.square_size
                y1 = start_y + y * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                
                color = self.grid[x][y].get_color()
                color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                
                self.canvas.create_rectangle(x1, y1, x2, y2, 
                                           fill=color_hex, outline="gray")
                
    def update_stats(self):
        """Update statistics display"""
        if self.lifeforms:
            avg_health = sum(lf.health for lf in self.lifeforms) / len(self.lifeforms)
            stats_text = f"Population: {len(self.lifeforms)} | Avg Health: {avg_health:.1f}"
        else:
            stats_text = "Population: 0 | All lifeforms extinct!"
            
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
            self.root.after(100, self.update_loop)  # Update every 100ms
            
    def run(self):
        """Start the GUI"""
        self.reset_simulation()
        self.root.mainloop()

if __name__ == "__main__":
    sim = GridSimulation()
    sim.run()