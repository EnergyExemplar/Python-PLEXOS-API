# -*- coding: utf-8 -*-
"""
Launch a PLEXOS Connect run
Created on Thu Aug 06 2020
@author: Harika Kuppa

P9 partially functional
"""


# standard Python/SciPy libraries
import getpass, sys, os, clr

# .NET related imports
sys.path.append('C:\\Program Files\\Energy Exemplar\\PLEXOS 10.0 API')
clr.AddReference('PLEXOS_NET.Core')
clr.AddReference('EEUTILITY')
clr.AddReference('EnergyExemplar.PLEXOS.Utility')

# .NET related imports
from PLEXOS_NET.Core import *
from EEUTILITY.Enums import *
from EnergyExemplar.PLEXOS.Utility.Enums import *
from System.IO import SearchOption

server =   input('Server:          ')
port =     input('Port (def:8888): ')
try:
    port = int(port)
except:
    port = 8888
username = input('Username:        ')
password = getpass.getpass('Password:        ')

# connect to the PLEXOS Connect server
cxn = PLEXOSConnect()
cxn.DisplayAlerts = False
cxn.Connection('Data Source={}:{};User Id={};Password={}'.format(server,port,username,password))

folder = input('Folder:   ')
local =  input('Local Folder: ')
dataset = input('Dataset:  ')

if len(dataset) == 0:
    dataset = 'testdb'
    

# verify that the dataset exists
if not cxn.CheckDatasetExists(folder,dataset):
    print('Dataset', dataset, 'does not exist in folder', folder)
    
    
else:
    '''
    String GetDatasetLatestVersion(
    	String strFolderPath,
    	String strDatasetName
    	)
    '''
    ver = cxn.GetDatasetLatestVersion(folder,dataset)

    if not os.path.exists(local):
        os.mkdir(local)

    '''
    Boolean DownloadDatasetVersion(
    	String strDestination,
    	String strFolderPath,
    	String strDatasetName,
    	String strVersion
    	)
    '''
    cxn.DownloadDatasetVersion(local, folder, dataset, ver)
    
    #Edit the dataset
    #Direct to the directory
    for root, dirs, files in os.walk(local):
        for f in files:
            if f.endswith(".xml"):
                xml_file = os.path.join(root, f)

    # Create an object to store the input data
    db = DatabaseCore()
    db.Connection(xml_file)
    collections = db.FetchAllCollectionIds()
    classes = db.FetchAllClassIds()
    properties = db.FetchAllPropertyEnums()
    
    # Add a category
    '''
    Int32 AddCategory(
        ClassEnum nClassId,
        String strCategory
        )
    '''
    db.AddCategory(classes["Generator"], 'API')
    db.AddCategory(classes["Node"], 'API')
    
    # Add an object (and the System Membership)
    '''
    Int32 AddObject(
        String strName,
        ClassEnum nClassId,
        Boolean bAddSystemMembership,
        String strCategory[ = None],
        String strDescription[ = None]
        )
    '''
    db.AddObject('ApiGen', classes["Generator"], True, 'API', 'Testing the API')
    db.AddObject('ApiNod', classes["Node"], True, 'API', 'Testing the API')
    
    # Add memberships
    '''
    Int32 AddMembership(
        CollectionEnum nCollectionId,
        String strParent,
        String strChild
        )
    '''
    db.AddMembership(collections["GeneratorNodes"], 'ApiGen', 'ApiNod')

    # Get the System.Generators membership ID for this new generator
    '''
    Int32 GetMembershipID(
        CollectionEnum nCollectionId,
        String strParent,
        String strChild
        )    
    '''
    mem_id = db.GetMembershipID(collections["SystemGenerators"], 'System', 'ApiGen')
                                
    # Add properties
    '''
    Int32 AddProperty(
        Int32 MembershipId,
        Int32 EnumId,
        Int32 BandId,
        Double Value,
        Object DateFrom,
        Object DateTo,
        Object Variable,
        Object DataFile,
        Object Pattern,
        Object Scenario,
        Object Action,
        PeriodEnum PeriodTypeId
        )
    
    Because of the number of parameters, we need
            a. An alias for AddProperty
            b. A tuple of parameter values
            c. A call to the alias
        
    Also we need to obtain the EnumId for each property
        that we intend to add
    '''
    # b. A tuple of parameter values
    db.AddProperty(mem_id, properties["SystemGenerators.Units"], \
            1, 1.0, None, None, None, None, None, None, \
            0, PeriodEnum.Interval)

    db.AddProperty(mem_id, properties["SystemGenerators.MaxCapacity"], \
            1, 250, None, None, None, None, None, None, \
            0, PeriodEnum.Interval)

    db.AddProperty(mem_id, properties["SystemGenerators.FuelPrice"], \
            1, 2.50, None, None, None, None, None, None, \
            0, PeriodEnum.Interval)

    db.AddProperty(mem_id, properties["SystemGenerators.HeatRate"], \
            1, 9000, None, None, None, None, None, None, \
            0, PeriodEnum.Interval)   


    # save the data set
    db.Close()

    print("Downloaded and modify the input database")

    '''
    String GetDatasetLatestVersion(
        String strFolderPath,
        String strDatasetName
        )
    '''
    ver = cxn.GetDatasetLatestVersion(folder,dataset)
    
    # compute the new version number by adding one to the
    #  last element of the current version number
    sub_ver = [int(s) for s in ver.split('.')]
    sub_ver[-1] += 1
    new_version = '.'.join([str(v) for v in sub_ver])
    print(new_version)

    '''    
    Void UploadDataSet(
        String strSourcePath,
        String strFolderPath,
        String strDatasetName,
        String strNewVersion,
        SearchOption search,
        Boolean bIgnoreBaseVersion
        )
    '''
    cxn.UploadDataSet(local, folder, dataset, new_version, SearchOption.AllDirectories, True)
    print("Uploaded the dataset")

    # prompt user to select a Model
    model = input('\nModel: (in this example you need to know the name) ')
    
    # set up the arguments for the job
    args = ['"{}" -m "{}"'.format(xml_file, model)]
    
    cxn.AddJobset("", dataset + " Job")
    job = cxn.AddJob("", dataset + " Job", folder, dataset, new_version, args)
    run_id = cxn.AddRun(job)
    if run_id == "0":
        print("Add run failed")
    else:
        # track the progress of the run
        while not cxn.IsRunComplete(run_id):
            print(cxn.GetRunProgress(run_id))
        
        # Download the result
        cxn.DownloadSolution('.', run_id)
        print('Run', run_id, 'is complete.')

