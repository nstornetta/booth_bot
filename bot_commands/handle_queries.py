import os
import difflib
import sqlite3
import itertools

import queries
import pyjokes

DATABASE_LOCATION = os.path.dirname(os.path.abspath(__file__)) + "/booth_classes.db"


# ----------- Methods to Determine Which Query and Logic to Apply ------------ #
def respond_to_command(command, user):
    try:
        command_list = [word.lower() for word in command.split()]
        if command_list[0] in ("help", "h", "?"):
            return help_them_out()
        elif "joke" in command_list:
            return tell_joke()
        elif "who are you" in command.lower():
            return "Beep boop. I'm booth_bot! My objective is to help you find classes and bring them up for easy \
            discussion here in Slack. At least until the Singularity... :wink:"
        else:
            conn = sqlite3.connect(DATABASE_LOCATION)
            cursor = conn.cursor()
            command_result = run_query_command(query_type=command_list[0],
                                               command_list=command_list,
                                               user=user,
                                               cursor=cursor)
            conn.commit()
            conn.close()
            return command_result

    except (IndexError, ValueError):
        return "Hmm... I don't recognize that command. Have you tried using `@booth_bot help` to see the things that I know how to do?"


def run_query_command(query_type, command_list, user, cursor):
    args_dict = {"course": ' '.join(command_list[1:]),
                 "course_num": command_list[1],
                 "instructor": ' '.join(command_list[1:]),
                 "mark_interest": command_list[1],
                 "remove_interest": command_list[1],
                 "see_interested": command_list[1]
                 }

    colname_dict = {"course": "title",
                    "course_num": "course",
                    "instructor": "instructor",
                    }

    try:
        if query_type in ("mark_interest", "remove_interest"):
            return update_interest(args_dict[query_type], query_type, cursor=cursor, user=user)
        elif query_type == "see_interested":
            return get_num_interested(args_dict[query_type], cursor=cursor)
        elif query_type == "instructor":  # Handle instructor case separately since the logic is just slightly different
            query = queries.instructor_last_name(instructor_val=args_dict[query_type])
        elif query_type in ("course", "course_num"):
            query = queries.by_colname_exact(colname=colname_dict[query_type], colname_val=args_dict[query_type])
        else:
            raise ValueError  # Query type has to match one of the predefined functions
        result = list(cursor.execute(query))
        assert len(result) > 0

        result_strings = results_strings_list(query_result=result) 
        return """Here's what I found:\n{results}""".format(results='\n'.join(result_strings))

    except AssertionError:  # i.e., if no results are returned when using exact match
        query = queries.by_colname_distinct(colname=colname_dict[query_type])
        result = list(itertools.chain(*list(cursor.execute(query))))
        if len(result) != 0:
            close_matches = difflib.get_close_matches(args_dict[query_type], result)
            if len(close_matches) > 0:
                return """I couldn't find anything matching that exact description. Perhaps you meant {this_or_these}\n\t\t{close_matches}\nIf you ask me again with {this_or_these}, I should be able to find some better results for you.
            """.format(this_or_these='one of these' if len(result) > 1 else 'this',
                       close_matches='\n\t\t'.join([x.title() for x in close_matches]))
            else: 
                return """I couldn't find any courses to match `{command}`; try checking your query. If your query is correct, it may be that there are no sections offered that fit your description.""".format(
                    command=' '.join(command_list))

        # As a last-ditch effort if there's no exact match or close spelling match, use a like-match for each word
        # (e.g., "Accounting" -> "Financial Accounting", a potentially common mistake)
        else:
            query = queries.by_colname_like(colname=colname_dict[query_type], colname_val=args_dict[query_type])
            result = list(cursor.execute(query))
            if len(result) == 0:
                return """I tried my hardest, but I couldn't seem to find what you were looking for.\nHave you tried using the `@booth_both help` command to see what I can do?"""
            else:
                result_strings = results_strings_list(query_result=result) 
                return """I'm not quite sure this is what you're looking for, but here's what I found:
                {results}""".format(results='\n'.join(result_strings))


# --------------- Actual Business Logic Below Here ---------------- #
def tell_joke():
    return """Well, I wasn't programmed for that, but here goes:\n""" + pyjokes.get_joke()


def help_them_out():
    return """
    Beep boop. I'm a bot and I'm here to make it just a little easier to learn about Fall classes you can take. 
    Here's are some example commands my creator (@nstornetta) has taught me so far:
    `@booth_bot help` -- Gives basic instructions on my commands
    `@booth_bot course Financial Accounting` -- Give basic info on the top-rated sections of Financial Accounting \
    offered this term
    `@booth_bot course_num 30000` -- Give basic info on top-rated sections of course 30000 this term
    `@booth_bot instructor Kleymenova` -- Give basic info on the courses taught by Professor Kleymenova this term
    `@booth_bot mark_interest 30000-01` -- Record yourself as being interested in enrolling in section 01 of course 30000
    `@booth_bot remove_interest 30000-01` -- Remove yourself from being recorded as interested in enrolling in section 01 of course 30000
    `@booth_bot see_interested 30000-01` -- See the number of people who have marked themselves as interested in enrolling in section 01 of course 30000 
    """


def results_strings_list(query_result):
    """
    Given a set of query results, convert it to a a list of formatted strings to be shown to user.
    """
    return ["""*{title} {section}. Taught by {instructor} on {time} at {location}.* \n\tRecommend rating: {recommend}.\n\tHours per week: {hours}. \n\tInteresting rating: {interesting}.
            """.format(title=x[0].title(),
                       section=x[1],
                       instructor=x[2].title(),
                       time=x[3],
                       location=x[4],
                       hours=x[5],
                       interesting=x[6],
                       recommend=x[7]) for x in query_result
            ]


def get_num_interested(section_num, cursor):
    interested_array = list(cursor.execute(queries.get_interest(section_num=section_num)))
    return """There are {num_interested} students who have registered their interest in {section_num}"""\
        .format(num_interested=str(len(interested_array)), section_num=section_num)


def update_interest(section_num, query_type, cursor, user):
    """
    Let somebody register or de-register their interest in a specific class.
    Note that this is a really terrible way to do this by pickling data in and out of sqlite, but for the moment we're
    going with hacky and done is better than refactoring with sqlalchemy.
    """

    interested_array = list(cursor.execute(queries.get_interest(section_num=section_num)))[0][0].split()

    if query_type == "mark_interest" and user in interested_array:
        return """You've already marked your interest. If you'd like to remove yourself as interested, try:\
        \n`@booth_bot remove_interest {section_num}`""".format(section_num=section_num)

    elif query_type == "mark_interest" and user not in interested_array:
        interested_array.append(user)
        query = queries.update_interested(section_num=section_num, interested_array=','.join(interested_array))
        cursor.execute(query)

        return """You've been added to the list of students who are interested in {section_num}.\
        \nThere are currently {num_interested} students who have registered their interest in that section."""\
            .format(section_num=section_num, num_interested=str(len(interested_array)))

    elif query_type == "remove_interest" and user not in interested_array:
        return """You hadn't previously marked your interest. If you'd like to add yourself as interested, try:\
        \n`@booth_bot mark_interest {section_num}`""".format(section_num=section_num)

    elif query_type == "remove_interest" and user in interested_array:
        interested_array.remove(user)
        query = queries.update_interested(section_num=section_num, interested_array=','.join(interested_array))
        cursor.execute(query)

        return """You've been removed from the list of students who are interested in {section_num}.\
        \nThere are currently {num_interested} students who have registered their interest in that section."""\
            .format(section_num=section_num, num_interested=str(len(interested_array)))

    else:
        raise ValueError
