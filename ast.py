# -*- coding:utf-8 -*-

import sys
import re
import unicodedata
import os
import subprocess
import json

import clang.cindex
from clang.cindex import Index
from clang.cindex import Config


class pycolor:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    END = '\033[0m'
    BOLD = '\038[1m'
    UNDERLINE = '\033[4m'
    INVISIBLE = '\033[08m'
    REVERCE = '\033[07m'


from chardet.universaldetector import UniversalDetector
import codecs

getchar = ['', 0, 0]
json_data = ''
element = ''


def is_japanese(ch):
        # print(ch+':'+unicodedata.east_asian_width(ch))
    jc = 0
    if unicodedata.east_asian_width(ch) in 'FWA':
        jc = 2
    if ch == '｡':
        jc = 2
    return jc


def str_slice(string, start, end):
    global getchar
    for a in range(end-1):
        # print(a, end, string[a])
        if(a == end-1):
            break
        jc = is_japanese(string[a])
        end = end - jc
        getchar[2] += jc
        if(a >= start-1):
            getchar[0] += string[a]
        else:
            start = start - jc
            getchar[1] += jc
        # print(getchar[0])
    return getchar[0]

    # jc = is_japanese(string) * 2
    # getchar[1] = jc
    # print(len(string),start,end,jc)
    # for a in range(start-1, end-1-jc):
    #    try:
    #        getchar[0] += string[a]
    #    except IndexError:
    #        print('', end='')
    # return getchar[0]


def make_jsondata(name, data, startline, endline, startcolumn, endcolumn):
    global json_data
    json_data += '{\"type\":\"'+name+'\",\"start_line\":'+str(startline)+',\"end_line\":'+str(endline) \
        + ',\"start_column\":' + str(startcolumn) \
        + ',\"end_column\":' + str(endcolumn)+',\"data\":\"'+data+'\"}'


def indent(depth, young_child, empty_indent):
    #print(depth, young_child, empty_indent, end='')
    if depth > 0:
        for i in range(depth-1):
            if empty_indent[i] == 1:
                print('    ', end='')
            else:
                print('|   ', end='')
        if young_child == 1:
            print('`---', end='')
            if len(empty_indent) < depth:
                empty_indent.append(1)
            else:
                empty_indent[depth-1] = 1
        else:
            print('|---', end='')
            if len(empty_indent) < depth:
                empty_indent.append(0)
            else:
                empty_indent[depth-1] = 0
    return depth+1, empty_indent


def print_node_tree(node, filepath, depth, young_child, empty_indent):
    global line, getchar, element, json_data
    if str(node.location.file) == filepath:
        indent_data = indent(depth, young_child, empty_indent)
        depth = indent_data[0]
        empty_indent = indent_data[1]
        print('%s : (%s,%s)<=>(%s,%s)' % (node.kind.name, node.extent.start.line,
                                          node.extent.start.column, node.extent.end.line, node.extent.end.column), end='')
        if node.extent.start.line == node.extent.end.line:
            getchar = ['', 0, 0]
            element = str_slice(line[int(node.extent.start.line)-1],
                                int(node.extent.start.column), int(node.extent.end.column))
            print(element)
        else:
            element = ''
            print('')

        # or 'UNARY_OPERATOR' in node.kind.name:
        if 'BINARY_OPERATOR' in node.kind.name:
            make_jsondata(node.kind.name, element, node.extent.start.line, node.extent.end.line,
                          node.extent.start.column-getchar[1], node.extent.end.column-getchar[2])
    i = 0
    for child in node.get_children():
        i = i+1
        if i == len(list(node.get_children())):
            print_node_tree(child, filepath, depth, 1, empty_indent)
        else:
            print_node_tree(child, filepath, depth, 0, empty_indent)


def check_encoding(file_path):
    result = subprocess.check_output(['nkf', '-g', file_path])
    return result.decode(encoding='utf-8')


def json_name(filename):
    orig_name = filename.split('.')
    return orig_name[0]+'.json'


def count_depth(jsn):
    if 'child' in jsn:
        return 1 + max([0] + list(map(count_depth, jsn['child'])))
    else:
        return 1


def max_check(AST, max_char):
    j = 0
    for i in range(0, len(AST)):
        k = i-j
        if(max_char[AST[k]['start_line']-1][1] < AST[k]['end_column'] - AST[k]['start_column']):
            if(max_char[AST[k]['start_line']-1][1] > -1):
                AST.pop(max_char[AST[k]['start_line']-1][0])
                j = j+1
            max_char[AST[k]['start_line']-1][0] = k
            max_char[AST[k]['start_line']-1][1] = AST[k]['end_column'] - \
                AST[k]['start_column']
        else:
            AST.pop(k)
            j = j+1
        print(max_char)

    print(AST)
    return AST


def make_ast(filepath):
    global line
    depth = 0
    filename = filepath.split('/')[-1]
    if re.compile(r'.*\.c').search(filename):

        filedata = codecs.open(filepath, 'r', check_encoding(filepath))
        contents = filedata.read()
        line = re.split(r'\n', contents)

        print(pycolor.YELLOW + filename + pycolor.END + ':'+'start AST tree')
        index = Index.create()
        tree = index.parse(filepath)
        print_node_tree(tree.cursor, filepath, depth, 0, [])
    else:
        print(pycolor.YELLOW + filename + ' is not Clanguage!!' + pycolor.END)


if sys.argv[1] == 'dir':
    dir_list = os.listdir(sys.argv[2])
    print(dir_list)
    for filename in dir_list:
        filepath = sys.argv[2] + '/' + filename
        make_ast(filepath)
elif sys.argv[1] == 'file':
    filepath = sys.argv[2]
    make_ast(filepath)
else:
    print(pycolor.YELLOW + 'command line error' + pycolor.END)

'''
    jsonfile = open('./json/'+json_name(filename), 'w')
    json_data += '{"AST":['
    make_ast(filename)
    json_data += ']}'
    json_data = json_data.replace('}{', '},{')
    jsonfile.write(json_data)
    jsonfile.close()

    jsonfile = open('./json/'+json_name(filename), 'r')
    json_dict = json.load(jsonfile)
    max_char = [[-1]*2 for i in range(1, len(line))]
    print(max_char)

    json_dict['AST'] = max_check(json_dict['AST'], max_char)

    jsonfile = open('./json/2-'+json_name(filename), 'w')
    json.dump(json_dict, jsonfile, indent=4)
'''
