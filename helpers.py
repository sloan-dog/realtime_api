import re
import datetime

def match_commands(string):
    regex = r"^\/" \
            r"(?:(send(?=\s\/(?:(set|get)(?=\s([\w]+):([\w.\s,!?]+)$))))" \
            r"|(connect(?=$))" \
            r"|(say(?=\s([\w.\-!_?\s]+)))" \
            r"|(connections(?=$))" \
            r"|(disconnect(?=$)))"

    return re.findall(regex, string, re.X)

def get_cur_srv_time_ms():
    t = datetime.datetime.now()
    ms = t.microsecond/1000
    ms_time = int(t.strftime("%s"))*1000 + ms
    return ms_time

def time_dif_from_val_to_now(ms_time):
    cur = get_cur_srv_time_ms()
    dif = cur - ms_time
    return dif

def format_ms_to_hmsf(ms_time):
    s, f = divmod(ms_time, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d.%03d" % (h, m, s, f)

def get_cur_srv_time():
    return datetime.datetime.now().strftime("%H%M%S%f")[:-3]