'''
roboviz.py - Python classes for displaying maps and robots

Requires: numpy, matplotlib

Copyright (C) 2018 Simon D. Levy

This file is part of PyRoboViz.

PyRoboViz is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as 
published by the Free Software Foundation, either version 3 of the 
License, or (at your option) any later version.

PyRoboViz is distributed in the hope that it will be useful,     
but WITHOUT ANY WARRANTY without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

'''
# Essential imports
import matplotlib.pyplot as plt
import matplotlib.cm as colormap
import matplotlib.lines as mlines
import numpy as np

# This helps with Raspberry Pi
import matplotlib
matplotlib.use('TkAgg')

class Visualizer(object):

    # Robot display params
    ROBOT_HEIGHT_M = 0.5
    ROBOT_WIDTH_M  = 0.3

    def __init__(self, map_size_pixels, map_size_meters, title, show_trajectory=False, zero_angle=None):
    
        # Store constants for update
        map_size_meters = map_size_meters
        self.map_size_pixels = map_size_pixels
        self.map_scale_meters_per_pixel = map_size_meters / float(map_size_pixels)

        # Create a byte array to display the map with a color overlay
        self.bgrbytes = bytearray(map_size_pixels * map_size_pixels * 3)
        
        # Make a nice big (10"x10") figure
        self.fig = plt.figure(figsize=(10,10))

        # Store Python ID of figure to detect window close
        self.figid = id(self.fig)

        self.fig.canvas.set_window_title('SLAM')
        plt.title(title)

        # Use an "artist" to speed up map drawing
        self.img_artist = None

        # No vehicle to show yet
        self.vehicle = None

        # Store previous position for trajectory
        self.prevpos = None
        self.showtraj = show_trajectory

        # Set up zero-angle
        self.zero_angle = float(zero_angle) if not zero_angle is None else None
        self.start_angle = None
        self.start_pos =  None

        # Set up default shift for centering at origin
        self.shift = -self.map_size_pixels / 2

    def display(self, x_m, y_m, theta_deg):

        self._setPose(x_m, y_m, theta_deg)

        return self._refresh()

    def _setPose(self, x_m, y_m, theta_deg):
        '''
        Sets vehicle pose:
        X:      left/right   (m)
        Y:      forward/back (m)
        theta:  rotation (degrees)
        '''

        if not self.zero_angle is None:
            if self.start_angle is None:
                self.start_angle = theta_deg
                self.start_pos = x_m,y_m

        if self.vehicle is None:

            self.ax = self.fig.gca()
            self.ax.set_aspect("auto")
            self.ax.set_autoscale_on(True)
            self.ax.set_xlabel('X (m)')
            self.ax.set_ylabel('Y (m)')
            self.ax.grid(False)

            # We base the axis on pixels, to support displaying the map
            self.ax.set_xlim([self.shift, self.map_size_pixels+self.shift])
            self.ax.set_ylim([self.shift, self.map_size_pixels+self.shift])

            # Hence we must relabel the axis ticks to show millimeters
            ticks = np.arange(self.shift,self.map_size_pixels+self.shift+100,100)
            labels = [str(self.map_scale_meters_per_pixel * tick) for tick in ticks]
            self.ax.set_xticklabels(labels)
            self.ax.set_yticklabels(labels)

        else:
            self.vehicle.remove()
        
        #Use a very short arrow shaft to orient the head of the arrow
        theta_rad = np.radians(theta_deg)
        c = np.cos(theta_rad)
        s = np.sin(theta_rad)
        l = 0.1
        dx = l * c
        dy = l * s
 
        s = self.map_scale_meters_per_pixel

        self.vehicle=self.ax.arrow(x_m/s, y_m/s, 
                dx, dy, head_width=Visualizer.ROBOT_WIDTH_M/s, 
                head_length=Visualizer.ROBOT_HEIGHT_M/s, fc='r', ec='r')


        # Show trajectory if indicated
        currpos = self._m2pix(x_m,y_m)
        if self.showtraj and not self.prevpos is None:
            self.ax.add_line(mlines.Line2D((self.prevpos[0],currpos[0]), (self.prevpos[1],currpos[1])))
        self.prevpos = currpos

    def _refresh(self):                   

        # If we have a new figure, something went wrong (closing figure failed)
        if self.figid != id(plt.gcf()):
            return False

        # Redraw current objects without blocking
        plt.draw()

        # Refresh display, setting flag on window close or keyboard interrupt
        try:
            plt.pause(.01) # Arbitrary pause to force redraw
            return True
        except:
            return False

        return True

    def _m2pix(self, x_m, y_m):

        s = self.map_scale_meters_per_pixel

        return x_m/s, y_m/s
    
class MapVisualizer(Visualizer):
    
    def __init__(self, map_size_pixels, map_size_meters, title='MapVisualizer', show_trajectory=False, zero_angle=None):

        Visualizer.__init__(self, map_size_pixels, map_size_meters, title, show_trajectory, zero_angle)

        # Put origin in lower-left
        self.shift = 0

    def display(self, x_m, y_m, theta_deg, mapbytes):

        self._setPose(x_m, y_m, theta_deg)

        mapimg = np.reshape(np.frombuffer(mapbytes, dtype=np.uint8), (self.map_size_pixels, self.map_size_pixels))

        # Pause to allow display to refresh
        plt.pause(.001)

        if self.img_artist is None:

            self.img_artist = self.ax.imshow(mapimg, cmap=colormap.gray)

        else:

            self.img_artist.set_data(mapimg)

        return self._refresh()

