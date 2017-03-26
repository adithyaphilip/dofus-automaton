#!/Users/aphilip/anaconda/bin/python3
import cv2
import numpy as np
from matplotlib import pyplot as plt
import sys
import time

if len(sys.argv) != 4:
    print("ERROR: Requires 3 arguments - COMMAND needle haystack threshold")
    exit(1)
t1 = time.time()
img_rgb = cv2.imread(sys.argv[2], 0)
img_gray = img_rgb
# img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
template = cv2.imread(sys.argv[1], 0)
# w, h, _ = template.shape[::-1]
w, h = template.shape[::-1]
res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)
threshold = float(sys.argv[3])
loc = np.where( res >= threshold)
for pt in zip(*loc[::-1]):
    cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
t2 = time.time()
print(t2 - t1)
cv2.imwrite('res.png',img_rgb)
