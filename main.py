import math
import os
import cv2
import numpy as np


IMAGE_SCALE_FACTOR = 50
CIRCLE_RADIUS_FACTOR = 50
OUTPUT_IMAGE_HEIGHT = 125
DEPTH_LEVELS = -1
BOARDER_WIDTH = 2


def showImage(img, window_name):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    h, w = img.shape[:2]

    # initial window size (fit to a reasonable height)
    init_h = min(900, h)
    init_w = int(w * (init_h / h))
    cv2.resizeWindow(window_name, init_w, init_h)

    min_zoom = 0.1
    max_zoom = 30.0
    zoom = min_zoom
    cx = w // 2
    cy = h // 2

    dragging = False
    last_mouse = (0, 0)

    def get_window_size():
        if hasattr(cv2, "getWindowImageRect"):
            try:
                _, _, ww, hh = cv2.getWindowImageRect(window_name)
                if ww > 0 and hh > 0:
                    return ww, hh
            except Exception:
                pass
        return init_w, init_h

    def render():
        nonlocal cx, cy
        win_w, win_h = get_window_size()
        view_w = max(1, int(round(win_w / zoom)))
        view_h = max(1, int(round(win_h / zoom)))

        x0 = int(cx - view_w // 2)
        y0 = int(cy - view_h // 2)
        x0 = max(0, min(x0, w - view_w))
        y0 = max(0, min(y0, h - view_h))

        cx = x0 + view_w // 2
        cy = y0 + view_h // 2

        crop = img[y0 : y0 + view_h, x0 : x0 + view_w]
        if crop.size == 0:
            return

        interp = cv2.INTER_AREA if zoom < 1 else cv2.INTER_LINEAR
        disp = cv2.resize(crop, (win_w, win_h), interpolation=interp)
        cv2.imshow(window_name, disp)

    def on_mouse(event, x, y, flags, param):
        nonlocal zoom, cx, cy, dragging, last_mouse
        if event == cv2.EVENT_LBUTTONDOWN:
            dragging = True
            last_mouse = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            dragging = False
        elif event == cv2.EVENT_MOUSEMOVE and dragging:
            dx = x - last_mouse[0]
            dy = y - last_mouse[1]
            cx -= int(round(dx / zoom))
            cy -= int(round(dy / zoom))
            last_mouse = (x, y)
            render()
        elif event == cv2.EVENT_MOUSEWHEEL:
            # flags > 0 : wheel forward (zoom in), flags < 0 : zoom out
            forward = flags > 0
            factor = 1.15 if forward else 1.0 / 1.15

            win_w, win_h = get_window_size()
            img_x = cx + int(round((x - win_w // 2) / zoom))
            img_y = cy + int(round((y - win_h // 2) / zoom))

            new_zoom = max(min_zoom, min(max_zoom, zoom * factor))
            if new_zoom == zoom:
                return

            # adjust center so zoom focuses on mouse position
            cx = img_x - int(round((x - win_w // 2) / new_zoom))
            cy = img_y - int(round((y - win_h // 2) / new_zoom))
            zoom = new_zoom
            render()

    cv2.setMouseCallback(window_name, on_mouse)

    render()
    return


def createIntensityGrid(img):
    width = int(img.shape[1] * (OUTPUT_IMAGE_HEIGHT / img.shape[0]))
    img = cv2.resize(img, (width, OUTPUT_IMAGE_HEIGHT))
    intensityGrid = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    for y in range(OUTPUT_IMAGE_HEIGHT):
        for x in range(width):
            p = img[y, x].astype(float)
            i = 0.2126 * p[2] + 0.7152 * p[1] + 0.0722 * p[0]
            intensityGrid[y, x] = i

    minVal = np.min(intensityGrid)
    maxVal = np.max(intensityGrid)

    # normalize the intensity grid to [0, 1]
    if maxVal > minVal:
        intensityGrid = (intensityGrid - minVal) * (1 / (maxVal - minVal))

    # make the intensity more distinct into Depth Levels
    if DEPTH_LEVELS > 1:
        intensityGrid = np.floor(intensityGrid * DEPTH_LEVELS) / (DEPTH_LEVELS - 1)

    return intensityGrid


def intensityToRadius(i):
    if i <= 0:
        return 0

    # formula for area of a circle: A = π * r^2

    r = np.sqrt(i / math.pi) * CIRCLE_RADIUS_FACTOR
    return int(r)


def drawCircleGrid(intensityGrid, borderWidth):
    h, w = intensityGrid.shape[:2]
    circleGridImg = 255 * np.ones((h * IMAGE_SCALE_FACTOR, w * IMAGE_SCALE_FACTOR), dtype=np.uint8)

    for y in range(h):
        for x in range(w):
            radius = intensityToRadius(1 - intensityGrid[y, x])
            if radius > 0:
                xPos = int((x+0.5) * IMAGE_SCALE_FACTOR)
                yPos = int((y+0.5) * IMAGE_SCALE_FACTOR)

                cv2.circle(circleGridImg, (xPos, yPos), radius, (0, 0, 0), borderWidth)

    print(f"Circle grid: {w}x{h} total circles: {h*w}")
    return circleGridImg


def main(input_path):

    if not os.path.exists(input_path):
        raise ValueError(f"Error: input file not found: {input_path}")

    ogImg = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if ogImg is None:
        raise ValueError(f"Failed to read image from: {input_path}")

    intensityGrid = createIntensityGrid(ogImg)
    circleImg = drawCircleGrid(intensityGrid, BOARDER_WIDTH)
    circleImgFilled = drawCircleGrid(intensityGrid, -1)

    # showImage(ogImg, "OG Image")
    # showImage(circleImg, "Circle Grid Image")
    # showImage(circleImgFilled, "Circle Grid Image Filled")
    # while True:
    #     k = cv2.waitKey(20) & 0xFF
    #     if k == 27 or k == ord("q"):
    #         break
    # cv2.destroyAllWindows()

    return circleImgFilled, circleImg


def saveImage(img, path):
    if path is not None:
        if not cv2.imwrite(path, img):
            raise ValueError(f"Error: failed to write image to: {path}")

        print(f"Saved image to: {path}")
    return


if __name__ == "__main__":

    inputFolderPath = "examples"
    for filename in os.listdir(inputFolderPath):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):

            filled, outline = main(os.path.join(inputFolderPath, filename))

            saveImage(filled, os.path.join("filled", filename))
            saveImage(outline, os.path.join("outline", filename))
            # break
