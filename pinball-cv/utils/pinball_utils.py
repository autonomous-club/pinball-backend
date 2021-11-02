"""Houses pinball image utilities in class PinballUtils"""
import cv2
import numpy as np

from .general_utils import GeneralUtils


class PinballUtils:
    def __init__(self, track_pipeline=False):
        self._gen_utils = GeneralUtils()
        self.track_pipeline = track_pipeline
        self._display_pipeline = []

    def get_playfield_corners(self, img):
        # Saving a copy of the image to return after cropping into the field
        org_img = img.copy()
        self.append_to_pipeline(org_img)

        cv2.normalize(img, img, 0, 255, cv2.NORM_MINMAX)
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        self.append_to_pipeline(blurred)

        lower_yellow = [15, 100, 200]
        upper_yellow = [40, 255, 255]
        lower_blue = [100, 200, 200]
        upper_blue = [200, 255, 255]

        # for detecting each of the corner tapes
        centroids_yellow = self.find_corner_rect(blurred, lower_yellow, upper_yellow, 2)
        centroids_blue = self.find_corner_rect(blurred, lower_blue, upper_blue, 2)

        if np.array(centroids_yellow).shape != (2, 2) or np.array(
            centroids_blue
        ).shape != (2, 2):
            print("Unable to the 4 corner points of the playfield!")
            return np.array([])

        centroids_yellow = np.array(centroids_yellow).reshape(2, 2)
        centroids_blue = np.array(centroids_blue).reshape(2, 2)
        centroids = np.append(centroids_yellow, centroids_blue, axis=0)
        return centroids

    def find_corner_rect(
        self, img, lower_bound, upper_bound, n_rects, rect_contour_thresh=0
    ):
        img = self._gen_utils.apply_color_filter(img, lower_bound, upper_bound)
        self.append_to_pipeline(img)

        thresh = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.GaussianBlur(thresh, (3, 3), 0)
        _, thresh = cv2.threshold(thresh, 0, 255, cv2.THRESH_OTSU)
        self.append_to_pipeline(thresh)

        canny = self._gen_utils.canny(thresh)
        self.append_to_pipeline(canny)

        contours, _ = cv2.findContours(
            canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = self._gen_utils.filter_contours_area(contours, rect_contour_thresh)

        contour_img = img.copy()
        cv2.drawContours(contour_img, contours, -1, (255, 0, 0), 3)
        self.append_to_pipeline(contour_img)

        rects = self._gen_utils.get_contours_of_shape(contours, 4)

        rects_img = img.copy()
        cv2.drawContours(rects_img, rects, -1, (255, 0, 0), 3)
        self.append_to_pipeline(rects_img)

        if len(rects) == 0:
            return rects

        rects = self._gen_utils.get_n_largest_contour(rects, n_rects)

        clean_rects = []
        for rect in rects:
            perimeter = cv2.arcLength(rect, True)
            clean_rects.append(cv2.approxPolyDP(rect, 0.05 * perimeter, True))

        print("clean rects:", clean_rects)

        # Get just centers of the rects
        centroids = self._gen_utils.get_contour_centers(clean_rects)
        print("centroids:", centroids)

        return centroids

    def append_to_pipeline(self, img):
        if self.track_pipeline:
            self._display_pipeline.append(img)

    @property
    def display_pipeline(self):
        """Gets the display_pipeline."""
        tmp = self._display_pipeline.copy()
        return tmp

    @display_pipeline.setter
    def display_pipeline(self, new):
        """Sets the display_pipeline."""
        self._display_pipeline = new

    @display_pipeline.deleter
    def display_pipeline(self):
        """Clears the display_pipeline."""
        self._display_pipeline = []
