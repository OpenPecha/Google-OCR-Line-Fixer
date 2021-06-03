import gzip
import json

from pathlib import Path

def read_json(fn):
    with gzip.open(fn, "rb") as f:
        data = json.loads(f.read())
    return data

def get_y_avg(char):
    y1 = char['boundingPoly']['vertices'][0]['y']
    y2 = char['boundingPoly']['vertices'][2]['y']
    y_avg = (y1+y2)/2
    return y_avg

def get_avg_line_height(chars):
    height_sum = 0
    for char in chars:
        y1 = char['boundingPoly']['vertices'][0]['y']
        y2 = char['boundingPoly']['vertices'][2]['y']
        height_sum += y2-y1
    avg_height = height_sum/len(chars)
    return avg_height

def is_in_cur_line(prev_char, char, avg_height):
    if get_y_avg(char)- get_y_avg(prev_char) < 12.5:
        return True
    else:
        return False

def get_lines(chars):
    prev_char = chars[1]
    lines = []
    cur_line = ''
    avg_line_height = get_avg_line_height(chars)
    for char in chars:
        if is_in_cur_line(prev_char, char, avg_line_height):
            cur_line += char['description']
        else:
            lines.append(cur_line)
            cur_line = char['description']
        prev_char = char
    if cur_line:
        lines.append(cur_line)
    return lines

def get_page_content(page):
    chars = page['textAnnotations'][1:]
    lines = get_lines(chars)
    page_content = "\n".join(lines)
    return page_content

def get_vol_content(vol_path):
    vol_content = ''
    page_paths = list(vol_path.iterdir())
    page_paths.sort()
    for page_path in page_paths:
        page = read_json(page_path)
        if page:
            vol_content += f'{page_path.stem}\n{get_page_content(page)}\n\n'
    return vol_content

if __name__ == "__main__":
    vol_path = Path('./data/json/I2KG212285')
    vol_content = get_vol_content(vol_path)
    Path(f'./data/text/{vol_path.stem}.txt').write_text(vol_content, encoding='utf-8')