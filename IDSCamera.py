#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 15:14:28 2018

IDS uEYE Camera Control module for Python3

@author: mhejda
"""

# MODULES ###############################
from pyueye import ueye
import numpy as np
import time
#########################################

class IDSCam():
    
    def __init__(self, frames_avg=1):
        """ Object constructor, called when creating instance of the BaslerCam class """   
        
        self.CamID = ueye.HIDS(1)
        
        self.intTime = 15000 
        self.iniFile = "" 
        self.frames_avg = frames_avg
        self.connected = False
        self.binningEnabled = False
        
        # ctypes process parameters
        self.memPointer = ueye.c_mem_p() 
        self.memID = ueye.c_int()    
        self.pPitch = ueye.c_int()  
        self.bitdepth = 16 #ueye.c_int(8)
        
        self.FPS = 8
        self.currentFPS = self.FPS
        self.pixelClock = 80
        
        # Sensor dimension variables: variable type in native python + fixed sensorSize in ctypes formats 
        self.sensorHeight_ctype = ueye.c_int(3088)
        self.sensorWidth_ctype = ueye.c_int(2076)
        self.currentWidth = 3088
        self.currentHeight = 2076  
        
        # Initialize camera
        self.connect()
        
    def connect(self):
        """ Connects to the USB camera, creates main controlling object + prints out confirmation """         
        connectRet = ueye.is_InitCamera(self.CamID, None)
        
        if connectRet == 0: # on succesful connection
            self.connected = True
            self.sensorInfo = ueye.SENSORINFO()
            print('IDS camera connected.')
            ueye.is_GetSensorInfo(self.CamID, self.sensorInfo)
            
            self.sensorHeight_ctype, self.sensorWidth_ctype = self.sensorInfo.nMaxHeight, self.sensorInfo.nMaxWidth
            self.currentHeight, self.currentWidth = self.sensorHeight_ctype.value, self.sensorWidth_ctype.value

            # Settings block
            ueye.is_PixelClock(self.CamID,ueye.IS_PIXELCLOCK_CMD_SET, ueye.c_int(self.pixelClock), ueye.sizeof(ueye.c_int(self.pixelClock)))
            self.currentFPS = ueye.c_double(0)
            
            #ueye.is_SetFrameRate(self.CamID, ueye.c_int(self.FPS),self.currentFPS)
            
            ueye.is_SetDisplayMode(self.CamID,ueye.IS_SET_DM_DIB)   
            ueye.is_SetColorMode(self.CamID,ueye.IS_CM_SENSOR_RAW12)  
            
            ueye.is_SetAutoParameter(self.CamID,ueye.IS_SET_ENABLE_AUTO_GAIN, ueye.c_double(0), ueye.c_double(0))
            ueye.is_SetAutoParameter(self.CamID,ueye.IS_SET_ENABLE_AUTO_SENSOR_GAIN, ueye.c_double(0), ueye.c_double(0))
            ueye.is_SetAutoParameter(self.CamID,ueye.IS_SET_ENABLE_AUTO_SHUTTER, ueye.c_double(0), ueye.c_double(0))
            ueye.is_SetAutoParameter(self.CamID,ueye.IS_SET_ENABLE_AUTO_SENSOR_SHUTTER, ueye.c_double(0), ueye.c_double(0))
            ueye.is_SetAutoParameter(self.CamID,ueye.IS_SET_ENABLE_AUTO_WHITEBALANCE, ueye.c_double(0), ueye.c_double(0))
            ueye.is_SetAutoParameter(self.CamID,ueye.IS_SET_ENABLE_AUTO_SENSOR_WHITEBALANCE, ueye.c_double(0), ueye.c_double(0))
            ueye.is_SetHardwareGain(self.CamID, ueye.c_int(0), ueye.c_int(0), ueye.c_int(0), ueye.c_int(0))
            
            # Show a pattern (for testing)
            #ueye.is_SetSensorTestImage(self.CamID,ueye.IS_TEST_IMAGE_HORIZONTAL_GREYSCALE, ueye.c_int(0))

        else:
            print('Camera connecting failure...')
        
             
    def disconnect(self):

        exitRet = ueye.is_ExitCamera(self.CamID)
        if exitRet == 0:
            self.connected = False
            print('IDS camera disconnected.')
        else:
            print("Disconencting failure.")

    def info(self):  
        print('======================= Camera info ==========================')
        if self.sensorInfo.strSensorName.decode('utf8')[-1] == 'C':
            print('COLOR sensor detected.')
        elif self.sensorInfo.strSensorName.decode('utf8')[-1] == 'M':
            print('MONOCHROMATIC sensor detected.')
        elif self.sensorInfo.strSensorName.decode('utf8')[-1] != 'C' and self.sensorInfo.strSensorName.decode('utf8')[-1] != 'M':
            print('WARNING: Unknown sensor type (mono/RGB). Image capturing will not work correctly.')        
        print('--------------------------------------------------------------')
        
        #print('Current maximal acquisition speed: ' + str(self.currentFPS) + ' fps')
        
        expTimeMin = ueye.c_double(0)
        expTimeMax = ueye.c_double(1000)       
        ueye.is_Exposure(self.CamID, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MIN, expTimeMin, ueye.sizeof(expTimeMin))
        ueye.is_Exposure(self.CamID, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MAX, expTimeMax, ueye.sizeof(expTimeMax))        
        
        print('Exposure time range: ' + str(round(expTimeMin.value*1000,3)) + ' to ' + str(round(expTimeMax.value*1000,3)) + ' us')
        print('--------------------------------------------------------------')
        for i in self.sensorInfo._fields_:
            print(str(i[0]) + ": " + str(eval('self.sensorInfo.%s'%i[0])))
        
    def capture_image(self):
        """ In order to preserve compatibility with the old version, this function returns (R , G1 , G1 , B) images in the form of dictionary. """
        
        time.sleep(0.25)
        
        if self.frames_avg == 1:
            
            ueye.is_AllocImageMem(self.CamID, self.sensorWidth_ctype, self.sensorHeight_ctype, self.bitdepth, self.memPointer, self.memID)
            ueye.is_SetImageMem(self.CamID, self.memPointer, self.memID)
            
            imageArray = np.zeros((self.sensorHeight_ctype.value,self.sensorWidth_ctype.value), dtype=np.uint16)
            
            ueye.is_FreezeVideo(self.CamID, ueye.IS_WAIT)
            ueye.is_CopyImageMem(self.CamID, self.memPointer, self.memID, imageArray.ctypes.data) 
            # Clean memory
            ueye.is_FreeImageMem(self.CamID, self.memPointer, self.memID)      
                  
        else:
            imageStack = []
            print('('+str(self.frames_avg)+'x) ',end='')  
            for i in range(self.frames_avg):  
                ueye.is_AllocImageMem(self.CamID, self.sensorWidth_ctype, self.sensorHeight_ctype, self.bitdepth, self.memPointer, self.memID)
                ueye.is_SetImageMem(self.CamID, self.memPointer, self.memID)
                
                imageArrayFrame = np.zeros((self.sensorHeight_ctype.value,self.sensorWidth_ctype.value), dtype=np.uint16)
                
                ueye.is_FreezeVideo(self.CamID, ueye.IS_WAIT)
                ueye.is_CopyImageMem(self.CamID, self.memPointer, self.memID, imageArrayFrame.ctypes.data) 
                # Clean memory
                ueye.is_FreeImageMem(self.CamID, self.memPointer, self.memID) 
                
                imageStack.append(np.array(imageArrayFrame, dtype=np.uint16))
                
            imageArray = np.mean(imageStack, axis=0)  
            
         
        #Binning Recuting
        if self.binningEnabled == True:
            imageArray=imageArray[0:self.currentHeight,0:self.currentWidth]
            
        #imageArrayResized = self.resizeImage(imageArray)
        if self.sensorInfo.strSensorName.decode('utf8')[-1] == 'C':
            imageDict = self.colorPipe_Bayer12(imageArray)
        elif self.sensorInfo.strSensorName.decode('utf8')[-1] == 'M':
            imageDict = self.colorPipe_Mono(imageArray)  
        elif self.sensorInfo.strSensorName.decode('utf8')[-1] != 'C' and self.sensorInfo.strSensorName.decode('utf8')[-1] != 'M':
            raise NameError('Sensor type not recognized by the IDSCamera.capture_image function!')
        
        return imageDict
    
    def colorPipe_RGB8(self,image):
        """ Convert an RGB8 to its (R, G1, G2, B) components """
        image_byColor = {'R':  image[:,:,0],
                         'G1': image[:,:,1],
                         'G2': image[:,:,1],
                         'B':  image[:,:,2]}    
        
        return image_byColor
    
    def colorPipe_Bayer12(self, raw):
        """ Convert a RAW image to its (R, G1, G2, B) components """
        # The raw image contains all the (R, G1, G2, B) pixel values one after the 
        # other following this RGB pattern:
        #       G1, R, G1, R, ...           (indices   0:971 )
        #       B, G2, B, G2, ...           (indices 972:1943)
        #       etc. ...
        
        image_byColor = {'R':  np.zeros([self.currentHeight//2, self.currentWidth//2]),
                         'G1': np.zeros([self.currentHeight//2, self.currentWidth//2]),
                         'G2': np.zeros([self.currentHeight//2, self.currentWidth//2]),
                         'B':  np.zeros([self.currentHeight//2, self.currentWidth//2])}
        
        for i_line in range(self.currentHeight//2):
            line_idx_RG1 =  2 * i_line      #* width
            line_idx_G2B = (2 * i_line + 1) #* width
            
            image_byColor['R'][i_line,:] = raw[line_idx_RG1, 0 : self.currentWidth-1 : 2]
            image_byColor['G1'][i_line,:] = raw[line_idx_RG1, 1 : self.currentWidth   : 2]
            image_byColor['G2'][i_line,:] = raw[line_idx_G2B, 0 : self.currentWidth-1 : 2]
            image_byColor['B'][i_line,:] = raw[line_idx_G2B, 1 : self.currentWidth   : 2]
                
        return image_byColor

    def colorPipe_Mono(self,image):
        """ Copy monochromatic image to the (R, G1, G2, B) expected components of the dict """
        image_byColor = {'R':  image,
                         'G1': image,
                         'G2': image,
                         'B':  image}  
        
        return image_byColor
    
    def resizeImage(self, imageBig,x = 972,y=1296):
        """ Resizes images using scikit-mage. Significantly slows down capture times."""
        from skimage.transform import resize
        #image = resize(imageBig, (imageBig.shape[0]/2, imageBig.shape[1]/2), mode="constant")
        
        image = resize(imageBig, (972,1296), mode="constant",preserve_range = True)
        return image

    def set_intTime(self, intTime):
        intTime = intTime/1000
        """ Set the exposure time in microseconds. """ 

        expTime = ueye.c_double(intTime)
        ueye.is_Exposure(self.CamID, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE, expTime, ueye.sizeof(expTime))  
        wert=ueye.c_double()
        sizeo=ueye.sizeof(wert)
        ueye.is_Exposure(self.CamID, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE, wert, sizeo)

    def set_autoIntTime(self):
        """ Set the exposure time to automatic mode. """
        #to be added
        pass
    
    def toggleBinning(self, switch):  
        """ Depending on the input argument, it tries to Enable or Disable binning. If the function proceeds correctly (and changes binning state), it returns True."""

        if switch == True and self.binningEnabled == False:             
            # The binning function
            ret = ueye.is_SetBinning(self.CamID, ueye.IS_BINNING_2X_HORIZONTAL + ueye.IS_BINNING_2X_VERTICAL)
            # print('binningToggleStatus: ' + str(self.ueyeMessage(ret)))
            
            if ret == 0:
                # To properly handle the captured arrays
                self.binningEnabled = True
                # Count with proper field size
                self.currentHeight = int(self.sensorHeight_ctype.value/2)
                self.currentWidth = int(self.sensorWidth_ctype.value/2)
                return True
            else:
                return False
                
            
        if switch == False and self.binningEnabled == True:
            # The binning function
            ret = ueye.is_SetBinning(self.CamID, ueye.IS_BINNING_DISABLE)
            # print('binningToggleStatus: ' + str(self.ueyeMessage(ret)))
            
            if ret == 0:
                # To properly handle the captured arrays
               self.binningEnabled = False
               self.currentHeight = int(self.sensorHeight_ctype.value)
               self.currentWidth = int(self.sensorWidth_ctype.value)
               return True
            else:
                return False
               
        if switch == False and self.binningEnabled == False: 
            #print('Binning not active, cant be switched off.')
            return False
            
        if switch == True and self.binningEnabled == True: 
            #print('Binning currently active, cant be switched on.')
            return False           
    
    def get_intTime(self):
        wert=ueye.c_double()
        sizeo=ueye.sizeof(wert)
        ueye.is_Exposure(self.CamID, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE, wert, sizeo)
        return wert.value*1000
        
    def get_pixelSize(self):
        
        divider = 100
        
        if self.sensorInfo.strSensorName.decode('utf8')[-1] == 'C':
            divider = 50
        elif self.sensorInfo.strSensorName.decode('utf8')[-1] == 'M':
            divider = 100  
        elif self.sensorInfo.strSensorName.decode('utf8')[-1] != 'C' and self.sensorInfo.strSensorName.decode('utf8')[-1] != 'M':
            raise NameError('Sensor type not recognized by the IDSCamera.get_pixelSize function!')
            return 1
        
        if not self.sensorInfo.wPixelSize:
            raise ValueError('Pixel size couldnt be queried from the camera. get_pixelSize function returns Null.')
            return 1
        
        return int(self.sensorInfo.wPixelSize)/divider
    
    def get_width_height(self):
        
        if self.sensorInfo.strSensorName.decode('utf8')[-1] == 'C':
            return [int(self.currentHeight/2),int(self.currentWidth/2)]
        elif self.sensorInfo.strSensorName.decode('utf8')[-1] == 'M':
            return [int(self.currentHeight),int(self.currentWidth)]
        elif self.sensorInfo.strSensorName.decode('utf8')[-1] != 'C' and self.sensorInfo.strSensorName.decode('utf8')[-1] != 'M':
            raise NameError('Sensor type not recognized by the IDSCamera.get_width_height function!')
            return [999,999]

    def get_temperature(self):
        temp = ueye.c_double()
        nRet = ueye.is_DeviceFeature(self.CamID, ueye.IS_DEVICE_FEATURE_CMD_GET_TEMPERATURE, temp,ueye.sizeof(temp))
        if nRet == 0:
            return temp
        else:
            raise RuntimeError('Temperature readout failed. Error code:' + self.ueyeMessage(nRet))
            
    def plot_image(self, image_byColor):
        """ Plot image_byColor in Python """
        # For display with Matplotlib, convert the values to float between 0.0 and 
        # 1.0 by dividing by 4095 (2**12 - 1)
        import matplotlib.pyplot as mpl
        mpl.figure()
        normFac = 4095.0
        rows, cols = image_byColor['R'].shape
        rgbArray = np.zeros((rows, cols, 3), 'float')
        rgbArray[..., 0] = image_byColor[ 'R']/(normFac)  # Red   channel
        rgbArray[..., 1] = image_byColor['G2']/(normFac)  # Green channel
        rgbArray[..., 2] = image_byColor[ 'B']/(normFac)  # Blue  channel
        mpl.imshow(rgbArray, interpolation='none')
        mpl.show()

    def ueyeMessage(self, errorCode):
        from pyueye import ueye
        if errorCode == ueye.IS_TRANSFER_ERROR:
            return ('IS_TRANSFER_ERROR')
        elif errorCode ==ueye.IS_TIMED_OUT:
            return ('IS_TIMED_OUT')
        elif errorCode ==ueye.IS_OUT_OF_MEMORY:
            return ('IS_OUT_OF_MEMORY')
        elif errorCode ==ueye.IS_NOT_SUPPORTED:
            return ('IS_NOT_SUPPORTED')
        elif errorCode ==ueye.IS_NOT_CALIBRATED:
            return ('IS_NOT_CALIBRATED')
        elif errorCode ==ueye.IS_NO_SUCCESS:
            return ('IS_NO_SUCCESS')
        elif errorCode ==ueye.IS_NO_USB20:
            return ('IS_NO_USB20')
        elif errorCode ==ueye.IS_NO_ACTIVE_IMG_MEM:
            return ('IS_NO_ACTIVE_IMG_MEM')
        elif errorCode ==ueye.IS_IO_REQUEST_FAILED:
            return ('IS_IO_REQUEST_FAILED')
        elif errorCode ==ueye.IS_INVALID_PARAMETER:
            return ('IS_INVALID_PARAMETER')
        elif errorCode ==ueye.IS_INVALID_MEMORY_POINTER:
            return ('IS_INVALID_MEMORY_POINTER')
        elif errorCode ==ueye.IS_INVALID_CAMERA_HANDLE:
            return ('IS_INVALID_CAMERA_HANDLE')
        elif errorCode ==ueye.IS_INVALID_EXPOSURE_TIME:
            return ('IS_INVALID_EXPOSURE_TIME')
        elif errorCode ==ueye.IS_INVALID_CAMERA_TYPE:
            return ('IS_INVALID_CAMERA_TYPE')
        elif errorCode ==ueye.IS_INVALID_BUFFER_SIZE:
            return ('IS_INVALID_BUFFER_SIZE')
        elif errorCode ==ueye.IS_CAPTURE_RUNNING:
            return ('IS_CAPTURE_RUNNING')
        elif errorCode ==ueye.IS_CANT_COMMUNICATE_WITH_DRIVER:
            return ('IS_CANT_COMMUNICATE_WITH_DRIVER')
        elif errorCode ==ueye.IS_BAD_STRUCTURE_SIZE:
            return ('IS_BAD_STRUCTURE_SIZE')
        elif errorCode ==ueye.IS_NO_SUCCESS:
            return ('IS_NO_SUCCESS')
        elif errorCode == ueye.IS_SUCCESS:
            return ('IS_SUCCESS')
        elif errorCode == ueye.INVALID_PARAMETER:
            return ('IS_INVALID_PARAMETER')    
        elif errorCode == ueye.INVALID_MODE:
            return ('IS_INVALID_MODE')   
