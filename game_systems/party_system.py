"""
Party System for Terminusa Online
"""
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import random
import logging
from models import db, User, Party, PartyMember, Gate
from game_config import PARTY_CONFIG

logger = logging.getLogger(__name__)

class PartySystem:
    """Handles party formation and management"""
    
    def __init__(self):
        self.active_parties = {}  # Track active party instances

    def create_party(self, leader: User, name: str) -> Dict:
        """Create a new party"""
        try:
            # Check if user is already in a party
            if self._get_user_party(leader):
                return {
                    "success": False,
                    "message": "Already in a party"
                }

            # Create party
            party = Party(
                name=name,
                leader_id=leader.id,
                created_at=datetime.utcnow()
            )
            db.session.add(party)
            db.session.flush()  # Get party ID

            # Add leader as member
            member = PartyMember(
                party_id=party.id,
                user_id=leader.id,
                joined_at=datetime.utcnow()
            )
            db.session.add(member)

            # Initialize party instance
            self.active_parties[party.id] = {
                "party": party,
                "members": {leader.id: leader},
                "current_gate": None,
                "ready_status": {leader.id: False}
            }

            db.session.commit()

            return {
                "success": True,
                "message": "Party created successfully",
                "party_id": party.id
            }

        except Exception as e:
            logger.error(f"Failed to create party: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to create party"
            }

    def join_party(self, user: User, party_id: int) -> Dict:
        """Join an existing party"""
        try:
            # Check if user is already in a party
            if self._get_user_party(user):
                return {
                    "success": False,
                    "message": "Already in a party"
                }

            party = Party.query.get(party_id)
            if not party:
                return {
                    "success": False,
                    "message": "Party not found"
                }

            # Check member limit
            current_members = PartyMember.query.filter_by(party_id=party_id).count()
            if current_members >= PARTY_CONFIG['max_members']:
                return {
                    "success": False,
                    "message": "Party is full"
                }

            # Add member
            member = PartyMember(
                party_id=party_id,
                user_id=user.id,
                joined_at=datetime.utcnow()
            )
            db.session.add(member)

            # Update active party instance
            if party_id in self.active_parties:
                self.active_parties[party_id]["members"][user.id] = user
                self.active_parties[party_id]["ready_status"][user.id] = False

            db.session.commit()

            return {
                "success": True,
                "message": "Successfully joined party"
            }

        except Exception as e:
            logger.error(f"Failed to join party: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to join party"
            }

    def leave_party(self, user: User) -> Dict:
        """Leave current party"""
        try:
            party = self._get_user_party(user)
            if not party:
                return {
                    "success": False,
                    "message": "Not in a party"
                }

            # Check if in gate
            if party.id in self.active_parties:
                party_instance = self.active_parties[party.id]
                if party_instance["current_gate"]:
                    return {
                        "success": False,
                        "message": "Cannot leave party while in gate"
                    }

            # If leader, assign new leader or disband
            if party.leader_id == user.id:
                result = self._handle_leader_leave(party, user)
                if not result["success"]:
                    return result
            else:
                # Remove member
                PartyMember.query.filter_by(
                    party_id=party.id,
                    user_id=user.id
                ).delete()

            # Update active party instance
            if party.id in self.active_parties:
                if user.id in self.active_parties[party.id]["members"]:
                    del self.active_parties[party.id]["members"][user.id]
                if user.id in self.active_parties[party.id]["ready_status"]:
                    del self.active_parties[party.id]["ready_status"][user.id]

            db.session.commit()

            return {
                "success": True,
                "message": "Successfully left party"
            }

        except Exception as e:
            logger.error(f"Failed to leave party: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to leave party"
            }

    def set_ready_status(self, user: User, is_ready: bool) -> Dict:
        """Set party member ready status"""
        try:
            party = self._get_user_party(user)
            if not party:
                return {
                    "success": False,
                    "message": "Not in a party"
                }

            if party.id not in self.active_parties:
                return {
                    "success": False,
                    "message": "Party instance not found"
                }

            # Update ready status
            self.active_parties[party.id]["ready_status"][user.id] = is_ready

            # Check if all members are ready
            all_ready = all(self.active_parties[party.id]["ready_status"].values())

            return {
                "success": True,
                "message": "Ready status updated",
                "is_ready": is_ready,
                "all_ready": all_ready
            }

        except Exception as e:
            logger.error(f"Failed to set ready status: {str(e)}")
            return {
                "success": False,
                "message": "Failed to set ready status"
            }

    def enter_gate(self, party_id: int, gate: Gate) -> Dict:
        """Enter gate as a party"""
        try:
            party_instance = self.active_parties.get(party_id)
            if not party_instance:
                return {
                    "success": False,
                    "message": "Party instance not found"
                }

            # Check if already in gate
            if party_instance["current_gate"]:
                return {
                    "success": False,
                    "message": "Already in a gate"
                }

            # Check if all members are ready
            if not all(party_instance["ready_status"].values()):
                return {
                    "success": False,
                    "message": "Not all members are ready"
                }

            # Check level requirements
            for member in party_instance["members"].values():
                if member.level < gate.level_requirement:
                    return {
                        "success": False,
                        "message": f"Member {member.username} does not meet level requirement"
                    }

            # Set current gate
            party_instance["current_gate"] = gate

            return {
                "success": True,
                "message": "Party entered gate successfully"
            }

        except Exception as e:
            logger.error(f"Failed to enter gate: {str(e)}")
            return {
                "success": False,
                "message": "Failed to enter gate"
            }

    def calculate_rewards(self, party_id: int, base_rewards: Dict) -> Dict:
        """Calculate reward distribution for party members"""
        try:
            party_instance = self.active_parties.get(party_id)
            if not party_instance:
                return {
                    "success": False,
                    "message": "Party instance not found"
                }

            member_count = len(party_instance["members"])
            reward_scale = PARTY_CONFIG["reward_scaling"].get(
                member_count,
                PARTY_CONFIG["reward_scaling"][10]  # Use 10+ scaling for larger parties
            )

            # Calculate individual shares
            rewards_per_member = {
                member_id: {
                    "crystals": int(base_rewards["crystals"] * reward_scale),
                    "experience": int(base_rewards["experience"] * reward_scale)
                }
                for member_id in party_instance["members"]
            }

            # Handle equipment drops
            if "equipment" in base_rewards:
                for item in base_rewards["equipment"]:
                    # Randomly assign to a member
                    lucky_member = random.choice(list(party_instance["members"].keys()))
                    if lucky_member not in rewards_per_member:
                        rewards_per_member[lucky_member] = {}
                    if "items" not in rewards_per_member[lucky_member]:
                        rewards_per_member[lucky_member]["items"] = []
                    rewards_per_member[lucky_member]["items"].append(item)

            return {
                "success": True,
                "rewards": rewards_per_member,
                "scale": reward_scale
            }

        except Exception as e:
            logger.error(f"Failed to calculate rewards: {str(e)}")
            return {
                "success": False,
                "message": "Failed to calculate rewards"
            }

    def get_party_info(self, party_id: int) -> Dict:
        """Get party information"""
        try:
            party = Party.query.get(party_id)
            if not party:
                return {
                    "success": False,
                    "message": "Party not found"
                }

            members = User.query.join(PartyMember).filter(
                PartyMember.party_id == party_id
            ).all()

            # Get ready status if party is active
            ready_status = {}
            if party_id in self.active_parties:
                ready_status = self.active_parties[party_id]["ready_status"]

            return {
                "success": True,
                "party": {
                    "id": party.id,
                    "name": party.name,
                    "leader_id": party.leader_id,
                    "created_at": party.created_at.isoformat(),
                    "members": [
                        {
                            "id": member.id,
                            "username": member.username,
                            "level": member.level,
                            "job_class": member.job_class,
                            "is_ready": ready_status.get(member.id, False)
                        }
                        for member in members
                    ],
                    "current_gate": (
                        self.active_parties[party_id]["current_gate"].id
                        if party_id in self.active_parties and
                        self.active_parties[party_id]["current_gate"]
                        else None
                    )
                }
            }

        except Exception as e:
            logger.error(f"Failed to get party info: {str(e)}")
            return {
                "success": False,
                "message": "Failed to get party info"
            }

    def _get_user_party(self, user: User) -> Optional[Party]:
        """Get user's current party"""
        member = PartyMember.query.filter_by(user_id=user.id).first()
        if member:
            return Party.query.get(member.party_id)
        return None

    def _handle_leader_leave(self, party: Party, leader: User) -> Dict:
        """Handle party leader leaving"""
        try:
            # Get remaining members
            remaining_members = User.query.join(PartyMember).filter(
                PartyMember.party_id == party.id,
                PartyMember.user_id != leader.id
            ).all()

            if not remaining_members:
                # No members left, disband party
                if party.id in self.active_parties:
                    del self.active_parties[party.id]
                db.session.delete(party)
                return {
                    "success": True,
                    "message": "Party disbanded"
                }

            # Assign new leader (highest level member)
            new_leader = max(remaining_members, key=lambda m: m.level)
            party.leader_id = new_leader.id

            # Remove old leader
            PartyMember.query.filter_by(
                party_id=party.id,
                user_id=leader.id
            ).delete()

            return {
                "success": True,
                "message": f"Leadership transferred to {new_leader.username}"
            }

        except Exception as e:
            logger.error(f"Failed to handle leader leave: {str(e)}")
            raise
