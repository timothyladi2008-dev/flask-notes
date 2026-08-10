from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, User
from . import db
import json

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note_data = request.form.get('note')
        color = request.form.get('color') or current_user.default_note_color or '#ffffff'

        if len(note_data) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note_data, user_id=current_user.id, color=color)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    # Get active notes (not in trash), ordered by pinned status first, then newest date
    notes = Note.query.filter_by(user_id=current_user.id, is_deleted=False)\
                      .order_by(Note.is_pinned.desc(), Note.date.desc()).all()

    return render_template("home.html", user=current_user, notes=notes, show_trash=False)


@views.route('/trash')
@login_required
def trash():
    # View soft-deleted notes
    trashed_notes = Note.query.filter_by(user_id=current_user.id, is_deleted=True)\
                              .order_by(Note.date.desc()).all()
    return render_template("home.html", user=current_user, notes=trashed_notes, show_trash=True)


@views.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    data = json.loads(request.data)
    note_id = data.get('noteId')
    permanent = data.get('permanent', False)

    note = Note.query.get(note_id)
    if note and note.user_id == current_user.id:
        if permanent:
            db.session.delete(note)
        else:
            note.is_deleted = True  # Soft delete to trash
        db.session.commit()

    return jsonify({})


@views.route('/restore-note', methods=['POST'])
@login_required
def restore_note():
    data = json.loads(request.data)
    note_id = data.get('noteId')

    note = Note.query.get(note_id)
    if note and note.user_id == current_user.id:
        note.is_deleted = False
        db.session.commit()

    return jsonify({})


@views.route('/toggle-pin', methods=['POST'])
@login_required
def toggle_pin():
    data = json.loads(request.data)
    note_id = data.get('noteId')

    note = Note.query.get(note_id)
    if note and note.user_id == current_user.id:
        note.is_pinned = not note.is_pinned
        db.session.commit()

    return jsonify({})


@views.route('/profile')
@login_required
def profile():
    active_count = Note.query.filter_by(user_id=current_user.id, is_deleted=False).count()
    return render_template("profile.html", user=current_user, active_notes_count=active_count)


@views.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    default_color = request.form.get('default_color')
    if default_color:
        current_user.default_note_color = default_color
        db.session.commit()
        flash('Preferences saved!', category='success')
    return redirect(url_for('views.profile'))