import difflib
import sqlite3
import itertools

import queries
import pyjokes

DATABASE_LOCATION = "/Users/nstornetta/Boothbot scraping/bot_commands/booth_classes.db"


def respond_to_command(command):
    command_list = [word.lower() for word in command.split()]
    if command_list[0] in ("help", "h", "?"):
        return help_them_out()
    elif "joke" in command_list:
        return tell_joke()
    elif "who are you" in command.lower():
        return "Beep boop. I'm booth_bot! My objective is to help you find classes and bring them up for easy \
        discussion here in Slack. At least until the Singularity... :wink:"
    else:
        return run_query_command(query_type=command_list[0], command_list=command_list)


def tell_joke():
    return """Well, I wasn't programmed for that, but here goes:\n""" + pyjokes.get_joke()


def help_them_out():
    return """
    Beep boop. I'm a bot and I'm here to 
    Here's are some example commands my creator (@nstornetta) has taught me so far:
    `@booth_bot help` -- Gives basic instructions on my commands
    `@booth_bot course Financial Accounting` -- Give basic info on the top-rated sections of Financial Accounting \
    offered this term
    `@booth_bot course_num 30000` -- Give basic info on top-rated sections of course 30000 this term
    `@booth_bot instructor Kleymenova` -- Give basic info on the courses taught by Professor Kleymenova this term
    """


def results_strings_list(query_result):
    """
    Given a set of query results, convert it to a a list of formatted strings using those results.
    """
    return ["""*{title} {section}. Taught by {instructor} on {time} at {location}.* \n\tRecommend rating: {recommend}. 
            \n\tHours per week: {hours}. \n\tInteresting rating: {interesting}.
            """.format(title=query_result[0].title(), section=query_result[1], instructor=query_result[2].title(),
                       time=query_result[3], location=query_result[4], hours=query_result[5],
                       interesting=query_result[6], recommend=x[7]) for x in query_result
            ]


def run_query_command(query_type, command_list):
    args_dict = {"course": ' '.join(command_list[1:]),
                 "course_num": command_list[1],
                 "instructor": ' '.join(command_list[1:])
                }
    
    colname_dict = {"course": "title",
                    "course_num": "course",
                    "instructor": "instructor"
                   }
    
    conn = sqlite3.connect(DATABASE_LOCATION)
    
    try:
        if query_type == "instructor":
            query = queries.instructor_last_name(instructor_val=args_dict[query_type])
        else:
            query = queries.by_colname_exact(colname=colname_dict[query_type], colname_val=args_dict[query_type])
        result = list(conn.execute(query))
        assert len(result) > 0
        
        result_strings = results_strings_list(query_result=result)
        
        return """Here's what I found:\n{results}""".format(results='\n'.join(result_strings))

    except AssertionError:  # If no results returned when using exact match
        query = queries.by_colname_distinct(colname=colname_dict[query_type])
        result = list(itertools.chain(*list(conn.execute(query))))
        if len(result) != 0:
            close_matches = difflib.get_close_matches(args_dict[query_type], result)
        
            return """I couldn't find anything matching that exact description. Perhaps you meant {this_or_these}
            \t{close_matches}\nIf you ask me again with one of ^^^ those, I should be able to find some better results for you.
            """.format(this_or_these='one of these' if len(result) > 1 else 'this',
                       close_matches='\n\t'.join(close_matches))
        else:
            query = queries.by_colname_like(colname=colname_dict[query_type], colname_val=args_dict[query_type])
            result = list(conn.execute(query))
            if len(result) == 0:
                return """I tried my hardest, but I couldn't seem to find what you were looking for.
                Have you tried using the `@booth_both help` command to see what I can do?"""
            else:
                result_strings = results_strings_list(query_result=result)
                return """I'm not quite sure this is what you're looking for, but here's what I found:
                {results}""".format(results='\n'.join(result_strings))