# engine/model/ecs/entity.py
from __future__ import annotations
from typing import Dict, Any, List, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from ..game_model import GameModel


class Component:
    """Base component – all components inherit from this"""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class Entity:
    """
    Neural MMO 2 style Entity-Component-System core.
    An Entity is just an ID + bag of components.
    """
    def __init__(self, model: "GameModel", entity_id: str = None):
        self.model = model
        self.id = entity_id or str(uuid.uuid4())
        self.components: Dict[str, Component] = {}

    def add_component(self, component_type: str, component: Component):
        self.components[component_type] = component

    def get_component(self, component_type: str) -> Component | None:
        return self.components.get(component_type)

    def has_component(self, component_type: str) -> bool:
        return component_type in self.components

    def remove_component(self, component_type: str):
        self.components.pop(component_type, None)

    def serialize(self) -> Dict[str, Any]:
        """Default serialization – override in subclasses if needed"""
        data = {
            "id": self.id,
            "type": self.__class__.__name__.lower(),
            "components": {}
        }
        for name, comp in self.components.items():
            data["components"][name] = comp.__dict__
        return data

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id[:8]}>"


class EntityManager:
    """Central registry of all entities"""
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.entities_by_type: Dict[str, List[Entity]] = {}

    def add(self, entity: Entity):
        self.entities[entity.id] = entity
        typ = entity.__class__.__name__
        if typ not in self.entities_by_type:
            self.entities_by_type[typ] = []
        self.entities_by_type[typ].append(entity)

    def remove(self, entity: Entity):
        self.entities.pop(entity.id, None)
        typ = entity.__class__.__name__
        if typ in self.entities_by_type:
            self.entities_by_type[typ] = [e for e in self.entities_by_type[typ] if e.id != entity.id]

    def all(self) -> List[Entity]:
        return list(self.entities.values())

    def of_type(self, entity_class) -> List[Entity]:
        name = entity_class.__name__
        return self.entities_by_type.get(name, [])

    def find_by_id(self, entity_id: str) -> Entity | None:
        return self.entities.get(entity_id)