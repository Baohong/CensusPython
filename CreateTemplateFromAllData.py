
import sys, os
import subprocess
import arcpy.mapping
import arcpy
from arcpy import env
#import pythonaddins

import string
from collections import OrderedDict

from arcpy.sa import *
from arcpy.management import *
from arcpy.analysis import *
import arcgisscripting


#********************************************************
#There are only 3 types of field: Double, String, Integer
# SourceType        sTemplateTypeTobeAdjusted           Return

# Double            String                      ==>     String
#                   else                        ==>     Double
# String            String                      ==>     String (take the longer length of the two)
#                   else                        ==>     SourceType
# Integer           Integer                     ==>     Integer
#                   else                        ==>     sTemplateTypeTobeAdjusted
#********************************************************

def adjustType(sSourceType, sTemplateTypeTobeAdjusted):
    sSourceSplit = sSourceType.split(" ")
    sSource = sSourceSplit[0]
    if len(sSourceSplit) == 2:
       sSourceLength =  sSourceSplit[1]

    sTemplateSplit = sTemplateTypeTobeAdjusted.split(" ")
    sTemplate = sTemplateSplit[0]
    if len(sTemplateSplit) == 2:
        sTemplateLength =  sTemplateSplit[1]

    if (string.upper(sSource) == "DOUBLE"):
        if (string.upper(sTemplate) == "STRING"):
            return sTemplateTypeTobeAdjusted
        else:
            return "DOUBLE"
        
    elif (string.upper(sSource) == "STRING"):
        if (string.upper(sTemplate) == "STRING"):
            if float(sSourceLength) < float(sTemplateLength):
                return sTemplateTypeTobeAdjusted
            else:
                return sSourceType
        
        else:
            return sSourceType        
            
    elif (string.upper(sSource) == "INTEGER"):
        if (string.upper(sTemplate) == "INTEGER"):
            return "INTEGER"
        else:
            return sTemplateTypeTobeAdjusted
    else:
        return ""
def InsertDict(oldFieldTypeDic, index, key, value):
    newFieldTypeDic = OrderedDict()

    for ii in range(index):
        newFieldTypeDic[oldFieldTypeDic.items()[ii][0]] = oldFieldTypeDic.items()[ii][1]
    newFieldTypeDic[key] = value
    for ii in range(index, len(oldFieldTypeDic.keys())):
        newFieldTypeDic[oldFieldTypeDic.items()[ii][0]] = oldFieldTypeDic.items()[ii][1]
    return newFieldTypeDic


env.overwriteOutput = True
fwModified = open("C:/Users/Baohong_Inno/Documents/Ji_Inno/Project/GIS_Desktop/Merge/log/logTemplateFromAllDataModified", 'w' )
fwAdded = open("C:/Users/Baohong_Inno/Documents/Ji_Inno/Project/GIS_Desktop/Merge/log/logTemplateFromAllDataAdded", 'w' )
fwResult = open("C:/Users/Baohong_Inno/Documents/Ji_Inno/Project/GIS_Desktop/Merge/log/logResult", 'w' )
if (fwModified == None):
    print("Cannot open file " + "log")
    sys.exit("Cannot open file " + "log")
fwModified.write("my test logTemplateFromAllDataModified\n")
fwAdded.write("my test logTemplateFromAllDataAdded\n")

# Define the source and template data
workspace = "C:/Users/Baohong_Inno/Documents/Ji_Inno/Project/GIS_Desktop/Merge/Data/Data"
baseFeatureClass = "ACS_10_5YR_TRACT_06_CALIFORNIA"
#baseFeatureClass = "ACS_10_5YR_TRACT_02_ALASKA"
templateFeatures  = "C:/Users/Baohong_Inno/Documents/Ji_Inno/Project/GIS_Desktop/Merge/Result/Template.gdb/Result"


# Iterate all the featureclasses, record the field info for baseFeatureClass, make a list for feature_classes the rest 
feature_classes = []
oriFieldTypeDic = OrderedDict([])

for dirpath, dirnames, datatypes in arcpy.da.Walk(workspace,
                                                  datatype="FeatureClass",
                                                  type="Polygon"):
    for datatype in datatypes:
        if datatype == baseFeatureClass:
            
            fields= arcpy.ListFields(os.path.join(dirpath, datatype))

            for field in fields:
                if (string.upper(field.name[:8]) != "OBJECTID") and (string.upper(field.name) != "SHAPE") and (string.upper(field.name) != "SHAPE_LENGTH") and (string.upper(field.name) != "SHAPE_AREA"):
                    if string.upper(field.type) == "STRING":
                        currentField = "String " + str(field.length)
                    else:
                        currentField = field.type
                    #fwModified.write(currentField + "\n")
                    oriFieldTypeDic[string.upper(field.name)] = currentField
                    
        
        else: # Append all Polygon feature classes to a list for further processing
            feature_classes.append(os.path.join(dirpath, datatype))
            #fwModified.write("\nos.path.join(dirpath, datatype):" + os.path.join(dirpath, datatype))

# Adjust the field info according to the list of feature_classes
preFieldName = ""
for featureclass in feature_classes:
    fields= arcpy.ListFields(featureclass)
    for field in fields:
        if (string.upper(field.name[:8]) != "OBJECTID") and (string.upper(field.name) != "SHAPE") and (string.upper(field.name) != "SHAPE_LENGTH") and (string.upper(field.name) != "SHAPE_AREA"):

            # Address the DP field name for PUERTO_RICO
            if (featureclass[len(featureclass)-11:] == "PUERTO_RICO") and (field.name[:2] == "DP"):
                fieldName = field.name.replace("PR", "")
            else:
                fieldName = field.name

            if string.upper(fieldName) in oriFieldTypeDic.keys():
                oriFieldType = oriFieldTypeDic[string.upper(fieldName)]
                if string.upper(field.type) == "STRING":
                    currentFieldType = "String " + str(field.length)
                else:
                    currentFieldType = field.type
                oriFieldTypeDic[string.upper(fieldName)] = adjustType(currentFieldType, oriFieldType)
                if (string.upper(oriFieldTypeDic[string.upper(fieldName)]) != string.upper(oriFieldType)) and (fieldName[:2] != "DP"):
                    fwModified.write("\n" + fieldName + " is modified from " + oriFieldType + "  to type " + oriFieldTypeDic[string.upper(fieldName)] + " according to featureclass " + featureclass + "\n")
                
            else:# the field need to be inserted to oriFieldTypeDic
                if string.upper(field.type) == "STRING":
                    currentFieldType = "String " + str(field.length)
                else:
                    currentFieldType = field.type
                if preFieldName in oriFieldTypeDic.keys():
                    preFieldIndex = oriFieldTypeDic.keys().index(preFieldName)
                    #fwAdded.write("\n" + " preFieldIndex: " + str(preFieldIndex) + " before adding " + fieldName + "\n")
                    oriFieldTypeDic =  InsertDict(oriFieldTypeDic,preFieldIndex + 1, string.upper(fieldName), currentFieldType)
                    #only for debug
                    #AddedFieldIndex = oriFieldTypeDic.keys().index(fieldName)
                    #fwAdded.write("\n index of " + fieldName + ": " + str(AddedFieldIndex) + " after adding " + "\n")
                else: # The inserted field is the first field in the source
                    #oriFieldTypeDic.insert(0, string.upper(fieldName), currentFieldType)
                    oriFieldTypeDic =  InsertDict(oriFieldTypeDic, 0, string.upper(fieldName), currentFieldType)
                fwAdded.write("\n" + fieldName + " is added as type " + currentFieldType + " according to featureclass " + featureclass + "\n")
            preFieldName = string.upper(fieldName)

# Add the field to template
for fieldName, fieldType in oriFieldTypeDic.items():
    fwResult.write(fieldName + " " + fieldType + "\n")
try:
    for fieldName, fieldType in oriFieldTypeDic.items():
        sSourceSplit = fieldType.split(" ")
        sSource = sSourceSplit[0]
        if len(sSourceSplit) == 2:
           sSourceLength =  sSourceSplit[1]

        if (string.upper(sSource) == "DOUBLE") or (fieldName[:2] == "DP"):
            arcpy.AddField_management(templateFeatures, fieldName, "DOUBLE", 9, "", "",fieldName, "NULLABLE")
            
        elif (string.upper(sSource) == "STRING"):
            arcpy.AddField_management(templateFeatures, fieldName, "TEXT", "", "", sSourceLength,fieldName, "NULLABLE")
                
        elif (string.upper(sSource) == "INTEGER"):
            arcpy.AddField_management(templateFeatures, fieldName, "LONG", 9, "", "", fieldName, "NULLABLE")
            
    # Add one more field: name of STATE
    arcpy.AddField_management(templateFeatures, "STATE", "TEXT", "", "", 24,"STATE", "NULLABLE")
                
        
except Exception as e:
    #pythonaddins.MessageBox("Error at inserting field: " + fieldName + "  " + e.message, 'Error', 0)
    fwAdded.write("Error at inserting field: " + fieldName + "  " + e.message + "\n")
    fwModified.close()
    fwAdded.close()
    fwResult.close()
    sys.exit()
    
                    
fwModified.close()
fwAdded.close()
fwResult.close()
