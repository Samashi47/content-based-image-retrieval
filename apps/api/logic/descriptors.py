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

def get_gabor_texture(image):
    def build_gabor_filters():
        filters = []
        for theta in range(4):
            theta = theta * 45
            for sigma in (3, 5):
                for frequency in (0.01, 0.05):
                    kernel = cv2.getGaborKernel((5, 5), sigma, theta, frequency, 0.5, 0, ktype=cv2.CV_32F)
                    filters.append(kernel)
        return filters
    filters = build_gabor_filters()
    responses = []
    for kernel in filters:
        filtered = cv2.filter2D(image, cv2.CV_8UC3, kernel)
        responses.append(filtered.mean())
    return responses

def get_edge_histogram(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    hist = cv2.calcHist([edges], [0], None, [256], [0, 256])
    cv2.normalize(hist, hist)
    return hist.flatten().tolist()

def get_fourier_descriptors(image, n=20):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return [0.0] * (2 * n)
    contour = max(contours, key=cv2.contourArea)
    contour = contour.reshape(-1, 2).T
    fourier = np.fft.fft(contour, n=n, axis=1)
    magnitudes = np.abs(fourier)
    return magnitudes.flatten().tolist()