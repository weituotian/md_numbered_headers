# -*- coding:utf-8 -*-

import re

str_a = 'a'
# str_a += 1
print(str_a)

pattern_header_num = re.compile(
    r'(#+)\s+((?:\d\.)+\d)(.*)')  # 判断是否符合 '# 1.2.3.4 之类的'
pattern_header_num_replace = re.compile(r'(\d\.)*\d')  # 进行替换的reg

the_str = '## 1 reference(参考)'
the_str_insert = '# asd'

match = pattern_header_num.match(the_str)
if match:
    print(match.groups())

newstr = pattern_header_num_replace.sub('ggggg', the_str)
print(newstr)

print("other test:")
text = 'pythontab'
m = re.match(r"(.*)", text)
if m:
    print(m.groups())
else:
    print('not match')

items = [1, 2, 3, 4, 5]
items2 = [h + 1 for h in items if h > 3]
print(items2)

reg = '^.*?(?:(?:\r\n)|\n|\r)(?:-+|=+)$' if 5 < 3 else 'asd'
print(reg)

dotTest = 'asd.dsdd.d'
pattern_dot = re.compile("d\\.d")
findall = pattern_dot.findall(dotTest)
print(findall)
