import math
def piece_type(grid, x, y):
    mean = centerpoint_mean(grid, x, y)

    # Check for matching mean colors
    shape = 0
    found = False
    threshold = 7.2
    for color in shapes:
        # Two darkness levels for some colors
        for darkness in color:
            B = abs(mean[0] - darkness[0])
            G = abs(mean[1] - darkness[1])
            R = abs(mean[2] - darkness[2])
            if  B < threshold and G < threshold and R < threshold:
                found = True
                break
        if found:
            break   
        shape = shape+1

    # if no match found
    if found == False:
        shape = len(shapes)-1
        # # Check for interfering elements with standard deviation
        # threshold = 10
        # bgr_sd = centerpoint_sd(grid, x, y)
        # if  bgr_sd[0] < threshold and bgr_sd[1] < threshold and bgr_sd[2] < threshold:
        #     shape = 0
        # else:
        #     shape = len(shapes)-1
    return shape

def centerpoint_matrixBGR(grid, x, y, tam):
        #  cv2.circle(frame,(x, y), 2, (255,0,0), -1)
    first = math.trunc(tam/2)
    x_start = x-first
    y_start = y-first
    x_end = x+first
    y_end = y+first
    b = grid[y_start:y_end, x_start:x_end, 0]
    g = grid[y_start:y_end, x_start:x_end, 1]
    r = grid[y_start:y_end, x_start:x_end, 2]
    return [b, g, r]

def centerpoint_mean(grid, x, y):
    tam = 4
    bgr = centerpoint_matrixBGR(grid, x, y, tam)
    mean_b = np.sum(bgr[0])/(tam*tam) # total elements = tam*tam
    mean_g = np.sum(bgr[1])/(tam*tam)
    mean_r = np.sum(bgr[2])/(tam*tam)
    return [mean_b, mean_g, mean_r]

def centerpoint_sd(grid, x, y):
    tam = 4
    bgr = centerpoint_matrixBGR(grid, x, y, tam)
    mean = centerpoint_mean(grid, x, y)

    # print(bgr)
    # BLUE
    dif = 0
    for i in bgr[0]:
        for j in i:
            dif = dif + (j - mean[0])**2
    # print(dif)
    sd_b = math.sqrt(dif/tam**2)

    # GREEN
    dif = 0
    for i in bgr[1]:
        for j in i:
            dif = dif + (j - mean[1])**2
    sd_g = math.sqrt(dif/tam**2)

    # RED
    dif = 0
    for i in bgr[2]:
        for j in i:
            dif = dif + (j - mean[2])**2
    sd_r = math.sqrt(dif/tam**2)

    return [sd_b, sd_g, sd_r]