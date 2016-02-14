import re

def match_commands(string):
    regex = r"^\/(?P<send>send(?=\s" \
            r"\/(?P<action>set(?=\s(?P<key>[\w]+):(?P<value>[\w.\s,!?]+))" \
            r"|get(?=\s(?P<key2>[\w]+)$))))|(connect(?=$))|(say(?=\s([\w.\-!_?\s]+)))" \
            r"|(connections(?=$))"

    return re.findall(regex, string, re.X)