from ..list import List as ListBase


class List(ListBase):
    """ Use laterals to compose a list query.

    WITH ep0(included, type, id, fields) AS (
    SELECT
          'f',
          'movies',
          movies.id,
          jsonb_build_array(movies.name, ep0_actors.values)
    FROM movies
    LIMIT 20
    )
    SELECT * FROM ep0
    INNER JOIN LATERAL (
      SELECT
       't',
       'people',
       people.id,
       jsonb_build_array(people.name, ep1_rented.values),
      FROM people
      WHERE people.id IN (SELECT value FROM jsonb_array_elements(
    
    """

    def get_sql(self):
        sql = getattr(self, '_sql', None)
        if not sql:
            self._aliases, self._subselects = self.get_components()
            cte = self.get_cte(self._subselects)
            main = self.get_main_select(self._aliases)
            sql = f'{cte} {main}'
            self._sql = sql
        return sql

    def 
