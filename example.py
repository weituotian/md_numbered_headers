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


class ExampleCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        sels = self.view.sel()

        for sel in sels:

            self.get_toc(sel.end(), edit)

            self.log('run')

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
        
    def remove_items_in_codeblock(self, items):

        codeblocks = self.view.find_all("^`{3,}[^`]*$")
        codeblockAreas = [] # [[area_begin, area_end], ..]
        i = 0
        while i < len(codeblocks)-1:
            area_begin = codeblocks[i].begin()
            area_end   = codeblocks[i+1].begin()
            if area_begin and area_end:
                codeblockAreas.append([area_begin, area_end])
            i += 2

        items = [h for h in items if is_out_of_areas(h.begin(), codeblockAreas)]
        return items

    def log(self, arg):
        arg = str(arg)
        sublime.status_message(arg)
        pp.pprint(arg)
