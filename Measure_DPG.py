import pyrealsense2 as rs   
import numpy as np
import math
import operator
import time
import json

started = 0
class ConfigMat:
    def __init__(self) -> None:
        #Camera start parameters
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        
        #Point click registeration
        self.ords = {"o":None, "ox": None, "oy": None } 
        
        wrapper = rs.pipeline_wrapper(self.pipeline)
        self.profile = self.config.resolve(wrapper)
        
        # Gets the all avaiable devices
        self.device = self.profile.get_device()
        model = str(self.device.get_info(rs.camera_info.product_line))
        
        #Check for RGB sensor and among the sensors of the camera
        found_rgb = False
        for s in self.device.sensors:
            if s.get_info(rs.camera_info.name) == "RGB Camera": found_rgb = True
        if not found_rgb: print(u"\u001b[32m"+u"-> RGB camera not found!"+"\u001b[0m")
        
        #Enable depth stream of the camera
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

        if model == 'L500':
            self.config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
        else:
            #Enable color streaming of the camera
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        # Start streaming
        self.pipeline.start(self.config)    
        print(u"\u001b[34;1m"+u"\t= = = = = = = = = =  C A M E R A    I N I T I A L I Z A T I O N  = = = = = = = = = =\n"+u"\u001b[0m")

    def get_a_frame(self):
        align_to = rs.stream.color
        align = rs.align(align_to)
        for i in range(10):
            frame = self.pipeline.wait_for_frames()
            if frame:
                aligned_frames = align.process(frame)
                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()
                depth_color_frame = rs.colorizer().colorize(depth_frame)
                depth_color_image = np.asanyarray(depth_color_frame.get_data())
                color_image = np.asanyarray(color_frame.get_data())
        self.pipeline.stop()

        return [color_image, depth_color_image]
        
    def find_device_that_supports_advanced_mode(self) :
        DS5_product_ids = ["0AD1", "0AD2", "0AD3", "0AD4", "0AD5", "0AF6", "0AFE", "0AFF", "0B00", "0B01", "0B03", "0B07", "0B3A", "0B5C"]

        ctx = rs.context()
        devices = ctx.query_devices()
        for dev in devices:
            if dev.supports(rs.camera_info.product_id) and str(dev.get_info(rs.camera_info.product_id)) in DS5_product_ids:
                if dev.supports(rs.camera_info.name):
                    print(u"\u001b[32m\u2713"+u" Found device that supports advanced mode:", dev.get_info(rs.camera_info.name)+u"\u001b[0m")
                return dev
        raise Exception(u"->\u001b[31m"+u"No D400 product line device that supports advanced mode was found"+u"\u001b[0m")

    def load_settings(self, file_path: str):
        with open(file_path) as file:
            as_json_object = json.load(file)
            if type(next(iter(as_json_object))) != str:
                as_json_object = {k.encode('utf-8'): v.encode("utf-8") for k, v in as_json_object.items()}
            json_string = str(as_json_object).replace("'", '\"')

                
        try:
            dev = self.find_device_that_supports_advanced_mode()
            advnc_mode = rs.rs400_advanced_mode(dev)
            print(u"\u001b[32m\u2713"+ u" Advanced mode is", "enabled" if advnc_mode.is_enabled() else u"disabled"+u"\u001b[0m")
        
            # Loop until we successfully enable advanced mode
            while not advnc_mode.is_enabled():
                print(u"\n\u001b[33m"+u"Trying to enable advanced mode...")
                advnc_mode.toggle_advanced_mode(True)
                # At this point the device will disconnect and re-connect.
                print(u"Sleeping for 5 seconds...")
                time.sleep(5)
                # The 'dev' object will become invalid and we need to initialize it again
                dev = self.find_device_that_supports_advanced_mode()
                advnc_mode = rs.rs400_advanced_mode(dev)
                print(u"\u001b[32m\u2713"+u"Advanced mode is", u"enabled"+"\u001b[0m" if advnc_mode.is_enabled() else u"disabled"+u"\u001b[0m")
        except Exception as e:
            print(u"\u001b[31m"+u"No devices found with advanced mode !"+u"\u001b[0m")
            print(e)
            pass
        
        print(u"\n\u001b[36m"+u"Loading the settings......"+u"\u001b[0m")    
        advnc_mode.load_json(json_string)
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        print(u"\u001b[32m\u2713"+u" Settings loaded"+u"\u001b[0m\n")

        wrapper = rs.pipeline_wrapper(self.pipeline)
        self.profile = self.config.resolve(wrapper)

        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.pipeline.start(self.config)
        self.depth_sensor =  self.device.query_sensors()[0]   
        self.hole_filling = rs.hole_filling_filter(1)
  
        
    def video(self):
        
        # Align the depth frame with the color frame
        align_to = rs.stream.color
        align = rs.align(align_to)

        #  0 - fill_from_left - Use the value from the left neighbor pixel to fill the hole
        #  1 - farest_from_around - Use the value from the neighboring pixel which is furthest away from the sensor 
        #  2 - nearest_from_around - Use the value from the neighboring pixel closest to the sensor

        # Wait for the camera to initialize. (Startup delay)
        global started
        if not started:
            print(u"\n\u001b[36mStarting stream\u001b[0m", end="")    
            for i in range(10):
                print(u"\u001b[36m......", end="")
                time.sleep(0.1)
            
                self.pipeline.wait_for_frames()
            print(u"\n\u001b[32m\u2713 Camera stream started!....\u001b[0m\n")
            
            started = 1
        
        # Wait for a new frame
        frames = self.pipeline.wait_for_frames()
        # Align the depth frame with the color frame
        aligned_frames = align.process(frames)
        
        # From the aligned frames, get depth and color frame
        color_frame = aligned_frames.get_color_frame()
        depth_frame = aligned_frames.get_depth_frame()
        depth_filled = self.hole_filling.process(depth_frame)
        # Convert the color frame to numpy array
        color_image = np.asanyarray(color_frame.get_data())

        # Add color map( rs.colorizer()) to the depth frame for visualitation
        depth_color_frame = rs.colorizer().colorize(depth_filled)
        depth_color_image = np.asanyarray(depth_color_frame.get_data()) 

        # Save the depth frame
        self.depth_frame = depth_frame
        # Get instrinsics of the depth frame ( Used to get the depth values)
        self.depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics

        # color_image = np.asanyarray(color_frame.get_data())
        color_cvt = color_image[:,:,[2,1,0]] 
        
        
        return color_cvt, depth_color_image, depth_frame

            
        
    def calculate_distance(self, ords:dict, depth_frame):
        self.ords = ords
        o_x, o_y = self.ords["O"][0], self.ords["O"][1]
        ox_x, ox_y = self.ords["OX"][0], self.ords["OX"][1]
        oy_x, oy_y = self.ords["OY"][0], self.ords["OY"][1]
        
        point_O, point_X, point_Y = [],[],[]
        dists = []
        
        for point in self.ords.values():
            dist = depth_frame.get_distance(point[0], point[1])
            dists.append(dist)
            
        point_O = rs.rs2_deproject_pixel_to_point(self.depth_intrin, [o_x, o_y], dists[0])
        point_X = rs.rs2_deproject_pixel_to_point(self.depth_intrin, [ox_x, ox_y], dists[1])
        point_Y = rs.rs2_deproject_pixel_to_point(self.depth_intrin, [oy_x, oy_y], dists[2])
        
        #Save the points for further calculations
        self.point_O = point_O; self.point_X = point_X; self.point_Y = point_Y
        
        
        dist_OX = math.sqrt( math.pow(point_O[0] - point_X[0], 2) + math.pow(point_O[1] - point_X[1],2) + math.pow(
                                    point_O[2] - point_X[2], 2))    
        dist_OY = math.sqrt( math.pow(point_O[0] - point_Y[0], 2) + math.pow(point_O[1] - point_Y[1],2) + math.pow(
                                    point_O[2] - point_Y[2], 2))    
        
        # print("********************************************************************************************************")
        # print("\n--> O:   ",point_O,"    X:   ", point_X,"    Y:   ", point_Y)
        # print("\n--> Distance: O-X: ", dist_OX,"\t","Distance: O-Y: ", dist_OY)  
        if all(len(x)!=0 for x in [point_O, point_X, point_Y]):
            unitvectors = self.Vectors()
        return unitvectors
            

    def Vectors(self):
        #Vector OX & OY     ### Calculation of Vector OZ
        vecOX = list(map(operator.sub, self.point_X, self.point_O))             # Similar to [a-b for a,b in zip(self.point_X, self.point_Y)]
        vecOY = list(map(operator.sub, self.point_Y, self.point_O))
        
        vecOZ = np.cross(vecOX, vecOY)
        
        uvecOX, uvecOY, uvecOZ = [], [], []
        #Unitvectors of OX & OY &OZ
        uvecOX = vecOX / np.linalg.norm(vecOX)
        uvecOY = vecOY / np.linalg.norm(vecOY)
        uvecOZ = vecOZ / np.linalg.norm(vecOZ)
        matrix = np.transpose([uvecOX, uvecOY, uvecOZ])
        matrix = np.c_[matrix, self.point_O]
        matrix = np.r_[matrix, [[0.0, 0.0, 0.0, 1.0]]]
        # print(f"\n\t\t= = = = = = = OX = = = = = = =:\n\n\tVector:     {vecOX}\t\tUnitVector:     {uvecOX}")
        # print(f"\n\t\t= = = = = = = OY = = = = = = =:\n\n\tVector:     {vecOY}\t\tUnitVector:     {uvecOY}")
        # print(f"\n\t\t= = = = = = = OZ = = = = = = =:\n\n\tVector:     {vecOZ}\t\tUnitVector:     {uvecOZ}\n\n")
        # print(f"Z Value:   {np.linalg.norm(vecOZ)}")
        
        #Save the points for further calculations

        return matrix

    
