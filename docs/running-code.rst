Running Code
============

Programming your robot is done in `Python <https://www.python.org/>`__,
specifically version 3.9.7. You can learn more about Python from their
`docs <https://docs.python.org/3/>`__, and our whirlwind tour.

.. rubric:: Setup

The following two lines are required to complete initialisation of the
kit:

.. code:: python

   from sr.robot3 import Robot

   r = Robot()

Once this has been done, this ``Robot`` object can be used to control
the robot's functions.

The remainder of the tutorials pages will assume your ``Robot`` object
is defined as ``r``.

.. rubric:: Running your code

Your code needs to be built into a ``robot.zip`` bundle file for your
robot to be able to execute it. Once you have a ``robot.zip``, it needs 
to be put on a USB drive.On insertion into the robot, this file will be
executed.

To stop your code running, you can just remove the USB drive. This will
also stop the motors and any other peripherals connected to the kit.

You can then reinsert the USB drive into the robot and it will run your
``robot.zip`` again (from the start). This allows you to make changes and
test them quickly.

.. Hint:: If this file is missing or incorrectly named, your
  robot won't do anything. No log file will be created.

.. rubric:: Start Button

After the robot has finished starting up, it will wait for the *Start
Button* on the power board to be pressed before continuing with your
code, so that you can control when it starts moving. There is a green
LED next to the start button which flashes when the robot is finished
setting up and the start button can be pressed.

.. rubric:: Running Code before pressing the start button

If you want to do things before the start button press, such as setting
up servos or motors, you can pass ``wait_start`` to the ``Robot`` constructor. You will
then need to wait for the start button 
`manually <kit/power-board/#start-button>`__.

.. code:: python

   r = Robot(wait_start=False)

   # Do your setup here

   r.wait_start()

.. rubric:: Logs

A log file is saved on the USB drive so you can see what your robot did,
what it didn't do, and any errors it raised. The file is saved to
``log.txt`` in the top-level directory of the USB drive.

.. Warning:: The previous log file is deleted at the start of
   each run, so copy it elsewhere if you need to keep hold of it!

.. rubric:: Serial number

All kit boards have a serial number, unique to that specific board,
which can be read using the ``serial`` property:

.. code:: python

   r.power_board.serial
   >>> 'sr158B'
   r.servo_board.serial
   >>> 'sr1T9B'
   r.motor_board.serial
   >>> 'sr981B1'
