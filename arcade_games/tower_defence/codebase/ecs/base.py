"""
ECS Base Classes
Entity-Component-System architecture core classes
"""

class Entity:
    """Base class for all game entities"""
    
    def __init__(self, entity_id):
        self.id = entity_id
        self.components = {}
        self.alive = True
    
    def add_component(self, component):
        """Add a component to this entity"""
        component.entity = self
        self.components[type(component).__name__] = component
    
    def get_component(self, component_class):
        """Get a component by class"""
        return self.components.get(component_class.__name__)
    
    def has_component(self, component_class):
        """Check if entity has a specific component"""
        return component_class.__name__ in self.components
    
    def remove_component(self, component_class):
        """Remove a component from this entity"""
        if component_class.__name__ in self.components:
            del self.components[component_class.__name__]
    
    def destroy(self):
        """Mark entity for removal"""
        self.alive = False


class Component:
    """Base class for all components"""
    
    def __init__(self):
        self.entity = None


class System:
    """Base class for all systems"""
    
    def __init__(self):
        self.entities = []
    
    def add_entity(self, entity):
        """Add an entity to this system"""
        if entity not in self.entities:
            self.entities.append(entity)
    
    def remove_entity(self, entity):
        """Remove an entity from this system"""
        if entity in self.entities:
            self.entities.remove(entity)
    
    def update(self, dt):
        """Update system - override in subclasses"""
        pass
    
    def render(self, screen):
        """Render system - override in subclasses"""
        pass


class EntityManager:
    """Manages all entities in the game"""
    
    def __init__(self):
        self.entities = {}
        self.next_id = 0
    
    def create_entity(self):
        """Create a new entity"""
        entity = Entity(self.next_id)
        self.entities[self.next_id] = entity
        self.next_id += 1
        return entity
    
    def get_entity(self, entity_id):
        """Get entity by ID"""
        return self.entities.get(entity_id)
    
    def destroy_entity(self, entity_id):
        """Destroy an entity"""
        if entity_id in self.entities:
            del self.entities[entity_id]
    
    def get_all_entities(self):
        """Get all entities"""
        return list(self.entities.values())
    
    def get_entities_with(self, component_class):
        """Get all entities with a specific component"""
        return [e for e in self.entities.values() 
                if e.has_component(component_class)]
    
    def clear_dead_entities(self):
        """Remove all dead entities"""
        dead = [e.id for e in self.entities.values() if not e.alive]
        for entity_id in dead:
            self.destroy_entity(entity_id)
