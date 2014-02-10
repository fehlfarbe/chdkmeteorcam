# -*- coding: utf-8 -*-
'''
Created on 04.10.2013

@author: kolbe
'''

import subprocess, sys, re, time, os, datetime, thread, signal, shutil

from PIL import Image, ImageFont, ImageDraw, ImageOps, ImageChops
import numpy
from gi.repository import GExiv2
import astroscripts as astro

SAVEDIR = "./capture/"
DARKDIR  = "./darks/"
SERVERDIR = "/mnt/allsky"
LAT = 51.05
LON = 14
GPIOPIN = 7
DARKCOUNT = 4
SOLALT = 12

def getDark():
    if os.path.exists('dark.png'):
        return Image.open('dark.png')
    
    return None

def moveToServer():
    
    if len(os.listdir(dst)) < 0:
        print "Server not mounted?"
        return

    for root, d, files in os.walk(SAVEDIR):
    
        for f in files:
            srcFile = os.path.join(root,f)
            dstFile = os.path.join(SERVERDIR, srcFile.replace(SAVEDIR, '')).replace(':', '-')
            dstDir = os.path.dirname(dstFile)
            print srcFile + " --> " + dstFile
            
            if not os.path.exists(dstDir):
                print "create %s" % dstDir
                os.makedirs(dstDir)
            
            shutil.copyfile(srcFile, dstFile)

    for d in os.listdir(SAVEDIR):
        print "delete %s" % d
        shutil.rmtree(os.path.join(SAVEDIR, d))
        

def postProcess(filename, dst, dt, tv, iso):
    
    ### edit exif / get exif data
    exif = GExiv2.Metadata(filename)
    av = exif['Exif.Photo.FNumber']
    
    img = Image.open(filename)
    
    ### subtract dark
    try:
        dark = Image.open(os.path.join(DARKDIR, 'dark.png'))
        img = ImageChops.subtract(img, dark)
        del dark
    except Exception, e:
        print e

    text = "Init"
    img_fraction = 0.03
    fontsize = 1
    font = ImageFont.truetype("arial.ttf", fontsize)
    
    while font.getsize(text)[1] < img_fraction*img.size[1]:
        fontsize += 1
        font = ImageFont.truetype("arial.ttf", fontsize)
    border = int(font.getsize(text)[1]*1.1)
    
    img = ImageOps.expand(img, border=(0, border), fill='black')
    size = img.size
    
    draw = ImageDraw.Draw(img) 
       
    ### text
    tvVal = float(tv.split('/')[0]) / float(tv.split('/')[1])
    avVal = float(av.split('/')[0]) / float(av.split('/')[1])
    ttl = u"Meteorberry %.2f°N, %.2f°E (www.millionen-von-sonnen.de)" % (LAT, LON)
    ttr = u"Sol: Az %.2f°, Alt: %.2f°" % astro.getSunAzAlt(LAT, LON, dt)
    tbl = "Exposure: %.1fs, f%.1f, ISO: %s" % (tvVal, avVal, iso)
    tbr = dt.strftime('%Y-%m-%d_%H:%M:%S_UTC').replace('_', ' ')
    
    ### draw text
    draw.text((size[0]-font.getsize(ttr)[0]-5, 0), ttr,(255,255,255),font=font)
    draw.text((5, 0), ttl,(255,255,255),font=font)
    draw.text((5, size[1]-border), tbl,(255,255,255),font=font)
    draw.text((size[0]-font.getsize(tbr)[0]-5, size[1]-border), tbr,(255,255,255),font=font)
    
    ### save image
    img.save(dst)
    del img
    
    ### add some old exif data
    exif = GExiv2.Metadata(dst)
    exif['Exif.Photo.FNumber'] = av
    exif['Exif.Photo.ExposureTime'] = tv
    exif['Exif.Photo.ISOSpeedRatings'] = iso
    exif.save_file()
    
    os.remove(filename)


def downloadAndProcess(path, dt, tv, iso):
    ### create folder if not exists
    directory = dt.strftime('%Y/%Y-%m-%d/')
    directory = os.path.join(SAVEDIR, directory)
    if not os.path.exists(directory):
        os.makedirs(directory)
    time = dt.strftime('%Y-%m-%d_%H:%M:%S_UTC')
    filename = os.path.join(directory, "%s.jpg" % time).replace(':', '-')
    tmpname = os.path.join('/tmp/', "%s.jpg" % time)
    
    cmd = 'download %s %s' % (path, tmpname)
    process = subprocess.Popen(['./ptpcam', '--chdk'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    response = process.communicate( cmd )
    
    ### test error
    if not checkSuccess(response):
        return
    
    print "%s saved to -> %s.jpg" % (path, tmpname)
    
    ### start postProcess in new thread
    thread.start_new_thread(postProcess, (tmpname, filename, dt, tv, iso))
    
def turnOn():
    subprocess.Popen('gpio -g mode %d out' % GPIOPIN, shell=True)
    subprocess.Popen('gpio -g write %d 1' % GPIOPIN, shell=True)
    time.sleep(3)
        
def turnOff():
    subprocess.Popen('gpio -g mode %d out' % GPIOPIN, shell=True)
    subprocess.Popen('gpio -g write %d 0' % GPIOPIN, shell=True)
    
def checkSuccess(response):
    ### test connection error
    r = response[1]
    #or r.find('runtime error') >= 0 or r.find('error reading messages') >= 0 or
    if len(r.splitlines()) > 10 or r.find('return code 0x2ff') >= 0:
        print '!!!! Error %s' % r
        return False
    return True

def getMsg():
    print "getMSG"
    process = subprocess.Popen(['./ptpcam', '--chdk'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    response = process.communicate('getm')
        
    if checkSuccess(response):
        ### remove <conn> and test message
        print response
        response = response[0].replace('<conn>', '').replace('2:msg:', '').replace("'", '').lstrip().rstrip().split('\n')
        if len(response) > 0 and response[0] != '':
            return response
    
    return None

def releaseCam():
    print "Release Camera and turn off"
    turnOff()

def initCam():
    print "Init Camera"
    turnOn()
    process = subprocess.Popen(['./ptpcam', '--chdk'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    response = process.communicate("""mode 1
upload ./lua/meteorutils.lua A/CHDK/SCRIPTS/meteorutils.lua
upload ./lua/meteorcam.lua A/CHDK/SCRIPTS/meteorcam.lua
upload ./lua/meteorcam.lua A/CHDK/SCRIPTS/meteordark.lua
lua loadfile("A/CHDK/SCRIPTS/meteorcam.lua")()
""")
    
    return checkSuccess(response)

def createAverage(imlist, outpath):
    # Assuming all images are the same size, get dimensions of first image
    w,h=Image.open(imlist[0]).size
    N=len(imlist)
    
    # Create a numpy array of floats to store the average (assume RGB images)
    arr=numpy.zeros((h,w,3),numpy.float)
    
    # Build up average pixel intensities, casting each image as an array of floats
    for im in imlist:
        print "open %s" % im
        imarr=numpy.array(Image.open(im),dtype=numpy.float)
        arr=arr+imarr/N
    
    # Round values in array and cast as 8-bit integer
    arr=numpy.array(numpy.round(arr),dtype=numpy.uint8)
    
    # Generate, save and preview final image
    out=Image.fromarray(arr,mode="RGB")
    out.save(outpath)
    
'''
def takeMasterdarkDark(n):
    success = False
    while not success:
        success = initCam()
    
    success = False
    print 'Take Masterdark'
    
    while not success:
        process = subprocess.Popen(['./ptpcam', '--chdk'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        response = process.communicate("""mode 1
lua loadfile("A/CHDK/SCRIPTS/meteordark.lua")(%d)
        """ % n)
        success = checkSuccess(response)
    
    darks = []
    takeDarks = True
    print "take darks"
    while takeDarks:
        msg = getMsg()
        if msg:
            for m in msg:
                print m
                if m.find('A/DCIM') >= 0:
                    darks.append( re.search('A/DCIM/[0-9]{3}CANON/IMG_[0-9]{4}.JPG', m).group(0) )
                    print "Dark %d" % len(darks)
                elif m.find("end") >= 0:
                    print "All darks taken..."
                    takeDarks = False
                    break

    cmd = ""
    i = 0
    for d in darks:
        cmd += "download %s %s/%d.jpg\n" % (d, DARKDIR, i)
        i += 1

    process = subprocess.Popen(['./ptpcam', '--chdk'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    response = process.communicate( cmd )
    
    darklist = []
    for dark in os.listdir(DARKDIR):
        if dark.endswith('.jpg'):
            darklist.append(os.path.join(DARKDIR, dark))
    
    print darklist
    createAverage(darklist, os.path.join(DARKDIR, "dark.png"))
    print 'Masterdark created in %s' % os.path.join(DARKDIR, "dark.png")
    
    print "Clean up"
    filelist = [ f for f in os.listdir(DARKDIR) if f.endswith(".jpg") ]
    for f in filelist:
        os.remove(f)
'''

def restart():
    releaseCam()
    time.sleep(1)
    success = False
    while not success:
        success = initCam()    
        
def exit_handler(signal, frame):
        print 'You pressed Ctrl+C!'
        releaseCam()
        exit()
        


'''####################################

    MAIN LOOP
    
#######################################'''

if __name__ == '__main__':
    
    ### init stuff
    signal.signal(signal.SIGINT, exit_handler)
    
    

    ts = 0
    active = False
    
    ### start endless loop
    print "Enter endless loop.."    
    while True:
        sunaz, sunalt = astro.getSunAzAlt(LAT, LON, datetime.datetime.utcnow())
        if sunalt < SOLALT:
            if not active:
                restart()
                active = True
            process = subprocess.Popen(['./ptpcam', '--chdk'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            response = process.communicate('getm')
                
            if checkSuccess(response):
                ### remove <conn> and test message
                response = response[0].replace('<conn>', '').replace('2:msg:', '').replace("'", '').lstrip().rstrip().split('\n')
                if len(response) > 0 and response[0] != '':
                    for r in response:
                        print "[%s] %s" % (datetime.datetime.now().strftime('%H:%M:%S'), r)
                        if r.find('end') >= 0:
                            pass
                        if r.find('TV') >= 0:
                            tv = r[3:]
                        if r.find('ISO') >= 0:
                            iso = r[4:]
                        if r.find('shoot') >= 0:
                            dt = datetime.datetime.utcnow()
                        if r.find('A/DCIM') >= 0:
                            cmd = re.search('A/DCIM/[0-9]{3}CANON/IMG_[0-9]{4}.JPG', r).group(0)
                            downloadAndProcess(cmd, dt, tv, iso)
        else:
            if active:
                turnOff()
                active = False
                moveToServer()
            print "waiting for night (sol < %f)...(sol az: %f, alt %f)" % (SOLALT, sunaz, sunalt)
            time.sleep(60)
