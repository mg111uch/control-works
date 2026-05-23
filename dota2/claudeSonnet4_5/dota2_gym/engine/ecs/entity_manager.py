"""Entity Manager for ECS architecture"""
from typing import Dict, Set, Any, List, Optional


class EntityManager:
    """
    Manages all entities and their components.
    Entities are just IDs, components are data stored in dictionaries.
    """
    
    def __init__(self):
        self.next_entity_id: int = 0
        self.entities: Set[int] = set()
        self.components: Dict[str, Dict[int, Any]] = {}
        self.spatial_hash = None  # Reference to spatial hash for efficient queries
        
    def create_entity(self) -> int:
        """Create a new entity and return its unique ID"""
        entity_id = self.next_entity_id
        self.next_entity_id += 1
        self.entities.add(entity_id)
        return entity_id
    
    def destroy_entity(self, entity_id: int) -> None:
        """Destroy an entity and remove all its components"""
        if entity_id in self.entities:
            self.entities.remove(entity_id)
            
            # Remove from all component dictionaries
            for component_type in self.components:
                if entity_id in self.components[component_type]:
                    del self.components[component_type][entity_id]
            
            # Remove from spatial hash if present
            if self.spatial_hash is not None:
                self.spatial_hash.remove(entity_id)
    
    def add_component(self, entity_id: int, component_type: str, component_data: Any) -> None:
        """Add a component to an entity"""
        if entity_id not in self.entities:
            raise ValueError(f"Entity {entity_id} does not exist")
        
        if component_type not in self.components:
            self.components[component_type] = {}
        
        self.components[component_type][entity_id] = component_data
    
    def remove_component(self, entity_id: int, component_type: str) -> None:
        """Remove a component from an entity"""
        if component_type in self.components and entity_id in self.components[component_type]:
            del self.components[component_type][entity_id]
    
    def get_component(self, entity_id: int, component_type: str) -> Optional[Any]:
        """Get a component from an entity"""
        if component_type in self.components and entity_id in self.components[component_type]:
            return self.components[component_type][entity_id]
        return None
    
    def has_component(self, entity_id: int, component_type: str) -> bool:
        """Check if an entity has a specific component"""
        return (component_type in self.components and 
                entity_id in self.components[component_type])
    
    def get_entities_with_component(self, component_type: str) -> List[int]:
        """Get all entities that have a specific component"""
        if component_type in self.components:
            return list(self.components[component_type].keys())
        return []
    
    def get_entities_with_components(self, *component_types: str) -> List[int]:
        """Get all entities that have ALL specified components"""
        if not component_types:
            return []
        
        result = set(self.get_entities_with_component(component_types[0]))
        
        for component_type in component_types[1:]:
            result &= set(self.get_entities_with_component(component_type))
        
        return list(result)
    
    def get_all_entities(self) -> Set[int]:
        """Get all active entities"""
        return self.entities.copy()
    
    def clear(self) -> None:
        """Clear all entities and components"""
        self.entities.clear()
        self.components.clear()
        self.next_entity_id = 0