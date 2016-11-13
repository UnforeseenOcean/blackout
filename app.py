import os
import random
from statistics import mean
import string

import tracery
import spacy

import pyocr
import pyocr.builders
from PIL import Image, ImageDraw, ImageFilter

BOUND_PADDING = 50
BOX_PADDING = 50 # 10
WOBBLE_MAX = 2

nlp = spacy.load('en')

def draw_vertical_lines(draw, boxes, doc_bounding_box, line_width):
    line_weight_factor = random.choice([1, 0.02, 0.05, 0.07, 0.1, 0.2])
    current_x = doc_bounding_box[0] - line_width / 2
    color = (0, 0, 0)
    adjacent_line = False
    while current_x < doc_bounding_box[2]:
        start_x = current_x
        start_y = doc_bounding_box[1] - line_width / 2
        end_x = start_x
        end_y = doc_bounding_box[3] - line_width / 2

        bx0 = start_x
        bx1 = start_x + line_width

        select_boxes = []
        for box in boxes:
            wx0 = box.position[0][0] - BOUND_PADDING
            wx1 = box.position[1][0] + BOUND_PADDING
            if bx0 < wx0 and wx1 < bx1 or \
               wx0 < bx1 and bx1 < wx1 or \
               wx0 < bx0 and bx0 < wx1:
                select_boxes.append(box)

        if select_boxes:
            y0 = start_y
            y1 = end_y
            adjacent_line = True
            for box in select_boxes:
                y1 = box.position[0][1] - BOX_PADDING
                draw_line(draw, [start_x, y0, start_x, y1], line_width=line_width,
                          line_weight_factor=line_weight_factor)
                y0 = box.position[1][1] + BOX_PADDING
            draw_line(draw, [start_x, y0, start_x, end_y], line_width=line_width,
                      line_weight_factor=line_weight_factor)
        else:
            draw_line(draw, [start_x, start_y, end_x, end_y], line_width=line_width,
                      line_weight_factor=line_weight_factor)
            adjacent_line = False

        current_x = start_x + line_width



def draw_horizontal_lines(draw, boxes, doc_bounding_box, line_width):
    """Draw black horizontal lines across the page _except_ for that word"""
    line_weight_factor = random.choice([1, 0.02, 0.05, 0.07, 0.1, 0.2])
    color = (0, 0, 0)
    adjacent_line = False
    start_x = doc_bounding_box[0]
    current_y = doc_bounding_box[1]
    end_x = doc_bounding_box[2]
    end_y = doc_bounding_box[3] - line_width / 2

    while current_y < doc_bounding_box[3]:
        by0 = current_y
        by1 = current_y + line_width

        select_boxes = []
        for box in boxes:
            wy0 = box.position[0][1]
            wy1 = box.position[1][1]
            if by0 <= wy0 and wy1 <= by1 or \
               wy0 <= by1 and by1 <= wy1 or \
               wy0 <= by0 and by0 <= wy1:
                select_boxes.append(box)

        if select_boxes:
            adjacent_line = True
            x0 = start_x
            x1 = end_x
            for box in select_boxes:
                x1 = box.position[0][0] - BOX_PADDING
                draw_line(draw, [x0, current_y, x1, current_y],
                          line_width=line_width,
                          line_weight_factor=line_weight_factor,
                          dir="h")
                x0 = box.position[1][0] + BOX_PADDING
            draw_line(draw, [x0 + BOX_PADDING, current_y, end_x, current_y],
                      line_width=line_width, line_weight_factor=line_weight_factor, dir="h")
        else:
            draw_line(draw, [start_x, current_y, end_x, current_y],
                      line_width=line_width, color=color,
                      line_weight_factor=line_weight_factor,
                      dir="h")
            adjacent_line = False

        current_y = by1



def draw_line(draw, pos, line_width, boundary_index=None, dir="h", color=(0, 0, 0), line_weight_factor=1):
    # Draw a fuzzy line of randomish width repeat times
    repeat = 20
    width = int(line_width) * line_weight_factor
    default_padding = line_width / 3

    # Slide the center of the line down width/2 based on dir
    if dir == 'h':
        pos[1] += width / 2
        pos[3] += width / 2
        # Introduce some randomness into the margins
        pos[0] -= random.uniform(width / 2, width * 2)
        pos[2] += random.uniform(width / 2, width * 2)
    else:
        pos[0] -= width / 2
        pos[2] -= width / 2
        # Introduce some randomness into the margins
        pos[1] -= random.uniform(width / 2, width * 2)
        pos[3] += random.uniform(width / 2, width * 2)

    for i in range(0, repeat):

        width = int(random.uniform(line_width - default_padding, line_width))

        if boundary_index == 0:
            padding = 0.1
        else:
            padding = default_padding

        pos[0] = random.uniform(pos[0] - padding, pos[0] + padding)

        if boundary_index == 1:
            padding = 0.1
        else:
            padding = default_padding
        pos[1] = random.uniform(pos[1] - padding, pos[1] + padding)

        if boundary_index == 2:
            padding = 0.1
        else:
            padding = default_padding
        pos[2] = random.uniform(pos[2] - padding, pos[2] + padding)

        if boundary_index == 3:
            padding = 0.1
        else:
            padding = default_padding
        pos[3] = random.uniform(pos[3] - padding, pos[3] + padding)

        opacity = 230 + i
        draw.line(pos, width=width, fill=(*color, opacity))

def get_boxes(imagefile, tool):
    num_words = 5
    boxes = tool.image_to_string(
        Image.open(imagefile), lang="eng",
        builder=pyocr.builders.WordBoxBuilder()
    )
    return boxes

def image_filter(img):
    for i in range(10):
        img = img.filter(ImageFilter.SMOOTH_MORE)
    return img


def parse_words(boxes):
    words = []
    for box in boxes:
        word = box.content.strip()
        word = word.translate(str.maketrans({a:None for a in string.punctuation}))
        words.append({'text': word, 'box': box})
    sent = ' '.join([w['box'].content for w in words])
    doc = nlp(sent)
    for token in doc:
        for word in words:
            text = word['text']
            if token.text == text:
                word['token'] = token
                word['pos'] = token.pos_
    return words

def find_boxes_for_grammar(boxes):
    words = parse_words(boxes)
    grammars = [
        ['DET', 'NOUN', 'VERB', 'NOUN'],
        ['ADJ', 'NOUN', 'VERB', 'NOUN'],
        ['ADJ', 'NOUN', 'VERB', 'ADV'],
        ['DET', 'NOUN', 'VERB', 'NOUN', 'CONJ', 'NOUN'],
    ]
    grammar = random.choice(grammars)
    picks = []
    word_index = 0
    prev_word = None
    prev_pos = None

    for pos in grammar:
        while True:
            word = words[word_index]
            if len(picks) > 0:
                prev_word = picks[-1]
                prev_pos = prev_word['pos']
            pick_this = True
            if prev_pos == 'DET':
                if prev_word['text'] == 'a' or prev_word['text'] == 'an':
                    # Pick this if it's singular
                    pick_this = not is_plural(word)
                if prev_word['text'] == 'a':
                    # Pick this if it doesn't start with a vowel
                    pick_this = not starts_with_vowel(word) and pick_this
                if prev_word['text'] == 'an':
                    pick_this = starts_with_vowel(word) and pick_this
                if prev_word['text'] == 'this':
                    pick_this = not is_plural(word) and pick_this
                if prev_word['text'] == 'these':
                    pick_this = is_plural(word) and pick_this
            if prev_pos == 'NOUN':
                # If the previous noun was plural, the verb must be plural
                if is_plural(prev_word):
                    pick_this = is_plural_verb(word) and pick_this
                if not is_plural(prev_word):
                    pick_this = not is_plural_verb(word) and pick_this
            if prev_pos == 'VERB':
                # If the verb was plural, the noun must be
                if is_plural_verb(prev_word):
                    pick_this = is_plural(word) and pick_this
                if not is_plural_verb(prev_word):
                    pick_this = not is_plural(word) and pick_this
            if pos == 'VERB':
                # Don't pick auxilliary verbs as they won't have a helper
                pick_this = word['token'].dep_ != 'AUX' and pick_this

            if word['pos'] == pos and pick_this and random.randint(0, 30) == 0:
                print("Picking ", word['text'], " ", word['token'].dep_)
                picks.append(word)
                prev_pos = pos
                word_index += 1
                break

            word_index += 1
    return [p['box'] for p in picks]

def is_plural(word):
    if word['text'] == 'men' or word['text'] == 'women':  # Special case this since one comes up a lot
        return True
    return word['text'][-1] == 's'

def is_plural_verb(word):
    if word['text'] == 'have':
        return True
    return word['text'][-1] != 's'

def is_present(word):
    return word['text'][-1] == 's'

def starts_with_vowel(word):
    vowels = set(['a', 'e', 'i', 'o', 'u'])
    return word['text'][0] in vowels

def draw(imagefile):
    tool = pyocr.get_available_tools()[0]
    lang = tool.get_available_languages()[0]

    boxes = get_boxes(imagefile, tool)

    while True:
        try:
            select_boxes = find_boxes_for_grammar(boxes)
            break
        except IndexError:
            print("Retrying...")
            pass

    # Get the line height by taking the average of all the box heights
    box_heights = []
    margin_lefts = []
    margin_rights = []
    margin_top = boxes[0].position[0][1]
    margin_bottom = boxes[-1].position[1][1]

    for box in boxes:
        margin_lefts.append(box.position[0][0])
        margin_rights.append(box.position[1][0])
        box_heights.append(box.position[1][1] - box.position[0][1])

    margin_left = min(margin_lefts)
    margin_right = max(margin_rights)

    line_width = mean(box_heights)
    line_spaces = [0]
    last_y_pos = boxes[0].position[1][1]

    src = Image.open(imagefile)
    src = src.convert('RGBA')
    img = Image.new('RGBA', (src.size[0], src.size[1]))
    draw = ImageDraw.Draw(img)


    doc_bounding_box = (margin_left, margin_top, margin_right, margin_bottom)

    line_choices = random.choice(('v', 'h', 'a'))
    if line_choices == 'v':
        draw_vertical_lines(draw, select_boxes, doc_bounding_box=doc_bounding_box, line_width=line_width)
    elif line_choices == 'h':
        draw_horizontal_lines(draw, select_boxes,
                              doc_bounding_box=doc_bounding_box,
                              line_width=line_width)
    else:
        draw_vertical_lines(draw, select_boxes, doc_bounding_box=doc_bounding_box, line_width=line_width)
        draw_horizontal_lines(draw, select_boxes,
                              doc_bounding_box=doc_bounding_box,
                              line_width=line_width)



    img = image_filter(img)
    out = Image.alpha_composite(src, img)

    repeat = 10
    f = 10

    for box in select_boxes:
        pad = BOX_PADDING
        d = ImageDraw.Draw(out)
        p0 = [box.position[0][0] - pad, box.position[0][1] - pad]
        p1 = [box.position[1][0] + pad, box.position[0][1] - pad]
        p2 = [box.position[1][0] + pad, box.position[1][1] + pad]
        p3 = [box.position[0][0] - pad, box.position[1][1] + pad]
        b = (*p0, *p2)
        crop = src.crop(box=b)
        out.paste(crop, box=b)
        w = 10 + int(random.uniform(-5, 5))
        for i in range(0, repeat):
            fuzz = random.uniform(-f, f)
            p0 = [p + fuzz for p in p0]
            fuzz = random.uniform(-f, f)
            p1 = [p + fuzz for p in p1]
            fuzz = random.uniform(-f, f)
            p2 = [p + fuzz for p in p2]
            fuzz = random.uniform(-f, f)
            p3 = [p + fuzz for p in p3]
            fuzz = random.uniform(-f, f)
            d.line(p0 + p1, width=w, fill="black")
            d.line(p1 + p2, width=w, fill="black")
            d.line(p2 + p3, width=w, fill="black")
            d.line(p3 + p0, width=w, fill="black")


    final = Image.new('RGBA', (src.size[0], src.size[1]))
    canvas = ImageDraw.Draw(final)
    canvas.rectangle([0, 0, final.size[0], final.size[1]], fill='white')
    final = Image.alpha_composite(final, out)
    outfile = os.path.basename(imagefile)
    final.save("build/" + outfile)


if __name__ == '__main__':
    imagefile = 'data/books/vindication/0046.png'
    draw(imagefile)
