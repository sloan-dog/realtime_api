import re

def match_commands(string):
    regex = r"^\/(?P<send>send(?=\s\/(?P<action>set(?=\s(?P<key>[\w]+):(?P<value>[\w.\s,!?]+))|get(?=\s(?P<key2>[\w]+)$))))|(connect)"
    return re.findall(regex, string)