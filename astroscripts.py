'''
Created on 06.10.2013

@author: kolbe
'''
from math import cos, sin, acos, asin
import datetime
from dateutil import tz


def getSunAzAlt(lat, lon, dt):

    loctime = dt.replace(tzinfo=tz.tzlocal())
    #print loctime
    if loctime.timetuple().tm_isdst == 1:
        loctime = loctime - datetime.timedelta(hours=1)
    loctime = loctime + loctime.utcoffset()
    #print loctime
    
    k = 0.017453;
    day = dt.timetuple().tm_yday
    h = loctime.hour
    m = dt.minute
    
    #calc it!
    dec = -23.45*cos(k*360*(day+10)/365);
    tf = 60*(-0.171*sin(0.0337*day+0.465)-0.1299*sin(0.01787*day-0.168));
    ra = 15*(h+m/60-(15-lon)/15 -12 + tf/60);
    x = sin(k*lat)*sin(k*dec)+cos(k*lat)*cos(k*dec)*cos(k*ra);
    elev = asin(x)/k;
    y = -(sin(k*lat)*sin(k*elev)-sin(k*dec)) / (cos(k*lat)*sin(acos(sin(k*elev))));
    azimut= 360-acos(y)/k;
    
    return azimut, elev