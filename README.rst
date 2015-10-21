DatisaWorkReportIntegrator
==========================

Integrates DATISA accounting with our work report software

Installation
------------

Python 3 needs to be installed on all environments. It is recommended to add Python binaries to the PATH.


Windows
^^^^^^^

Download the appropriate psycopg2 for your Python version and architecture. You can find it `here <http://www.lfd.uci.edu/~gohlke/pythonlibs/#psycopg>`_. Choose the version that matches your Python version (that is, if you have Python 3.5 installed, choose the file that contains 'cp35', and if your OS is 64 bits, choose the file that also contains 'win_amd64'). Install it.

Execute 'pip -r requirements.txt' while on the main directory of this repository, the one that contains the requirements.txt file.

The entry point is main.py. When you execute it (with python main.py) make sure the environment variable CONNECTION_STRING is set to the database's proper connection string. You can simply use a bat file:

.. code-block::

    set CONNECTION_STRING=postgresql://user:password@host/database
    python main.py
