from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired
import requests
import my_secrets


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies_list2.db"
app.config['SECRET_KEY'] = my_secrets.SECRET_KEY
Bootstrap5(app)

db = SQLAlchemy()
db.init_app(app)

key = my_secrets.key
header = my_secrets.header


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


class Rating(FlaskForm):
    rating = StringField('Your Rating out of 10', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Submit')


class Add(FlaskForm):
    name = StringField('Name of the movie', validators=[DataRequired()])
    submit = SubmitField('Add')


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_m = result.scalars().all()
    for i in range(len(all_m)):
        all_m[i].ranking = len(all_m) - i
    db.session.commit()
    return render_template("index.html", all_m=all_m)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = Rating()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    movie_id = request.args.get('id')
    movie_selected = db.get_or_404(Movie, movie_id)
    return render_template('edit.html', form=form, mov=movie_selected)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add():
    form = Add()
    if form.validate_on_submit():
        to_search = str(form.name.data)
        url = f"https://api.themoviedb.org/3/search/movie?query={to_search}&include_adult=true&language=en-US&page=1"
        result = requests.get(url, headers=header).json()['results']
        return render_template('select.html', result=result)
    return render_template('add.html', form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        url2 = f'https://api.themoviedb.org/3/movie/{movie_api_id}?language=en-US'
        response = requests.get(url2, params=my_secrets.params, headers=header)
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
