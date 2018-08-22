## What is UMS?

**UMS (unified measurement software)** is a set of tools to control common lab-equipment mostly from Keithley, Tektronix, Zahner, Solartron, Gamry, Linkam and Eurotherm 
to make life of scientists and engineers easier. All code is written in easy-understandable Python, in an object-oriented programming style and well documented.
Over other implementations UMS has the following key benefits:

*  Free software published under the GPL v3. Therefore no more a black-box implementation where you don't know what it is doing exactly.
*  No dependence on any NI-products like VISA, LabView and all this other bloated and overpriced proprietary technology.
*  It runs basically on all platforms. However, so far we only tested it to run under Linux and Mac OS. Getting it to run under Windows should be pretty easy (However, this is not our focus since Windows has some clear disadvantages to be used as a measurement operating system. For more info on this read the section below)

## Getting Started

* [Installation](#installation)
* [Using UMS](#using-ums)
* [Measuring a voltage vs time curve](#measuring-a-voltage-vs-time-curve)
* [Frequently asked Questions](#frequently-asked-questions)


## Installation

### Installation instructions for UMS:

The following instructions should provide you with the necessary steps that need to be conducted to get UMS running under your platform.

### Prerequisites for running UMS:

*  We recommend a Linux-PC with Ubuntu or Debian installed. Also Mac OS will work
*  Ensure you have Python 2.7.x installed - eg. OSX 10.7+ has this pre-installed. (3.x is not supported) Choose the 32-bit version, especially on non-Linux machines!
*  Download the latest version of UMS from GitHub to your favourite directory. Unpack the folders that they are no longer zip, gzip, tar or bzip
*  Ensure you have all additional packages installed needed to run the GUI and the scientific calculations (namely you need: python-numpy python-scipy python-qt4 python-qt4-dbus python-qt4-gl)

```
sudo apt-get install python-numpy python-scipy python-qt4 python-qt4-dbus python-qt4-gl
```

## Using UMS

### Running your first test script:

Please keep in mind: Keeping the right directory structure is essential for running a script successfully. The program has the following hierarchy, if we assume you extracted the UMS code to the folder "yourfolder" at any location 
on your harddisk. Then you have:

yourfolder/
           source/
                  devices/            <- Here are all device-drivers located
                  tools/              <- Needed for developers
                  pyqtgraph/          <- Plotting functions. Do not touch
                  template_scripts/   <- Help directory for beginning. But to actually run those demoscripts they NEED TO BE MOVED to "yourfolder" to run. 
                  ums.py              <- This file consists all the basic functions like plotting voltage-time curves and so forth.
                  _init_.py           <- Python interna. Do not touch
                  manual.pdf          <- Read that! Describes all functions in ums.py and how you can use them
                  README	          <- Useful information about UMS
         yourtestscript.py

Keep in mind that ALL your scripts need to be located directly inside "yourfolder". It will not work if you put them in subdirectories. This is due to some strange import issues of python, which I didn't fully understand.

## Measuring a voltage vs time curve

In this section, we quickly walk you through a simple demo-program. For this, we assume you created a new script file under: yourfolder/demo_script.py with the following content:
```
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from source.ums import *
# We create the device file which we would like to use for our measurements
keithley_2000 = keithley_2000("/dev/ttyUSB0","1") # Connected via USB (Prologix Adapter), GPIB-Address set to 1

# Here we start a graphical user interface to see in real-time how voltage evolves over time for 300 seconds
voltage_logger(keithley_2000,300)

# Here we put an infinite-loop in order for the graphical window to stay open after the measurement is done
while True: # run forever
    i=0
```

Easy as that! You can now export your data to CVS or any other format (PNG, EPS) by just right clicking on the graph of interest.

## Frequently asked Questions

### My motivation to develop UMS

When I was starting my PhD at ETH in Zürich I faced quite challenging tasks to electrically measure memristive random-access-memory elements
as well as fuel-cells and microbatteries as they are developed by our research group. To my big surprise, no suitable open-source software package was
available, which was mature enough to allow for real-time monitoring, as well as modular enough to also integrate multiple instruments like furnaces and impedace bridges in 
an easy and script-based manner.
The only option to record a simple voltage-over-time curve at that time, was to download a 20 GB library from NI and install expensive and proprietary software. 

Since I mainly work with Debian Linux and heavily rely on free software, this was not an acceptable option for me, and I started developing UMS. It turned out that less than 10 MB is actually enough disk space
needed to perform all measurement tasks needed by our research group. I hereby publish all my work under a free license to also make YOUR life easier since I think it's enough if one engineer wasted weeks of his lifetime 
for writing device-drivers to all those nitty-gritty lab instruments. Make good use of it! :-)

### Why is Windows not the main operating system the software is developed for?

In science, the usual consensus that all experiments are performed reproducible is just violated! If you are using an operating system, which can change its behaviour by any newly installed security-patch, then
this is not what I consider comprehensible. Is your newly developed ReRAM wafer performing weaker because of a processing step you changed, or is it just because your OS installed overnight a certain patch, which 
interferes with the Windows-Kernel? Since proprietary software is a black box, you will never know! This is simply unacceptable!
Furthermore, Windows has still today not implemented a fully deterministic real-time scheduler which is highly needed in measurement applications. This is a deeply hidden subroutine in the Kernel which determines which thread is executed 
at which point in time, and by when it will for sure be finished. In Linux all this issues are resolved and you can track every bit of your computer down to the source code.


### Why should you avoid LabView?

Simple answer: Because LabView is broken-by-design!
Even the smallest and most trivial program is just huge and incomprehensive, once it has to be drawn together in a graphical programming environment.
I would consider myself a pretty OK programmer, and still, I have no clue how to write usable code in LabView! This has to tell you something: If you were lucky to have received a proper programming 
course at university, and still do not know how to write in LabView, then it is not YOU which is wrong BUT LabView.
LabView always advertises their "development environment" as the perfect match, even for people not familiar with programming at all.
But someone who cannot program properly, probably also shouldn't do it in the first place!


### Why is instrument xxx (put in a random model) not yet implemented?

Simply because my resources are limited! All this code was written as a tool-set for university research. I had to finish my PhD and do some exciting battery research apart from this, but your help is very much welcome on ANY new or improved 
device driver. Please just keep the programming style roughly the same, and send me your patches and I will try to keep the software up-to-date. 

### How can I make instrument xxx (put in a random model) work under UMS?

By writing a corresponding device driver in the subfolder ./devices
Orient yourself on the already existing files. Maybe even small modification on an similar device can make your new device work perfectly. Try it out! Most of them use the SCPI-programming language, which just needs you to send plain-text to the 
nework-card. Any help from you is highly appreciated. 
*The aim of this project is to make all lab equipment in the world controllable by free and open source software!*


### Why is UMS script-based? What is the point of scripts?

Have you ever found yourself sitting the whole day in the lab, just to press on a button every -say- two hours to start a new measurement? Then you know what I am talking about. Most of scientific work that has to be performed needs some repetitive 
operation on certain lab-equipment. In a script-based environment, you can simply automatise all this and the software will do it for you. No more the need to stay overnight or over the weekend in the lab, just to get a measurement series finished. 
You write your script and get the job done and saved automatically. Furthermore, scripts are not a so-called compiled language. You write plain-text and the computer translates it to machine instructions at runtime. Especially for lab-environments 
where requirements change all the time this is of great advantage.


### What is the codex an engineer should follow?

Being an engineer or scientist is a privilege and you not only have certain freedoms, but also obligation towards society to fulfil in this role. 
Maybe you are not aware of this, but you are part of the privileged crowd on this planet, that can actually produce significant changes!
This is, on one hand very powerful, but also needs to be balanced with care in an ethical context. Maybe you have been hired by a big company and you are constantly monitored by some manager-stereotype guy, trying to influence you to do things 
that do not feel right. Here some guidelines, on how to use your knowledge for the good sake only:

#### *Rule 1:* Do not use your engineering skills to develop or produce products, that are aimed to kill people.####
Sounds reasonable and commonsense, but often (especially in the US) is very well hidden in some sort of "greater-purpose project", for which the different defence-departments of governments are trying to misuse your skills.
Even though this is wrong, one often hears explanation that sound like "...at least they spend it on something reasonable and not on weapons directly...". Nonsense. A university is not a military base. So military money or money 
from weapon industry does not belong there! You can almost be sure that they *will* find a way to use your invention for the bad!

#### *Rule 2:* Do not misuse your engineering skills to built products that contain parts, that are designed to limit the lifetime of a product. ####
Often in big companies, the manager may walk up to you with exactly this request. Just ignore and don't do it! Because the manager cannot do it himself, so it won't be done at all for the sake of the good. 
It is clearly unethical and just driven by interests of selling more products, if you have to artificially shorten lifetime. Also from an environmental perspective it makes absolutely NO SENSE to design products for planned premature failure!

#### *Rule 3:* Do not write software or hardware that takes away the freedom of the end-user. ####
It is clearly a misbehaviour if you think you are better than anyone else because you are a programmer! 
By employing some "digital rights management" aka "digital restriction management" you effectively patronize other people, for which you have neither mutual agreement nor any justification.
At least all software written in an academic environment should be published freely available. If unsure, choose (A)GPLv3 or v2 as an initial license for your future software project.

#### *Rule 4:* Don't be ignorant. ####
This rule applies in particular to engineers, that work at inkjet-printer companies and spend their whole day, trying to find a way to make it impossible for regular users to NOT use the overpriced genuine-ink for their printers. 
This clearly violates all good engineering practices, and there is no reason why honest engineers should ever get involved in such development.

#### *Rule 5:* Engineer smart. ####
What needs to be done in this world is quite obvious for an educated person (and I assume you are, if you need tools such as UMS): We will soon run out of oil, and have to move away from it to renewable energy resources. And yes, 
there *IS* climate change. So instead of spending or wasting your time wrongly like fracking-oil-engineers or combustion-engine engineers do, just do the right thing in the first place. 
We need strong engagement in solar, wind, fuel-cell and battery research in order to move forward. Be part of it, if you have the possibility to do so! I feel honored that I can.






