#!/usr/bin/python3
# coding: utf-8

import pytesseract
import argparse
import logging
from collections import Counter

try:
    import Image, ImageOps, ImageFilter, imread
except ImportError:
    from PIL import Image, ImageOps, ImageFilter


# setup logging
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


def solve_captcha(path):
    """
    Convert a captcha image into a text,
    using PyTesseract Python-wrapper for Tesseract
    Arguments:
        path (str):
            path to the image to be processed
    Return:
        'textualized' image

    General Idea:
    1. Get list of all colors in the image
    2. Top 5 common colours consists of letters + background (Most common colour is the background)
    3. Convert all colours that aren't in the top 5 including background to white
    4. Apply Box Blur to fill in gaps and process into B/W image for OCR
    5. Use Tesseract
    """
    image = Image.open(path).convert("RGB")
    # image.convert("RGB")
    image = ImageOps.autocontrast(image)
    # image.show()

    # Get List Of Main Colors
    pixel_count = Counter(image.getdata())
    main_colours = pixel_count.most_common(5)[1:]

    # Filtering Colours
    copy = image.copy()
    pixels = copy.load()
    main_colours_list = list(zip(*main_colours))[0]
    for x in range(image.size[0]):  # For Every Pixel:
        for y in range(image.size[1]):
            if (
                pixels[x, y] not in main_colours_list
            ):  # Change All Non-Main Colour to White
                pixels[x, y] = (255, 255, 255)
    # copy.show()

    # Fill holes using box blur then flatten into B/W image
    def fillHoles(text, thresh):
        text = text.filter(ImageFilter.BoxBlur(1))
        fn = lambda x: 255 if x > thresh else 0
        text = text.convert("L").point(fn, mode="1")
        # text.show()
        return text

    # OCR Part
    def OCR(image):
        data = pytesseract.image_to_data(
            image,
            output_type="data.frame",
            config=(
                "-c tessedit"
                "_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
                "_char_blacklist=!?"
                " --psm 10"
                " --oem 3"
            ),
        )
        logging.info(
            "Text: {} | Confidence: {}%".format(data.text[4], int(data.conf[4]))
        )
        return (str(data.text[4]), int(data.conf[4]))

    return OCR(fillHoles(copy, 225))


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-i", "--image", required=True, help="path to input image to be OCR'd"
    )
    args = vars(argparser.parse_args())
    path = args["image"]
    print("-- Resolving")
    captcha_text = solve_captcha(path)[0]
    print("-- Result: {}".format(captcha_text))
