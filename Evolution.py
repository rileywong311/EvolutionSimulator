import numpy as np
import matplotlib.pyplot as plt

# traits
all_traits = ("foraging", "long_neck", "fat_tissue", "horns", "hard_shell", \
              "defensive_herding", "burrowing", "scavenging", "fertile",  \
              "warning_call", "climbing", "carnivore", "ambush", "pack_hunting")

dict_traits = {"foraging": 0, "long_neck": 0, "fat_tissue": 0, "horns": 0, "hard_shell": 0, \
              "defensive_herding": 0, "burrowing": 0, "scavenging": 0, "fertile": 0,  \
              "warning_call": 0, "climbing": 0, "carnivore": 0, "ambush": 0, "pack_hunting": 0}

# Species Instancer
class Species:
    population_max = 6 
    body_size_max = 6

    def __init__(self, gamestate, traits=[None, None, None]):
        self.age = gamestate.steps
        self.total_food = 0
        self.traits = traits
        self.population = 1
        self.body_size = 1
        self.phase_food = 0
        self.satisfied = False
        self.dead = False
        gamestate.all_species.insert(1, self) # add instance object to gamestate list

    def action(self, gamestate):
        if self.traits.count("carnivore"):
            self.carnivore_action(gamestate)
            self.satisfy_checker()
        else:
            self.regular_eat(gamestate)
            self.satisfy_checker()
            if self.traits.count("foraging") and gamestate.watering_hole_food:
                if not self.satisfied:
                    self.regular_eat(gamestate)
                    self.satisfy_checker()

    def carnivore_action(self, gamestate):
        priority = {}

        for i in range(len(gamestate.all_species)):
            if self.get_attack(gamestate.all_species[i]) > gamestate.all_species[i].get_defense() and not gamestate.all_species[i].dead:
                priority[i] = gamestate.all_species[i].phase_food
        
        if not priority:                # if no possible targets
            self.population -= 1
            self.death_check(gamestate)
            self.satisfy_checker()
            if not self.satisfied:
                self.phase_food += 1
                self.satisfy_checker()
        else:
            gamestate.all_species[max(priority)].population -= 1
            gamestate.all_species[max(priority)].death_check(gamestate)
            gamestate.all_species[max(priority)].satisfy_checker()
            if gamestate.all_species[max(priority)].traits.count("horns"):
                self.population -= 1
                self.satisfy_checker()
                if not self.satisfied:
                    self.phase_food += 1
                    self.satisfy_checker()

        gamestate.trigger_scavenge()
            
    def get_attack(self, target):
        attack = self.body_size
        if self.traits.count("pack_hunting"):
            attack += self.population
        if target.traits.count("warning_call") and not self.traits.count("ambush"):
            attack = -1
        if target.traits.count("climbing") and not self.traits.count("climbing"):
            attack = -1
        if target.traits.count("burrowing") and target.satisfied:
            attack = -1

        return attack

    def get_defense(self):
        defense = self.body_size
        if self.traits.count("defensive_herding"):
            defense += self.population
        if self.traits.count("hard_shell"):
            defense += 4

        return defense

    def satisfy_checker(self):
        if self.traits.count("fat_tissue") and self.phase_food == self.population + self.body_size:
            self.satisfied = True
        elif self.phase_food == self.population:
            self.satisfied = True
        elif self.phase_food < self.population: # works as a reset as well
            self.satisfied = False
        
    def regular_eat(self, gamestate):
        self.phase_food += 1
        gamestate.watering_hole_food -= 1
        self.satisfy_checker()

    def pick_new_trait(self):
        new_trait = all_traits[np.random.randint(0, len(all_traits))]
        if new_trait in self.traits:
            return self.pick_new_trait()
        return new_trait

    def death_check(self, gamestate):
        if not self.population:
            self.dead = True

    # grow options
    def mutate(self, gamestate):
        new_trait = self.pick_new_trait()
        new_traits = self.traits[:]

        if self.traits[0] and self.traits[1] and self.traits[2]:
            new_traits[np.random.randint(0,3)] = new_trait
        elif not self.traits[0]:
            new_traits[0] = new_trait
        elif not self.traits[1]:
            new_traits[1] = new_trait
        elif not self.traits[2]:
            new_traits[2] = new_trait

        for species in gamestate.all_species:
            if new_traits[0] in species.traits and new_traits[1] in species.traits and new_traits[2] in species.traits:
                Species(gamestate)
                return 0

        Species(gamestate, new_traits)

    def grow_pop(self):
        self.population += 1

    def grow_body(self):
        self.body_size += 1
        
# Game Simulator
class GameState:

    def __init__(self):
        self.steps = 0
        self.species_count = []

        self.watering_hole_food = 10
        self.all_species = []
        self.food_add_range = (-1, 2)
        
    def add_food(self):
        self.watering_hole_food += \
            np.random.randint(self.food_add_range[0], self.food_add_range[1])
        if self.watering_hole_food < 0:
            self.watering_hole_food = 0

    def grow_species(self, species, past=-1):
        choice = np.random.randint(1, 4)
        while choice == past:
            choice = np.random.randint(1, 4)

        if choice == 1:
            species.mutate(self)

        elif choice == 2:
            if species.population < species.population_max:
                species.grow_pop()
            #else:
            #    self.grow_species(species, 2)

        elif choice == 3:
            if species.body_size < species.body_size_max:
                species.grow_body()
            #else:
            #   self.grow_species(species, 3)

    def trigger_scavenge(self):
        for species in self.all_species:                  
            if species.traits.count("scavenging") and not species.satisfied:
                species.phase_food += 1
                species.satisfy_checker()
    
    def step(self):
        # start of turn growth
        for species in self.all_species[:]:                    
            self.grow_species(species)

        for species in self.all_species:                    # fertile ability
            if species.traits.count("fertile") and species.population != species.population_max and self.watering_hole_food:
                species.grow_pop()

        # add/remove food
        self.add_food()
        start_food = self.watering_hole_food

        # feed in order
        for species in self.all_species:                                      
            if species.traits.count("long_neck"):               # long neck priority    
                species.phase_food += 1
            species.satisfy_checker()                          # check satisfication of all specues

        finished = 0
        while finished < len(self.all_species):
            for species in self.all_species:              # all other traits
                if species.satisfied or species.dead or not self.watering_hole_food:
                    finished += 1 
                else:
                    finished = 0
                    species.action(self)

        # score phase
        for species in self.all_species[:]:
            species.population = min(6, species.phase_food) # accounts for fatty tissue
            species.death_check(self)
            species.total_food += species.phase_food
            species.phase_food -= species.population
            species.satisfy_checker()
            if species.dead:
                self.all_species.remove(species)

        # re-order
        if self.all_species:
            temp = self.all_species.pop(0)
            self.all_species.append(temp)            

        
        self.species_count.append(len(self.all_species))
        for species in self.all_species:
            for trait in species.traits:
                if trait:
                    dict_traits[trait] += 1

        self.steps += 1

        print("Step = ", self.steps, end=" ")
        print("Food = ", start_food, "->", self.watering_hole_food, end=" | ")
        for species in self.all_species:
            print(species.total_food, " ", species.population, " ", species.body_size, end=" ")
            print(species.traits, end=" | ")
        print("\n\n")

        

Game = GameState()

for _ in range(1):
    Species(Game)

print("Step = ", Game.steps, end=" ")
print("Food = ", Game.watering_hole_food, end=" | ")
for species in Game.all_species:
    print(species.total_food, " ", species.population, " ", species.body_size, end=" ")
    print(species.traits, end=" | ")
print("\n\n")

for _ in range(200):
    Game.step()
    if not Game.all_species:
        print("EXTINCTION")
        Species(Game)


plt.plot(range(Game.steps), Game.species_count)
plt.show()
plt.figure(figsize=[20,5])
plt.bar(dict_traits.keys(), dict_traits.values())
plt.show()