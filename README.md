# TMat-IntelRealsense-GUI


- In robotic pick and place tasks, the robot is equipped with a camera that can detect objects in its environment. There robot must be able to parse the information passed by the camera and determine the location of the object in it's(robot) coordinates. 
- A GUI has been built to get the Transformation matrix of the table (![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}&space;T_{Table-Camera}})) for further calculations to create a Hand Eye Coordination.



https://user-images.githubusercontent.com/75990547/206319819-cc9bb8c5-74a1-4922-bbb9-ba27f5f12d87.mp4



![Image](/Demo.png)

- For a robot to grip an object from the container, the orientation of the object with respect to the robot, i.e. ![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}T_{Object-Robot}}) must be known. 

The ![](https://latex.codecogs.com/svg.image?\inline&space;&space;{\color{DarkOrange}&space;T_{Object-Robot}&space;&space;}) is obtained as follows,


## Equations:


  - ![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}T_{Object-Robot}&space;=&space;T_{Object-Table}*T_{Table-Robot}&space;&space;\to&space;(1)&space;&space;})
  - ![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}T_{Object-Camera}&space;=&space;T_{Table-Camera}*T_{Object-Table}\to(2)})
    - ![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}T_{Object-Table}=T_{Table-Camera}^{-1}*T_{Object-Camera}\to(2.1)})

![](https://latex.codecogs.com/svg.image?&space;{\color{DarkOrange}&space;\textup{Substituting&space;(2.1)&space;in&space;(1)}&space;&space;})
- ![](https://latex.codecogs.com/svg.image?{\color{DarkOrange}T_{Object-Robot}&space;=&space;T_{Table-Camera}^{-1}*T_{Object-Camera}*T_{Table-Robot}}&space;)


