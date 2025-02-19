from typing import Dict, List, Optional
from datetime import datetime
import json

from models import (
    db, User, Gate, Guild, Party, InventoryItem, Item,
    Mount, Pet, Skill, Quest, GuildQuest, Achievement,
    HunterClass, JobClass, HealthStatus
)
from game_handler import GameHandler
from ai_agent import AIAgent
from game_config import (
    SHOP_ITEMS, POTIONS, ANTIDOTES,
    CRYSTAL_TAX_RATE, EXON_TAX_RATE,
    GUILD_CREATION_COST
)

class TerminalCommands:
    def __init__(self):
        self.game_handler = GameHandler()
        self.ai_agent = AIAgent()

    def handle_command(self, user: User, command: str, args: List[str]) -> Dict:
        """Handle terminal commands"""
        commands = {
            'help': self._cmd_help,
            'status': self._cmd_status,
            'inventory': self._cmd_inventory,
            'skills': self._cmd_skills,
            'quests': self._cmd_quests,
            'achievements': self._cmd_achievements,
            'gates': self._cmd_gates,
            'enter': self._cmd_enter_gate,
            'party': self._cmd_party,
            'guild': self._cmd_guild,
            'shop': self._cmd_shop,
            'buy': self._cmd_buy,
            'sell': self._cmd_sell,
            'trade': self._cmd_trade,
            'market': self._cmd_market,
            'repair': self._cmd_repair,
            'use': self._cmd_use_item,
            'equip': self._cmd_equip,
            'unequip': self._cmd_unequip,
            'flip': self._cmd_flip_coin,
            'balance': self._cmd_balance,
            'wallet': self._cmd_wallet,
            'mount': self._cmd_mount,
            'pet': self._cmd_pet,
            'gacha': self._cmd_gacha
        }

        command = command.lower()
        if command not in commands:
            return {
                "success": False,
                "message": f"Unknown command: {command}. Type 'help' for available commands."
            }

        return commands[command](user, args)

    def _cmd_help(self, user: User, args: List[str]) -> Dict:
        """Show help information"""
        help_text = """
Available Commands:
  General:
    help        - Show this help message
    status      - Show your hunter status
    inventory   - Show your inventory
    skills      - Show your skills
    quests      - Show available quests
    achievements- Show your achievements
    balance     - Check currency balance
    wallet      - Manage Web3 wallet

  Combat:
    gates       - Show available gates
    enter [id]  - Enter a gate
    party       - Party management commands
    guild       - Guild management commands

  Items and Shopping:
    shop        - Access hunter shop
    buy [item]  - Buy an item
    sell [item] - Sell an item
    trade       - Trade with other players
    market      - Access marketplace
    repair      - Repair equipment
    use [item]  - Use an item
    equip [id]  - Equip an item
    unequip [id]- Unequip an item

  Mounts and Pets:
    mount       - Mount management
    pet         - Pet management
    gacha       - Access gacha system

  Gambling:
    flip [amount] - Flip a coin to gamble crystals

Type 'help [command]' for more information about a specific command.
"""
        if args:
            specific_command = args[0].lower()
            specific_help = {
                'status': 'Show your hunter status, level, class, and stats.',
                'inventory': 'Show your inventory items and equipment.',
                'gates': 'Show available gates that you can enter.',
                'enter': 'Enter a gate. Usage: enter [gate_id]',
                'party': 'Party management. Sub-commands: create, invite, join, leave',
                'guild': 'Guild management. Sub-commands: create, invite, join, leave',
                'shop': 'Access the hunter shop to buy items.',
                'market': 'Access the marketplace to buy/sell items.',
                'gacha': 'Try your luck with mounts and pets. Usage: gacha [mount/pet]'
            }
            return {
                "success": True,
                "message": specific_help.get(
                    specific_command,
                    f"No detailed help available for '{specific_command}'"
                )
            }

        return {
            "success": True,
            "message": help_text
        }

    def _cmd_status(self, user: User, args: List[str]) -> Dict:
        """Show user status"""
        status_text = f"""
Hunter Status:
  Name: {user.username}
  Level: {user.level} ({user.exp} EXP)
  Hunter Class: {user.hunter_class.value}
  Job: {user.job_class.value if user.job_class else 'None'} (Level {user.job_level})
  
Stats:
  HP: {user.hp}/{user.max_hp}
  MP: {user.mp}/{user.max_mp}
  Strength: {user.strength}
  Agility: {user.agility}
  Intelligence: {user.intelligence}
  Vitality: {user.vitality}
  Luck: {user.luck}

Status: {user.health_status.value}
Location: {'In Gate' if user.is_in_gate else 'Town'}
Party: {'Yes' if user.is_in_party else 'No'}
Guild: {user.guild.name if user.guild else 'None'}
"""
        return {
            "success": True,
            "message": status_text
        }

    def _cmd_inventory(self, user: User, args: List[str]) -> Dict:
        """Show inventory"""
        if not user.inventory_items:
            return {
                "success": True,
                "message": "Your inventory is empty."
            }

        inventory_text = f"\nInventory ({len(user.inventory_items)}/{user.inventory_slots} slots):\n"
        
        # Group items by equipped status
        equipped = []
        unequipped = []
        
        for inv_item in user.inventory_items:
            item = inv_item.item
            item_text = (
                f"[{inv_item.id}] {item.name} "
                f"(x{inv_item.quantity}) "
                f"- {item.description}\n"
                f"    Rarity: {item.rarity.value}"
            )
            
            if item.type == 'equipment':
                item_text += f" | Durability: {inv_item.durability}%"
                
            if inv_item.is_equipped:
                equipped.append(item_text)
            else:
                unequipped.append(item_text)

        if equipped:
            inventory_text += "\nEquipped Items:\n" + "\n".join(equipped)
        if unequipped:
            inventory_text += "\nUnequipped Items:\n" + "\n".join(unequipped)

        return {
            "success": True,
            "message": inventory_text
        }

    def _cmd_skills(self, user: User, args: List[str]) -> Dict:
        """Show skills"""
        if not user.skills:
            return {
                "success": True,
                "message": "You don't have any skills yet."
            }

        skills_text = "\nSkills:\n"
        for skill in user.skills:
            skills_text += (
                f"[{skill.id}] {skill.name} (Level {skill.level})\n"
                f"    {skill.description}\n"
                f"    MP Cost: {skill.mp_cost}"
            )
            if skill.damage > 0:
                skills_text += f" | Damage: {skill.damage}"
            if skill.heal > 0:
                skills_text += f" | Heal: {skill.heal}"
            if skill.status_effect:
                skills_text += f" | Effect: {skill.status_effect.value}"
            skills_text += "\n"

        return {
            "success": True,
            "message": skills_text
        }

    def _cmd_gates(self, user: User, args: List[str]) -> Dict:
        """Show available gates"""
        # Get AI-recommended gates
        profile = self.ai_agent.analyze_player(user)
        available_gates = Gate.query.filter(
            Gate.min_level <= user.level,
            Gate.min_hunter_class <= user.hunter_class
        ).all()

        if not available_gates:
            return {
                "success": True,
                "message": "No gates available for your level and class."
            }

        gates_text = "\nAvailable Gates:\n"
        for gate in available_gates:
            confidence = self.ai_agent.calculate_gate_confidence(user, gate, profile)
            recommendation = (
                "Recommended!" if confidence > 0.7
                else "Challenging" if confidence > 0.4
                else "Dangerous!"
            )
            
            gates_text += (
                f"[{gate.id}] {gate.name}\n"
                f"    Rank: {gate.rank.value}\n"
                f"    Min Level: {gate.min_level}\n"
                f"    Min Class: {gate.min_hunter_class.value}\n"
                f"    Rewards: {gate.crystal_reward_min}-{gate.crystal_reward_max} Crystals\n"
                f"    Status: {recommendation}\n"
            )

        return {
            "success": True,
            "message": gates_text
        }

    def _cmd_enter_gate(self, user: User, args: List[str]) -> Dict:
        """Enter a gate"""
        if not args:
            return {
                "success": False,
                "message": "Please specify a gate ID. Usage: enter [gate_id]"
            }

        try:
            gate_id = int(args[0])
        except ValueError:
            return {
                "success": False,
                "message": "Invalid gate ID. Must be a number."
            }

        gate = Gate.query.get(gate_id)
        if not gate:
            return {
                "success": False,
                "message": f"Gate {gate_id} not found."
            }

        # Check requirements
        if user.level < gate.min_level:
            return {
                "success": False,
                "message": f"Required level: {gate.min_level}"
            }

        if user.hunter_class < gate.min_hunter_class:
            return {
                "success": False,
                "message": f"Required class: {gate.min_hunter_class.value}"
            }

        # Enter gate
        result = self.game_handler.enter_gate(user)
        return result

    def _cmd_party(self, user: User, args: List[str]) -> Dict:
        """Party management"""
        if not args:
            return {
                "success": False,
                "message": "Party sub-commands: create, invite, join, leave, list"
            }

        sub_command = args[0].lower()
        if sub_command == 'create':
            if user.party_id:
                return {
                    "success": False,
                    "message": "You are already in a party."
                }
            
            party = Party(leader_id=user.id)
            db.session.add(party)
            user.party_id = party.id
            user.is_in_party = True
            db.session.commit()
            
            return {
                "success": True,
                "message": "Party created."
            }
            
        elif sub_command == 'invite':
            if len(args) < 2:
                return {
                    "success": False,
                    "message": "Please specify a player to invite."
                }
                
            if not user.party_id:
                return {
                    "success": False,
                    "message": "You are not in a party."
                }
                
            party = Party.query.get(user.party_id)
            if party.leader_id != user.id:
                return {
                    "success": False,
                    "message": "Only the party leader can invite players."
                }
                
            target = User.query.filter_by(username=args[1]).first()
            if not target:
                return {
                    "success": False,
                    "message": f"Player {args[1]} not found."
                }
                
            if target.party_id:
                return {
                    "success": False,
                    "message": f"{target.username} is already in a party."
                }
                
            # TODO: Implement party invites system
            return {
                "success": True,
                "message": f"Invited {target.username} to party."
            }
            
        elif sub_command == 'join':
            if len(args) < 2:
                return {
                    "success": False,
                    "message": "Please specify a party ID to join."
                }
                
            if user.party_id:
                return {
                    "success": False,
                    "message": "You are already in a party."
                }
                
            try:
                party_id = int(args[1])
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid party ID."
                }
                
            party = Party.query.get(party_id)
            if not party:
                return {
                    "success": False,
                    "message": f"Party {party_id} not found."
                }
                
            # TODO: Check party invite
            user.party_id = party.id
            user.is_in_party = True
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Joined party {party_id}."
            }
            
        elif sub_command == 'leave':
            if not user.party_id:
                return {
                    "success": False,
                    "message": "You are not in a party."
                }
                
            party = Party.query.get(user.party_id)
            if party.leader_id == user.id:
                # Disband party if leader leaves
                for member in party.members:
                    member.party_id = None
                    member.is_in_party = False
                db.session.delete(party)
                message = "Party disbanded."
            else:
                user.party_id = None
                user.is_in_party = False
                message = "Left party."
                
            db.session.commit()
            return {
                "success": True,
                "message": message
            }
            
        elif sub_command == 'list':
            if user.party_id:
                party = Party.query.get(user.party_id)
                members_text = "\nParty Members:\n"
                for member in party.members:
                    members_text += (
                        f"{'(Leader) ' if member.id == party.leader_id else ''}"
                        f"{member.username} "
                        f"[Level {member.level} {member.job_class.value if member.job_class else 'None'}]\n"
                    )
                return {
                    "success": True,
                    "message": members_text
                }
            else:
                active_parties = Party.query.all()
                if not active_parties:
                    return {
                        "success": True,
                        "message": "No active parties found."
                    }
                    
                parties_text = "\nActive Parties:\n"
                for party in active_parties:
                    leader = User.query.get(party.leader_id)
                    members = len(party.members)
                    parties_text += (
                        f"[{party.id}] Leader: {leader.username} "
                        f"| Members: {members}\n"
                    )
                return {
                    "success": True,
                    "message": parties_text
                }

        return {
            "success": False,
            "message": f"Unknown party sub-command: {sub_command}"
        }

    def _cmd_guild(self, user: User, args: List[str]) -> Dict:
        """Guild management"""
        if not args:
            return {
                "success": False,
                "message": "Guild sub-commands: create, invite, join, leave, info"
            }

        sub_command = args[0].lower()
        if sub_command == 'create':
            if len(args) < 2:
                return {
                    "success": False,
                    "message": "Please specify a guild name."
                }
                
            if user.guild_id:
                return {
                    "success": False,
                    "message": "You are already in a guild."
                }
                
            # Check creation cost
            if user.crystals < GUILD_CREATION_COST['crystals']:
                return {
                    "success": False,
                    "message": f"Need {GUILD_CREATION_COST['crystals']} crystals."
                }
                
            if user.exons_balance < GUILD_CREATION_COST['exons']:
                return {
                    "success": False,
                    "message": f"Need {GUILD_CREATION_COST['exons']} exons."
                }
                
            guild_name = ' '.join(args[1:])
            if Guild.query.filter_by(name=guild_name).first():
                return {
                    "success": False,
                    "message": "Guild name already taken."
                }
                
            # Create guild
            guild = Guild(
                name=guild_name,
                leader_id=user.id
            )
            db.session.add(guild)
            
            # Deduct creation cost
            user.crystals -= GUILD_CREATION_COST['crystals']
            user.exons_balance -= GUILD_CREATION_COST['exons']
            user.guild_id = guild.id
            
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Guild '{guild_name}' created."
            }
            
        elif sub_command == 'info':
            guild = None
            if len(args) > 1:
                guild_name = ' '.join(args[1:])
                guild = Guild.query.filter_by(name=guild_name).first()
            elif user.guild_id:
                guild = Guild.query.get(user.guild_id)
                
            if not guild:
                return {
                    "success": False,
                    "message": "Guild not found."
                }
                
            leader = User.query.get(guild.leader_id)
            info_text = (
                f"\nGuild: {guild.name}\n"
                f"Leader: {leader.username}\n"
                f"Level: {guild.level}\n"
                f"Members: {len(guild.members)}\n"
                f"Treasury: {guild.crystals} Crystals, {guild.exons_balance} Exons\n"
            )
            
            if guild.id == user.guild_id:
                info_text += "\nMembers:\n"
                for member in guild.members:
                    info_text += (
                        f"{'(Leader) ' if member.id == guild.leader_id else ''}"
                        f"{member.username} "
                        f"[Level {member.level} {member.job_class.value if member.job_class else 'None'}]\n"
                    )
            
            return {
                "success": True,
                "message": info_text
            }
            
        # Add more guild commands as needed
        return {
            "success": False,
            "message": f"Unknown guild sub-command: {sub_command}"
        }

    def _cmd_shop(self, user: User, args: List[str]) -> Dict:
        """Access hunter shop"""
        if user.is_in_gate and not any(
            item.item.name == 'Remote Shop License' and item.is_equipped
            for item in user.inventory_items
        ):
            return {
                "success": False,
                "message": "Need Remote Shop License to shop in gates."
            }

        shop_text = "\nHunter Shop:\n"
        
        # List shop items
        shop_text += "\nUtility Items:\n"
        for item_id, item in SHOP_ITEMS.items():
            shop_text += f"[{item_id}] {item['name']}"
            if 'price_crystals' in item:
                shop_text += f" - {item['price_crystals']} Crystals"
            if 'price_exons' in item:
                shop_text += f" - {item['price_exons']} Exons"
            shop_text += f"\n    {item['description']}\n"
            
        # List potions
        shop_text += "\nPotions:\n"
        for potion_id, potion in POTIONS.items():
            shop_text += (
                f"[{potion_id}] {potion['name']} "
                f"- {potion['price_crystals']} Crystals\n"
            )
            
        # List antidotes
        shop_text += "\nAntidotes:\n"
        for antidote_id, antidote in ANTIDOTES.items():
            shop_text += (
                f"[{antidote_id}] {antidote['name']} "
                f"- {antidote['price_crystals']} Crystals\n"
            )

        return {
            "success": True,
            "message": shop_text
        }

    def _cmd_buy(self, user: User, args: List[str]) -> Dict:
        """Buy items from shop"""
        if not args:
            return {
                "success": False,
                "message": "Please specify an item to buy."
            }

        item_id = args[0].lower()
        quantity = 1
        if len(args) > 1:
            try:
                quantity = int(args[1])
                if quantity < 1:
                    raise ValueError
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid quantity."
                }

        # Check shop items
        if item_id in SHOP_ITEMS:
            item = SHOP_ITEMS[item_id]
            if 'price_crystals' in item:
                total_cost = item['price_crystals'] * quantity
                if user.crystals < total_cost:
                    return {
                        "success": False,
                        "message": f"Need {total_cost} crystals."
                    }
                user.crystals -= total_cost
            elif 'price_exons' in item:
                total_cost = item['price_exons'] * quantity
                if user.exons_balance < total_cost:
                    return {
                        "success": False,
                        "message": f"Need {total_cost} exons."
                    }
                user.exons_balance -= total_cost
                
            # Handle special items
            if item_id == 'inventory_expansion':
                user.inventory_slots += 10 * quantity
            elif item_id == 'remote_shop':
                # Create license item
                shop_license = Item(
                    name='Remote Shop License',
                    description='Allows shop access in gates',
                    type='license',
                    is_tradeable=False
                )
                db.session.add(shop_license)
                db.session.flush()
                
                inv_item = InventoryItem(
                    user_id=user.id,
                    item_id=shop_license.id,
                    quantity=quantity
                )
                db.session.add(inv_item)
            # Add more special items as needed
            
            db.session.commit()
            return {
                "success": True,
                "message": f"Bought {quantity}x {item['name']}."
            }
            
        # Check potions
        elif item_id in POTIONS:
            potion = POTIONS[item_id]
            total_cost = potion['price_crystals'] * quantity
            if user.crystals < total_cost:
                return {
                    "success": False,
                    "message": f"Need {total_cost} crystals."
                }
                
            # Create potion item if needed
            potion_item = Item.query.filter_by(name=potion['name']).first()
            if not potion_item:
                potion_item = Item(
                    name=potion['name'],
                    type='potion',
                    is_tradeable=True
                )
                db.session.add(potion_item)
                db.session.flush()
                
            # Add to inventory
            inv_item = InventoryItem.query.filter_by(
                user_id=user.id,
                item_id=potion_item.id
            ).first()
            
            if inv_item:
                inv_item.quantity += quantity
            else:
                inv_item = InventoryItem(
                    user_id=user.id,
                    item_id=potion_item.id,
                    quantity=quantity
                )
                db.session.add(inv_item)
                
            user.crystals -= total_cost
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Bought {quantity}x {potion['name']}."
            }
            
        # Check antidotes
        elif item_id in ANTIDOTES:
            antidote = ANTIDOTES[item_id]
            total_cost = antidote['price_crystals'] * quantity
            if user.crystals < total_cost:
                return {
                    "success": False,
                    "message": f"Need {total_cost} crystals."
                }
                
            # Create antidote item if needed
            antidote_item = Item.query.filter_by(name=antidote['name']).first()
            if not antidote_item:
                antidote_item = Item(
                    name=antidote['name'],
                    type='antidote',
                    is_tradeable=True
                )
                db.session.add(antidote_item)
                db.session.flush()
                
            # Add to inventory
            inv_item = InventoryItem.query.filter_by(
                user_id=user.id,
                item_id=antidote_item.id
            ).first()
            
            if inv_item:
                inv_item.quantity += quantity
            else:
                inv_item = InventoryItem(
                    user_id=user.id,
                    item_id=antidote_item.id,
                    quantity=quantity
                )
                db.session.add(inv_item)
                
            user.crystals -= total_cost
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Bought {quantity}x {antidote['name']}."
            }

        return {
            "success": False,
            "message": f"Item '{item_id}' not found in shop."
        }

    def _cmd_balance(self, user: User, args: List[str]) -> Dict:
        """Check currency balance"""
        balance_text = (
            f"\nBalance:\n"
            f"Solana: {user.solana_balance:.8f}\n"
            f"Exons: {user.exons_balance:.2f}\n"
            f"Crystals: {user.crystals:,}"
        )
        return {
            "success": True,
            "message": balance_text
        }

    def _cmd_wallet(self, user: User, args: List[str]) -> Dict:
        """Manage Web3 wallet"""
        if not args:
            if user.web3_wallet:
                return {
                    "success": True,
                    "message": f"Connected wallet: {user.web3_wallet}"
                }
            else:
                return {
                    "success": True,
                    "message": "No wallet connected. Use 'wallet connect' to connect."
                }

        sub_command = args[0].lower()
        if sub_command == 'connect':
            if len(args) < 2:
                return {
                    "success": False,
                    "message": "Please provide wallet address."
                }
                
            wallet = args[1]
            # TODO: Validate wallet address
            user.web3_wallet = wallet
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Wallet connected: {wallet}"
            }
            
        elif sub_command == 'disconnect':
            if not user.web3_wallet:
                return {
                    "success": False,
                    "message": "No wallet connected."
                }
                
            user.web3_wallet = None
            db.session.commit()
            
            return {
                "success": True,
                "message": "Wallet disconnected."
            }

        return {
            "success": False,
            "message": f"Unknown wallet sub-command: {sub_command}"
        }

    def _cmd_flip_coin(self, user: User, args: List[str]) -> Dict:
        """Flip coin gambling"""
        if not args:
            return {
                "success": False,
                "message": "Please specify bet amount."
            }

        try:
            bet = int(args[0])
            if bet < 100:
                return {
                    "success": False,
                    "message": "Minimum bet is 100 crystals."
                }
        except ValueError:
            return {
                "success": False,
                "message": "Invalid bet amount."
            }

        if user.crystals < bet:
            return {
                "success": False,
                "message": f"Need {bet} crystals."
            }

        # Get AI-adjusted win chance
        profile = self.ai_agent.analyze_player(user)
        base_chance = 0.48  # Slight house edge
        win_chance = self.ai_agent.adjust_gambling_odds(user, base_chance, profile)
        
        # Flip coin
        win = random.random() < win_chance
        if win:
            user.crystals += bet
            message = f"You won {bet} crystals!"
        else:
            user.crystals -= bet
            message = f"You lost {bet} crystals."
            
        db.session.commit()
        
        return {
            "success": True,
            "message": message
        }

    # Add more command handlers as needed
