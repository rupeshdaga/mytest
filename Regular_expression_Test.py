import re


my_data = 'ip domain name mdlz.net'

fun = re.compile(r'\s+\\.net', my_data)

print (fun)