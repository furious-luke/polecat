authenticate_query = '''mutation($email: String!, $password: String!) {
  authenticate(input: {email: $email, password: $password}) {
    token
  }
}
'''

all_movies_query = '''query {
  allMovies {
    id,
    title,
    star {
      id,
      firstName,
      lastName,
      age,
      address {
        id,
        country
      }
    }
  }
}
'''

all_actors_query = '''query {
  allActors {
    id,
    firstName,
    lastName,
    age,
    moviesByStar {
      id,
      title
    }
  }
}
'''
