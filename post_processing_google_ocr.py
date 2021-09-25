import gzip
import json
import logging

from pathlib import Path
from antx import transfer

logging.basicConfig(filename="postprocessing_issue.log", level=logging.DEBUG, filemode="w")

def read_json(fn):
    with gzip.open(fn, "rb") as f:
        data = json.loads(f.read())
    return data

def get_bounding_poly_mid(bounding_poly):
    """Calculate middle of the bounding poly vertically using y coordinates of the bounding poly
​
    Args:
        bounding_poly (dict): bounding poly's details
​
    Returns:
        float: mid point's y coordinate of bounding poly
    """
    y1 = bounding_poly["boundingPoly"]["vertices"][0].get('y', 0)
    y2 = bounding_poly["boundingPoly"]["vertices"][2].get('y', 0)
    y_avg = (y1 + y2) / 2
    return y_avg

def get_avg_bounding_poly_height(bounding_polys):
    """Calculate the average height of bounding polys in page
​
    Args:
        bounding_polys (list): list of boundingpolys
​
    Returns:
        float: average height of bounding ploys
    """
    height_sum = 0
    for bounding_poly in bounding_polys:
        y1 = bounding_poly["boundingPoly"]["vertices"][0].get('y', 0)
        y2 = bounding_poly["boundingPoly"]["vertices"][2].get('y', 0)
        height_sum += y2 - y1
    avg_height = height_sum / len(bounding_polys)
    return avg_height

def is_in_cur_line(prev_bounding_poly, bounding_poly, avg_height):
    """Check if bounding poly is in same line as previous bounding poly
    a threshold to check the conditions set to 10 but it can varies for pecha to pecha
​
    Args:
        prev_bounding_poly (dict): previous bounding poly
        bounding_poly (dict): current bounding poly
        avg_height (float): average height of all the bounding polys in page
​
    Returns:
        boolean: true if bouding poly is in same line as previous bounding poly else false
    """
    threshold = 10
    if get_bounding_poly_mid(bounding_poly)- get_bounding_poly_mid(prev_bounding_poly)< avg_height/threshold:
        return True
    else:
        return False

def get_lines(bounding_polys):
    prev_bounding_poly = bounding_polys[0]
    lines = []
    cur_line = ''
    avg_line_height = get_avg_bounding_poly_height(bounding_polys)
    for bounding_poly in bounding_polys:
        if is_in_cur_line(prev_bounding_poly, bounding_poly, avg_line_height):
            cur_line += bounding_poly.get("description", "")
        else:
            lines.append(cur_line)
            cur_line = bounding_poly.get("description", "")
        prev_bounding_poly = bounding_poly
    if cur_line:
        lines.append(cur_line)
    return lines

def get_page_content(page):
    """parse page response to generate page content by reordering the bounding polys
​
    Args:
        page (dict): page content response given by google ocr engine
​
    Returns:
        str: page content
    """
    postprocessed_page_content =''
    try:
        page_content = page['textAnnotations'][0]['description']
    except:
        postprocessed_page_content += '---------\n'
        return postprocessed_page_content
    bounding_polys = page['textAnnotations'][1:]
    lines = get_lines(bounding_polys)
    page_content_without_space = "\n".join(lines)
    postprocessed_page_content = transfer_space(page_content, page_content_without_space)
    return postprocessed_page_content

def get_vol_content(vol_path):
    vol_content = ''
    page_paths = list(vol_path.iterdir())
    page_paths.sort()
    for pg_num, page_path in enumerate(page_paths,1):
        page = read_json(page_path)
        if page:
            vol_content += f'{get_page_content(page)}\n\n'
        logging.info(f'{page_path} completed..')
    return vol_content

def transfer_space(base_with_space, base_without_space):
    """transfer space from base with space to without space
​
    Args:
        base_with_space (str): base with space which is extracted from page['textAnnotations'][0]['description']
        base_without_space (str): base without space as it is generated using accumulating non space bounding_poly only
​
    Returns:
        [str]: page content
    """
    new_base = transfer(
        base_with_space,[
        ["space",r"( )"],
        ],
        base_without_space,
        output="txt",
    )
    return new_base

def process_pecha(pecha_path, output_path):
    vol_paths = list(Path(pecha_path).iterdir())
    vol_paths.sort()
    for vol_path in vol_paths:
        vol_content = get_vol_content(vol_path)
        (Path(output_path) / f'{vol_path.stem}.txt').write_text(vol_content, encoding='utf-8')
        print(f'{vol_path.stem} completed...')

if __name__ == "__main__":
    pecha_path = './data/json/P000009/'
    output_path = './data/text/P000009'
    process_pecha(pecha_path, output_path)