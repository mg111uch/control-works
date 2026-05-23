from typing import Dict, Tuple, Optional

# =============================================================================
# TASK 10: Snapshot System
# =============================================================================

class SnapshotSystem:
    """Save/load game state"""
    
    @staticmethod
    def save_snapshot(game_model) -> Dict:
        """Save complete game state"""
        import json
        
        snapshot = {
            'version': '1.0',
            'tick_count': game_model.tick_count,
            'game_time': game_model.game_time,
            'game_ended': game_model.game_ended,
            'winner': game_model.winner,
            'entities': []
        }
        
        em = game_model.entity_manager
        
        for entity_id in em.get_all_entities():
            entity_data = {'id': entity_id, 'components': {}}
            
            # Save position
            pos = em.get_component(entity_id, 'position')
            if pos:
                entity_data['components']['position'] = {'x': pos.x, 'y': pos.y}
            
            # Save stats
            stats = em.get_component(entity_id, 'stats')
            if stats:
                entity_data['components']['stats'] = {
                    'max_hp': stats.max_hp,
                    'current_hp': stats.current_hp,
                    'max_mana': stats.max_mana,
                    'current_mana': stats.current_mana,
                    'armor': stats.armor,
                    'magic_resist': stats.magic_resist
                }
            
            # Save hero
            hero = em.get_component(entity_id, 'hero')
            if hero:
                entity_data['components']['hero'] = {
                    'hero_id': hero.hero_id,
                    'level': hero.level,
                    'team': hero.team,
                    'souls': hero.souls,
                    'strength': hero.strength,
                    'agility': hero.agility,
                    'intelligence': hero.intelligence
                }
            
            # Save combat
            combat = em.get_component(entity_id, 'combat')
            if combat:
                entity_data['components']['combat'] = {
                    'damage_min': combat.damage_min,
                    'damage_max': combat.damage_max,
                    'attack_range': combat.attack_range,
                    'attack_speed': combat.attack_speed,
                    'attack_cooldown': combat.attack_cooldown,
                    'last_attack_time': combat.last_attack_time
                }
            
            snapshot['entities'].append(entity_data)
        
        return snapshot
    
    @staticmethod
    def load_snapshot(game_model, snapshot: Dict) -> None:
        """Load game state from snapshot"""
        from engine.ecs.components import PositionComponent, StatsComponent, HeroComponent, CombatComponent
        
        # Clear current state
        game_model.entity_manager.clear()
        
        # Restore game state
        game_model.tick_count = snapshot['tick_count']
        game_model.game_time = snapshot['game_time']
        game_model.game_ended = snapshot.get('game_ended', False)
        game_model.winner = snapshot.get('winner', None)
        
        # Restore entities
        em = game_model.entity_manager
        
        for entity_data in snapshot['entities']:
            entity_id = em.create_entity()
            
            # Restore position
            if 'position' in entity_data['components']:
                p = entity_data['components']['position']
                em.add_component(entity_id, 'position', PositionComponent(p['x'], p['y']))
            
            # Restore stats
            if 'stats' in entity_data['components']:
                s = entity_data['components']['stats']
                em.add_component(entity_id, 'stats', StatsComponent(
                    max_hp=s['max_hp'], current_hp=s['current_hp'],
                    max_mana=s['max_mana'], current_mana=s['current_mana'],
                    armor=s['armor'], magic_resist=s['magic_resist']
                ))
            
            # Restore hero
            if 'hero' in entity_data['components']:
                h = entity_data['components']['hero']
                em.add_component(entity_id, 'hero', HeroComponent(
                    hero_id=h['hero_id'], level=h['level'], team=h['team'],
                    souls=h['souls'], strength=h['strength'],
                    agility=h['agility'], intelligence=h['intelligence']
                ))
            
            # Restore combat
            if 'combat' in entity_data['components']:
                c = entity_data['components']['combat']
                em.add_component(entity_id, 'combat', CombatComponent(
                    damage_min=c['damage_min'], damage_max=c['damage_max'],
                    attack_range=c['attack_range'], attack_speed=c['attack_speed'],
                    attack_cooldown=c['attack_cooldown'],
                    last_attack_time=c['last_attack_time']
                ))
        
        print(f"[Snapshot] Loaded state from tick {game_model.tick_count}")