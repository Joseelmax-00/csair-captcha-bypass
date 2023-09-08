# Most of the code produced in this script was generated with the help (and not by) ChatGPT.
# It's not blind copy-pasting, It's using the available tools to the fullest for education

import cv2
import numpy as np
import sys

methods = [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED, cv2.TM_CCORR, cv2.TM_CCORR_NORMED, cv2.TM_CCOEFF, cv2.TM_CCOEFF_NORMED]
DEBUG = "--debug" in sys.argv
SHOW_IMAGES = "--show" in sys.argv

def darken_yellow_outline(image):
    """
    Replace yellow pixels in an image with black ones. 
    Primarily used to remove the yellow outline on the puzzle piece in this captcha.
    :param image: Input image.
    :return: Output image with yellow pixels turned black.
    """
    # Convert image to BGR color space (with alpha channel)
    bgr = cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA)
    if DEBUG:
        cv2.imwrite(f"debug_bgr_{captcha_id}.png", bgr)

    # Convert the BGR image to HSV image
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    if DEBUG:
        cv2.imwrite(f"debug_hsv_{captcha_id}.png", hsv)

    # Debug
    if DEBUG:
        hsv_pixel = hsv[1]  # Replace 'y' and 'x' with the coordinates of a representative yellow pixel
        print(f'HSV values: {hsv_pixel}')

    lower_yellow = np.array([80, 100, 200])  # Slightly lower than your representative yellow pixel
    upper_yellow = np.array([100, 255, 255])

    # Threshold the HSV image to get only yellow colors
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    if DEBUG:
        cv2.imwrite(f"debug_mask_{captcha_id}.png", mask)

    # Copy the original image
    res = bgr.copy()

    # Replace yellow outline with black in the copy of the original image
    res[mask > 0] = ([11, 11, 11, 255])  # Change color to black, alpha to 255
    if DEBUG:
        cv2.imwrite(f"debug_res_{captcha_id}.png", res)

    # Convert back to RGBA color space
    result = cv2.cvtColor(res, cv2.COLOR_BGRA2RGBA)
    if DEBUG:
        cv2.imwrite(f"debug_result_{captcha_id}.png", result)

    return result

def adjust_saturation_and_brightness(image, saturation_scale, brightness_scale):
    """
    Adjusts the saturation and brightness of an image.
    :param image: Input image.
    :param saturation_scale: Float indicating the saturation scaling factor.
    :param brightness_scale: Float indicating the brightness scaling factor.
    :return: Adjusted image.
    """
    # Convert the image to the RGB color space (removing alpha channel)
    rgb = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

    # Convert the image to the HSV color space
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

    # Scale the saturation channel
    hsv[:, :, 1] = hsv[:, :, 1] * saturation_scale

    # Scale the value (brightness) channel
    hsv[:, :, 2] = hsv[:, :, 2] * brightness_scale

    # Make sure that the pixel values remain in the valid range
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 255)

    # Convert the image back to the RGB color space
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    # Convert RGB back to original format (RGBA)
    rgba = cv2.cvtColor(rgb, cv2.COLOR_RGB2RGBA)

    # Copy alpha channel from original image
    rgba[:, :, 3] = image[:, :, 3]

    # Save image to check and return it
    if DEBUG:
        cv2.imwrite(f'adjusted_{captcha_id}.png', rgba)
    return rgba

def process_image_for_edges(image):
    """
    Applies Canny Edge detection on a grayscale version of the image.
    :param image: Input image.
    :return: Grayscale image with edges highlighted.
    """
    # Convert to grayscale if image is not already grayscale
    if len(image.shape) > 2:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Perform Canny edge detection
    edges = cv2.Canny(gray, 50, 150)

    
    if DEBUG:
        cv2.imwrite(f'edges_{captcha_id}.png', edges)
    return edges

def crop_puzzle_piece(captcha_id = "0cef46d889dc4b9b9970abedbd9a8a18.png"):
    """
    Detect and crop the puzzle piece from the small image, return the puzzle piece
    with the fixed size of (35x35).
    :param captcha_id: ID of the captcha image.
    :return: Cropped piece of the image.
    """
    # Load the image
    image = cv2.imread(f"small_imgs/{captcha_id}.png", cv2.IMREAD_UNCHANGED)

    

    # Set alpha values lower than 200 to 0
    image[image[:,:,3] < 200] = [0, 0, 0, 0]
    
    # Save the loaded image
    if DEBUG:
        cv2.imwrite(f'loaded_{captcha_id}.png', image)
    
    # Get the alpha channel
    alpha_channel = image[:,:,3]

    # Find the first non-zero row in alpha_channel, which corresponds to startY
    startY = np.where(alpha_channel > 200)[0][0]

    # Define the width and height of your piece
    width = 35
    height = 35

    # Now you can crop the image
    piece = image[startY:startY+height, 0:width]

    # Save the cropped image
    if DEBUG:
        cv2.imwrite(f'piece_{captcha_id}.png', piece)
    return piece



def match_piece_to_gap(cropped_piece, image):
    """
    Matches the cropped puzzle piece to a gap in a given image using template matching.
    :param cropped_piece: The cropped piece from the image.
    :param image: The full image where the piece needs to be placed.
    :return: Location of the best match of the piece in the image.
    """
    piece = cropped_piece
    
    # Darken the yellow outline of the puzzle piece
    piece = darken_yellow_outline(piece)
    
    if DEBUG:
        cv2.imwrite(f"piece_after_yellow_darkened_{captcha_id}.png", piece)

    # Adjust the saturation and brightness
    image = adjust_saturation_and_brightness(image, 3, 1.01)
    piece = adjust_saturation_and_brightness(piece, 1, 1)
    
    # Process the images for edge detection
    image_edges = process_image_for_edges(image)
    piece_edges = process_image_for_edges(piece)

    # The dimensions of the puzzle piece
    w = piece.shape[1]
    h = piece.shape[0]

    methods = ['cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR', 'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
    colors = [(0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255)]  # Green, Red, Yellow, Cyan, Magenta
    locations = []
    for method, color in zip(methods, colors):
        # Perform template matching
        result = cv2.matchTemplate(image, piece, eval(method))
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum, else take maximum
        match_loc = min_loc if method in ['cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED'] else max_loc

        # Draw a rectangle around the matched area
        cv2.rectangle(image, match_loc, (match_loc[0] + w, match_loc[1] + h), color, 2)
        locations.append(match_loc)

    # Display the image
    if SHOW_IMAGES:
        cv2.imshow('Detected', image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return locations

def load_images(captcha_id):
    """
    Loads the original captcha image and the cropped puzzle piece image.
    :param captcha_id: ID of the captcha.
    :return: Original image and the cropped puzzle piece.
    """
    image = cv2.imread(f'big_imgs/{captcha_id}.png', cv2.IMREAD_UNCHANGED)
    cropped_piece = crop_puzzle_piece(captcha_id)
    return image, cropped_piece


### Used for testing purposes
if __name__ == "__main__":
    img_name = input("Enter img id: ")
    while img_name:

        captcha_id = img_name

        image, cropped_piece = load_images(captcha_id)
        
        match_loc = match_piece_to_gap(cropped_piece, image)

        print(match_loc)

        img_name = input("Enter img id: ")
