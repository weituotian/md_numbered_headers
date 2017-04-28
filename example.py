import sublime
import sublime_plugin
import re
import pprint
import os.path


pattern_h1_h2_equal_dash = "^.*?(?:(?:\r\n)|\n|\r)(?:-+|=+)$"

pp = pprint.PrettyPrinter(indent=4)


def is_out_of_areas(num, areas):
    for area in areas:
        if area[0] < num and num < area[1]:
            return False
    return True

# 计算相对深度，比如md中只有三号，四号，五号标题，那么三号标题就是第一，四号就是第二。五号就是第三等等。


def format(items):
    headings = []
    for item in items:
        headings.append(item[0])
    # --------------------------

    # minimize diff between headings -----
    _depths = list(set(headings))  # sort and unique

    # print(_depths)
    # replace with depth rank
    for i, item in enumerate(headings):
        headings[i] = _depths.index(headings[i]) + 1
    # ----- /minimize diff between headings

    # print(headings)
    # --------------------------
    for i, item in enumerate(items):
        item.append(headings[i])
    return items

# 注册命令


class MarkdownAddNumberedNums(sublime_plugin.TextCommand):

    def run(self, edit):
        sels = self.view.sel()
        self.log('run insert/update---------------------')
        for sel in sels:

            items = self.get_toc(sel.end(), edit)
            self.update_herader_num(items)
            self.do_update_header_num(items, edit)
        # self.view.insert(edit, 0, "Hello, World!")
        # for region in reversed(self.view.find_all("<")):
        #     if not region.empty():
        #         self.view.replace(edit, region, "<")
        #         for region in reversed(self.view.find_all(">")):
        #             if not region.empty():
        #                 self.view.replace(edit, region, ">")
        self.log('end run--------------------')

    def remove(self, edit):
        sels = self.view.sel()
        self.log('run remove')
        for sel in sels:
            items = self.get_toc(sel.end(), edit)
            self.do_remove(items, edit)
        self.log('end run')

    def get_toc(self, begin, edit):

        # Search headings in docment
        pattern_hash = "^#+?[^#]"
        headings = self.view.find_all(
            "%s|%s" % (pattern_h1_h2_equal_dash, pattern_hash))

        headings = self.remove_items_in_codeblock(headings)

        if len(headings) < 1:
            return ''

        # self.log('headings:')
        # self.log(headings)

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

        # Shape TOC  ------------------
        items = format(items)

        self.log(items)

        # 深度限制   ------------------
        _depth = int(self.get_setting('depth'))
        if 0 < _depth:
            items = list(filter((lambda i: i[0] <= _depth), items))

        return items

    def update_herader_num(self, items):

        # h1 = 0  # 标题1编号
        # h2 = 0  # 标题2编号
        # h3 = 0
        # h4 = 0
        # h5 = 0
        # h6 = 0

        attrs = self.get_settings()
        dot = self.get_setting('dottype')

        levels = [attrs['h1'], attrs['h2'], attrs['h3'], attrs[
            'h4'], attrs['h5'], attrs['h6']]  # 各个标题等级的初始标号

        for item in items:

            # item 大概是 [3, '啊啊21', 55, 1]
            level = item[3]

            # level 从1到6
            levels[level - 1] += 1  # 当前这一级的序号+1
            if level < len(levels):
                levels[level] = attrs['h' + str(level)]  # 下一级的序号重新开始

            # 循环
            new_num = str(levels[0])

            for i in range(1, level):
                if levels[i] > 0:
                    new_num += dot + str(levels[i])

            item.append(new_num)  # 保存进入item

            # print(new_num)
            self.log(item)

            # if level == 1:
            #   h1 += 1
            #   h2 = 0
            # elif level == 2:
            #   h2 += 1
            #   h3 = 0
            # elif level == 3:
            #   h3 += 1
            #   h4 = 0
            # elif level == 4:
            #   h4 += 1
            #   h5 = 0
            # elif level == 5:
            #   h5 += 1
            #   h6 = 0
            # elif level == 6:
            #   h6 += 1

            # print(anchor_region) 这一行的开始和结束位置，如 (55, 63)
            # print(v.substr(anchor_region)) 这一行的字符串，如 ### 啊啊

    def do_update_header_num(self, items, edit):

        v = self.view
        dot = self.get_setting('dottype')

        pattern_header_num = re.compile(
            r'(#+)\s+((?:\d' + dot + ')*\d)(.*)')  # 判断是否符合 '# 1-2-3-4 之类的'
        pattern_header_num_replace = re.compile(
            r'(\d' + dot + ')*\d')  # 进行替换的reg

        for item in reversed(items):

            level = item[0]
            title = item[1]
            start_pos = item[2]
            relative_level = item[3]
            header_num = item[4]

            anchor_region = v.line(start_pos)  # 找到标题的这一行
            line_str = v.substr(anchor_region)
            match = pattern_header_num.match(line_str)

            if match:

                # 更新
                self.log('update')
                # self.log(match.groups())

                new_line_str = pattern_header_num_replace.sub(
                    header_num, line_str)

                print(new_line_str)
                v.replace(edit, anchor_region, new_line_str)
            else:

                # 插入
                self.log('insert')
                new_line_str = "#" * level + ' ' + header_num
                new_line_str += ' ' + title.strip()

                v.replace(edit, anchor_region, new_line_str)

    def do_remove(self, items, edit):

        v = self.view

        dot = self.get_setting('dottype')

        print(dot)

        pattern_header_num = re.compile(
            r'(#+)\s+((?:\d' + dot + ')*\d)(.*)')  # 判断是否符合 '# 1-2-3-4 之类的'

        for item in reversed(items):
            level = item[0]
            title = item[1]
            start_pos = item[2]

            anchor_region = v.line(start_pos)  # 找到标题的这一行
            line_str = v.substr(anchor_region)
            match = pattern_header_num.match(line_str)

            if match:
                print('remove one')

                # print(match.groups());
                # 匹配到match groups大概是('###', '1.3.2', ' 啊啊sss')
                # group下标从1开始

                new_line_str = "#" * level + ' ' + match.group(3).strip()
                v.replace(edit, anchor_region, new_line_str)

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
        if self.get_setting('logging'):
            arg = str(arg)
            sublime.status_message(arg)
            pp.pprint(arg)

    def get_setting(self, attr):
        settings = sublime.load_settings(
            'MarkdownNumberedHeaders.sublime-settings')
        return settings.get(attr)

    def get_settings(self):
        """return dict of settings"""
        return {
            "h1":           self.get_setting('h1'),
            "h2":             self.get_setting('h2'),
            "h3":              self.get_setting('h3'),
            "h4":                self.get_setting('h4'),
            "h5":               self.get_setting('h5'),
            "h6": self.get_setting('h6'),
            "depth": self.get_setting('depth')
        }


# 注册命令
class MarkdownRemoveNumberedNums(MarkdownAddNumberedNums):

    def run(self, edit):
        MarkdownAddNumberedNums.remove(self, edit)
