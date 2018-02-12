#!/usr/bin/env python
import sys
import os
import cv2
import numpy as np
import dicom
from gallery import Gallery
import subprocess as sp
from glob import glob

sp.check_call('rm -rf pethtmlview', shell=True)
os.mkdir('pethtmlview')

DIRS = []
for d in glob('MM_tasks_0929_PET/PT.FUSED-AXIAL.20170421/EE*'):
    dcm = dicom.read_file(d)
    #print dcm.AcquisitionTime
    #continue
    if dcm.AcquisitionTime == '072510':
        try:
            DIRS.append(d)
            print d
        except:
            print XXXX


#for d in glob('*/DICOM/*/*/*/*'):
#    DIRS.append(d)
#DIRS = DIRS[:20]
#print DIRS


def load_dicom_volume (path):
    slices = []
    shape = None
    desc = []
#    for f in glob(path + '/*'):
    for f in glob(path):
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
                #print 'noloc:', f
                try:
                    loc = dcm.InstanceNumber
                except:
                    'noloc:', f
                pass

            image = dcm.pixel_array.astype(np.float)
            #print image.shape
            if image.shape[0] == 3:
                print image.shape
                C, H, W = image.shape
                image = np.reshape(image, (H, W, C))#np.swapaxes(image, 0, 2)
            image = np.copy(image, order='C')
            image = image.astype(np.float32)
            #slices.append((loc, image))
            
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
    # normalize volume value to 0-255
    max_ = np.max(volume)
    min_ = np.min(volume)
    volume -= min_
    volume /= (max_ - min_)
    volume *= 255.0
    return volume, desc

def write_dicom_volume_html (volume, path, title):
    gal = Gallery('pethtmlview/'+path, score=False, title=title)
    for i in range(volume.shape[0]):
        cv2.imwrite(gal.next(), volume[i])
        pass
    gal.flush()

index = open('pethtmlview/index.html', 'w')
index.write('<html><body><ul>\n')
CC = 0
for d in DIRS:
    print '---', d
    volume, desc = load_dicom_volume(d)
    index.write('<li>%s</li>\n' % d)
    #index.write('<li><a href="%d/index.html" target="_blank">%s</a></li><br/>\n' % (view_path, d))
    for line in desc:
        index.write('<li>%s</li>\n' % line)
    view1_path = '%d_view1' % CC
    write_dicom_volume_html(volume, view1_path, d)

    n1 = volume.shape[0]/2

    # [z, y, x, _]
    volume = np.swapaxes(volume, 0, 1)

    # now [y, z, x, _]
    view2_path = '%d_view2' % CC
    write_dicom_volume_html(volume, view2_path, d)

    n2 = volume.shape[0]/2

    volume = np.swapaxes(volume, 0, 2)
    # now [x, z, y, _]

    view3_path = '%d_view3' % CC
    write_dicom_volume_html(volume, view3_path, d)

    n3 = volume.shape[0]/2
    index.write('<ul><table><tr><td>Axial</td><td>Coronal</td><td>Sagittal</td></tr><tr><td><a href="%s/index.html"><img src="%s/%03d.png"/></a></td><td><a href="%s/index.html"><img src="%s/%03d.png"/></a></td><td><a href="%s/index.html"><img src="%s/%03d.png"/></a></td></tr></table></ul>\n' % (view1_path, view1_path, n1, view2_path, view2_path, n2, view3_path, view3_path, n3))
    CC += 1
index.write('</ul></body></html>\n')
index.close()
