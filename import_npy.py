#!/usr/bin/enc python 
import sys
import os
import cv2
import numpy as np
import dicom
import re
import pickle
from glob import glob 
from scipy.ndimage import rotate
import scipy.ndimage 
from skimage import measure,morphology


ROOT = 'MM_tasks_0929_PET'
DIRS = []

if True:
    for d in glob(ROOT+'/*'):
        DIRS.append(d)

def load_dicom_volume (path):
    slices = []
    shape = None
    desc = []
    for f in glob(path + '/*'):
        try:
            dcm = dicom.read_file(f)
            if len(desc) == 0:
                try:
                    desc.append(dcm.StudyDescription)
                    desc.append(dcm.SeriesDescription)
                except:
                    print "xxxxxx"
                pass

            loc = None
            try:
                loc = dcm.SliceLocation
            except:
                try:
                    loc = dcm.InstanceNumber
                except:
                    'noloc:', f
                pass

            image = dcm.pixel_array.astype(np.float)
            #print image.shape
            if image.shape[0] == 3:
                #print image.shape #########################3
                C, H, W = image.shape
                image = np.reshape(image, (H, W, C))#np.swapaxes(image, 0, 2)
            image = np.copy(image, order='C')
            image = image.astype(np.float32)
            
            #sys.exit(0)
            modality = dcm.Modality
            #cv2.normalize(image, image, 0, 255, cv2.NORM_MINMAX)
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            else:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            #cv2.imwrite(gal.next(score=loc), image)
            if shape is None:
                shape = image.shape
            if shape == image.shape:
                slices.append((loc, image))
            else:
                print 'bad shape', f
        except Exception as e:
            print 'failed:', f, e
            pass
        pass
    print slices[0][1].shape
    H, W, C = slices[0][1].shape
    N = len(slices)

    volume = np.zeros((N, H, W, C), dtype=np.float32)
    i = 0
    for _, image in sorted(slices, key=lambda x: -x[0]):
        volume[i, :, :, :] = image
        i += 1
        pass
    #print volume.shape##############
    # normalize volume value to 0-255
    max_ = np.max(volume)
    min_ = np.min(volume)
    volume -= min_
    volume /= (max_ - min_)
    volume *= 255.0
    print "volume.shape:"
    print volume.shape ########
    ####resample######

    return volume, desc

#write to a file 
i = 0 
for d in DIRS:
    volume,desc = load_dicom_volume(d)
    np.save('./db/'+str(i)+'.npy',volume)
    i += 1
    pass
