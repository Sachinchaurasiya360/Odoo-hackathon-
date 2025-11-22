"""
User profile routes.

This module defines routes for user profile management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required
from config.database import get_db
from werkzeug.security import check_password_hash, generate_password_hash
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
@login_required
def view():
    """View user profile."""
    try:
        db = get_db()
        user_id = session.get('user_id')
        
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            flash("User not found", "danger")
            return redirect(url_for('dashboard.index'))
        
        return render_template('profile/view.html', user=user)
    except Exception as e:
        logger.error(f"Error viewing profile: {e}")
        flash(f"Error loading profile: {str(e)}", "danger")
        return redirect(url_for('dashboard.index'))

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """Edit user profile."""
    try:
        db = get_db()
        user_id = session.get('user_id')
        
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            flash("User not found", "danger")
            return redirect(url_for('dashboard.index'))
        
        if request.method == 'POST':
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            
            # Check if email is already used by another user
            existing = db.users.find_one({
                'email': email,
                '_id': {'$ne': ObjectId(user_id)}
            })
            if existing:
                flash("Email already in use by another account", "danger")
                return render_template('profile/edit.html', user=user)
            
            # Update profile
            update_data = {
                'full_name': full_name,
                'email': email,
                'phone': phone,
                'updated_at': datetime.utcnow()
            }
            
            db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            
            # Update session
            session['full_name'] = full_name
            
            flash("Profile updated successfully", "success")
            return redirect(url_for('profile.view'))
        
        # GET request
        return render_template('profile/edit.html', user=user)
        
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        flash(f"Error updating profile: {str(e)}", "danger")
        return redirect(url_for('profile.view'))

@profile_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password."""
    try:
        db = get_db()
        user_id = session.get('user_id')
        
        if request.method == 'POST':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Get user
            user = db.users.find_one({'_id': ObjectId(user_id)})
            if not user:
                flash("User not found", "danger")
                return redirect(url_for('dashboard.index'))
            
            # Verify current password
            if not check_password_hash(user.get('password', ''), current_password):
                flash("Current password is incorrect", "danger")
                return render_template('profile/change_password.html')
            
            # Validate new password
            if new_password != confirm_password:
                flash("New passwords do not match", "danger")
                return render_template('profile/change_password.html')
            
            if len(new_password) < 6:
                flash("Password must be at least 6 characters long", "danger")
                return render_template('profile/change_password.html')
            
            # Update password
            hashed_password = generate_password_hash(new_password)
            db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {
                    'password': hashed_password,
                    'updated_at': datetime.utcnow()
                }}
            )
            
            flash("Password changed successfully", "success")
            return redirect(url_for('profile.view'))
        
        # GET request
        return render_template('profile/change_password.html')
        
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        flash(f"Error changing password: {str(e)}", "danger")
        return redirect(url_for('profile.view'))
