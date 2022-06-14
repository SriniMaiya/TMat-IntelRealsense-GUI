import os

import dearpygui.dearpygui as dpg
import numpy as np

from Measure_DPG import ConfigMat

# Create the GUI context
dpg.create_context()
# Create main window(Viewport)
dpg.create_viewport(
    title="Caliberation matrix",
    height=1080,
    width=1640,
    large_icon=os.path.join("assets", "Icon.ico"),
)
# Setup the main window
dpg.setup_dearpygui()

# RUN: If the streaming is on
RUN = 0
# CLICK: If the "Select Points" btn is clicked
CLICK = 0
# ID: Point IDs. p1 => Origin p2 => x-axis point p3 => y-axis point
ID = ["p1", "p2", "p3"]
# NCLICKS: number of points selected
NCLICKS = 0
# Store the coordinates
CO_ORD = {"O": None, "OX": None, "OY": None}
# Final generated matrix
MATRIX = None
# Class obect from the Measure_DPG.py
cam_object = ConfigMat()
# Get a 3 frames to setup the height, WIDTH of stream window
COL_FRAME, IR_FRAME, DEP_FRAME = cam_object.get_a_frame()
# Width and height of the frame
WIDTH = DEP_FRAME.shape[1]
HEIGHT = DEP_FRAME.shape[0]
# Color image array for initialization of GUI
COLOR = np.zeros(shape=(WIDTH * HEIGHT, 1))
# Depth image array for initialization of GUI
DEPTH = np.zeros(shape=(WIDTH * HEIGHT, 1))
# Infrared image array for initialization of GUI
IR = np.zeros(shape=(WIDTH * HEIGHT, 1))

##################################################
################ Stream functions ################
##################################################


def stream():
    """
    Get camera frames and display on the stream window
    """
    # Clear the plot annotations when streaming
    try:
        for i in ID:
            dpg.delete_item(i)
    except:
        pass

    global DEP_FRAME
    # Get COLOR, DEPTH and infrared frames
    COLOR, IR, DEPTH, DEP_FRAME = cam_object.video()

    # Convert the frame to a list
    COLOR = np.ravel(COLOR)
    DEPTH = np.ravel(DEPTH)
    IR = np.ravel(IR)
    # Normalize the list
    COLOR = np.asfarray(COLOR, dtype=np.float32) / 255
    DEPTH = np.asfarray(DEPTH, dtype=np.float32) / 255
    IR = np.asfarray(IR, dtype=np.float32) / 255
    # Set the values of respective textures
    dpg.set_value("color_tag", COLOR)
    dpg.set_value("depth_tag", DEPTH)
    dpg.set_value("ir_tag", IR)
    # Enable the stop button to be clicked once the stream begins.
    dpg.enable_item("BtnStop")


def trigger_click(sender, value, user_data):
    """
    Triggers the clicking and click registeration
    when "Select Point" button is clicked.
    """
    global CLICK, CO_ORD, MATRIX, NCLICKS
    # If left clicked on the "Select Point " button
    if user_data == 1:
        # Set trigger variable to 1
        CLICK = 1
        MATRIX = None
        CO_ORD = {"O": None, "OX": None, "OY": None}
        # Delete the displayed matrix
        dpg.delete_item("matrix_table", children_only=True)
        # f-sting for printing of the clicked pixels
        fstring = f"Registered points: \nO      :  {CO_ORD['O']}\tO->X :  {CO_ORD['OX']}\tO->Y :  {CO_ORD['OY']}"
        # Set the text item "Print_coords" to the fstring
        dpg.set_value("Print_coords", fstring)
        # Set the Info Item-"Select Point" to 0
        dpg.set_value("Clicked", "0")

        try:
            for i in ID:
                dpg.delete_item(i)
        except:
            pass
        # Set variable NCLICKS to 0
        NCLICKS = 0


def get_clicks():
    """Register clicks, display matrix and enable the save button"""
    global CLICK, CO_ORD, DEP_FRAME, MATRIX, NCLICKS
    if CLICK == 1:
        # Get the plot mouse position
        pixel = dpg.get_plot_mouse_pos()
        # Convert the float value to int
        pixel = [int(np.round_(x)) for x in pixel]
        dpg.add_plot_annotation(
            parent="color_img",
            label=" + ",
            default_value=pixel,
            color=(255, 0, 0, 80),
            tag=ID[NCLICKS - 1],
            clamped=False,
        )
        # Invert the pixel value of height
        pixel[1] = HEIGHT - pixel[1]
        # Add red annotations for the clicked points
        # Store the mouse position in the dictionary
        for key, _ in CO_ORD.items():
            if CO_ORD[key] == None:
                CO_ORD[key] = pixel
                break
        # Display the registered points
        fstring = f"Registered points: \nO  :  {CO_ORD['O']}\tO->X : {CO_ORD['OX']}\tO->Y : {CO_ORD['OY']}   "
        # Set the f-string to text item "Print_coords"
        dpg.set_value("Print_coords", fstring)
        # Increment the number of clicks
        NCLICKS += 1
        # Set the Info Item-"Select Point" to number of clicks
        dpg.set_value("Clicked", str(NCLICKS))

    # if all 3 points are not None,
    if all(CO_ORD.values()):
        # Set the Info Item-"Select Point" to "Done"
        dpg.set_value("Clicked", "Done!")
        # Calculate the transformation matrix
        MATRIX = cam_object.calculate_distance(ords=CO_ORD, depth_frame=DEP_FRAME)
        # Set CLICK, fstring to default values
        CLICK = 0
        fstring = f"Registered points: \nO  :  {CO_ORD['O']}\tO->X : {CO_ORD['OX']}\tO->Y : {CO_ORD['OY']}   "
        # Set the test item to default
        dpg.set_value("Print_coords", fstring)
        # Deleté the matrix contents
        dpg.delete_item("matrix_table", children_only=True)

    # if the matrix has been calculated,
    if MATRIX is not None:
        # Set the table element cells to the matrix values
        for i in range(4):
            dpg.add_table_column(parent="matrix_table")
        for i in range(4):
            with dpg.table_row(parent="matrix_table"):
                for j in range(4):
                    dpg.add_text(round(MATRIX[i][j], 3))
        # Enable save button
        dpg.enable_item("SaveBtn")


def crosshair(sender, app_data, user_data):
    """
    -> Adds a annotation crosshair to the neighbor plot
    of the mouse position
    -> Called by: hover handler.
    """
    # delete the previous crosshair if present
    try:
        dpg.delete_item("temp")
    except:
        pass
    # Get present mouse position
    pixel = dpg.get_plot_mouse_pos()
    # If the mouse is hovering in the color image
    if app_data == "color_img":
        # crosshair on depth image
        reciever = "depth_img"
    else:
        # crosshair on color image
        reciever = "color_img"
    # Draw a temporary crosshair on the reciever
    dpg.add_plot_annotation(
        parent=reciever,
        label=" + ",
        default_value=pixel,
        clamped=False,
        tag="temp",
        color=(128, 0, 128, 80),
    )
    # If the plot is clicked, trigger get_clicks function
    if dpg.is_item_left_clicked(app_data):
        get_clicks()


def set_camera_config(sender, app_data):
    """
    -> Sets the camera config
       Called by : file_dialog_tag
    """
    json_path = app_data["file_path_name"]
    # Loads the object with the settings present in json file
    cam_object.load_settings(file_path=json_path)
    # Change Info Text
    dpg.set_value("Loaded", "Done!")
    # If the config successfully loaded,
    if dpg.get_value("Loaded") == "Done!":
        # Enable stream button
        dpg.enable_item("BtnStart")


def save_matrix(sender, app_data):
    """
    -> Saves generated matrix to a file
       Called by: file_save_tag
    """
    global MATRIX
    dpg.set_value("Saved", "")
    # Save necessary elements of the matrix
    save_arr = np.ravel(MATRIX[:3, :].T)
    file_path = app_data["file_path_name"]
    # Write the save_arr to text with a seperator
    with open(file_path, "w") as file:
        for i, val in enumerate(save_arr, start=1):
            val = f"{val:.3f} "
            file.write(val)
    dpg.set_value("Saved", "Saved!")


def stream_button(sender, app_data, user_data):
    """
    -> Reads the sent user_data and changes button theme accordingly
        -> User data is only sent when the button has been clicked
    -> By default color stream is True
    """
    # Read the userdata
    state, enabled_theme, disabled_theme = user_data
    # Toggle the state
    state = not state
    # If the IR Button is clicked
    if sender == "BtnIR" and state == True:
        # Toggle to IR stream the color window
        dpg.configure_item("color_window", texture_tag="ir_tag")
        # Set the current user_data of the IR button
        dpg.set_item_user_data(
            "BtnIR",
            (
                state,
                enabled_theme,
                disabled_theme,
            ),
        )
        # Set the current user_data of the color button
        dpg.set_item_user_data(
            "BtnColor",
            (
                not state,
                enabled_theme,
                disabled_theme,
            ),
        )
        # Toggle theme of IR button to enabled_theme
        dpg.bind_item_theme("BtnIR", enabled_theme)
        # Toggle theme of color button to disabled_theme
        dpg.bind_item_theme("BtnColor", disabled_theme)
    # If the Color button is clicked
    if sender == "BtnColor" and state == True:
        # Toggle to Color stream the color window
        dpg.configure_item("color_window", texture_tag="color_tag")
        # Set the current user_data of the IR button
        dpg.set_item_user_data(
            "BtnIR",
            (
                not state,
                enabled_theme,
                disabled_theme,
            ),
        )
        # Set the current user_data of the color button
        dpg.set_item_user_data(
            "BtnColor",
            (
                state,
                enabled_theme,
                disabled_theme,
            ),
        )
        # Toggle theme of IR button to enabled_theme
        dpg.bind_item_theme("BtnIR", disabled_theme)
        # Toggle theme of color button to disabled_theme
        dpg.bind_item_theme("BtnColor", enabled_theme)


##################################################
################## GUI Elements ##################
##################################################


# Set red as disabled theme
with dpg.theme() as disabled_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(
            dpg.mvThemeCol_Text, (255, 0, 0), category=dpg.mvThemeCat_Core
        )
# Set green as enabled_theme
with dpg.theme() as enabled_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(
            dpg.mvThemeCol_Text, (0, 255, 0), category=dpg.mvThemeCat_Core
        )

# Load the font file
font_path = os.path.join("assets", "OpenSans-Regular.ttf")
# Set two sized fonts
with dpg.font_registry():
    default_font = dpg.add_font(file=font_path, size=30)
    second_font = dpg.add_font(file=font_path, size=24)


# File Dialog to read the configuration file
with dpg.file_dialog(
    directory_selector=False,
    show=False,
    callback=set_camera_config,
    file_count=1,
    tag="file_dialog_tag",
    height=800,
    max_size=[1000, 800],
):
    dpg.add_file_extension(".json", color=(255, 255, 0, 255))

# File Dialog to save the matrix to a file
with dpg.file_dialog(
    directory_selector=False,
    show=False,
    callback=save_matrix,
    file_count=1,
    tag="file_save_tag",
    height=800,
    max_size=[1000, 800],
    default_filename="Target_Cam",
):
    dpg.add_file_extension(".trf", color=(255, 255, 0, 255))
# textures
with dpg.texture_registry():
    # Add a texture color_stream
    dpg.add_raw_texture(
        width=WIDTH,
        height=HEIGHT,
        default_value=COLOR,
        format=dpg.mvFormat_Float_rgb,
        tag="color_tag",
    )
    # Add a texture depth_stream
    dpg.add_raw_texture(
        width=WIDTH,
        height=HEIGHT,
        default_value=DEPTH,
        format=dpg.mvFormat_Float_rgb,
        tag="depth_tag",
    )
    # Add a texture IR_stream
    dpg.add_raw_texture(
        width=WIDTH,
        height=HEIGHT,
        default_value=IR,
        format=dpg.mvFormat_Float_rgb,
        tag="ir_tag",
    )


# Stream Window
with dpg.window(
    label="Camera Stream",
    autosize=True,
    pos=[350, 0],
    no_move=True,
    tag="Stream Window",
):
    # Horizontal grouping of the color/IR and depth windows
    with dpg.group(horizontal=True):
        # Add a plot window for color/IR stream
        with dpg.plot(
            equal_aspects=True,
            tag="color_img",
            crosshairs=True,
            pan_mod=None,
            width=WIDTH,
            height=HEIGHT,
        ):
            # Add X plot axis
            dpg.add_plot_axis(
                dpg.mvXAxis, no_tick_labels=True, no_gridlines=True, no_tick_marks=True
            )
            # With X add Y plot axis
            with dpg.plot_axis(
                dpg.mvYAxis, no_tick_labels=True, no_gridlines=True, no_tick_marks=True
            ):
                # Add Image from the color_texture
                dpg.add_image_series(
                    "color_tag", [0, 0], [WIDTH, HEIGHT], tag="color_window"
                )
        # Add a plot window for depth stream
        with dpg.plot(
            equal_aspects=True,
            tag="depth_img",
            crosshairs=True,
            pan_mod=None,
            width=WIDTH,
            height=HEIGHT,
        ):
            # Add X plot axis
            dpg.add_plot_axis(
                dpg.mvXAxis, no_tick_labels=True, no_gridlines=True, no_tick_marks=True
            )
            # With X add Y plot axis
            with dpg.plot_axis(
                dpg.mvYAxis, no_tick_labels=True, no_gridlines=True, no_tick_marks=True
            ):
                # Add Image from the color_texture
                dpg.add_image_series(
                    "depth_tag", [0, 0], [WIDTH, HEIGHT], tag="depth_window"
                )
    # Add buttons to switch color and IR streams
    with dpg.group(horizontal=False):
        # Color stream button
        dpg.add_button(
            label="Color Stream",
            pos=[100, HEIGHT + 50],
            callback=stream_button,
            user_data=(True, enabled_theme, disabled_theme),
            tag="BtnColor",
        )
        # IR stream button
        dpg.add_button(
            label="Infrared Stream",
            pos=[415, HEIGHT + 50],
            callback=stream_button,
            user_data=(False, enabled_theme, disabled_theme),
            tag="BtnIR",
        )
        # Depth stream info
        dpg.add_text(
            default_value="Depth Stream", pos=[int(WIDTH / 2) + WIDTH - 80, HEIGHT + 50]
        )
        dpg.add_separator()
        # Prints mouse click pixels.
        # Values set by get_clicks() and trigger_click()
        dpg.add_text(
            default_value="", pos=[WIDTH + 50, HEIGHT + 130], tag="Print_coords"
        )
        # Transformation matrix label/text
        dpg.add_text(
            default_value="Transformation Matrix: ",
            pos=[20, HEIGHT + 130],
            tag="matrix",
        )
        # Set fonts to respective elements
        dpg.bind_item_font("Print_coords", second_font)
        dpg.bind_item_font("matrix", second_font)
        dpg.bind_item_theme("BtnIR", disabled_theme)
        dpg.bind_item_theme("BtnColor", enabled_theme)
    # Add a table to print the matrix.
    # Values set by get_clicks()
    with dpg.table(
        label="Transformation Matrix",
        header_row=False,
        tag="matrix_table",
        pos=[40, HEIGHT + 160],
        width=350,
        borders_innerH=True,
        borders_innerV=True,
        borders_outerH=True,
        borders_outerV=True,
        resizable=False,
    ):
        pass


# Left Button Window
with dpg.window(
    pos=[40, 200],
    no_move=True,
    no_collapse=True,
    no_title_bar=True,
    no_resize=True,
    no_background=True,
    autosize=True,
):
    # Vertically align the buttons
    with dpg.group(horizontal=False, tag="Btn_instruction"):
        # Text description for all the buttons
        # Present on top of respective button
        dpg.add_text(default_value="1. Load Camera settings.", pos=[20, 10])
        dpg.add_text(default_value="2. Start streaming.", pos=[20, 90])
        dpg.add_text(default_value="3. Capture a frame.", pos=[20, 170])
        dpg.add_text(default_value="4. Select points", pos=[20, 250])
        dpg.add_text(default_value="5. Save Matrix", pos=[20, 330])
    dpg.bind_item_font("Btn_instruction", second_font)

    # Button to Load camera config.
    # When clicked, file dialog is made visible
    dpg.add_button(
        label="Camera Config",
        pos=[20, 40],
        callback=lambda: dpg.show_item("file_dialog_tag"),
        width=200,
    )
    dpg.bind_item_font("file_dialog_tag", second_font)
    # Info Text for "Camera Config" button
    dpg.add_text(default_value="", pos=[230, 40], tag="Loaded")
    #  Button to start camera. Controlled in last while loop
    dpg.add_button(
        label="Start Camera", pos=[20, 120], tag="BtnStart", width=200, enabled=False
    )
    # Info Text for "Start Camera" button
    dpg.add_text(default_value="", pos=[230, 120], tag="Streaming")
    # Button to Capture a frame. Controlled in last while loop
    dpg.add_button(
        label="Capture frame", pos=[20, 200], tag="BtnStop", width=200, enabled=False
    )
    # Info Text for "Capture frame" button
    dpg.add_text(default_value="", pos=[230, 200], tag="Captured")
    # Button to select points. Controlled by trigger_click()-> get_clicks()
    dpg.add_button(
        label="Select Points",
        pos=[20, 280],
        callback=trigger_click,
        user_data=1,
        width=200,
        enabled=False,
        tag="click",
    )
    # Info Text for "Select points" button
    dpg.add_text(default_value="", pos=[230, 280], tag="Clicked")
    # Button to save generated matrix.
    # called in get_clicks()
    dpg.add_button(
        label="Save matrix",
        pos=[20, 360],
        width=200,
        enabled=False,
        tag="SaveBtn",
        callback=lambda: dpg.show_item("file_save_tag"),
    )
    # Info Text for "Save Matrix" button
    dpg.add_text(default_value="", pos=[230, 360], tag="Saved")

# Item Clicked handler.
# Registers button clicks for "Start Camera" and "Capture frame" buttons
with dpg.item_handler_registry(tag="Button_reg") as reg:
    dpg.add_item_clicked_handler(button=1)
dpg.bind_item_handler_registry("BtnStart", "Button_reg")
dpg.bind_item_handler_registry("BtnStop", "Button_reg")

# Hover handler
# Registers if the mouse is hovered over the color/IR plots
# If yes then triggers the second crosshair
with dpg.item_handler_registry(tag="hover_reg"):
    dpg.add_item_hover_handler(callback=crosshair)
dpg.bind_item_handler_registry("color_img", "hover_reg")
dpg.bind_item_handler_registry("depth_img", "hover_reg")

# Set the default font
dpg.bind_font(default_font)
# Show the base viewport
dpg.show_viewport()

# When the GUI is running,
while dpg.is_dearpygui_running():
    # If the "Start Camera" button is clicked, set RUN to 1
    if dpg.is_item_clicked("BtnStart"):
        RUN = 1
    # If the "Capture frame" button is clicked, set RUN to 0
    elif dpg.is_item_clicked("BtnStop") and dpg.is_item_enabled("BtnStop"):
        RUN = 0
        # Change the Info Texts of the corresponding buttons
        dpg.set_value("Captured", "Yes")
        dpg.set_value("Streaming", "")
        # Enable the "Select Points" button
        if not dpg.is_item_enabled("click"):
            dpg.enable_item("click")
    # If "Start camera" has been clicked and config is loaded (enabling the "Start Camera" button),
    # Start streaming.
    if RUN == 1 and dpg.is_item_enabled("BtnStart"):
        stream()
        dpg.set_value("Streaming", "Yes")
        dpg.set_value("Captured", "")
    # Render the present frame
    dpg.render_dearpygui_frame()

# Exit
dpg.destroy_context()
