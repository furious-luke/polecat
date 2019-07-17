authenticate_query = '''mutation($email: String!, $password: String!) {
  authenticate(input: {email: $email, password: $password}) {
    token
  }
}
'''

all_addresses_query = '''query {
  allAddresss {
    id
  }
}
'''

get_address_query = '''query($id: Int) {
  getAddress(id: $id) {
    id
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

create_actors_query = '''mutation {
  firstActor: createActor(input: {firstName: "a", lastName: "b", age: 30}) {
    id,
    firstName,
    lastName,
    age
  }
  secondActor: createActor(input: {firstName: "c", lastName: "d", age: 40}) {
    id,
    firstName,
    lastName,
    age
  }
}
'''

create_actor_and_movies_query = '''mutation {
  createActor(input: {
    firstName: "a",
    lastName: "b",
    moviesByStar: {create: [{title: "c"}, {title: "d"}]}
  }) {
    id,
    firstName,
    lastName,
    moviesByStar {
      id,
      title
    }
  }
}
'''

update_actors_query = '''mutation($id1: Int!, $id2: Int!) {
  firstActor: updateActor(id: $id1, input: {age: 60}) {
    id,
    firstName,
    lastName,
    age
  }
  secondActor: updateActor(id: $id2, input: {age: 80}) {
    id,
    firstName,
    lastName,
    age
  }
}
'''

update_or_create_actor_query = '''mutation($id: Int, $firstName: String!) {
  updateOrCreateActor(id: $id, input: {firstName: $firstName}) {
    id,
    firstName
  }
}
'''

update_or_create_store_query = '''mutation($name: String!) {
  updateOrCreateStore(input: {name: $name}) {
    id,
    name
  }
}
'''

delete_movie_query = '''mutation($id: Int!) {
  deleteMovie(input: {id: $id}) {
    id
  }
}
'''
