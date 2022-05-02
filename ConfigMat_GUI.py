import dearpygui.dearpygui as dpg
import numpy as np
import os

from Measure_DPG import ConfigMat


dpg.create_context()
dpg.create_viewport(title="Caliberation matrix", height=1080, width=1640)
dpg.setup_dearpygui()

RUN = 0
CLICK = 0
uvectors = None
co_ord = {"O": None,"OX":None, "OY":None}
matrix = None

cam_object = ConfigMat()
color_frame, depth_frame = cam_object.get_a_frame()
# print(color_frame, depth_frame)
width = depth_frame.shape[1]
height = depth_frame.shape[0]
window_dim = np.add(np.multiply(2, [height, width]), 10)
width_w = window_dim[1]
height_w = window_dim[0]
color = np.ravel(color_frame)
color = np.zeros(color.shape)
depth = np.ravel(depth_frame)
depth = np.zeros(depth.shape)

def stream():
    global depth_frame
    # with ThreadPoolExecutor(max_workers=4) as executor:
    #     future = executor.submit(cam_object.video)
    #     color, depth, depth_frame = future.result()
    color, depth, depth_frame = cam_object.video()
    color = np.ravel(color)
    depth = np.ravel(depth)
    color = np.asfarray(color, dtype=np.float32)/255
    depth = np.asfarray(depth, dtype=np.float32)/255
    dpg.set_value("color_tag", color)
    dpg.set_value("depth_tag", depth)
    dpg.enable_item("BtnStop")
    dpg.enable_item("click")


def trigger_click(sender, value, user_data):
    global CLICK, co_ord, matrix
    if user_data == 1:
        CLICK = 1
        matrix = None
        co_ord = {"O": None,"OX":None, "OY":None}
        dpg.delete_item("matrix_table", children_only=True)

        fstring = f"Registered points: \nO      :  {co_ord['O']}\tO->X :  {co_ord['OX']}\tO->Y :  {co_ord['OY']}   "
        dpg.set_value("Print_coords", fstring )
        dpg.set_value("Clicked", "")


def get_clicks(sender, value, user_data):
    global CLICK, co_ord, depth_frame, matrix
    if CLICK == 1:  
        pixel = dpg.get_plot_mouse_pos()
        if value[1] == "depth_img" and value[0] == 0:
            pixel = [int(np.round_(x)) for x in pixel]
            pixel[1] = height - pixel[1]
            
        for key, _ in co_ord.items():
            if co_ord[key] == None:
                co_ord[key] = pixel
                break
        fstring = f"Registered points: \nO  :  {co_ord['O']}\tO->X  :  {co_ord['OX']}\tO->Y  :  {co_ord['OY']}   "
        dpg.set_value("Print_coords", fstring )

    if all(co_ord.values()) :
        dpg.set_value("Clicked", "Done!")
        matrix = cam_object.calculate_distance(ords= co_ord, depth_frame=depth_frame)
        CLICK = 0
        fstring = f"Registered points: \nO  :  {co_ord['O']}\tO->X  :  {co_ord['OX']}\tO->Y  :  {co_ord['OY']}   "
        dpg.set_value("Print_coords", fstring )
        dpg.delete_item("matrix_table", children_only=True)

    if matrix is not None :
        for i in range(4):
            dpg.add_table_column(parent="matrix_table")
        for i in range(4):
            with dpg.table_row(parent="matrix_table"):
                for j in range(4):
                    dpg.add_text(round(matrix[i][j], 3) )   
        dpg.enable_item("SaveBtn")


def set_camera_config(sender, app_data):
    json_path = app_data["file_path_name"]
    cam_object.load_settings(file_path=json_path)
    dpg.set_value("Loaded", "Done!")
    if dpg.get_value("Loaded") == "Done!":
        dpg.enable_item("BtnStart")

def save_matrix(sender, app_data):
    global matrix
    dpg.set_value("Saved", "")
    save_arr = np.ravel(matrix)
    file_path = app_data["file_path_name"]
    with open(file_path, "w") as file:
        for i, val in enumerate(save_arr, start=1):
            val = f"{val:.3f} "
            file.write(val)
            if i%4 == 0 and i:
                file.write("\n")
    dpg.set_value("Saved", "Saved!")
## Fonts
font_path = os.path.join("open-sans","OpenSans-Regular.ttf" )

with dpg.font_registry():
    default_font = dpg.add_font(file = font_path, size=30)
    second_font  = dpg.add_font(file = font_path, size=24)
    # third_font   = dpg.add_font(file = font_path, size=21)

## File Dialog
with dpg.file_dialog(directory_selector=False, show=False, callback=set_camera_config, file_count=1, tag="file_dialog_tag", height=800, max_size=[1000, 800]):
    dpg.add_file_extension(".json", color=(255, 255, 0, 255))

with dpg.file_dialog(directory_selector=False, show=False, callback=save_matrix, file_count=1, tag="file_save_tag", height=800, max_size=[1000, 800],
                                default_filename="Config_Mat",  ):
    dpg.add_file_extension(".glx", color=(255, 255, 0, 255))
## textures
with dpg.texture_registry():
        dpg.add_raw_texture(width=width, height=height, default_value=color, format=dpg.mvFormat_Float_rgb, tag="color_tag" )
        dpg.add_raw_texture(width=width, height=height, default_value=depth, format=dpg.mvFormat_Float_rgb, tag="depth_tag" )
   
## Stream Window
with dpg.window(label="Camera Stream", autosize=True, pos=[350, 0], no_move=True,tag = "Stream Window", ):

    with dpg.group(horizontal=True):
        with dpg.plot(equal_aspects=True, tag="color_img", crosshairs=False, pan_button=2000, width=width, height=height ):
            dpg.add_plot_axis(dpg.mvXAxis, no_tick_labels=True, no_gridlines=True, no_tick_marks=True)
            with dpg.plot_axis(dpg.mvYAxis, no_tick_labels=True, no_gridlines=True, no_tick_marks=True):
                dpg.add_image_series("color_tag",[0,0],[width,height], )
        
        with dpg.plot(equal_aspects=True, tag="depth_img", crosshairs=True, pan_button=2000, width=width, height=height ):
            dpg.add_plot_axis(dpg.mvXAxis, no_tick_labels=True, no_gridlines=True, no_tick_marks=True)
            with dpg.plot_axis(dpg.mvYAxis, no_tick_labels=True, no_gridlines=True, no_tick_marks=True):
                dpg.add_image_series("depth_tag",[0,0],[width,height], tag = "depth_window")
    
    with dpg.group():
        dpg.add_text(default_value="Color Stream" ,pos=[int(width/2)-80, height + 50] )
        dpg.add_text(default_value="Depth Stream" ,pos=[int(width/2)+width-80, height + 50] )
        dpg.add_separator()
        dpg.add_text(default_value="", pos = [width + 50, height + 130], tag = "Print_coords")
        dpg.add_text(default_value="Transformation Matrix: ", pos=[20, height+130], tag="matrix")
        dpg.bind_item_font("Print_coords", second_font)
        dpg.bind_item_font("matrix", second_font)
 

    with dpg.table(label="Transformation Matrix", header_row=False, tag="matrix_table", pos = [40, height+160],
                             width=300, borders_innerH=True, borders_innerV=True, resizable=False):
        # dpg.bind_item_font("matrix_table", second_font)
        pass



## Button Window
with dpg.window( pos=[40,200], no_move=True, no_collapse=True, no_title_bar=True, no_resize=True, 
                                                                no_background=True, autosize=True ):
    with dpg.group(horizontal=False, tag="Btn_instruction"):
        dpg.add_text(default_value="1. Load Camera settings.", pos=[40, 10])
        dpg.add_text(default_value="2. Start streaming.", pos=[40, 90])
        dpg.add_text(default_value="3. Capture a frame.", pos=[40, 170])
        dpg.add_text(default_value="4. Select points", pos = [40, 250 ])
        dpg.add_text(default_value="5. Save Matrix", pos=[40, 320])
    dpg.bind_item_font("Btn_instruction", second_font)


    dpg.add_button(label="Camera Config",pos=[40, 40], callback=lambda: dpg.show_item("file_dialog_tag"), width=170 )
    # dpg.bind_item_font("file_dialog_tag", second_font)
    dpg.add_text(default_value="" ,pos=[220, 40],  tag="Loaded" )
    dpg.add_button(label="Start Camera" , pos=[40, 120], tag= "BtnStart", width=170, enabled=False )
    dpg.add_text(default_value="",pos=[220, 120],  tag= "Streaming")
    dpg.add_button(label="Capture frame", pos=[40, 200], tag= "BtnStop", width=170, enabled=False)
    dpg.add_text(default_value="", pos=[220, 200],  tag="Captured")
    dpg.add_button(label= "Select Points", pos= [40, 280], callback=trigger_click, user_data=1 , width=170, enabled=False, tag="click")  
    dpg.add_text(default_value="", pos=[220, 280],  tag="Clicked")
    dpg.add_button(label="Save matrix", pos=[40, 360],width=170, enabled=False , tag = "SaveBtn", callback=lambda: dpg.show_item("file_save_tag"))
    dpg.add_text(default_value="", pos=[220, 360],  tag="Saved")



    
with dpg.item_handler_registry(tag="Button_reg") as reg:
    dpg.add_item_clicked_handler()

dpg.bind_item_handler_registry("BtnStart","Button_reg" )
dpg.bind_item_handler_registry("BtnStop", "Button_reg" )

with dpg.item_handler_registry(tag = "Plot_reg"):
    dpg.add_item_clicked_handler(tag = "Image_reg", callback=get_clicks)
dpg.bind_item_handler_registry("depth_img", "Plot_reg")


dpg.bind_font(default_font)
dpg.show_viewport()



while dpg.is_dearpygui_running():
    if dpg.is_item_clicked("BtnStart"):
        RUN = 1
    elif dpg.is_item_clicked("BtnStop") and dpg.is_item_enabled("BtnStop"):
        RUN = 0
        dpg.set_value("Captured", "Yes")
        dpg.set_value("Streaming", "")


    if RUN == 1 and dpg.is_item_enabled("BtnStart"):
        stream()
        dpg.set_value("Streaming", "Yes")
        dpg.set_value("Captured", "")
    
    dpg.render_dearpygui_frame()


dpg.destroy_context()