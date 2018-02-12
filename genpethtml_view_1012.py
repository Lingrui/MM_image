#!/usr/bin/env python
import sys
import os
import cv2
import numpy as np
import dicom
from gallery import Gallery
import subprocess as sp
from glob import glob
import re
from scipy.ndimage import rotate
import scipy.ndimage 
from skimage import measure, morphology

sp.check_call("rm -rf pethtmlview", shell=True)
os.mkdir("pethtmlview")

DIRS = []

if True:
    for d in glob('MM_tasks_0929_PET/*'):
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
    if dcm.SeriesDescription == 'FUSED AXIAL':
        spacing = np.array([2.7,1,1,3],dtype=np.float32)
    else:
        spacing = np.array([2.2,1,1,3],dtype=np.float32)
    new_spacing=np.array([1,1,1,3],dtype=np.float32)
    resize_factor = spacing /new_spacing
    new_real_shape = volume.shape * resize_factor
    new_shape = np.round(new_real_shape)
    real_resize_factor = new_shape / volume.shape
    new_spacing = spacing / real_resize_factor 
    
    volume = scipy.ndimage.interpolation.zoom(volume,real_resize_factor, mode='nearest')

    return volume, desc

def write_dicom_volume_html (volume, path, title):
    gal = Gallery('pethtmlview/'+path, score=False, title=title)
    for i in range(volume.shape[0]):
        cv2.imwrite(gal.next(), volume[i])
        pass
    gal.flush()

def write_dicom_volume_html_resize_half (volume, path, title):
    gal = Gallery('pethtmlview/'+path, score=False, title=title)
    for i in range(volume.shape[0]):
        resizedImage = cv2.resize(volume[i],(0,0),fx=0.5,fy=0.5,interpolation=cv2.INTER_NEAREST)
        cv2.imwrite(gal.next(), resizedImage)
        pass
    gal.flush()

def write_dicom_volume_html_resize_twice (volume, path, title):
    gal = Gallery('pethtmlview/'+path, score=False, title=title)
    for i in range(volume.shape[0]):
        resizedImage = cv2.resize(volume[i],(0,0),fx=2.0,fy=2.0,interpolation=cv2.INTER_NEAREST)
        cv2.imwrite(gal.next(), resizedImage)
        pass
    gal.flush()


def write_dicom_volume_html_flip (volume, path, title):
    gal = Gallery('pethtmlview/'+path,score=False,title=title)
    for i in range(volume.shape[0]):
        transposedImage = cv2.transpose(volume[i])
        flippedImage = cv2.flip(transposedImage,1)
        cv2.imwrite(gal.next(), flippedImage)
        pass
    gal.flush()

def write_dicom_volume_html_flip_resize (volume, path, title):
    gal = Gallery('pethtmlview/'+path,score=False,title=title)
    for i in range(volume.shape[0]):
        transposedImage = cv2.transpose(volume[i])
        flippedImage = cv2.flip(transposedImage,1)
        resizedImage = cv2.resize(flippedImage,(0,0),fx=0.5,fy=0.5,interpolation=cv2.INTER_NEAREST)
        cv2.imwrite(gal.next(), resizedImage)
        pass
    gal.flush()

index = open('pethtmlview/index.html', 'w')
index.write('<html><body><ul>\n')
CC = 0
fused = re.compile('AXIAL') ###determin if axial faced
for d in DIRS:
    print '---', d
    volume, desc = load_dicom_volume(d)
    index.write('<li>%s</li>\n' % d)
    #index.write('<li><a href="%d/index.html" target="_blank">%s</a></li><br/>\n' % (view_path, d))
    m = 0
    for line in desc:
        #print line###############
        index.write('<li>%s</li>\n' % line) 
        #####orderd depends on axial or cornal faced
        if fused.search(line):
            m = 1
            #print 'yes'
    if (m == 1) :
        view1_path = '%d_view1' % CC
        write_dicom_volume_html(volume, view1_path, d)

        n1 = volume.shape[0]/2

    # [z, y, x, _]
        volume = np.flipud(volume)
        volume = np.swapaxes(volume, 0, 1)
    # now [y, z, x, _]
        view2_path = '%d_view2' % CC
        write_dicom_volume_html_resize_half(volume, view2_path, d)

        n2 = volume.shape[0]/2
        
        volume = np.swapaxes(volume, 0, 2)
         # now [x, z, y, _]

        view3_path = '%d_view3' % CC
        write_dicom_volume_html_resize_half(volume, view3_path, d)

        n3 = volume.shape[0]/2

    else:
        print 'no'
        view2_path = '%d_view2' %CC
        write_dicom_volume_html(volume, view2_path, d)
        print volume.shape[0]
        n2 = volume.shape[0]/2

    # [z, y, x, _]
        volume = np.swapaxes(volume, 0, 1)
        #volume_s = np.flipud(volume) 
    # now [y, z, x, _]
        view1_path = '%d_view1' % CC
        write_dicom_volume_html_resize_twice(volume, view1_path, d)
        n1 = volume.shape[0]/2
 

        volume = np.swapaxes(volume, 0, 2)
        #volume_r = rotate(volume,270,reshape=False) ###scipy.ndimage   rotate
        # now [x, z, y, _]

        view3_path = '%d_view3' % CC
        write_dicom_volume_html_flip(volume, view3_path, d)
        n3 = volume.shape[0]/2
    index.write('<ul><table><tr><td>Axial</td><td>Coronal</td><td>Sagittal</td></tr><tr><td><a href="%s/index.html"><img src="%s/%03d.png"/></a></td><td><a href="%s/index.html"><img src="%s/%03d.png"/></a></td><td><a href="%s/index.html"><img src="%s/%03d.png"/></a></td></tr></table></ul>\n' % (view1_path, view1_path, n1, view2_path, view2_path, n2, view3_path, view3_path, n3))
    CC += 1
index.write('</ul></body></html>\n')
index.close()
