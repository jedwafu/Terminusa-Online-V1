from datetime import datetime
import random
from typing import Dict, List, Optional, Tuple
import numpy as np

from models import (
    db, User, Gate, MagicBeast, InventoryItem, Item, Mount, Pet,
    Skill, Quest, GuildQuest, Achievement, Transaction, Currency,
    HunterClass, JobClass, GateRank, ItemRarity, HealthStatus
)
from game_config import (
    CRYSTAL_TAX_RATE, EXON_TAX_RATE, SOLANA_TAX_RATE,
    GUILD_CRYSTAL_TAX_RATE, GUILD_EXON_TAX_RATE,
    ADMIN_USERNAME, ADMIN_WALLET,
    PARTY_REWARD_MULTIPLIERS,
    EQUIPMENT_DURABILITY_LOSS,
    STATUS_EFFECT_CHANCES
)
from ai_agent import AIAgent

class GameHandler:
    def __init__(self, websocket):
        """Initialize game handler with websocket connection."""
        self.ai_agent = AIAgent()
        
        # Initialize handlers
        self.combat_sessions = {}
        
        self.party_sessions = {}
        self.event_system = EventSystem(websocket)

    def enter_gate(self, user: User, party=None) -> Dict:
        """Enter a gate solo or with party"""
        if user.is_in_gate:
            return {"success": False, "message": "Already in a gate"}
            
        if user.health_status != HealthStatus.NORMAL:
            return {"success": False, "message": f"Cannot enter gate while {user.health_status.value}"}

        # Get AI-orchestrated gate
        gate_data = self.ai_agent.orchestrate_gate(user, party)
        
        # Create gate instance
        gate = Gate(
            name=f"{gate_data['rank']} Rank Gate",
            rank=GateRank[gate_data['rank']],
            min_level=max(1, user.level - 5),
            min_hunter_class=user.hunter_class,
            crystal_reward_min=gate_data['crystal_rewards']['min'],
            crystal_reward_max=gate_data['crystal_rewards']['max']
        )
        db.session.add(gate)
        
        # Create magic beasts
        for beast_data in gate_data['magic_beasts']:
            beast = MagicBeast(
                gate=gate,
                name=beast_data['name'],
                level=beast_data['level'],
                rank=GateRank[beast_data['rank']],
                hp=beast_data['hp'],
                max_hp=beast_data['hp'],
                mp=beast_data['mp'],
                max_mp=beast_data['mp'],
                is_monarch=beast_data.get('is_monarch', False)
            )
            db.session.add(beast)

        # Update user status
        user.is_in_gate = True
        if party:
            user.party_id = party.id
            user.is_in_party = True
            
        db.session.commit()
        
        # Initialize combat session
        session_id = f"gate_{gate.id}_{datetime.utcnow().timestamp()}"
        self.combat_sessions[session_id] = {
            'gate': gate,
            'user': user,
            'party': party,
            'beasts': gate_data['magic_beasts'],
            'difficulty': gate_data['difficulty_multiplier'],
            'start_time': datetime.utcnow(),
            'combat_log': []
        }
        
        return {
            "success": True,
            "message": f"Entered {gate.rank.value} Rank Gate",
            "session_id": session_id
        }

    def process_combat(self, session_id: str) -> Dict:
        """Process combat round in gate"""
        if session_id not in self.combat_sessions:
            return {"success": False, "message": "Invalid combat session"}
            
        session = self.combat_sessions[session_id]
        user = session['user']
        party = session['party']
        beasts = session['beasts']
        
        # Process party combat if in party
        if party:
            return self._process_party_combat(session)
            
        # Process solo combat
        combat_result = self._process_solo_combat(session)
        
        # Update equipment durability
        self._update_equipment_durability(user, session)
        
        # Check for status effects
        if combat_result['damage_taken'] > 0:
            self._check_status_effects(user)
            
        # Check if gate is cleared
        if combat_result['gate_cleared']:
            rewards = self._calculate_rewards(session)
            self._distribute_rewards(user, rewards)
            self._cleanup_combat_session(session_id)
            
        return combat_result

    def process_skill(self, user: User, skill: Skill, target_id: int) -> Dict:
        """Process skill usage"""
        if not user.is_in_gate:
            return {"success": False, "message": "Must be in gate to use skills"}
            
        if user.mp < skill.mp_cost:
            return {"success": False, "message": "Not enough MP"}
            
        # Handle resurrection skills
        if skill.is_resurrection:
            return self._process_resurrection(user, skill, target_id)
            
        # Handle Arise skill
        if skill.is_arise:
            return self._process_arise(user, skill, target_id)
            
        # Handle combat skills
        target = None
        session = None
        for s in self.combat_sessions.values():
            if s['user'].id == user.id:
                session = s
                for beast in s['beasts']:
                    if beast['id'] == target_id:
                        target = beast
                        break
                break
                
        if not target:
            return {"success": False, "message": "Invalid target"}
            
        # Apply skill effects
        result = {
            "success": True,
            "damage_dealt": 0,
            "healing_done": 0,
            "status_applied": None
        }
        
        # Apply damage
        if skill.damage > 0:
            damage = self._calculate_skill_damage(user, skill, target)
            target['hp'] -= damage
            result['damage_dealt'] = damage
            
        # Apply healing
        if skill.heal > 0:
            healing = self._calculate_skill_healing(user, skill)
            user.hp = min(user.hp + healing, user.max_hp)
            result['healing_done'] = healing
            
        # Apply status effect
        if skill.status_effect:
            if random.random() < STATUS_EFFECT_CHANCES.get(skill.status_effect.value.lower(), 0):
                target['status'] = skill.status_effect
                result['status_applied'] = skill.status_effect.value
                
        # Deduct MP
        user.mp -= skill.mp_cost
        db.session.commit()
        
        return result

    def _process_solo_combat(self, session: Dict) -> Dict:
        """Process solo combat round"""
        user = session['user']
        beasts = session['beasts']
        difficulty = session['difficulty']
        
        result = {
            "success": True,
            "damage_dealt": 0,
            "damage_taken": 0,
            "gate_cleared": False,
            "drops": [],
            "messages": [],
            "pet_effects": [],
            "mount_effects": []
        }
        
        # Apply pet stat boost if active
        active_pet = next((p for p in user.pets if p.is_active), None)
        if active_pet and active_pet.can_use_ability('Stat Boost'):
            pet_effect = active_pet.get_ability_effects('Stat Boost')
            stat_multiplier = pet_effect['value']
            user.strength *= stat_multiplier
            user.agility *= stat_multiplier
            user.intelligence *= stat_multiplier
            user.vitality *= stat_multiplier
            active_pet.use_ability('Stat Boost')
            result['pet_effects'].append(f"Pet {active_pet.name} boosted stats by {(stat_multiplier-1)*100}%")
        
        # Apply mount stamina bonus
        equipped_mount = next((m for m in user.mounts if m.is_equipped), None)
        if equipped_mount:
            stamina_bonus = equipped_mount.stats.get('stamina', 0) * 0.1  # 10% of stamina adds to HP
            user.hp += int(stamina_bonus)
            user.max_hp += int(stamina_bonus)
            result['mount_effects'].append(f"Mount {equipped_mount.name} increased HP by {int(stamina_bonus)}")
        
        # Player attacks
        for beast in beasts:
            if beast['hp'] > 0:
                damage = self._calculate_damage(user, beast, difficulty)
                beast['hp'] -= damage
                result['damage_dealt'] += damage
                result['messages'].append(f"Dealt {damage} damage to {beast['name']}")
                
        # Beasts attack
        for beast in beasts:
            if beast['hp'] > 0:
                damage = self._calculate_damage(beast, user, difficulty)
                user.hp -= damage
                result['damage_taken'] += damage
                result['messages'].append(f"Took {damage} damage from {beast['name']}")
                
                if user.hp <= 0:
                    self._handle_player_death(user, session)
                    result['messages'].append("You have died!")
                    return result
                    
        # Check if gate is cleared
        if all(beast['hp'] <= 0 for beast in beasts):
            result['gate_cleared'] = True
            drops = self._generate_drops(session)
            result['drops'] = drops
            result['messages'].append("Gate cleared!")
            
        db.session.commit()
        return result

    def _process_party_combat(self, session: Dict) -> Dict:
        """Process party combat round"""
        party = session['party']
        beasts = session['beasts']
        difficulty = session['difficulty']
        
        result = {
            "success": True,
            "damage_dealt": 0,
            "damage_taken": 0,
            "gate_cleared": False,
            "drops": [],
            "messages": []
        }
        
        # Party members attack
        for member in party.members:
            if member.hp > 0:
                for beast in beasts:
                    if beast['hp'] > 0:
                        damage = self._calculate_damage(member, beast, difficulty)
                        beast['hp'] -= damage
                        result['damage_dealt'] += damage
                        result['messages'].append(f"{member.username} dealt {damage} damage to {beast['name']}")
                        
        # Beasts attack
        alive_members = [m for m in party.members if m.hp > 0]
        for beast in beasts:
            if beast['hp'] > 0 and alive_members:
                target = random.choice(alive_members)
                damage = self._calculate_damage(beast, target, difficulty)
                target.hp -= damage
                result['damage_taken'] += damage
                result['messages'].append(f"{target.username} took {damage} damage from {beast['name']}")
                
                if target.hp <= 0:
                    self._handle_player_death(target, session)
                    result['messages'].append(f"{target.username} has died!")
                    alive_members.remove(target)
                    
        # Check if party is wiped
        if not alive_members:
            result['messages'].append("Party wiped!")
            return result
            
        # Check if gate is cleared
        if all(beast['hp'] <= 0 for beast in beasts):
            result['gate_cleared'] = True
            drops = self._generate_drops(session)
            result['drops'] = self._distribute_party_drops(drops, party)
            result['messages'].append("Gate cleared!")
            
        db.session.commit()
        return result

    def _calculate_damage(self, attacker: Dict, defender: Dict, difficulty: float) -> int:
        """Calculate damage for combat"""
        if isinstance(attacker, User):
            # Base damage calculation
            base_damage = attacker.strength * 2 + attacker.level * 1.5
            
            # Apply mount bonuses if equipped
            equipped_mount = next((m for m in attacker.mounts if m.is_equipped), None)
            if equipped_mount:
                mount_bonus = equipped_mount.stats.get('speed', 0) * 0.1  # 10% of speed adds to damage
                base_damage += mount_bonus
            
            # Apply active pet bonuses
            active_pet = next((p for p in attacker.pets if p.is_active), None)
            if active_pet and active_pet.can_use_ability('Combat Support'):
                pet_effect = active_pet.get_ability_effects('Combat Support')
                base_damage *= pet_effect['value']
                active_pet.use_ability('Combat Support')
                
        else:  # MagicBeast
            base_damage = attacker['level'] * 3
            # Apply shadow beast bonus if applicable
            if attacker.get('is_shadow', False):
                base_damage *= 1.5  # 50% bonus for shadow beasts
            
        # Apply difficulty modifier
        base_damage *= difficulty
        
        # Add randomness
        variance = random.uniform(0.8, 1.2)
        damage = int(base_damage * variance)
        
        return max(1, damage)  # Minimum 1 damage

    def _handle_player_death(self, user: User, session: Dict) -> None:
        """Handle player death in gate"""
        user.hp = 0
        user.health_status = HealthStatus.NORMAL  # Reset status on death
        
        # Drop some items and currency
        dropped_items = self._process_death_drops(user)
        
        # Remove from gate/party
        user.is_in_gate = False
        if user.party_id:
            user.is_in_party = False
            user.party_id = None
            
        db.session.commit()

        # Emit death event
        self.event_system.emit_event(GameEvent(
            type=EventType.COMBAT_UPDATE,
            user_id=user.id,
            gate_id=session['gate'].id,
            guild_id=user.guild_id,
            data={
                'type': 'player_death',
                'player': user.username,
                'dropped_items': dropped_items,
                'location': session['gate'].name
            }
        ))

    def _process_death_drops(self, user: User) -> List[Dict]:
        """Process item and currency drops on death"""
        dropped_items = []
        
        # Drop 10% of crystals
        crystal_drop = int(user.crystals * 0.1)
        if crystal_drop > 0:
            user.crystals -= crystal_drop
            dropped_items.append({
                'type': 'currency',
                'currency': 'crystals',
                'amount': crystal_drop
            })
        
        # Drop random inventory items (20% chance per item)
        for item in user.inventory_items:
            if random.random() < 0.2:
                if item.quantity > 1:
                    drop_amount = random.randint(1, item.quantity)
                    item.quantity -= drop_amount
                    dropped_items.append({
                        'type': 'item',
                        'item_id': item.id,
                        'name': item.name,
                        'quantity': drop_amount
                    })
                else:
                    db.session.delete(item)
                    dropped_items.append({
                        'type': 'item',
                        'item_id': item.id,
                        'name': item.name,
                        'quantity': 1
                    })
                    
        db.session.commit()
        
        # Emit inventory update event
        self.event_system.emit_event(GameEvent(
            type=EventType.INVENTORY_UPDATE,
            user_id=user.id,
            data={
                'type': 'death_drops',
                'dropped_items': dropped_items
            }
        ))
        
        return dropped_items

    def _generate_drops(self, session: Dict) -> List[Dict]:
        """Generate drops from cleared gate"""
        drops = []
        gate_rank = session['gate'].rank
        user = session['user']
        
        # Calculate drop modifiers
        drop_modifier = 1.0
        
        # Apply active pet bonus
        active_pet = next((p for p in user.pets if p.is_active), None)
        if active_pet and active_pet.can_use_ability('Item Finder'):
            pet_effect = active_pet.get_ability_effects('Item Finder')
            drop_modifier *= pet_effect['value']
            active_pet.use_ability('Item Finder')
        
        # Apply mount carrying capacity bonus
        equipped_mount = next((m for m in user.mounts if m.is_equipped), None)
        if equipped_mount:
            capacity_bonus = equipped_mount.stats.get('carrying_capacity', 0) * 0.001  # 0.1% per point
            drop_modifier *= (1 + capacity_bonus)
        
        # Generate items with modified rates
        base_items = random.randint(1, 3 + gate_rank.value.index)
        num_items = int(base_items * drop_modifier)
        
        for _ in range(num_items):
            rarity = self._determine_drop_rarity(gate_rank)
            item = self._generate_random_item(rarity, session['user'].level)
            drops.append({
                'type': 'item',
                'item': item
            })
            
        # Generate crystals with modified amount
        base_crystal_amount = random.randint(
            session['gate'].crystal_reward_min,
            session['gate'].crystal_reward_max
        )
        crystal_amount = int(base_crystal_amount * drop_modifier)
        
        drops.append({
            'type': 'crystal',
            'amount': crystal_amount
        })
        
        return drops

    def _determine_drop_rarity(self, gate_rank: GateRank) -> ItemRarity:
        """Determine item rarity based on gate rank"""
        rarity_weights = {
            'E': {'Common': 0.7, 'Uncommon': 0.25, 'Rare': 0.05},
            'D': {'Common': 0.5, 'Uncommon': 0.35, 'Rare': 0.13, 'Epic': 0.02},
            'C': {'Common': 0.3, 'Uncommon': 0.4, 'Rare': 0.25, 'Epic': 0.05},
            'B': {'Uncommon': 0.4, 'Rare': 0.35, 'Epic': 0.2, 'Legendary': 0.05},
            'A': {'Rare': 0.4, 'Epic': 0.35, 'Legendary': 0.2, 'Immortal': 0.05},
            'S': {'Epic': 0.4, 'Legendary': 0.4, 'Immortal': 0.2},
            'Monarch': {'Legendary': 0.6, 'Immortal': 0.4}
        }
        
        weights = rarity_weights[gate_rank.value]
        rarity_name = random.choices(
            list(weights.keys()),
            weights=list(weights.values())
        )[0]
        
        return ItemRarity[rarity_name.upper()]

    def _generate_random_item(self, rarity: ItemRarity, level: int) -> Item:
        """Generate a random item with given rarity"""
        item_types = ['weapon', 'armor', 'accessory']
        item_type = random.choice(item_types)
        
        # Base stats based on rarity
        rarity_multiplier = {
            ItemRarity.COMMON: 1,
            ItemRarity.UNCOMMON: 1.5,
            ItemRarity.RARE: 2,
            ItemRarity.EPIC: 3,
            ItemRarity.LEGENDARY: 5,
            ItemRarity.IMMORTAL: 10
        }
        
        multiplier = rarity_multiplier[rarity]
        
        item = Item(
            name=f"{rarity.value} {item_type.title()}",
            description=f"A {rarity.value.lower()} {item_type}",
            type=item_type,
            rarity=rarity,
            level_requirement=max(1, level - 5),
            price_crystals=int(100 * multiplier * (level/10)),
            price_exons=multiplier * (level/100),
            is_tradeable=True
        )
        
        db.session.add(item)
        return item

    def _distribute_party_drops(self, drops: List[Dict], party) -> Dict[int, List[Dict]]:
        """Distribute drops among party members"""
        member_drops = {member.id: [] for member in party.members if member.hp > 0}
        living_members = [m for m in party.members if m.hp > 0]
        
        if not living_members:
            return member_drops
            
        # Distribute items randomly among living members
        item_drops = [d for d in drops if d['type'] == 'item']
        for drop in item_drops:
            recipient = random.choice(living_members)
            member_drops[recipient.id].append(drop)
                
        # Distribute crystals evenly among living members
        crystal_drops = [d for d in drops if d['type'] == 'crystal']
        if crystal_drops:
            total_crystals = sum(d['amount'] for d in crystal_drops)
            per_member = total_crystals // len(living_members)
            
            for member_id in member_drops:
                member_drops[member_id].append({
                    'type': 'crystal',
                    'amount': per_member
                })
        
        # Emit loot distribution event
        self.event_system.emit_event(GameEvent(
            type=EventType.COMBAT_UPDATE,
            guild_id=party.guild_id if party.guild_id else None,
            data={
                'type': 'loot_distribution',
                'party_id': party.id,
                'distributions': {
                    str(member_id): {
                        'items': [d for d in drops if d['type'] == 'item'],
                        'crystals': per_member if crystal_drops else 0
                    }
                    for member_id, drops in member_drops.items()
                }
            }
        ))
                
        return member_drops

    def _update_equipment_durability(self, user: User, session: Dict) -> None:
        """Update equipment durability based on combat"""
        time_in_gate = (datetime.utcnow() - session['start_time']).total_seconds() / 60
        
        for item in user.inventory_items:
            if item.is_equipped and item.durability > 0:
                # Damage taken loss
                hp_loss_pct = (user.max_hp - user.hp) / user.max_hp
                durability_loss = hp_loss_pct * EQUIPMENT_DURABILITY_LOSS['damage_taken']
                
                # MP used loss
                mp_used_pct = (user.max_mp - user.mp) / user.max_mp
                durability_loss += mp_used_pct * EQUIPMENT_DURABILITY_LOSS['mana_used']
                
                # Time factor loss
                durability_loss += time_in_gate * EQUIPMENT_DURABILITY_LOSS['time_factor']
                
                item.durability = max(0, item.durability - int(durability_loss))
                
        db.session.commit()

    def _check_status_effects(self, user: User) -> None:
        """Check for status effects during combat"""
        for status, chance in STATUS_EFFECT_CHANCES.items():
            if random.random() < chance:
                user.health_status = HealthStatus[status.upper()]
                break
                
        db.session.commit()

    def _process_resurrection(self, user: User, skill: Skill, target_id: int) -> Dict:
        """Process resurrection skill"""
        target = User.query.get(target_id)
        if not target:
            return {"success": False, "message": "Invalid target"}
            
        if target.hp > 0:
            return {"success": False, "message": "Target is not dead"}
            
        if target.health_status == HealthStatus.SHADOW:
            return {"success": False, "message": "Cannot resurrect shadows"}
            
        # Resurrect target
        heal_amount = int(target.max_hp * 0.5)  # 50% HP
        target.hp = heal_amount
        target.health_status = HealthStatus.NORMAL
        
        user.mp -= skill.mp_cost
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Resurrected {target.username} with {heal_amount} HP"
        }

    def _process_arise(self, user: User, skill: Skill, target_id: int) -> Dict:
        """Process Arise skill (Shadow Monarch only)"""
        if user.job_class != JobClass.SHADOW_MONARCH:
            return {"success": False, "message": "Only Shadow Monarchs can use Arise"}
            
        target = None
        session = None
        
        # Check if target is player
        target_user = User.query.get(target_id)
        if target_user and target_user.hp <= 0:
            target = target_user
            
        # Check if target is magic beast
        if not target:
            for s in self.combat_sessions.values():
                if s['user'].id == user.id:
                    session = s
                    for beast in s['beasts']:
                        if beast['id'] == target_id and beast['hp'] <= 0:
                            target = beast
                            break
                    break
                    
        if not target:
            return {"success": False, "message": "Invalid target"}
            
        # Convert target to shadow
        if isinstance(target, User):
            target.health_status = HealthStatus.SHADOW
            target.hp = target.max_hp
        else:  # MagicBeast
            target['is_shadow'] = True
            target['shadow_owner_id'] = user.id
            target['hp'] = target['max_hp']
            
        user.mp -= skill.mp_cost
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Raised {target.username if isinstance(target, User) else target['name']} as shadow"
        }

    def _cleanup_combat_session(self, session_id: str) -> None:
        """Clean up combat session data"""
        if session_id in self.combat_sessions:
            session = self.combat_sessions[session_id]
            
            # Update user status
            user = session['user']
            gate = session['gate']
            party = session['party']
            
            user.is_in_gate = False
            if user.party_id:
                user.is_in_party = False
                user.party_id = None
                
            db.session.commit()
            
            # Emit session end event
            self.event_system.emit_event(GameEvent(
                type=EventType.COMBAT_UPDATE,
                user_id=user.id,
                gate_id=gate.id,
                guild_id=user.guild_id,
                data={
                    'type': 'session_end',
                    'gate_name': gate.name,
                    'duration': (datetime.utcnow() - session['start_time']).total_seconds(),
                    'party_size': len(party.members) if party else 1,
                    'success': session.get('cleared', False)
                }
            ))
            
            # Remove session
            del self.combat_sessions[session_id]

    def handle_currency_transaction(self, user_id: int, transaction_type: str, currency: str, amount: float) -> Dict:
        """Handle currency transactions for users."""
        # Fetch the currency object
        currency_obj = Currency.get_by_symbol(currency)
        if not currency_obj:
            return {"success": False, "message": "Invalid currency."}

        # Create a new transaction
        transaction = Transaction(
            user_id=user_id,
            type=transaction_type,
            currency=currency,
            amount=amount
        )
        
        # Add transaction to the session
        db.session.add(transaction)
        
        # Commit the transaction
        try:
            db.session.commit()
            return {"success": True, "transaction_id": transaction.id}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}
