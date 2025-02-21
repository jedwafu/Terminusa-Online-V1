from flask import Blueprint, render_template
from flask_login import login_required, current_user

from game_systems.marketplace_system import MarketplaceSystem
from game_systems.gacha_system import GachaSystem
from game_systems.inventory_system import InventorySystem

pages_bp = Blueprint('pages', __name__)
marketplace_system = MarketplaceSystem()
gacha_system = GachaSystem()
inventory_system = InventorySystem()

@pages_bp.route('/marketplace')
@login_required
def marketplace():
    """Render marketplace page"""
    # Get current rates for gacha
    mount_rates = gacha_system.get_rates(current_user, 'mount')
    pet_rates = gacha_system.get_rates(current_user, 'pet')
    pity_info = gacha_system.get_pity_info(current_user)
    
    # Get current listings
    listings = marketplace_system.get_listings()
    my_listings = marketplace_system.get_listings(seller_id=current_user.id)
    
    return render_template(
        'marketplace.html',
        user=current_user,
        mount_rates=mount_rates,
        pet_rates=pet_rates,
        pity_info=pity_info,
        listings=listings,
        my_listings=my_listings
    )

@pages_bp.route('/inventory')
@login_required
def inventory():
    """Render inventory page"""
    # Get inventory data
    inventory_data = inventory_system.get_inventory(current_user)
    
    # Get mount and pet stats
    mount_stats = inventory_system.get_mount_stats(current_user)
    pet_abilities = inventory_system.get_pet_abilities(current_user)
    
    return render_template(
        'inventory.html',
        user=current_user,
        inventory=inventory_data.get('inventory', {}),
        mount_stats=mount_stats,
        pet_abilities=pet_abilities
    )

@pages_bp.route('/profile')
@login_required
def profile():
    """Render profile page"""
    # Get player stats and achievements
    mount_stats = inventory_system.get_mount_stats(current_user)
    pet_abilities = inventory_system.get_pet_abilities(current_user)
    
    return render_template(
        'profile.html',
        user=current_user,
        mount_stats=mount_stats,
        pet_abilities=pet_abilities
    )

@pages_bp.route('/leaderboard')
def leaderboard():
    """Render leaderboard page"""
    # Get top players and guilds
    top_hunters = User.query.order_by(User.level.desc()).limit(100).all()
    top_guilds = Guild.query.order_by(Guild.level.desc()).limit(50).all()
    
    return render_template(
        'leaderboard.html',
        top_hunters=top_hunters,
        top_guilds=top_guilds
    )

@pages_bp.route('/gate-stats')
def gate_stats():
    """Render gate statistics page"""
    # Get overall gate statistics
    gate_stats = {
        'total_cleared': Gate.query.filter_by(cleared=True).count(),
        'by_rank': {
            rank.name: Gate.query.filter_by(rank=rank, cleared=True).count()
            for rank in GateRank
        }
    }
    
    return render_template(
        'gate_stats.html',
        stats=gate_stats
    )

@pages_bp.route('/guild/<int:guild_id>')
def guild_page(guild_id):
    """Render guild page"""
    guild = Guild.query.get_or_404(guild_id)
    
    return render_template(
        'guild.html',
        guild=guild,
        members=guild.members,
        quests=guild.active_quests
    )

@pages_bp.route('/help')
def help_page():
    """Render help/documentation page"""
    return render_template('help.html')

# Error handlers
@pages_bp.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', error=error), 404

@pages_bp.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error=error), 500

# Register blueprint in app.py
# app.register_blueprint(pages_bp)
