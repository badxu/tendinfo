from flask import render_template, request, session, redirect, url_for, current_app,flash
from .. import db
from ..models import User, Role, Tendinfo, Permission
from ..email import send_email
from . import main
from .forms import NameForm,EditProfileForm, EditProfileAdminForm, TendInfo
from datetime import datetime
from flask.ext.login import login_user,current_user,login_required 
from ..decorators import admin_required



@main.route('/', methods=['GET', 'POST'])
def index():
    form = TendInfo()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        key = form.key.data
        return redirect(url_for('.select', key=key))
    page = request.args.get('page', 1, type=int)
    pagination = Tendinfo.query.order_by(Tendinfo.td_time.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    tendinfos = pagination.items
    return render_template('index.html', form=form, tendinfos=tendinfos,
                            pagination=pagination)

@main.route('/select/<key>', methods=['GET', 'POST'])
def select(key):
    form = TendInfo()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        key = form.key.data.strip()
        return redirect(url_for('.select', key=key))

    #filter must declare class name and score bigger than filter_by
    keywords = '%' + key + '%'
    page = request.args.get('page', 1, type=int)
    pagination = Tendinfo.query.filter(Tendinfo.td_name.like(keywords)).order_by(Tendinfo.td_time.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    tendinfos = pagination.items
    counts = Tendinfo.query.filter(Tendinfo.td_name.like(keywords)).count()
    return render_template('selectresult.html', form=form, tendinfos=tendinfos,
                           pagination=pagination, counts=counts,key=key)
    

@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('你的用户信息已更新！')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)

@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)
