# -*- coding: utf-8 -*-
"""
Update PLEXOS attributes in an input dataset

Created on Sat Sep 09 19:19:57 2017

@author: Steven
"""

import os, sys, clr
from shutil import copyfile

# load PLEXOS assemblies

__program_files__ = os.environ["ProgramFiles(x86)"]
__plexos_base_folder__ = os.path.join(__program_files__, 'Energy Exemplar', 'PLEXOS 8.0')

sys.path.append(__plexos_base_folder__)
clr.AddReference('PLEXOS7_NET.Core')
clr.AddReference('EEUTILITY')

# .NET related imports
from PLEXOS7_NET.Core import DatabaseCore
from EEUTILITY.Enums import *
from System import *

if os.path.exists('rts_PLEXOS.xml'):

    # delete the modified file if it already exists
    if os.path.exists('rts3.xml'):
        os.remove('rts3.xml')

    # copy the PLEXOS input file
    copyfile('rts_PLEXOS.xml', 'rts3.xml')
    
    # Create an object to store the input data
    db = DatabaseCore()
    db.Connection('rts3.xml')

    '''
    Int32 CopyObject(
    	String strName,
    	String strNewName,
    	ClassEnum nClassId
    	)
    '''
    db.CopyObject('Q1 DA', 'APIModel', ClassEnum.Model)
    db.CopyObject('Q1 DA', 'APIHorizon', ClassEnum.Horizon)
    
    '''
    Int32 RemoveMembership(
    	CollectionEnum nCollectionId,
    	String strParent,
    	String strChild
    	)
    '''
    db.RemoveMembership(CollectionEnum.ModelHorizon, 'Q1 DA', 'APIHorizon')
    db.RemoveMembership(CollectionEnum.ModelHorizon, 'APIModel', 'Q1 DA')
    
    '''
    Int32 AddMembership(
    	CollectionEnum nCollectionId,
    	String strParent,
    	String strChild
    	)
    <---- not necessary in this case since APIHorizon was copied
        from Q1 DA
    '''
    db.AddMembership(CollectionEnum.ModelHorizon, 'APIModel', 'APIHorizon')    
    db.AddMembership(CollectionEnum.ModelReport, 'APIModel', 'Default Report')
    '''
    Boolean UpdateAttribute(
    	ClassEnum nClassId,
    	String strObjectName,
    	Int32 nAttributeEnum,
    	Double dNewValue <--- always a Double... need to convert DateTime to Double
                         <--- using the ToOADate() method of the DateTime class
    	)
    '''    
    # a list of tuples... these tuples match the signature of UpdateAttribute and AddAttribute
    #   i.e., (ClassEnum, String, Int32, Double)
    attr = [(ClassEnum.Horizon, 'APIHorizon', HorizonAttributeEnum.DateFrom, DateTime(2024,1,1).ToOADate()), \
            (ClassEnum.Horizon, 'APIHorizon', HorizonAttributeEnum.StepType, 4.0), \
            (ClassEnum.Horizon, 'APIHorizon', HorizonAttributeEnum.StepCount, 1.0), \
            (ClassEnum.Horizon, 'APIHorizon', HorizonAttributeEnum.ChronoDateFrom, DateTime(2024,2,15).ToOADate()), \
            (ClassEnum.Horizon, 'APIHorizon', HorizonAttributeEnum.ChronoStepType, 2.0), \
            (ClassEnum.Horizon, 'APIHorizon', HorizonAttributeEnum.ChronoAtaTime, 3.0), \
            (ClassEnum.Horizon, 'APIHorizon', HorizonAttributeEnum.ChronoStepCount, 4.0)]

    # loop through the attributes to add/update    
    for param in attr:
        if not db.UpdateAttribute(*param):
            # if we cannot update it, add it
            db.AddAttribute(*param)
            
    # save the data set
    db.Close()
    