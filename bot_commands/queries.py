"""Set of queries for handling the basic interaction with the sqlite database"""


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
        booth_classes
    where 
        {colname} = '{colname_val}'
    order by
        recommend desc,
        interesting desc,
        hours asc
    limit 5
    """.format(colname=colname, colname_val=colname_val)


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
        booth_classes
    where
        substr(instructor, 1, instr(instructor, ',') - 1) = '{instructor_val}'
    order by
        recommend desc,
        interesting desc,
        hours asc
    limit 5
    """.format(instructor_val=instructor_val)

               
def by_colname_distinct(colname):
    return """
    select 
        distinct {colname}
    from
        booth_classes
    """.format(colname=colname)


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
        like_unit = "{colname} like '%{word}%' and "
        like_clause = ""
        for word in like_list:
            like_clause += like_unit.format(colname=colname, word=word)
        return like_clause
    
    return """
    select
        lower(title),
        lower(section),
        lower(instructor),
        time,
        building,
        hours,
        interesting,
        recommend
    from
        booth_classes
    where
        {where_clause}
    recommend > 0
    limit 3
    """.format(where_clause=like_clause_constructor(colname=colname, colname_val=colname_val))


def get_interest(section_num):
    return """
    select
        registered_interest
    from
        booth_classes
    where section = '{section_num}'
    """.format(section_num=section_num)


# ------------ Queries to update the database -------------- #
def update_interested(section_num, interested_array):
    return """
    update
        booth_classes
    set
        registered_interest = '{interested_array}'
    where
        section = '{section_num}'
    """.format(interested_array=interested_array, section_num=section_num)
