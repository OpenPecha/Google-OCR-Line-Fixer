from pathlib import Path
from bs4 import BeautifulSoup
from statistics import mean
from collections import defaultdict


def read_xml(xml):
    """
    The function returns xml content of transkribus output.
    
    Args:
        xml(.xml file): It is the output of Transkribus OCR model which contains the coordinates and text of
                        recognized box.
    Return:
        xml_content (String):It is the content of .xml file
    
    """
    with open(xml) as f:
        xml_content = f.read()
    return xml_content


def get_coord(point):
    """
    This function returns coordinate of a point.
    
    Args:
        point (String): It contain coordinate of a point. Eg : '233,55'
    Return:
        coord (list): It contains x and y coordinate of a point as element of a list for easy access. Eg: [233,55]
    """
    coord = point.split(",")
    return coord


def get_line_indicator(coords):
    """
    This function return y axis coordinate of 
    """
    ys = []
    for coord in coords:
        point = get_coord(coord)
        ys.append(int(point[1]))
    y_mean = mean(ys)
    mid = int(len(coords) / 2)
    if y_mean % 70 > 35:
        result = (y_mean // 70 + 1) * 70
    else:
        result = (y_mean // 70) * 70
    return result


def get_text(region):
    result = ""
    lines = region.find_all("TextEquiv", recursive=False)
    for line in lines:
        if line.Unicode.string:
            result = line.Unicode.string
        else:
            result = ""
    return result


def get_main_region(regions):
    """
    This function traverse all the regions recognised by the segmentor and find the largest region by finding
    the region where maximum textLine is found. It return the index of that region.
    """
    len_lines = []
    for region in regions:
        region_text = get_text(region)
        len_lines.append(len(region_text))
    try:
        main_region_index = len_lines.index(max(len_lines))
    except:
        main_region_index = 0
    return main_region_index


def create_box(xml):
    """
    This function parse the xml file contain. It creates dictionary call boxes which contains text, staring x 
    coordinate of baseline and average y coordinate of baseline.
    
    Args:
        xml (String): Contains the Transkribus output.
    
    Returns:
        boxes (dict): Contains text, staring x coordinate of baseline and average y coordinate of baseline.
    """
    boxes = {}
    soup = BeautifulSoup(xml, "xml")
    regions = soup.find_all("TextRegion")
    if regions:
        main_region = get_main_region(regions)
        lines = regions[main_region].find_all("TextLine")
    else:
        return boxes
    for i, line in enumerate(lines):
        boxes[f"box{i}"] = {}
        baseline_coords = line.Baseline[
            "points"
        ].split()  # Extracting all coordinates of baseline points
        start_base_point = get_coord(
            baseline_coords[0]
        )  # Getting x coordinate of staring point of baseline point
        line_indicator = get_line_indicator(baseline_coords)
        print(line_indicator)
        if line.TextEquiv:
            text = line.TextEquiv.Unicode.string
        else:
            text = None
        boxes[f"box{i}"]["bl_start_x"] = int(start_base_point[0])
        boxes[f"box{i}"]["text"] = text
        boxes[f"box{i}"]["line_indicator"] = int(line_indicator)
    return boxes


def vertical_sort(boxes):
    result = sorted(boxes.items(), key=lambda x: x[1]["line_indicator"])
    return dict(result)


def horizontal_sort(boxes):
    res = defaultdict(list)
    sorted_box = {}
    for key, box in boxes.items():
        res[box["line_indicator"]].append(key)
    res = dict(res)
    for key, re in res.items():
        sub_box = {key: boxes[key] for key in re}
        sorted_sub_box = dict(sorted(sub_box.items(), key=lambda x: x[1]["bl_start_x"]))
        sorted_box.update(sorted_sub_box)
    return sorted_box


def line_simplification(sub_box):
    line = ""
    for key, box in sub_box.items():
        if box["text"]:
            if len(box["text"]) > 5:
                line += box["text"]

    return line


def get_content(boxes):
    result = ""
    res = defaultdict(list)
    sorted_box = {}
    for key, box in boxes.items():
        res[box["line_indicator"]].append(key)
    res = dict(res)
    line_counter = 0
    for key, re in res.items():
        sub_box = {key: boxes[key] for key in re}
        # print(sub_box)
        line = line_simplification(sub_box)
        result += line + "\n"
    return result


def flow(pecha_id):
    content = f"{pecha_id}\n\n"
    input_path = Path(f"./transkribus_output/{pecha_id}/page")
    output_path = Path(f"./transcript/{pecha_id}.txt")
    input_pages = list(input_path.iterdir())
    input_pages.sort()
    for i, input_page in enumerate(input_pages):
        print(input_page)
        content += f"Page no:{input_page.stem}\n"
        xml = read_xml(input_page)
        boxes = create_box(xml)
        vertical_sorted = vertical_sort(boxes)
        sorted_boxes = horizontal_sort(vertical_sorted)
        content += get_content(sorted_boxes) + "\n"
    with open(output_path, "w+") as f:
        f.write(content)
    print("Output Ready")


if __name__ == "__main__":
    pecha_id_body = "PI2KG210"
    for i in range(407, 423):
        pecha_id = pecha_id_body + str(i)
        flow(pecha_id)
        print(f"{pecha_id} ..Completed")
