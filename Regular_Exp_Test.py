import re
from pprint import pprint

# txt = 'INMPR-FC-ON      24'
#
# x = txt.replace('    ', ':')
#
# print (x)


##### Learning from Edureka

# nameage = '''Jaince is 22 and Theon is 33
# Gabriel is 44 and Joey is 21'''
#
# ages = re.findall(r'\d{1,3}',nameage) # This will find number starting from Position 1 and ending in position 2 but not 3
#
# print (ages) # Output looks like ['22', '33', '44', '21']
#
# names = re.findall(r'[A-Z][a-z]*', nameage) # This Will find all the Letter starting with Capital Letter and ending with small letter
#
# print (names) # output looks like ['Jaince', 'Theon', 'Gabriel', 'Joey']
#
# agedict= {}
#
# x = 0
# for eachname in names:
#     agedict[eachname] = ages[x]
#     x+=1
# print (agedict) # Output looks like {'Jaince': '22', 'Theon': '33', 'Gabriel': '44', 'Joey': '21'}

#example 2


ipfun = 'My ip is 192.168.23.22 and wifi ip is 192.168.222.222'



funny = re.findall ('\d{1,4}', ipfun)

print (funny)


# Example 3

str = 'sat, hat, rat, pat. mat'

allstr = re.findall('[shrpm]at', str) # this will match at with each letter in []

print (allstr) # output is ['sat', 'hat', 'rat', 'pat', 'mat']
# for i in allstr:
#     print (allstr)

# for i in range (len(x)):
#
#     if x[i ]
# ipam = 'INMPR'
#
# you = f"{ipam}" + '-FC'
#
# # print (you)
# x = re.findall(you, txt)
#
# if ipam in txt:
#     spell = re.split('/s', txt)
#     print (spell)
# i = {x : }
# print(x)
