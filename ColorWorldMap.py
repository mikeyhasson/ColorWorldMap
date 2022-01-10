# coding: utf-8
import math
import random
import re
import sys
from urllib.request import urlopen

import matplotlib.colors as mcolors
import svgwrite
from qwikidata.sparql import return_sparql_query_results
from svgpathtools.paths2svg import big_bounding_box
from svgpathtools.svg_to_paths import svg2paths

MAP_FILENAME = "https://upload.wikimedia.org/wikipedia/commons/4/4d/BlankMap-World.svg"
MAP_FILENAME = "https://upload.wikimedia.org/wikipedia/commons/4/4d/BlankMap-World.svg"
API_ENDPOINT = "https://www.wikidata.org/w/api.php"
BBOX_PRECENT = 0.15 / 2
MARK_RATIO = 25
X_BOUND = 2754
Y_BOUND = 1398


def create_index(lines):
    flag_pre = True
    cur_id = ""
    d = {}
    matcher_id = re.compile(r'id=\"([a-z][a-z])\"')
    matcher_title = re.compile(r'<title>(.+)</title>')

    for line in lines:
        if flag_pre:
            temp = matcher_id.search(line)
            if temp:
                flag_pre = False
                cur_id = temp.group(1)
            else:
                continue

        if cur_id:
            temp = matcher_title.search(line)
            if temp:
                d[temp.group(1)] = cur_id
                cur_id = None
        else:
            cur_id = matcher_id.search(line)
            if cur_id:
                cur_id = cur_id.group(1)
    return d


def get_from_dict(d, title):
    if title not in d:
        print(F"Error: {title} is not in the index of supported countries")
        print("See supported countries below by using python ColorWorldMap.svg index")
        exit(1)

    return d[title]


def create_file(lst, lines):
    css_index = None

    for i in range(len(lines)):
        if "</style>" in lines[i]:
            css_index = i
            break

    for val in lst:
        country_id, color = val
        color_str = F".{country_id} {{opacity:1; fill:{color};}}\n"
        lines.insert(css_index, color_str)

    return lines


def translate_country(country, lang):

    country = country.strip()
    query_country = F"""SELECT ?res
    {{
      ?item wdt:P297 ?value .
      ?item rdfs:label ?itemLabel .
      FILTER(LANG(?itemLabel) = "{lang}") .
      FILTER(regex(?itemLabel, '{country}') ).
      BIND (LCASE( ?value ) as ?res).
    }}"""

    query_disputed = F"""SELECT ?res
    {{
      ?item wdt:P31 wd:Q15239622 .
      ?item rdfs:label ?itemLabelhe .
      FILTER(LANG(?itemLabelhe) = "{lang}") .
      FILTER(regex(?itemLabelhe, '{country}') ).
      ?item rdfs:label ?itemLabelen .
      FILTER(LANG(?itemLabelen) = "en") .
      BIND (CONCAT ("x",LCASE(SUBSTR(?itemLabelen, 1, 1))) as ?res).
    }}"""
    queries = [query_country, query_disputed]
    for query in queries:
        res = return_sparql_query_results(query)
        if len(res["results"]["bindings"]) != 0:
            return res["results"]["bindings"][0]["res"]["value"]

    print(F"Error: Couldn't translate {country} from the Wikidata database")
    exit(1)
    return


def translate_countries(lst, lang):
    for i in range(len(lst)):
        lst[i][0] = translate_country(lst[i][0], lang)


def get_color(x, multiple=False):
    color_picks = list(mcolors.TABLEAU_COLORS.keys())
    random.shuffle(color_picks)

    if not multiple:
        x = [x]

    for val in x:
        if len(val) == 1:
            cur_key = color_picks.pop()
            val.append(mcolors.TABLEAU_COLORS[cur_key])


def create_coloring_lst(color_format, lst, lines):
    d = create_index(lines)

    if '-' in color_format:
        color_format, lang = color_format.split("-")
        translate_countries(lst, lang)
    else:
        for i in range(len(lst)):
            lst[i][0] = get_from_dict(d, lst[i][0])

    if color_format == "all":
        get_color(lst[0])
        first_color = lst[0][1]
        lst = [[x[0], first_color] for x in lst]
    elif color_format == "":
        get_color(lst, multiple=True)
    elif not color_format == "bilateral":
        print(f"Unsupported format: {color_format}")
        exit(1)

    return lst


def add_relevent_paths_to_svg(ids, out_filename, lines):
    new_svg = []
    matcher_id = re.compile(r'id=\"([a-z][a-z])\"')

    for i in range(len(lines)):
        new_svg.append(lines[i])
        if "</style>" in lines[i]:
            css_index = i
            break

    i = css_index + 1
    while i != len(lines):
        matches = matcher_id.search(lines[i])
        if matches and matches.group(1) in ids:
            new_svg.append(lines[i])
            if "g id=" in lines[i]:
                balance = 1
                i += 1
                while balance != 0:
                    new_svg.append(lines[i])
                    if "g id=" in lines[i]:
                        balance += 1
                    elif "</g>" in lines[i]:
                        balance -= 1
                    i += 1
                i -= 1
            else:
                while "</path>" not in lines[i]:
                    i += 1
                    new_svg.append(lines[i])
        i += 1

    new_svg.append(lines[-1])
    f = open(out_filename, 'w')
    f.writelines(new_svg)
    f.close()


def check_bbox_bounds(xmin, xmax, ymin, ymax):
    xmin = xmin if xmin > 0 else 0
    ymin = ymin if ymin > 0 else 0
    xmax = xmax if xmax < X_BOUND else X_BOUND
    ymax = ymax if ymax < Y_BOUND else Y_BOUND
    ratio = (ymax - ymin) / (xmax - xmin)  # height/width
    return xmin, xmax, ymin, ymax, ratio


def get_bbox(ids, out_filename, lines):
    add_relevent_paths_to_svg(ids, out_filename, lines)
    paths_lst = svg2paths(out_filename)[0]

    o_xmin, o_xmax, o_ymin, o_ymax = big_bounding_box(paths_lst)
    xmin = o_xmin - BBOX_PRECENT * (o_xmax - o_xmin)
    xmax = o_xmax + BBOX_PRECENT * (o_xmax - o_xmin)
    ymin = o_ymin - BBOX_PRECENT * (o_ymax - o_ymin)
    ymax = o_ymax + BBOX_PRECENT * (o_ymax - o_ymin)

    xmin, xmax, ymin, ymax, ratio = check_bbox_bounds(xmin, xmax, ymin, ymax)
    while not 0.3 <= ratio <= 1.2:
        if ratio < 1:  # width is longer
            height = ymax - ymin
            xmin = (xmin + o_xmin) / 2
            xmax = (xmax + o_xmax) / 2
            ymin -= BBOX_PRECENT / 2 * height
            ymax += BBOX_PRECENT / 2 * height
        else:
            width = xmax - xmin
            ymin = (ymin + o_ymin) / 2
            ymax = (ymax + o_ymax) / 2
            xmin -= BBOX_PRECENT / 2 * width
            xmax += BBOX_PRECENT / 2 * width
        xmin, xmax, ymin, ymax, ratio = check_bbox_bounds(xmin, xmax, ymin, ymax)

    return [xmin, xmax, ymin, ymax]


def add_bbox_to_file(out_filename, bbox, lines):
    xmin, xmax, ymin, ymax = bbox
    height = ymax - ymin
    width = xmax - xmin
    viewbox = (" ".join([str(x) for x in [xmin, ymin, width, height]]))
    dwg = svgwrite.Drawing(filename=out_filename, size=(width, height), viewBox=viewbox)
    clip_path = dwg.defs.add(dwg.clipPath(id='clipsq'))
    clip_path.add(dwg.rect((xmin, ymin), (width, height)))
    dwg.save(pretty=True)
    f = open(out_filename, 'r')
    clip_lines = f.readlines()
    f.close()

    clip_idx = [-1, -1]
    for i in range(len(clip_lines)):
        if clip_idx[0] == -1 and "<defs>" in clip_lines[i]:
            clip_idx[0] = i
        if clip_idx[1] == -1 and "</defs>" in clip_lines[i]:
            clip_idx[1] = i
    i = 0
    while "<title>" not in lines[i]:
        i += 1

    return clip_lines[:-1] + lines[i:]


def calc_radius(o_xmin, o_xmax, o_ymin, o_ymax, cx, cy):
    big_area = ((o_xmax - o_xmin) * (o_ymax - o_ymin))
    r = math.sqrt(big_area / (MARK_RATIO * math.pi))
    r_bounds_min = min([-1 * x if x < 0 else x for x in [o_xmax - cx, o_xmin - cx, o_ymax - cy, o_ymin - cy]])
    return min(r_bounds_min, r)


def mark_small_contries(color_lst, out_filename, bbox, svg_lines):
    flag = False
    for id, color in color_lst:
        add_relevent_paths_to_svg([id], out_filename, lines)
        paths_lst = svg2paths(out_filename)[0]
        xmin, xmax, ymin, ymax = big_bounding_box(paths_lst)
        o_xmin, o_xmax, o_ymin, o_ymax = bbox
        ratio = ((o_xmax - o_xmin) * (o_ymax - o_ymin)) / ((xmax - xmin) * (ymax - ymin))
        if ratio > 300:
            flag = True
            cx = (xmax + xmin) / 2
            cy = (ymax + ymin) / 2
            radius = calc_radius(o_xmin, o_xmax, o_ymin, o_ymax, cx, cy)
            circle_style = F"style=\"fill:{color};stroke:{color};\""
            circle_str = F"<circle class=\"markxx\" id=\"mark_{id}\" r = \"{radius}\" cy = \"{cy}\" cx = \"{cx}\"\n{circle_style}/>\n"
            svg_lines.insert(len(svg_lines) - 1, circle_str)

    if flag:
        css_index = None
        for i in range(len(svg_lines)):
            if "</style>" in svg_lines[i]:
                css_index = i
                break
            mark_class = "\n".join([".markxx",
                                    "{",
                                    "opacity: 1;",
                                    "fill-opacity:0.240469;",
                                    "stroke-width:5.85442",
                                    "stroke-opacity:1",
                                    "}\n"])

        svg_lines.insert(css_index, mark_class)

    f = open(out_filename, 'w')
    f.writelines(svg_lines)
    f.close()


if __name__ == "__main__":
    args = sys.argv
    lines = urlopen(MAP_FILENAME).read().decode('utf-8').splitlines(True)
    color_format = args[1]

    if color_format == "index":
        d = create_index(lines)
        print(d)
        exit(0)

    out_filename = args[2]

    if len(args) == 3 and "bilateral" in color_format:  # format is: bilateral country1-country2
        countries = out_filename.split("-")
        out_filename+= " locator"
        lst = [[x, y] for x, y in zip(countries, ["#008000", "#e3801c"])]
    elif 3 <= len(args) <= 4:
        if color_format[0]=='-':
            args.remove(color_format)
        if len(args) == 3 or (len(args)==4 and color_format[0]=='-'):  # format is: filename instructions_file
            color_format = "" if color_format is None else color_format
            out_filename = args[1]
            instructions_filename = args[2]
        else:  # format is: format filename instructions_file
            instructions_filename = sys.argv[3]

        f = open(instructions_filename)
        lst = [line.split(",") for line in f.readlines()]
        f.close()
    else:
        print("Argument format is wrong. See docs.")
        exit(1)

    color_lst = create_coloring_lst(color_format, lst, lines)
    out_filename += ".svg"
    countries_ids = [x[0] for x in color_lst]
    bbox = get_bbox(countries_ids, out_filename, lines)
    svg_lines = create_file(color_lst, lines)
    if "bilateral" in color_format:
        svg_lines = add_bbox_to_file(out_filename, bbox, svg_lines)
        mark_small_contries(color_lst, out_filename, bbox, svg_lines)
    else:
        f = open(out_filename, 'w')
        f.writelines(svg_lines)
        f.close()
