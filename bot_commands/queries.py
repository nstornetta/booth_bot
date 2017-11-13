"""Set of queries for handling the basic interaction with the sqlite database"""
TABLE_NAME="winter_2018"

# ------------ Queries to read from the database ------------ #
def by_colname_exact(colname, colname_val):
    return """
    select 
        title,
        section,
        instructor,
        time,
        building,
        hours,
        interesting,
        recommend
    from 
        {table_name}
    where 
        lower({colname}) = lower('{colname_val}')
    order by
        recommend desc,
        interesting desc,
        hours asc
    limit 5
    """.format(colname=colname, colname_val=colname_val, table_name=TABLE_NAME)


def instructor_last_name(instructor_val):
    return """
    select
        title,
        section,
        instructor,
        time,
        building,
        hours,
        interesting,
        recommend
    from
        {table_name}
    where
        lower(substr(instructor, 1, instr(instructor, ',') - 1)) = lower('{instructor_val}')
    order by
        recommend desc,
        interesting desc,
        hours asc
    limit 5
    """.format(instructor_val=instructor_val, table_name=TABLE_NAME)

               
def by_colname_distinct(colname):
    return """
    select 
        distinct {colname}
    from
        {table_name}
    """.format(colname=colname, table_name=TABLE_NAME)


def by_colname_like(colname, colname_val):
    """
    Query to handle the cases in which somebody has the correct
    words within their query, but in the incorrect order (likely 
    to be especially relevant for professors).
    """
    def like_clause_constructor(colname, colname_val):
        """
        Helper function for constructing like clause.
        """
        like_list = colname_val.split(' ')
        like_unit = "lower({colname}) like lower('%{word}%') and "
        like_clause = ""
        for word in like_list:
            like_clause += like_unit.format(colname=colname, word=word)
        return like_clause
    
    return """
    select
        title,
        section,
        instructor,
        time,
        building,
        hours,
        interesting,
        recommend
    from
        {table_name}
    where
        {where_clause}
    recommend > 0
    limit 3
    """.format(where_clause=like_clause_constructor(colname=colname, colname_val=colname_val), table_name=TABLE_NAME)
