import sublime
import sublime_plugin
import re
import pprint
import os.path

pattern_header_num = re.compile(
    r'(#+)\s+((?:\d\.)+\d)(.*)')  # 判断是否符合 '# 1.2.3.4 之类的'
pattern_header_num_replace = re.compile(r'(\d\.)+\d')  # 进行替换的reg

pattern_h1_h2_equal_dash = "^.*?(?:(?:\r\n)|\n|\r)(?:-+|=+)$"

pp = pprint.PrettyPrinter(indent=4)


def is_out_of_areas(num, areas):
    for area in areas:
        if area[0] < num and num < area[1]:
            return False
    return True


class ExampleCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        sels = self.view.sel()
        self.log('run')
        for sel in sels:

            items = self.get_toc(sel.end(), edit)
            self.update_toc(items, edit)
        # self.view.insert(edit, 0, "Hello, World!")
        # for region in reversed(self.view.find_all("<")):
        #     if not region.empty():
        #         self.view.replace(edit, region, "<")
        #         for region in reversed(self.view.find_all(">")):
        #             if not region.empty():
        #                 self.view.replace(edit, region, ">")

    def get_toc(self, begin, edit):

        # Search headings in docment
        pattern_hash = "^#+?[^#]"
        headings = self.view.find_all(
            "%s|%s" % (pattern_h1_h2_equal_dash, pattern_hash))

        headings = self.remove_items_in_codeblock(headings)

        if len(headings) < 1:
            return ''

        self.log('headings:')
        self.log(headings)

        items = []  # [[headingNum,text,position,anchor_id],...]
        for heading in headings:
            if begin < heading.end():
                lines = self.view.lines(heading)
                if len(lines) == 1:
                    # handle hash headings, ### chapter 1
                    r = sublime.Region(
                        heading.end() - 1, self.view.line(heading).end())
                    text = self.view.substr(r).strip().rstrip('#')
                    indent = heading.size() - 1
                    items.append([indent, text, heading.begin()])
                elif len(lines) == 2:
                    # handle - or + headings, Title 1==== section1----
                    text = self.view.substr(lines[0])
                    if text.strip():
                        indent = 1 if (
                            self.view.substr(lines[1])[0] == '=') else 2
                        items.append([indent, text, heading.begin()])
        self.log(items)
        return items

    def update_toc(self, items, edit):
        v = self.view

        # h1 = 0  # 标题1编号
        # h2 = 0  # 标题2编号
        # h3 = 0
        # h4 = 0
        # h5 = 0
        # h6 = 0

        levels = [1, 0, 0, 0, 0, 0]  # 各个标题等级的开始

        for item in items:

            # item 大概是 [3, '啊啊21', 55]
            level = item[0]
            title = item[1]
            start_pos = item[2]

            # leverl 从1到6
            levels[level - 1] += 1  # 当前这一级的序号+1
            if level < len(levels):
                levels[level + 1] = 0  # 下一级的序号重新开始

            # 循环
            new_num = str(levels[0])

            for i in range(1, level):
                if levels[i] > 0:
                    new_num += '.' + str(levels[i])

            print(new_num)
            print(item)

            anchor_region = v.line(start_pos)  # 找到标题的这一行
            line_str = v.substr(anchor_region)
            match = pattern_header_num.match(line_str)


            if match:

                # 更新
                print('update')
                print(match.groups())
                new_line_str = pattern_header_num_replace.sub(
                    new_num, line_str)

                v.replace(edit, anchor_region, new_line_str)
            else:

                # 插入
                print('insert')
                new_line_str = "#" * level + ' ' + new_num + ' ' + title.strip()
                v.replace(edit, anchor_region, new_line_str)

            # if level == 1:
            # 	h1 += 1
            # 	h2 = 0
            # elif level == 2:
            # 	h2 += 1
            # 	h3 = 0
            # elif level == 3:
            # 	h3 += 1
            # 	h4 = 0
            # elif level == 4:
            # 	h4 += 1
            # 	h5 = 0
            # elif level == 5:
            # 	h5 += 1
            # 	h6 = 0
            # elif level == 6:
            # 	h6 += 1

            # print(anchor_region) 这一行的开始和结束位置，如 (55, 63)
            # print(v.substr(anchor_region)) 这一行的字符串，如 ### 啊啊

    def remove_items_in_codeblock(self, items):

        codeblocks = self.view.find_all("^`{3,}[^`]*$")
        codeblockAreas = []  # [[area_begin, area_end], ..]
        i = 0
        while i < len(codeblocks) - 1:
            area_begin = codeblocks[i].begin()
            area_end = codeblocks[i + 1].begin()
            if area_begin and area_end:
                codeblockAreas.append([area_begin, area_end])
            i += 2

        items = [h for h in items if is_out_of_areas(
            h.begin(), codeblockAreas)]
        return items

    def log(self, arg):
        arg = str(arg)
        sublime.status_message(arg)
        pp.pprint(arg)
