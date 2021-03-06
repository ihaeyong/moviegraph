#!/usr/bin/env python
# coding: utf-8


from flask import Flask, abort, render_template, request
from neo4j.v1 import GraphDatabase


app = Flask(__name__)

# Set up a driver for the local graph database.
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))


def match_movies(tx, q):
    return tx.run("MATCH (movie:Movie) WHERE toLower(movie.title) CONTAINS toLower($term) "
                  "RETURN movie", term=q).value()


def match_movie(tx, title):
    return tx.run("MATCH (movie:Movie) WHERE movie.title = $title "
                  "OPTIONAL MATCH (person)-[:ACTED_IN]->(movie) "
                  "RETURN movie, collect(person) AS actors", title=title).single()


def match_person(tx, name):
    return tx.run("MATCH (person:Person) WHERE person.name = $name "
                  "OPTIONAL MATCH (person)-[:ACTED_IN]->(movie) "
                  "RETURN person, collect(movie) AS movies", name=name).single()


@app.route("/")
def get_index():
    """ Show the index page.
    """
    search_term = request.args.get("q", "")
    if search_term:
        with driver.session() as session:
            movies = session.read_transaction(match_movies, q=search_term)
    else:
        movies = []
    return render_template("index.html", movies=movies, q=search_term)


@app.route("/movie/<path:title>")
def get_movie(title):
    """ Display details of a particular movie.
    """
    with driver.session() as session:
        record = session.read_transaction(match_movie, title)
    if record is None:
        abort(404, "Movie not found")
    return render_template("movie.html", movie=record["movie"], actors=record["actors"])


@app.route("/person/<name>")
def get_person(name):
    """ Display details of a particular person.
    """
    with driver.session() as session:
        record = session.read_transaction(match_person, name)
    if record is None:
        abort(404, "Person not found")
    return render_template("person.html", person=record["person"], movies=record["movies"])


if __name__ == "__main__":
    app.run(debug=True)
