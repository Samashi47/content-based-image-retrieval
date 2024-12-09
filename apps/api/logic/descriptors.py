import cv2
import numpy as np
from sklearn.cluster import KMeans


def get_dominant_colors(image, k=16):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pixels = image.reshape(-1, 3)
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(pixels)
    return kmeans.cluster_centers_.tolist()


def get_color_histogram(image, bins=256):
    channels = cv2.split(image)
    histograms = []
    for channel in channels:
        hist = cv2.calcHist([channel], [0], None, [bins], [0, 256])
        cv2.normalize(hist, hist)
        histograms.append(hist.flatten().tolist())
    return histograms


def get_hu_moments(image):
    epsilon = 1e-10
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return [0.0] * 7
    contour = max(contours, key=cv2.contourArea)
    moments = cv2.moments(contour)
    hu = cv2.HuMoments(moments)
    hu = [-np.log10(np.abs(h) + epsilon).item() for h in hu]
    return hu