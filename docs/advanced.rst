Advanced Usage
==============

Robot Modes
-----------

TODO: Move this

Environments
------------

The ``sr.robot3`` API is able to run in one of several "environments". An environment defines how the code interacts 
with the actual robot, or something that behaves like a robot. Examples of environments could include a real hardware 
based robot, a simulation or test equipment.

By default, the :data:`sr.robot3.env.HARDWARE_ENVIRONMENT` is used, which will communicate with a real robotics kit.

You can change the environment from the default by passed ``env`` in the :class:`sr.robot3.Robot` constructor:

.. code-block:: python

    from sr.robot3 import Robot
    from sr.robot3.env import CONSOLE_ENVIRONMENT

    r = Robot(env=CONSOLE_ENVIRONMENT)


Available Environments
~~~~~~~~~~~~~~~~~~~~~~

.. data:: sr.robot3.env.HARDWARE_ENVIRONMENT

    The default environment for ``sr.robot3`` that will interact with a real SR kit.

    :type: j5.backends.Environment


.. data:: sr.robot3.env.CONSOLE_ENVIRONMENT

    Use the console to show the actions of the robot and get information from the user
    about the sensors of the robot. This is useful for testing code without a physical
    kit.

    :type: j5.backends.Environment



Custom Ruggeduino Firmware
--------------------------

TODO: This section