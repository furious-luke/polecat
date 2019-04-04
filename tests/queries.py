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
