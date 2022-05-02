# TMat-IntelRealsense-GUI


- In robotic pick and place tasks, the robot is equipped with a camera that can detect objects in its environment. There robot must be able to parse the information passed by the camera and determine the location of the object in it's(robot) coordinates. 
- A GUI has been built to get the Transformation matrix of the table (![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}&space;T_{Table-Camera}})) for further calculations to create a Hand Eye Coordination.

https://user-images.githubusercontent.com/75990547/166150607-f26ee662-1c7f-4f10-89fd-70e47ec7e033.mp4
 
![Image](/Demo.png)

- For a robot to grip an object from the container, the orientation of the object with respect to the robot, i.e. ![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}T_{Obj-Rob}}) must be known. 

    - As the location of the object is percieved by the camera, a connection between the camera and the robot, i.e. ![](https://latex.codecogs.com/svg.image?{\color{Cyan}T_{Rob-Cam}}) is necessary for the robot to parse the pixel information from the image into robot coordinates.





## Equations:

- The ![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}T_{Rob-Cam}}) can be obtained as follows.

    - ![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}T_{Object-Robot}&space;=&space;T_{Object-Table}*T_{Table-Robot}&space;&space;\to&space;(1)&space;&space;})
    - ![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}T_{Object-Camera}&space;=&space;T_{Table-Camera}*T_{Object-Table}\to(2)})
      - ![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}T_{Object-Table}=T_{Table-Camera}^{-1}*T_{Object-Camera}\to(2.1)})
- ![](https://latex.codecogs.com/svg.image?-&space;{\color{DarkOrange}&space;From&space;(1)&space;and&space;(2.1)})

- ![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}T_{Object-Robot}&space;=&space;T_{Table-Camera}^{-1}*T_{Object-Camera}*T_{Table-Robot}}&space;)


