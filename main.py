import bdb

from flask import Flask
from flask import render_template, make_response, request, redirect, abort
from flask_login import LoginManager, login_user, login_required,\
    current_user, logout_user
from data import db_session
from data.__all_models import *
from data.forms import *
import datetime
import random


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
lm = LoginManager()
lm.init_app(app)


@lm.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/')
def index():
    base = db_session.create_session()
    raw = base.query(Jobs)
    jobs = []
    for job in raw:
        res = []
        res.append(job.job)
        user = base.query(User).filter(User.id == job.team_leader).first()
        res.append(user.surname + ' ' + user.name)
        res.append(job.work_size)
        res.append(job.collaborators)
        res.append(', '.join([c.name for c in job.categories]))
        if job.is_finished:
            res.append('Завершено')
        else:
            res.append('Не завершено')
        res.append(job.team_leader)
        res.append(job.id)
        jobs.append(res)
    return render_template('jobs.html',
                           title='MARS', jobs=jobs)


@app.route('/departments')
def departments():
    base = db_session.create_session()
    raw = base.query(Department)
    deps = []
    for dep in raw:
        res = []
        res.append(dep.title)
        user = base.query(User).filter(User.id == dep.chief).first()
        res.append(user.surname + ' ' + user.name)
        res.append(', '.join([str(m.id) for m in dep.members]))
        res.append(dep.email)
        res.append(dep.chief)
        res.append(dep.id)
        deps.append(res)
    return render_template('departments.html',
                           title='MARS', deps=deps)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = UserForm()
    if form.validate_on_submit():
        if form.password.data != form.pwc.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Почта занята")
        user = User(
            surname=form.surname.data,
            name=form.name.data,
            age=form.age.data,
            sex=form.sex.data,
            position=form.position.data,
            speciality=form.speciality.data,
            address='module_' + str(random.choice(range(43))),
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/jobs',  methods=['GET', 'POST'])
@login_required
def add_jobs():
    form = JobsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        job = Jobs()
        job.job = form.job.data
        job.team_leader = form.tl.data
        job.work_size = form.duration.data
        job.collaborators = form.loc.data
        job.start_date = form.start.data
        job.end_date = form.start.data + datetime.timedelta(hours=form.duration.data)
        job.categories.extend(db_sess.query(Category).filter(Category.id.in_(form.cat.data.split(', '))))
        job.is_finished = False
        db_sess.add(job)
        db_sess.commit()
        return redirect('/')
    return render_template('redactor.html', title='Добавление работы',
                           form=form, alt=[7, 8])


@app.route('/jobs/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_jobs(id):
    form = JobsForm()
    if request.method == 'GET':
        db_sess = db_session.create_session()
        job = db_sess.query(Jobs).filter(Jobs.id == id).first()
        form.job.data = job.job
        form.tl.data = job.team_leader
        form.duration.data = job.work_size
        form.loc.data = job.collaborators
        form.start.data = job.start_date
        form.cat.data = ', '.join([str(c.id) for c in job.categories])
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        job = db_sess.query(Jobs).filter(Jobs.id == id).first()

        job.job = form.job.data
        job.team_leader = form.tl.data
        job.work_size = form.duration.data
        job.collaborators = form.loc.data
        job.start_date = form.start.data
        job.end_date = form.start.data + datetime.timedelta(hours=form.duration.data)
        job.categories.extend(db_sess.query(Category).filter(Category.id.in_(form.cat.data.split(', '))))
        job.is_finished = False
        db_sess.commit()
        return redirect('/')

    return render_template('redactor.html', title='Редактирование работы',
                           form=form, alt=[7, 8])


@app.route("/jobs_delete/<int:id>")
def delete_jobs(id):
    db_sess = db_session.create_session()
    job = db_sess.query(Jobs).filter(Jobs.id == id,
                                     Jobs.team_leader == current_user.id
                                     ).first()
    if job:
        db_sess.delete(job)
        db_sess.commit()
    return redirect('/')


@app.route('/deps',  methods=['GET', 'POST'])
@login_required
def add_deps():
    form = DepsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        dep = Department()
        dep.title = form.title.data
        dep.chief = form.chief.data
        dep.email = form.email.data
        print('\n', dep.members, type(dep.members), '\n')
        users = db_sess.query(User).filter(User.id.in_(form.members.data.split())).all()
        for u in users:
            if u not in dep.members:
                dep.members.append(u)
        dep.members.append(current_user)
        db_sess.add(dep)
        db_sess.commit()
        return redirect('/departments')
    return render_template('redactor.html', title='Добавление департамента',
                           form=form, alt=[5, 6])


@app.route('/deps/<int:id>',  methods=['GET', 'POST'])
@login_required
def edit_deps(id):
    form = DepsForm()
    if request.method == 'GET':
        db_sess = db_session.create_session()
        dep = db_sess.query(Department).filter(Department.id == id).first()
        form.title.data = dep.title
        form.chief.data = dep.chief
        form.email.data = dep.email
        form.members.data = ', '.join([str(m.id) for m in dep.members])
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        dep = Department
        dep.title = form.title.data
        dep.chief = form.chief.data
        dep.email = form.email.data
        users = db_sess.query(User).filter(User.id.in_(form.members.data.split()))
        dep.members.clear()
        for u in users:
            dep.members.append(u)
        dep.members.append(current_user)
        db_sess.add(dep)
        db_sess.commit()
        return redirect('/departments')
    return render_template('redactor.html', title='Добавление департамента',
                           form=form, alt=[5, 6])


def main():
    db_session.global_init("db/mars.db")
    app.run()


if __name__ == '__main__':
    main()